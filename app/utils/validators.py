"""
Input validation utilities for the Buy & Sell Bot.

Provides validators for listing fields, user input, and business rules.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.config import get_settings


# ── Supported Values ──────────────────────────────────────────────

SUPPORTED_CURRENCIES = ["ETB", "USD", "EUR", "GBP"]

LISTING_CONDITIONS = ["new", "like_new", "used", "refurbished"]

LISTING_TYPES = ["product", "service"]

SUPPORTED_LANGUAGES = ["en", "am"]

# Categories will be loaded from DB, but these are the defaults
DEFAULT_CATEGORIES = {
    "electronics": {"en": "Electronics", "am": "ኤሌክትሮኒክስ"},
    "vehicles": {"en": "Vehicles", "am": "ተሽከርካሪዎች"},
    "property": {"en": "Property", "am": "ንብረት"},
    "fashion": {"en": "Fashion & Clothing", "am": "ፋሽን እና ልብስ"},
    "home_garden": {"en": "Home & Garden", "am": "ቤት እና አትክልት"},
    "services": {"en": "Services", "am": "አገልግሎቶች"},
    "jobs": {"en": "Jobs", "am": "ስራዎች"},
    "health_beauty": {"en": "Health & Beauty", "am": "ጤና እና ውበት"},
    "sports": {"en": "Sports & Leisure", "am": "ስፖርት እና መዝናኛ"},
    "books_education": {"en": "Books & Education", "am": "መጻሕፍት እና ትምህርት"},
    "food_agriculture": {"en": "Food & Agriculture", "am": "ምግብ እና ግብርና"},
    "other": {"en": "Other", "am": "ሌሎች"},
}


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_title(title: str) -> str:
    """
    Validate a listing title.

    Args:
        title: Raw title input.

    Returns:
        Cleaned title.

    Raises:
        ValidationError: If title is invalid.
    """
    settings = get_settings()
    title = title.strip()
    if not title:
        raise ValidationError("Title cannot be empty.", field="title")
    if len(title) < 3:
        raise ValidationError(
            "Title must be at least 3 characters.", field="title"
        )
    if len(title) > settings.max_title_length:
        raise ValidationError(
            f"Title must be at most {settings.max_title_length} characters.",
            field="title",
        )
    return title


def validate_description(description: str) -> str:
    """
    Validate a listing description.

    Args:
        description: Raw description input.

    Returns:
        Cleaned description.

    Raises:
        ValidationError: If description is invalid.
    """
    settings = get_settings()
    description = description.strip()
    if not description:
        raise ValidationError(
            "Description cannot be empty.", field="description"
        )
    if len(description) < 10:
        raise ValidationError(
            "Description must be at least 10 characters.",
            field="description",
        )
    if len(description) > settings.max_description_length:
        raise ValidationError(
            f"Description must be at most {settings.max_description_length} characters.",
            field="description",
        )
    return description


def validate_price(price_str: str) -> Decimal:
    """
    Validate and parse a price string.

    Args:
        price_str: Raw price input (e.g., "15000", "15,000.50").

    Returns:
        Decimal price value.

    Raises:
        ValidationError: If price is invalid.
    """
    # Remove commas and whitespace
    price_str = price_str.strip().replace(",", "").replace(" ", "")
    try:
        price = Decimal(price_str)
    except (InvalidOperation, ValueError):
        raise ValidationError(
            "Invalid price format. Please enter a number (e.g., 15000 or 15000.50).",
            field="price",
        )

    if price <= 0:
        raise ValidationError("Price must be greater than zero.", field="price")
    if price > Decimal("99999999.99"):
        raise ValidationError(
            "Price exceeds the maximum allowed value.", field="price"
        )
    # Ensure at most 2 decimal places
    if price != price.quantize(Decimal("0.01")):
        raise ValidationError(
            "Price can have at most 2 decimal places.", field="price"
        )
    return price


def validate_currency(currency: str) -> str:
    """
    Validate currency code.

    Args:
        currency: Currency code (e.g., "ETB").

    Returns:
        Uppercase currency code.

    Raises:
        ValidationError: If currency is not supported.
    """
    currency = currency.strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValidationError(
            f"Unsupported currency. Choose from: {', '.join(SUPPORTED_CURRENCIES)}",
            field="currency",
        )
    return currency


def validate_location(location: str) -> str:
    """
    Validate location text.

    Args:
        location: Raw location input.

    Returns:
        Cleaned location string.

    Raises:
        ValidationError: If location is invalid.
    """
    location = location.strip()
    if not location:
        raise ValidationError("Location cannot be empty.", field="location")
    if len(location) < 2:
        raise ValidationError(
            "Location must be at least 2 characters.", field="location"
        )
    if len(location) > 200:
        raise ValidationError(
            "Location must be at most 200 characters.", field="location"
        )
    return location


def validate_condition(condition: str) -> str:
    """
    Validate item condition.

    Args:
        condition: Raw condition input.

    Returns:
        Validated condition string.

    Raises:
        ValidationError: If condition is invalid.
    """
    condition = condition.strip().lower()
    if condition not in LISTING_CONDITIONS:
        raise ValidationError(
            f"Invalid condition. Choose from: {', '.join(LISTING_CONDITIONS)}",
            field="condition",
        )
    return condition


def validate_listing_type(listing_type: str) -> str:
    """
    Validate listing type.

    Args:
        listing_type: "product" or "service".

    Returns:
        Validated listing type.

    Raises:
        ValidationError: If type is invalid.
    """
    listing_type = listing_type.strip().lower()
    if listing_type not in LISTING_TYPES:
        raise ValidationError(
            f"Invalid listing type. Choose from: {', '.join(LISTING_TYPES)}",
            field="listing_type",
        )
    return listing_type


def validate_brand(brand: str) -> str:
    """
    Validate brand name (optional field).

    Args:
        brand: Raw brand input.

    Returns:
        Cleaned brand string.

    Raises:
        ValidationError: If brand is too long.
    """
    brand = brand.strip()
    if len(brand) > 100:
        raise ValidationError(
            "Brand name must be at most 100 characters.", field="brand"
        )
    return brand


def validate_language(lang: str) -> str:
    """
    Validate language selection.

    Args:
        lang: Language code.

    Returns:
        Validated language code.

    Raises:
        ValidationError: If language is not supported.
    """
    lang = lang.strip().lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise ValidationError(
            f"Unsupported language. Choose from: {', '.join(SUPPORTED_LANGUAGES)}",
            field="language",
        )
    return lang
