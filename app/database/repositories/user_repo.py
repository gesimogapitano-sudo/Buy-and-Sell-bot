"""
User repository — data access for user-related operations.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Administrator, ConsentRecord, User
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Find a user by their Telegram user ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by their internal database ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "en",
    ) -> User:
        """Create a new user record."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            status="active",
            consent_given=False,
        )
        self.session.add(user)
        await self.session.flush()
        logger.info("Created user id=%d for telegram_id (hashed).", user.id)
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "en",
    ) -> tuple[User, bool]:
        """
        Get an existing user or create a new one.

        Returns:
            Tuple of (user, created) where created is True if a new user was created.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Update profile info if changed
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if last_name is not None and user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if changed:
                await self.session.flush()
            return user, False

        user = await self.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
        )
        return user, True

    async def update_language(self, user_id: int, language: str) -> None:
        """Update user's preferred language."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(language=language, updated_at=utc_now())
        )
        await self.session.execute(stmt)

    async def update_consent(
        self, user_id: int, consent_version: int
    ) -> None:
        """Record user consent acknowledgement."""
        # Update user record
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                consent_given=True,
                consent_version=consent_version,
                updated_at=utc_now(),
            )
        )
        await self.session.execute(stmt)

        # Create consent record
        record = ConsentRecord(
            user_id=user_id,
            notice_version=consent_version,
        )
        self.session.add(record)
        await self.session.flush()

    async def update_status(self, user_id: int, status: str) -> None:
        """Update user account status."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(status=status, updated_at=utc_now())
        )
        await self.session.execute(stmt)

    async def get_user_count(self) -> int:
        """Get total number of registered users."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_user_count(self) -> int:
        """Get number of active users."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.status == "active")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
