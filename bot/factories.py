from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from redis.asyncio import ConnectionPool, Redis

from bot.enums import Locale
from bot.handlers import admin, common, extra
from bot.middlewares import (
    DBSessionMiddleware,
    QueryMiddleware,
    RetryRequestMiddleware,
    StateControlMiddleware,
    UserManager,
    UserMiddleware,
)
from services.database.create_pool import create_pool
from utils import mjson

if TYPE_CHECKING:
    from bot.settings import Settings


def _setup_outer_middlewares(
    dispatcher: Dispatcher, settings: Settings
) -> None:
    pool = dispatcher["session_pool"] = create_pool(
        dsn=settings.postgres.build_dsn(),
        enable_logging=settings.sqlalchemy_logging,
    )
    i18n_middleware = dispatcher["i18n_middleware"] = I18nMiddleware(
        core=FluentRuntimeCore(
            path="lang/{locale}",
            raise_key_error=False,
            locales_map={Locale.RU: Locale.US},
        ),
        manager=UserManager(),
        default_locale=Locale.DEFAULT,
    )

    dispatcher.update.outer_middleware(DBSessionMiddleware(session_pool=pool))
    dispatcher.update.outer_middleware(UserMiddleware())
    dispatcher.update.outer_middleware(QueryMiddleware())
    dispatcher.update.outer_middleware(StateControlMiddleware())
    i18n_middleware.setup(dispatcher=dispatcher)


def _setup_inner_middlewares(dispatcher: Dispatcher) -> None:
    dispatcher.callback_query.middleware(CallbackAnswerMiddleware())


def create_dispatcher(settings: Settings) -> Dispatcher:
    """
    :return: Configured ``Dispatcher`` with
    installed middlewares and included routers
    """
    redis: Redis = Redis(
        connection_pool=ConnectionPool(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            username=settings.redis.user,
            password=settings.redis.password.get_secret_value(),
        )
    )

    dispatcher: Dispatcher = Dispatcher(
        name="main_dispatcher",
        storage=RedisStorage(
            redis=redis, json_loads=mjson.decode, json_dumps=mjson.encode
        ),
        redis=redis,
        settings=settings,
    )
    dispatcher.include_routers(admin.router, common.router, extra.router)
    _setup_outer_middlewares(dispatcher, settings)
    _setup_inner_middlewares(dispatcher)
    return dispatcher


def create_bot(settings: Settings) -> Bot:
    """
    :return: Configured ``Bot`` with retry request middleware
    """
    session: AiohttpSession = AiohttpSession(
        json_loads=mjson.decode, json_dumps=mjson.encode
    )
    session.middleware(RetryRequestMiddleware())
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
        session=session,
    )
