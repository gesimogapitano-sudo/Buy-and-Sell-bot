"""
Inline and reply keyboards for the Buy & Sell Marketplace Bot.

All keyboard builders accept a `lang` parameter for bilingual support.
"""

from __future__ import annotations

from typing import List, Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.locales.strings import t
from app.database.models import Category


# ── Helper ─────────────────────────────────────────────────────────────────


def _inline(*rows: list) -> InlineKeyboardMarkup:
    """Build an InlineKeyboardMarkup from rows of InlineKeyboardButton lists."""
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Main Menu ──────────────────────────────────────────────────────────────


def main_menu(lang: str = "en", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main menu reply keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("btn_sell", lang))
    builder.button(text=t("btn_my_listings", lang))
    builder.button(text=t("btn_messages", lang))
    builder.button(text=t("btn_settings", lang))
    builder.button(text=t("btn_help", lang))
    if is_admin:
        builder.button(text=t("btn_admin_panel", lang))
    builder.adjust(2, 2, 2 if is_admin else 1)
    return builder.as_markup(resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ── Consent ────────────────────────────────────────────────────────────────


def consent_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_accept_consent", lang),
                callback_data="consent:accept",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("btn_decline_consent", lang),
                callback_data="consent:decline",
            )
        ],
    )


# ── Listing Creation ───────────────────────────────────────────────────────


def listing_type_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_type_product", lang),
                callback_data="listing_type:product",
            ),
            InlineKeyboardButton(
                text=t("btn_type_service", lang),
                callback_data="listing_type:service",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="listing:cancel"
            )
        ],
    )


def categories_keyboard(
    categories: List[Category], lang: str = "en"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        name = cat.name_am if lang == "am" else cat.name_en
        builder.button(text=name, callback_data=f"category:{cat.id}")
    builder.button(text=t("btn_cancel", lang), callback_data="listing:cancel")
    builder.adjust(2)
    return builder.as_markup()


def condition_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_condition_new", lang),
                callback_data="condition:new",
            ),
            InlineKeyboardButton(
                text=t("btn_condition_like_new", lang),
                callback_data="condition:like_new",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_condition_used", lang),
                callback_data="condition:used",
            ),
            InlineKeyboardButton(
                text=t("btn_condition_refurbished", lang),
                callback_data="condition:refurbished",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="listing:cancel"
            )
        ],
    )


def currency_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    currencies = ["ETB", "USD", "EUR", "GBP"]
    builder = InlineKeyboardBuilder()
    for c in currencies:
        builder.button(text=c, callback_data=f"currency:{c}")
    builder.button(text=t("btn_cancel", lang), callback_data="listing:cancel")
    builder.adjust(2)
    return builder.as_markup()


def skip_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_skip", lang), callback_data="listing:skip"
            ),
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="listing:cancel"
            ),
        ]
    )


def done_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_done", lang), callback_data="listing:done_photos"
            ),
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="listing:cancel"
            ),
        ]
    )


def listing_confirm_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_submit_listing", lang),
                callback_data="listing:submit",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="listing:cancel"
            )
        ],
    )


# ── My Listings ────────────────────────────────────────────────────────────


def listing_actions_keyboard(
    listing_id: int,
    status: str,
    channel_message_id: Optional[int],
    channel_username: Optional[str],
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Actions for a seller's own listing."""
    rows = []

    # View in channel button (only for published listings with a message ID)
    if status == "published" and channel_message_id and channel_username:
        url = f"https://t.me/{channel_username.lstrip('@')}/{channel_message_id}"
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn_view_channel", lang), url=url
                )
            ]
        )

    # Mark as sold
    if status in ("published", "approved"):
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn_mark_sold", lang),
                    callback_data=f"listing_action:sold:{listing_id}",
                )
            ]
        )

    # Withdraw
    if status not in ("sold", "withdrawn", "removed", "rejected"):
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn_withdraw_listing", lang),
                    callback_data=f"listing_action:withdraw:{listing_id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t("btn_back", lang), callback_data="my_listings:back"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def paginate_keyboard(
    page: int,
    total_pages: int,
    prefix: str,
    lang: str = "en",
    extra_buttons: Optional[List[InlineKeyboardButton]] = None,
) -> InlineKeyboardMarkup:
    """Generic pagination keyboard."""
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text=t("btn_prev", lang),
                callback_data=f"{prefix}:page:{page - 1}",
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text=t("btn_next", lang),
                callback_data=f"{prefix}:page:{page + 1}",
            )
        )
    rows = []
    if extra_buttons:
        rows.append(extra_buttons)
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Messaging ──────────────────────────────────────────────────────────────


def contact_seller_keyboard(
    listing_id: int, lang: str = "en"
) -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("contact_seller_btn", lang),
                callback_data=f"contact_seller:{listing_id}",
            )
        ]
    )


def conversation_keyboard(
    conversation_id: int, lang: str = "en"
) -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_end_conversation", lang),
                callback_data=f"conv:end:{conversation_id}",
            )
        ]
    )


def conversations_list_keyboard(
    conversations: list,
    page: int,
    total_pages: int,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """List of conversations with pagination."""
    builder = InlineKeyboardBuilder()
    for conv in conversations:
        listing_title = (
            conv.listing.title[:30] + "..." if len(conv.listing.title) > 30 else conv.listing.title
        ) if conv.listing else "?"
        builder.button(
            text=f"💬 {listing_title}",
            callback_data=f"conv:open:{conv.id}",
        )
    builder.adjust(1)

    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(
                InlineKeyboardButton(
                    text=t("btn_prev", lang),
                    callback_data=f"conv_list:page:{page - 1}",
                )
            )
        if page < total_pages:
            nav.append(
                InlineKeyboardButton(
                    text=t("btn_next", lang),
                    callback_data=f"conv_list:page:{page + 1}",
                )
            )
        if nav:
            builder.row(*nav)

    return builder.as_markup()


# ── Reports ────────────────────────────────────────────────────────────────


def report_type_keyboard(
    listing_id: Optional[int] = None,
    user_id: Optional[int] = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    target = f"listing:{listing_id}" if listing_id else f"user:{user_id}"
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_report_spam", lang),
                callback_data=f"report_type:spam:{target}",
            ),
            InlineKeyboardButton(
                text=t("btn_report_fraud", lang),
                callback_data=f"report_type:fraud:{target}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_report_inappropriate", lang),
                callback_data=f"report_type:inappropriate:{target}",
            ),
            InlineKeyboardButton(
                text=t("btn_report_prohibited", lang),
                callback_data=f"report_type:prohibited:{target}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_report_other", lang),
                callback_data=f"report_type:other:{target}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="report:cancel"
            )
        ],
    )


# ── Settings ───────────────────────────────────────────────────────────────


def settings_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_change_language", lang),
                callback_data="settings:language",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("btn_delete_my_data", lang),
                callback_data="settings:delete_data",
            )
        ],
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="lang:am"),
        ]
    )


def confirm_delete_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_yes", lang),
                callback_data="settings:delete_confirm",
            ),
            InlineKeyboardButton(
                text=t("btn_no", lang),
                callback_data="settings:delete_cancel",
            ),
        ]
    )


# ── Admin ──────────────────────────────────────────────────────────────────


def admin_panel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_review_listings", lang),
                callback_data="admin:review_listings",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("btn_manage_users", lang),
                callback_data="admin:manage_users",
            ),
            InlineKeyboardButton(
                text=t("btn_manage_admins", lang),
                callback_data="admin:manage_admins",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_view_reports", lang),
                callback_data="admin:view_reports",
            )
        ],
    )


def listing_review_keyboard(
    listing_id: int, current: int, total: int, lang: str = "en"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t("btn_approve", lang),
                callback_data=f"admin_review:approve:{listing_id}",
            ),
            InlineKeyboardButton(
                text=t("btn_reject", lang),
                callback_data=f"admin_review:reject:{listing_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t("btn_request_changes", lang),
                callback_data=f"admin_review:changes:{listing_id}",
            )
        ],
    ]
    # Next button if more pending
    if current < total:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn_next_listing", lang),
                    callback_data="admin_review:next",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t("btn_back", lang), callback_data="admin:review_listings"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return _inline(
        [
            InlineKeyboardButton(
                text=t("btn_cancel", lang), callback_data="admin_review:cancel"
            )
        ]
    )
