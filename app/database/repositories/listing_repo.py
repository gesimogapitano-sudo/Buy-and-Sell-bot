"""
Listing repository — data access for listing operations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    Listing,
    ListingMedia,
    ListingStatusHistory,
)
from app.utils.helpers import utc_now
from app.utils.security import generate_listing_token

logger = logging.getLogger(__name__)


class ListingRepository:
    """Repository for listing CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        seller_id: int,
        category_id: int,
        listing_type: str,
        title: str,
        description: str,
        price: Decimal,
        currency: str,
        location: str,
        brand: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> Listing:
        """Create a new listing in draft status."""
        listing = Listing(
            seller_id=seller_id,
            category_id=category_id,
            listing_type=listing_type,
            public_token=generate_listing_token(),
            title=title,
            description=description,
            brand=brand,
            price=price,
            currency=currency,
            location=location,
            condition=condition,
            status="draft",
        )
        self.session.add(listing)
        await self.session.flush()

        # Record initial status
        history = ListingStatusHistory(
            listing_id=listing.id,
            old_status=None,
            new_status="draft",
            actor_id=seller_id,
        )
        self.session.add(history)
        await self.session.flush()

        logger.info("Created listing id=%d type=%s", listing.id, listing_type)
        return listing

    async def get_by_id(self, listing_id: int) -> Optional[Listing]:
        """Get a listing by internal ID with media loaded."""
        stmt = (
            select(Listing)
            .options(selectinload(Listing.media))
            .where(Listing.id == listing_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Optional[Listing]:
        """Get a listing by its public token with media loaded."""
        stmt = (
            select(Listing)
            .options(selectinload(Listing.media))
            .where(Listing.public_token == token)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_seller_listings(
        self,
        seller_id: int,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[Listing]:
        """Get listings for a specific seller."""
        stmt = (
            select(Listing)
            .options(selectinload(Listing.media))
            .where(Listing.seller_id == seller_id)
        )
        if status:
            stmt = stmt.where(Listing.status == status)
        stmt = stmt.order_by(Listing.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_seller_listing_count(
        self, seller_id: int, status: Optional[str] = None
    ) -> int:
        """Count listings for a specific seller."""
        stmt = (
            select(func.count())
            .select_from(Listing)
            .where(Listing.seller_id == seller_id)
        )
        if status:
            stmt = stmt.where(Listing.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_listing_count(self, seller_id: int) -> int:
        """Count active (non-terminal) listings for a seller."""
        active_statuses = ["draft", "pending", "approved", "published", "changes_requested"]
        stmt = (
            select(func.count())
            .select_from(Listing)
            .where(
                Listing.seller_id == seller_id,
                Listing.status.in_(active_statuses),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_pending_listings(
        self, offset: int = 0, limit: int = 10
    ) -> List[Listing]:
        """Get listings pending admin review."""
        stmt = (
            select(Listing)
            .options(selectinload(Listing.media), selectinload(Listing.seller))
            .where(Listing.status == "pending")
            .order_by(Listing.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_count(self) -> int:
        """Count pending listings."""
        stmt = (
            select(func.count())
            .select_from(Listing)
            .where(Listing.status == "pending")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_status(
        self,
        listing_id: int,
        new_status: str,
        actor_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Optional[Listing]:
        """Update listing status and record history."""
        listing = await self.get_by_id(listing_id)
        if not listing:
            return None

        old_status = listing.status

        # Record history
        history = ListingStatusHistory(
            listing_id=listing_id,
            old_status=old_status,
            new_status=new_status,
            actor_id=actor_id,
            reason=reason,
        )
        self.session.add(history)

        # Update listing
        listing.status = new_status
        listing.updated_at = utc_now()

        if new_status == "published":
            listing.published_at = utc_now()

        await self.session.flush()
        logger.info(
            "Listing %d status: %s → %s",
            listing_id, old_status, new_status,
        )
        return listing

    async def set_channel_message(
        self,
        listing_id: int,
        channel_message_id: int,
        channel_id: str,
    ) -> None:
        """Store the Telegram channel message ID after publication."""
        stmt = (
            update(Listing)
            .where(Listing.id == listing_id)
            .values(
                channel_message_id=channel_message_id,
                channel_id=channel_id,
                updated_at=utc_now(),
            )
        )
        await self.session.execute(stmt)

    async def add_media(
        self,
        listing_id: int,
        file_id: str,
        file_unique_id: str,
        media_type: str = "photo",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        sort_order: int = 0,
    ) -> ListingMedia:
        """Add a media file to a listing."""
        media = ListingMedia(
            listing_id=listing_id,
            file_id=file_id,
            file_unique_id=file_unique_id,
            media_type=media_type,
            file_name=file_name,
            file_size=file_size,
            sort_order=sort_order,
        )
        self.session.add(media)
        await self.session.flush()
        return media

    async def get_media_count(self, listing_id: int) -> int:
        """Count media files for a listing."""
        stmt = (
            select(func.count())
            .select_from(ListingMedia)
            .where(ListingMedia.listing_id == listing_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_media(self, listing_id: int) -> None:
        """Delete all media for a listing."""
        from sqlalchemy import delete

        stmt = delete(ListingMedia).where(ListingMedia.listing_id == listing_id)
        await self.session.execute(stmt)

    async def update_fields(
        self,
        listing_id: int,
        **kwargs,
    ) -> Optional[Listing]:
        """Update specific listing fields."""
        kwargs["updated_at"] = utc_now()
        stmt = (
            update(Listing)
            .where(Listing.id == listing_id)
            .values(**kwargs)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(listing_id)

    async def get_total_listing_count(self, status: Optional[str] = None) -> int:
        """Get total listing count, optionally filtered by status."""
        stmt = select(func.count()).select_from(Listing)
        if status:
            stmt = stmt.where(Listing.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_listings_submitted_recently(
        self, seller_id: int, hours: int = 1
    ) -> int:
        """Count listings submitted by a seller in the last N hours."""
        from datetime import timedelta
        cutoff = utc_now() - timedelta(hours=hours)
        stmt = (
            select(func.count())
            .select_from(Listing)
            .where(
                Listing.seller_id == seller_id,
                Listing.created_at >= cutoff,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
