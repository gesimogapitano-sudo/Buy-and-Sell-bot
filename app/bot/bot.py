"""
Bot initialization module.

Creates and configures the aiogram Bot and Dispatcher instances.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """
    Create and configure the Telegram Bot instance.

    Returns:
        Configured aiogram Bot.
    """
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("Bot instance created for @%s", settings.bot_username)
    return bot


def create_dispatcher() -> Dispatcher:
    """
    Create and configure the Dispatcher with FSM storage.

    Returns:
        Configured aiogram Dispatcher.
    """
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("Dispatcher created with MemoryStorage.")
    return dp
