"""
Report repository — data access for reports and blocked users.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BlockedUser, Report
from app.utils.helpers import utc_now
from app.utils.security import generate_report_id

logger = logging.getLogger(__name__)


class ReportRepository:
    """Repository for report and block operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Reports ───────────────────────────────────────────────────

    async def create_report(
        self,
        reporter_id: int,
        reason: str,
        report_type: str,
        reported_user_id: Optional[int] = None,
        reported_listing_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Report:
        """Create a new report."""
        report = Report(
            report_uid=generate_report_id(),
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reported_listing_id=reported_listing_id,
            conversation_id=conversation_id,
            reason=reason,
            report_type=report_type,
            status="open",
        )
        self.session.add(report)
        await self.session.flush()
        logger.info("Created report uid=%s type=%s", report.report_uid, report_type)
        return report

    async def get_report_by_uid(self, report_uid: str) -> Optional[Report]:
        """Get a report by its unique identifier."""
        stmt = select(Report).where(Report.report_uid == report_uid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_reports(
        self, offset: int = 0, limit: int = 10
    ) -> List[Report]:
        """Get open reports for admin review."""
        stmt = (
            select(Report)
            .where(Report.status == "open")
            .order_by(Report.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_open_report_count(self) -> int:
        """Count open reports."""
        stmt = (
            select(func.count())
            .select_from(Report)
            .where(Report.status == "open")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def resolve_report(
        self,
        report_id: int,
        status: str,
        resolution: str,
        resolved_by: int,
    ) -> None:
        """Resolve a report."""
        stmt = (
            update(Report)
            .where(Report.id == report_id)
            .values(
                status=status,
                resolution=resolution,
                resolved_by=resolved_by,
                resolved_at=utc_now(),
            )
        )
        await self.session.execute(stmt)

    # ── Blocked Users ─────────────────────────────────────────────

    async def block_user(
        self,
        blocker_id: int,
        blocked_id: int,
        reason: Optional[str] = None,
    ) -> BlockedUser:
        """Block a user."""
        block = BlockedUser(
            blocker_id=blocker_id,
            blocked_id=blocked_id,
            reason=reason,
        )
        self.session.add(block)
        await self.session.flush()
        return block

    async def unblock_user(self, blocker_id: int, blocked_id: int) -> None:
        """Unblock a user."""
        from sqlalchemy import delete

        stmt = delete(BlockedUser).where(
            BlockedUser.blocker_id == blocker_id,
            BlockedUser.blocked_id == blocked_id,
        )
        await self.session.execute(stmt)

    async def is_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        """Check if a user has blocked another user."""
        stmt = (
            select(func.count())
            .select_from(BlockedUser)
            .where(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_id == blocked_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def is_blocked_either_direction(
        self, user_id_1: int, user_id_2: int
    ) -> bool:
        """Check if either user has blocked the other."""
        from sqlalchemy import or_, and_

        stmt = (
            select(func.count())
            .select_from(BlockedUser)
            .where(
                or_(
                    and_(
                        BlockedUser.blocker_id == user_id_1,
                        BlockedUser.blocked_id == user_id_2,
                    ),
                    and_(
                        BlockedUser.blocker_id == user_id_2,
                        BlockedUser.blocked_id == user_id_1,
                    ),
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
