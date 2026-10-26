"""
Admin repository — data access for administrator operations.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    AdminAuditLog,
    Administrator,
    BotSetting,
    Category,
    User,
)
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)


class AdminRepository:
    """Repository for admin, audit, category, and settings operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Administrator Management ──────────────────────────────────

    async def get_admin_by_user_id(self, user_id: int) -> Optional[Administrator]:
        """Get admin record by user ID."""
        stmt = (
            select(Administrator)
            .options(selectinload(Administrator.user))
            .where(Administrator.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_admin_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[Administrator]:
        """Get admin record by Telegram user ID."""
        stmt = (
            select(Administrator)
            .join(User)
            .options(selectinload(Administrator.user))
            .where(User.telegram_id == telegram_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if a Telegram user is an active administrator."""
        admin = await self.get_admin_by_telegram_id(telegram_id)
        return admin is not None and admin.is_active

    async def is_superadmin(self, telegram_id: int) -> bool:
        """Check if a Telegram user is an active superadmin."""
        admin = await self.get_admin_by_telegram_id(telegram_id)
        return admin is not None and admin.is_active and admin.role == "superadmin"

    async def create_admin(
        self,
        user_id: int,
        role: str,
        created_by: Optional[int] = None,
    ) -> Administrator:
        """Create an administrator record."""
        admin = Administrator(
            user_id=user_id,
            role=role,
            is_active=True,
            created_by=created_by,
        )
        self.session.add(admin)
        await self.session.flush()
        logger.info("Created admin id=%d role=%s", admin.id, role)
        return admin

    async def update_admin_status(
        self, admin_id: int, is_active: bool
    ) -> None:
        """Activate or deactivate an administrator."""
        stmt = (
            update(Administrator)
            .where(Administrator.id == admin_id)
            .values(is_active=is_active, updated_at=utc_now())
        )
        await self.session.execute(stmt)

    async def update_admin_role(self, admin_id: int, role: str) -> None:
        """Update administrator role."""
        stmt = (
            update(Administrator)
            .where(Administrator.id == admin_id)
            .values(role=role, updated_at=utc_now())
        )
        await self.session.execute(stmt)

    async def get_all_admins(self) -> List[Administrator]:
        """Get all administrator records."""
        stmt = (
            select(Administrator)
            .options(selectinload(Administrator.user))
            .order_by(Administrator.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_moderator_telegram_ids(self) -> List[int]:
        """Get Telegram IDs of all active moderators and superadmins."""
        stmt = (
            select(User.telegram_id)
            .join(Administrator, Administrator.user_id == User.id)
            .where(Administrator.is_active == True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Audit Logs ────────────────────────────────────────────────

    async def log_action(
        self,
        administrator_id: int,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> AdminAuditLog:
        """Record an admin action in the audit log."""
        log = AdminAuditLog(
            administrator_id=administrator_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_audit_logs(
        self,
        administrator_id: Optional[int] = None,
        action: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[AdminAuditLog]:
        """Get audit log entries with optional filtering."""
        stmt = (
            select(AdminAuditLog)
            .options(selectinload(AdminAuditLog.administrator))
        )
        if administrator_id:
            stmt = stmt.where(AdminAuditLog.administrator_id == administrator_id)
        if action:
            stmt = stmt.where(AdminAuditLog.action == action)
        stmt = stmt.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Categories ────────────────────────────────────────────────

    async def get_active_categories(self) -> List[Category]:
        """Get all active categories, ordered."""
        stmt = (
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.sort_order.asc(), Category.name_en.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get a category by ID."""
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get a category by slug."""
        stmt = select(Category).where(Category.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_category(
        self,
        slug: str,
        name_en: str,
        name_am: str,
        sort_order: int = 0,
    ) -> Category:
        """Create a new category."""
        category = Category(
            slug=slug,
            name_en=name_en,
            name_am=name_am,
            sort_order=sort_order,
        )
        self.session.add(category)
        await self.session.flush()
        return category

    async def seed_default_categories(self) -> None:
        """Seed the database with default categories if none exist."""
        from app.utils.validators import DEFAULT_CATEGORIES

        existing = await self.get_active_categories()
        if existing:
            return

        for idx, (slug, names) in enumerate(DEFAULT_CATEGORIES.items()):
            await self.create_category(
                slug=slug,
                name_en=names["en"],
                name_am=names["am"],
                sort_order=idx * 10,
            )
        logger.info("Seeded %d default categories.", len(DEFAULT_CATEGORIES))

    # ── Bot Settings ──────────────────────────────────────────────

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a bot setting value by key."""
        stmt = select(BotSetting.value).where(BotSetting.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_setting(
        self,
        key: str,
        value: str,
        description: Optional[str] = None,
        updated_by: Optional[int] = None,
    ) -> None:
        """Set or update a bot setting."""
        existing = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        setting = existing.scalar_one_or_none()
        if setting:
            setting.value = value
            setting.updated_at = utc_now()
            if updated_by:
                setting.updated_by = updated_by
        else:
            setting = BotSetting(
                key=key,
                value=value,
                description=description,
                updated_by=updated_by,
            )
            self.session.add(setting)
        await self.session.flush()
