"""
Shared helper utilities for the Buy & Sell Bot.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_price(price: Decimal, currency: str) -> str:
    """
    Format a price with currency for display.

    Args:
        price: Price value.
        currency: Currency code (e.g., "ETB").

    Returns:
        Formatted string like "15,000.00 ETB".
    """
    formatted = f"{price:,.2f}"
    return f"{formatted} {currency}"


def format_datetime(dt: Optional[datetime], include_time: bool = True) -> str:
    """
    Format a datetime for display.

    Args:
        dt: Datetime to format.
        include_time: Whether to include time component.

    Returns:
        Human-readable date/time string.
    """
    if dt is None:
        return "N/A"
    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    return dt.strftime("%Y-%m-%d")


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_listing_status(status: str) -> str:
    """
    Format listing status with emoji for display.

    Args:
        status: Listing status string.

    Returns:
        Emoji + status text.
    """
    status_emojis = {
        "draft": "📝 Draft",
        "pending": "⏳ Pending Review",
        "approved": "✅ Approved",
        "published": "📢 Published",
        "rejected": "❌ Rejected",
        "changes_requested": "🔄 Changes Requested",
        "sold": "🏷️ Sold",
        "withdrawn": "↩️ Withdrawn",
        "removed": "🚫 Removed",
    }
    return status_emojis.get(status, f"❓ {status}")


def format_condition(condition: Optional[str]) -> str:
    """
    Format item condition for display.

    Args:
        condition: Condition string.

    Returns:
        Human-readable condition text.
    """
    if not condition:
        return "N/A"
    conditions = {
        "new": "✨ New",
        "like_new": "🌟 Like New",
        "used": "👍 Used",
        "refurbished": "🔧 Refurbished",
    }
    return conditions.get(condition, condition)


def get_deep_link_payload(listing_token: str) -> str:
    """
    Create the deep link start parameter for a listing.

    Args:
        listing_token: The listing's public token.

    Returns:
        Start parameter string.
    """
    return f"listing_{listing_token}"


def parse_deep_link_payload(start_param: str) -> Optional[str]:
    """
    Parse a listing token from a deep link start parameter.

    Args:
        start_param: The /start command parameter.

    Returns:
        The listing token, or None if the format is invalid.
    """
    prefix = "listing_"
    if start_param and start_param.startswith(prefix):
        token = start_param[len(prefix):]
        if token:
            return token
    return None


def safe_log_user(user_id: int) -> str:
    """
    Create a safe representation of a user ID for logging.

    Does not expose the full numeric ID.

    Args:
        user_id: Telegram user ID.

    Returns:
        A partially masked string.
    """
    user_str = str(user_id)
    if len(user_str) <= 4:
        return "***"
    return f"{user_str[:2]}...{user_str[-2:]}"
