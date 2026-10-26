"""
Bot middleware for authentication, rate limiting, database sessions, and logging.

Middleware runs on every incoming update before handlers.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.config import get_settings
from app.database.engine import get_session_factory
from app.database.repositories.user_repo import UserRepository
from app.utils.helpers import safe_log_user

logger = logging.getLogger(__name__)


class DatabaseSessionMiddleware(BaseMiddleware):
    """
    Middleware that provides a database session for each update.

    Injects an AsyncSession into handler data as 'session'.
    Commits on success, rolls back on error.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        factory = get_session_factory()
        async with factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class UserRegistrationMiddleware(BaseMiddleware):
    """
    Middleware that ensures every Telegram user has a database record.

    Injects the User model into handler data as 'db_user'.
    Also checks if the user is suspended.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user from the event
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user and not user.is_bot:
            session = data.get("session")
            if session:
                settings = get_settings()
                repo = UserRepository(session)
                db_user, created = await repo.get_or_create(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language=settings.default_language,
                )
                data["db_user"] = db_user

                # Check suspended status
                if db_user.status == "suspended":
                    if isinstance(event, Message):
                        await event.answer(
                            "⚠️ Your account has been suspended. "
                            "Contact support for assistance."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "Your account has been suspended.",
                            show_alert=True,
                        )
                    return  # Block further processing

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """
    Per-user message rate limiting middleware.

    Tracks message timestamps per user and blocks excessive requests.
    Uses an in-memory sliding window approach.
    """

    def __init__(self):
        self._user_timestamps: Dict[int, list] = defaultdict(list)
        self._cleanup_counter = 0

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            settings = get_settings()
            now = time.time()
            window = 60.0  # 1 minute window
            user_id = user.id

            # Clean old timestamps
            self._user_timestamps[user_id] = [
                ts for ts in self._user_timestamps[user_id]
                if now - ts < window
            ]

            if len(self._user_timestamps[user_id]) >= settings.message_rate_limit:
                logger.warning(
                    "Rate limit exceeded for user %s", safe_log_user(user_id)
                )
                if isinstance(event, Message):
                    await event.answer(
                        "⏳ You're sending messages too quickly. "
                        "Please wait a moment and try again."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "Please wait a moment before trying again.",
                        show_alert=True,
                    )
                return  # Block

            self._user_timestamps[user_id].append(now)

            # Periodic cleanup of inactive users
            self._cleanup_counter += 1
            if self._cleanup_counter >= 100:
                self._cleanup_counter = 0
                self._cleanup_old_entries(now, window)

        return await handler(event, data)

    def _cleanup_old_entries(self, now: float, window: float) -> None:
        """Remove entries for users who haven't sent messages recently."""
        to_remove = []
        for uid, timestamps in self._user_timestamps.items():
            if not timestamps or now - timestamps[-1] > window * 5:
                to_remove.append(uid)
        for uid in to_remove:
            del self._user_timestamps[uid]


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware that logs incoming updates for debugging.

    Redacts sensitive information from logs.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.time()

        user_info = "unknown"
        event_type = type(event).__name__

        if isinstance(event, Message) and event.from_user:
            user_info = safe_log_user(event.from_user.id)
            event_type = f"Message({event.content_type})"
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_info = safe_log_user(event.from_user.id)
            event_type = f"Callback({event.data[:30] if event.data else 'none'})"

        logger.debug("→ %s from user %s", event_type, user_info)

        try:
            result = await handler(event, data)
            elapsed = (time.time() - start_time) * 1000
            logger.debug(
                "← %s handled in %.1fms", event_type, elapsed
            )
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                "✗ %s from %s failed after %.1fms: %s",
                event_type, user_info, elapsed, str(e),
                exc_info=True,
            )
            raise
