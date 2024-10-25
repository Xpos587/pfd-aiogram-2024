from aiogram import Bot, Dispatcher

from bot.factories import create_bot, create_dispatcher
from bot.runners import run_polling, run_webhook
from bot.settings import settings
from utils.loggers import setup_logger


def main() -> None:
    setup_logger()
    dispatcher: Dispatcher = create_dispatcher(settings=settings)
    bot: Bot = create_bot(settings=settings)
    if settings.webhook.use:
        return run_webhook(dispatcher=dispatcher, bot=bot)
    return run_polling(dispatcher=dispatcher, bot=bot)


if __name__ == "__main__":
    main()
