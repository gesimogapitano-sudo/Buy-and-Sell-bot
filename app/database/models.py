"""
SQLAlchemy 2.x database models for the Buy & Sell Marketplace Bot.

All tables use:
- Foreign keys with appropriate ON DELETE behavior
- Indexes on frequently queried columns
- UTC timestamps
- Decimal for prices (no floating-point)
- Enum-like string columns for status fields
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class User(Base):
    """
    Telegram user profile for the marketplace.

    Stores preferences, consent state, and account status.
    Does NOT store phone numbers or contact lists.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, suspended, deleted
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    administrator: Mapped[Optional["Administrator"]] = relationship(
        back_populates="user", uselist=False
    )
    listings: Mapped[List["Listing"]] = relationship(
        back_populates="seller", foreign_keys="Listing.seller_id"
    )
    consent_records: Mapped[List["ConsentRecord"]] = relationship(back_populates="user")
    reports_filed: Mapped[List["Report"]] = relationship(
        back_populates="reporter", foreign_keys="Report.reporter_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg_id={self.telegram_id} status={self.status}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMINISTRATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Administrator(Base):
    """
    Administrator record linked to a user.

    Supports two roles: superadmin and moderator.
    The first superadmin is configured via environment variable.
    """
    __tablename__ = "administrators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # superadmin, moderator
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="administrator", foreign_keys=[user_id]
    )
    audit_logs: Mapped[List["AdminAuditLog"]] = relationship(back_populates="administrator")

    def __repr__(self) -> str:
        return f"<Administrator id={self.id} role={self.role} active={self.is_active}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CATEGORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Category(Base):
    """
    Listing category with localized names.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_am: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    listings: Mapped[List["Listing"]] = relationship(back_populates="category")

    def get_name(self, language: str = "en") -> str:
        """Get category name in the requested language."""
        if language == "am":
            return self.name_am
        return self.name_en

    def __repr__(self) -> str:
        return f"<Category id={self.id} slug={self.slug}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LISTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Listing(Base):
    """
    Marketplace listing for a product or service.

    Lifecycle: draft → pending → approved → published → sold
    Additional states: rejected, changes_requested, withdrawn, removed
    """
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    public_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Listing type
    listing_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # product, service

    # Core fields
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pricing — Decimal for precision
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(5), nullable=False, default="ETB")

    # Location and condition
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    condition: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # new, like_new, used, refurbished (products only)

    # Status management
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", index=True
    )

    # Publication tracking
    channel_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    seller: Mapped["User"] = relationship(back_populates="listings", foreign_keys=[seller_id])
    category: Mapped["Category"] = relationship(back_populates="listings")
    media: Mapped[List["ListingMedia"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan",
        order_by="ListingMedia.sort_order"
    )
    status_history: Mapped[List["ListingStatusHistory"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan",
        order_by="ListingStatusHistory.created_at"
    )
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="listing")
    moderation_results: Mapped[List["ModerationResult"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_listings_seller_status", "seller_id", "status"),
        Index("ix_listings_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Listing id={self.id} type={self.listing_type} status={self.status}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LISTING MEDIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ListingMedia(Base):
    """
    Media files attached to a listing.

    Uses Telegram file IDs to avoid storing binaries.
    """
    __tablename__ = "listing_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(String(512), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(256), nullable=False)
    media_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="photo"
    )  # photo, document, video
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(back_populates="media")

    def __repr__(self) -> str:
        return f"<ListingMedia id={self.id} type={self.media_type} order={self.sort_order}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LISTING STATUS HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ListingStatusHistory(Base):
    """
    Tracks listing status transitions with actor and reason.
    """
    __tablename__ = "listing_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(back_populates="status_history")
    actor: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return (
            f"<ListingStatusHistory listing={self.listing_id} "
            f"{self.old_status}→{self.new_status}>"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVERSATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Conversation(Base):
    """
    Private buyer-seller conversation about a listing.

    Each conversation is uniquely associated with a listing, buyer, and seller.
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_uid: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    buyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, ended, blocked, reported
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(back_populates="conversations")
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    __table_args__ = (
        UniqueConstraint("listing_id", "buyer_id", "seller_id", name="uq_conversation_participants"),
        Index("ix_conversations_buyer", "buyer_id", "state"),
        Index("ix_conversations_seller", "seller_id", "state"),
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} uid={self.conversation_uid} state={self.state}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Message(Base):
    """
    A message within a buyer-seller conversation.

    Stores content, direction, delivery status, and Telegram message IDs
    for both the original and relayed copies.
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # buyer_to_seller, seller_to_buyer

    # Message content
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="text"
    )  # text, photo, document, video
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Telegram message IDs for tracking
    original_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    relayed_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Delivery tracking
    delivery_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, delivered, failed, blocked

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped[Optional["User"]] = relationship()

    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} direction={self.direction} "
            f"type={self.message_type} status={self.delivery_status}>"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Report(Base):
    """
    User reports for suspicious listings, sellers, or abusive behavior.
    """
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_uid: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    reporter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reported_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reported_listing_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # scam, spam, abuse, inappropriate, other

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open, investigating, resolved, dismissed
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    reporter: Mapped[Optional["User"]] = relationship(
        foreign_keys=[reporter_id], back_populates="reports_filed"
    )
    reported_user: Mapped[Optional["User"]] = relationship(foreign_keys=[reported_user_id])
    reported_listing: Mapped[Optional["Listing"]] = relationship()
    conversation: Mapped[Optional["Conversation"]] = relationship()

    def __repr__(self) -> str:
        return f"<Report id={self.id} type={self.report_type} status={self.status}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODERATION RESULTS (AI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ModerationResult(Base):
    """
    AI-generated moderation flags for listings.
    """
    __tablename__ = "moderation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # scam, prohibited, spam, impersonation, suspicious, safe
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 0-100
    recommended_action: Mapped[str] = mapped_column(
        String(30), nullable=False, default="review"
    )  # approve, review, reject, flag
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, acknowledged, overridden
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(back_populates="moderation_results")

    def __repr__(self) -> str:
        return (
            f"<ModerationResult listing={self.listing_id} "
            f"risk={self.risk_category} score={self.severity_score}>"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSENT RECORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ConsentRecord(Base):
    """
    Record of user consent acknowledgement.

    Tracks which version of the privacy notice was acknowledged.
    """
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notice_version: Mapped[int] = mapped_column(Integer, nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="consent_records")

    __table_args__ = (
        UniqueConstraint("user_id", "notice_version", name="uq_consent_user_version"),
    )

    def __repr__(self) -> str:
        return f"<ConsentRecord user={self.user_id} version={self.notice_version}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN AUDIT LOGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AdminAuditLog(Base):
    """
    Audit trail for administrative actions.

    Records who did what, when, and to which target.
    """
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    administrator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("administrators.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # approve_listing, reject_listing, suspend_user, etc.
    target_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )  # listing, user, conversation, report
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    administrator: Mapped[Optional["Administrator"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_action_created", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AdminAuditLog admin={self.administrator_id} "
            f"action={self.action} target={self.target_type}:{self.target_id}>"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BLOCKED USERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class BlockedUser(Base):
    """
    User blocking relationship.

    A user can block another user to prevent further communication.
    """
    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    blocked_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    blocker: Mapped["User"] = relationship(foreign_keys=[blocker_id])
    blocked: Mapped["User"] = relationship(foreign_keys=[blocked_id])

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
        Index("ix_blocked_users_blocker", "blocker_id"),
        Index("ix_blocked_users_blocked", "blocked_id"),
    )

    def __repr__(self) -> str:
        return f"<BlockedUser blocker={self.blocker_id} blocked={self.blocked_id}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOT SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class BotSetting(Base):
    """
    Configurable non-secret operational settings stored in the database.

    For settings that admins can change at runtime without redeployment.
    """
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<BotSetting key={self.key}>"
