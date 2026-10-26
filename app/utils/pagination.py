"""
Pagination utilities for Telegram inline keyboards.

Provides paginated result sets with navigation buttons.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, List, TypeVar

from aiogram.types import InlineKeyboardButton

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """A paginated result set."""

    items: List[T]
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return max(1, ceil(self.total_items / self.page_size))

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def offset(self) -> int:
        """Calculate the database offset for this page."""
        return (self.page - 1) * self.page_size

    @property
    def page_info(self) -> str:
        """Human-readable page information."""
        return f"Page {self.page}/{self.total_pages} ({self.total_items} total)"


def get_pagination_buttons(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
) -> List[InlineKeyboardButton]:
    """
    Generate pagination navigation buttons.

    Args:
        current_page: Current page number (1-indexed).
        total_pages: Total number of pages.
        callback_prefix: Prefix for callback data (e.g., "listings_page_").

    Returns:
        List of InlineKeyboardButton for navigation.
    """
    buttons = []

    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Previous",
                callback_data=f"{callback_prefix}{current_page - 1}",
            )
        )

    if total_pages > 1:
        buttons.append(
            InlineKeyboardButton(
                text=f"📄 {current_page}/{total_pages}",
                callback_data="noop",
            )
        )

    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Next ▶️",
                callback_data=f"{callback_prefix}{current_page + 1}",
            )
        )

    return buttons


def paginate_list(
    items: List[T],
    page: int = 1,
    page_size: int = 5,
) -> PaginatedResult[T]:
    """
    Paginate an in-memory list of items.

    Args:
        items: All items to paginate.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        PaginatedResult for the requested page.
    """
    total = len(items)
    total_pages = max(1, ceil(total / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size

    return PaginatedResult(
        items=items[start:end],
        page=page,
        page_size=page_size,
        total_items=total,
    )
