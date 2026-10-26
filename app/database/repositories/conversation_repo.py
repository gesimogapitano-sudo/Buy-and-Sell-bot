"""
Conversation repository — data access for messaging operations.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Conversation, Message
from app.utils.helpers import utc_now
from app.utils.security import generate_conversation_id

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation and message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Conversations ─────────────────────────────────────────────

    async def create(
        self,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            conversation_uid=generate_conversation_id(),
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            state="active",
        )
        self.session.add(conversation)
        await self.session.flush()
        logger.info(
            "Created conversation uid=%s for listing=%d",
            conversation.conversation_uid,
            listing_id,
        )
        return conversation

    async def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by internal ID."""
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.listing),
                selectinload(Conversation.buyer),
                selectinload(Conversation.seller),
            )
            .where(Conversation.id == conversation_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uid(self, conversation_uid: str) -> Optional[Conversation]:
        """Get a conversation by its unique identifier."""
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.listing),
                selectinload(Conversation.buyer),
                selectinload(Conversation.seller),
            )
            .where(Conversation.conversation_uid == conversation_uid)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_existing(
        self,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
    ) -> Optional[Conversation]:
        """Find an existing conversation between buyer and seller for a listing."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.listing_id == listing_id,
                Conversation.buyer_id == buyer_id,
                Conversation.seller_id == seller_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
    ) -> tuple[Conversation, bool]:
        """Get existing or create new conversation."""
        existing = await self.get_existing(listing_id, buyer_id, seller_id)
        if existing:
            return existing, False
        conversation = await self.create(listing_id, buyer_id, seller_id)
        return conversation, True

    async def get_user_conversations(
        self,
        user_id: int,
        role: Optional[str] = None,
        state: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[Conversation]:
        """Get conversations for a user (as buyer or seller)."""
        stmt = select(Conversation).options(
            selectinload(Conversation.listing),
            selectinload(Conversation.buyer),
            selectinload(Conversation.seller),
        )

        if role == "buyer":
            stmt = stmt.where(Conversation.buyer_id == user_id)
        elif role == "seller":
            stmt = stmt.where(Conversation.seller_id == user_id)
        else:
            stmt = stmt.where(
                or_(
                    Conversation.buyer_id == user_id,
                    Conversation.seller_id == user_id,
                )
            )

        if state:
            stmt = stmt.where(Conversation.state == state)

        stmt = stmt.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_conversation_count(
        self,
        user_id: int,
        state: Optional[str] = None,
    ) -> int:
        """Count conversations for a user."""
        stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(
                or_(
                    Conversation.buyer_id == user_id,
                    Conversation.seller_id == user_id,
                )
            )
        )
        if state:
            stmt = stmt.where(Conversation.state == state)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_state(
        self, conversation_id: int, state: str
    ) -> None:
        """Update conversation state."""
        values = {"state": state, "updated_at": utc_now()}
        if state in ("ended", "blocked"):
            values["ended_at"] = utc_now()
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(**values)
        )
        await self.session.execute(stmt)

    # ── Messages ──────────────────────────────────────────────────

    async def add_message(
        self,
        conversation_id: int,
        sender_id: int,
        direction: str,
        message_type: str = "text",
        content: Optional[str] = None,
        file_id: Optional[str] = None,
        file_name: Optional[str] = None,
        original_message_id: Optional[int] = None,
        delivery_status: str = "pending",
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            direction=direction,
            message_type=message_type,
            content=content,
            file_id=file_id,
            file_name=file_name,
            original_message_id=original_message_id,
            delivery_status=delivery_status,
        )
        self.session.add(message)
        await self.session.flush()

        # Update conversation timestamp
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=utc_now())
        )
        await self.session.execute(stmt)

        return message

    async def update_message_delivery(
        self,
        message_id: int,
        delivery_status: str,
        relayed_message_id: Optional[int] = None,
    ) -> None:
        """Update message delivery status."""
        values = {"delivery_status": delivery_status}
        if relayed_message_id:
            values["relayed_message_id"] = relayed_message_id
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(**values)
        )
        await self.session.execute(stmt)

    async def get_conversation_messages(
        self,
        conversation_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Message]:
        """Get messages for a conversation, ordered chronologically."""
        stmt = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_message_count(self, conversation_id: int) -> int:
        """Count messages in a conversation."""
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_recent_messages_by_user(
        self, user_id: int, seconds: int = 60
    ) -> int:
        """Count recent messages from a user (for rate limiting)."""
        from datetime import timedelta

        cutoff = utc_now() - timedelta(seconds=seconds)
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.sender_id == user_id,
                Message.created_at >= cutoff,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_duplicate_messages(
        self,
        user_id: int,
        content: str,
        seconds: int = 60,
    ) -> int:
        """Count duplicate messages from a user in a time window (spam detection)."""
        from datetime import timedelta

        cutoff = utc_now() - timedelta(seconds=seconds)
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.sender_id == user_id,
                Message.content == content,
                Message.created_at >= cutoff,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ── Admin: Search & Monitoring ────────────────────────────────

    async def search_conversations(
        self,
        listing_id: Optional[int] = None,
        conversation_uid: Optional[str] = None,
        participant_telegram_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[Conversation]:
        """Search conversations for admin monitoring."""
        from app.database.models import User

        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.listing),
                selectinload(Conversation.buyer),
                selectinload(Conversation.seller),
            )
        )

        conditions = []
        if listing_id:
            conditions.append(Conversation.listing_id == listing_id)
        if conversation_uid:
            conditions.append(Conversation.conversation_uid == conversation_uid)
        if participant_telegram_id:
            # Need a subquery to find user_id from telegram_id
            user_subq = select(User.id).where(
                User.telegram_id == participant_telegram_id
            ).scalar_subquery()
            conditions.append(
                or_(
                    Conversation.buyer_id == user_subq,
                    Conversation.seller_id == user_subq,
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_conversation_count(self) -> int:
        """Get total number of conversations."""
        stmt = select(func.count()).select_from(Conversation)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_total_message_count(self) -> int:
        """Get total number of messages."""
        stmt = select(func.count()).select_from(Message)
        result = await self.session.execute(stmt)
        return result.scalar_one()
