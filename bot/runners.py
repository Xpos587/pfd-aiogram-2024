from __future__ import annotations

from aiogram import Bot, Dispatcher, loggers
from aiogram.webhook import aiohttp_server as server
from aiohttp import web

from bot.settings import settings
from utils.loggers import MultilineLogger


async def polling_startup(bots: list[Bot]) -> None:
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=settings.drop_pending_updates)
    if settings.drop_pending_updates:
        loggers.dispatcher.info("Updates skipped successfully")


async def webhook_startup(dispatcher: Dispatcher, bot: Bot) -> None:
    url: str = settings.webhook.build_url()
    if await bot.set_webhook(
        url=url,
        allowed_updates=dispatcher.resolve_used_update_types(),
        secret_token=settings.webhook.secret_token.get_secret_value(),
        drop_pending_updates=settings.drop_pending_updates,
    ):
        return loggers.webhook.info(
            "Main bot webhook successfully set on url '%s'", url
        )
    return loggers.webhook.error("Failed to set main bot webhook on url '%s'", url)


async def webhook_shutdown(bot: Bot) -> None:
    if not settings.webhook.reset:
        return
    if await bot.delete_webhook():
        loggers.webhook.info("Dropped main bot webhook.")
    else:
        loggers.webhook.error("Failed to drop main bot webhook.")
    await bot.session.close()


def run_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher.startup.register(polling_startup)
    return dispatcher.run_polling(bot)


def run_webhook(dispatcher: Dispatcher, bot: Bot) -> None:
    app = web.Application()
    server.SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.webhook.secret_token.get_secret_value(),
    ).register(app, path=settings.webhook.path)
    server.setup_application(
        app, dispatcher, bot=bot, reset_webhook=settings.webhook.reset
    )
    app.update(**dispatcher.workflow_data, bot=bot)

    dispatcher.startup.register(webhook_startup)
    dispatcher.shutdown.register(webhook_shutdown)

    return web.run_app(
        app=app,
        host=settings.webhook.host,
        port=settings.webhook.port,
        print=MultilineLogger(),
    )
