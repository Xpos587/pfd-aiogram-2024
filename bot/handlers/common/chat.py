import logging
from typing import Any, Final
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
import orjson

from bot.filters import ChatStates
from bot.keyboards import Button, common_keyboard
from bot.filters import CallbackData as cbd
from services.database import Repository
from services.qna import ask_question_with_memory, Answer

logger = logging.getLogger(__name__)
router: Final[Router] = Router(name=__name__)


async def format_response(answer: Answer, i18n: I18nContext) -> str:
    """Format the RAG response with i18n support."""
    response_parts = []

    # Добавляем краткий ответ без дополнительного форматирования
    response_parts.append(answer.brief_answer)

    # Добавляем подробный ответ, если он есть
    if answer.detailed_answer:
        response_parts.append(f"\n📝 {answer.detailed_answer}")

    # Добавляем источники, если они есть
    if answer.source_references:
        response_parts.append("\n📚 Источники:")
        for ref in answer.source_references:
            response_parts.append(
                f"• Раздел {ref.section} ({ref.relevance})\n  {
                    ref.exact_quote}"
            )

    # Добавляем шаги рассуждения, если они есть
    if answer.thinking_steps:
        response_parts.append("\n🤔 Ход рассуждения:")
        for step in answer.thinking_steps:
            response_parts.append(
                f"• {step.reasoning}\n  Вывод: {step.conclusion}"
            )

    return "\n".join(filter(None, response_parts))


async def process_question(
    question: str,
    message: Message,
    i18n: I18nContext,
    state: FSMContext,
    repository: Repository,
) -> Any:
    """Process the question and generate answer."""
    thinking_msg = await message.answer(i18n.msg.thinking())

    try:
        # Get response from RAG system
        answer = await ask_question_with_memory(question)

        # Format the response
        response_text = await format_response(answer, i18n)

        await thinking_msg.delete()

        # Create feedback entry
        feedback = await repository.feedback.create_feedback(
            user=message.from_user.id,
            question=question,
            answer=response_text,
            checklist=orjson.dumps(
                answer.checklist.model_dump(), option=orjson.OPT_INDENT_2
            ).decode("utf-8"),
        )

        # Send response with feedback buttons
        return await message.answer(
            text=response_text + "\n\n" + i18n.feedback.question(),
            reply_markup=common_keyboard(
                rows=[
                    (
                        Button(
                            i18n.btn.like(),
                            callback_data=cbd.like.extend(feedback.id),
                        ),
                        Button(
                            i18n.btn.dislike(),
                            callback_data=cbd.dislike.extend(feedback.id),
                        ),
                    ),
                    Button(i18n.btn.back(), callback_data=cbd.main),
                ]
            ),
        )

    except Exception as e:
        logger.error(f"Error in process_question: {str(e)}")
        await thinking_msg.delete()
        return await message.answer(
            text=i18n.msg.error(),
            reply_markup=common_keyboard(
                rows=[Button(i18n.btn.back(), callback_data=cbd.main)]
            ),
        )


@router.message(ChatStates.AwaitingQuestion, F.text)
async def handle_question(
    message: Message,
    i18n: I18nContext,
    state: FSMContext,
    repository: Repository,
) -> Any:
    data = await state.get_data()
    if data.get("is_processing"):
        return await message.answer(i18n.msg.busy())

    await state.update_data(is_processing=True)

    try:
        return await process_question(
            message.text, message, i18n, state, repository
        )
    except Exception as e:
        logger.error(f"Error handling question: {str(e)}")
        return await message.answer(
            text=i18n.msg.error(),
            reply_markup=common_keyboard(
                rows=[
                    Button(i18n.btn.back(), callback_data=cbd.main)
                ]  # Изменено с cbd.back на cbd.main
            ),
        )
    finally:
        await state.update_data(is_processing=False)


@router.callback_query(cbd.ask)
async def start_chat(
    callback: CallbackQuery, i18n: I18nContext, state: FSMContext
) -> Any:
    """Start chat session."""
    await state.set_state(ChatStates.AwaitingQuestion)
    return await callback.message.edit_text(
        text=i18n.msg.ask(),
        reply_markup=common_keyboard(
            rows=[
                Button(i18n.btn.back(), callback_data=cbd.main)
            ]  # Изменено с cbd.back на cbd.main
        ),
    )


@router.callback_query(cbd.like)
async def handle_like(
    query: CallbackQuery,
    i18n: I18nContext,
    repository: Repository,
) -> Any:
    """Handle positive feedback."""
    try:
        feedback_id = int(query.data.split(":", 1)[1])
        await repository.feedback.set_rating(feedback_id, True)
        await query.answer(i18n.feedback.like(), show_alert=True)

        new_markup = common_keyboard(
            rows=[
                (Button("👍", callback_data="none"),),
                Button(i18n.btn.back(), callback_data=cbd.main),
            ]
        )
        await query.message.edit_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.error(f"Error handling like feedback: {str(e)}")
        await query.answer(i18n.msg.error(), show_alert=True)


@router.callback_query(cbd.dislike)
async def handle_dislike(
    query: CallbackQuery,
    i18n: I18nContext,
    repository: Repository,
) -> Any:
    """Handle negative feedback."""
    try:
        feedback_id = int(query.data.split(":", 1)[1])
        await repository.feedback.set_rating(feedback_id, False)
        await query.answer(i18n.feedback.dislike(), show_alert=True)

        new_markup = common_keyboard(
            rows=[
                (Button("👎", callback_data="none"),),
                Button(i18n.btn.back(), callback_data=cbd.main),
            ]
        )
        await query.message.edit_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.error(f"Error handling dislike feedback: {str(e)}")
        await query.answer(i18n.msg.error(), show_alert=True)
