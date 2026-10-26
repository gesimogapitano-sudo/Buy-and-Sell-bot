"""
Security utilities for the Buy & Sell Bot.

Provides cryptographically secure token generation, HTML escaping,
and input sanitization.
"""

from __future__ import annotations

import hashlib
import html
import re
import secrets
import string
from typing import Optional


def generate_listing_token(length: int = 16) -> str:
    """
    Generate a cryptographically random, URL-safe listing token.

    These tokens are used in deep links so that internal database IDs
    are never exposed to users.

    Args:
        length: Number of random bytes (output will be longer due to base64).

    Returns:
        A URL-safe, non-guessable token string.
    """
    return secrets.token_urlsafe(length)


def generate_conversation_id() -> str:
    """
    Generate a unique conversation identifier.

    Returns:
        A short, unique conversation ID string.
    """
    return f"conv_{secrets.token_urlsafe(12)}"


def generate_report_id() -> str:
    """
    Generate a unique report identifier.

    Returns:
        A short, unique report ID string.
    """
    return f"rpt_{secrets.token_urlsafe(8)}"


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for safe display in Telegram messages.

    Telegram supports a subset of HTML. This ensures user-supplied text
    doesn't break message formatting or inject markup.

    Args:
        text: Raw text to escape.

    Returns:
        HTML-escaped text safe for Telegram.
    """
    return html.escape(text, quote=False)


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 parse mode.

    Args:
        text: Raw text to escape.

    Returns:
        MarkdownV2-escaped text.
    """
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


def sanitize_text_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user text input.

    Strips leading/trailing whitespace, normalizes internal whitespace,
    and enforces maximum length.

    Args:
        text: Raw user input.
        max_length: Maximum allowed length.

    Returns:
        Cleaned text.
    """
    # Strip and normalize whitespace
    text = text.strip()
    # Remove null bytes and other control characters (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    return text


def is_valid_telegram_id(user_id: int) -> bool:
    """
    Check if a value looks like a valid Telegram user ID.

    Args:
        user_id: The ID to validate.

    Returns:
        True if the ID is a positive integer in the expected range.
    """
    return isinstance(user_id, int) and 0 < user_id < 10**15


def hash_user_id(user_id: int) -> str:
    """
    Create a one-way hash of a user ID for logging purposes.

    This allows tracking user activity in logs without exposing
    the actual Telegram user ID.

    Args:
        user_id: Telegram user ID.

    Returns:
        A short hash string.
    """
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:12]


def redact_token(token: str) -> str:
    """
    Redact a token for safe logging.

    Shows only the first and last few characters.

    Args:
        token: Token to redact.

    Returns:
        Redacted string safe for logging.
    """
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def validate_callback_data(data: str, expected_prefix: str) -> Optional[str]:
    """
    Validate and extract payload from callback data.

    Ensures callback data starts with the expected prefix and
    contains only safe characters.

    Args:
        data: Raw callback data string.
        expected_prefix: Expected prefix (e.g., "approve_").

    Returns:
        The payload after the prefix, or None if invalid.
    """
    if not data or not data.startswith(expected_prefix):
        return None
    payload = data[len(expected_prefix):]
    # Allow only alphanumeric, underscore, hyphen, and dash
    if not re.match(r"^[a-zA-Z0-9_\-]+$", payload):
        return None
    return payload


def generate_listing_display_id(listing_id: int) -> str:
    """
    Format a listing's internal ID for display purposes.

    Args:
        listing_id: Internal database listing ID.

    Returns:
        Formatted display ID like "BS-000123".
    """
    return f"BS-{listing_id:06d}"
