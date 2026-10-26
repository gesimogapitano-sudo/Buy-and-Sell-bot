"""
My Listings handler — browsing and managing a user's own listings.

Features:
- Paginated listing of the user's listings
- View listing detail with status
- Withdraw a listing
- Mark a listing as sold
"""

from __future__ import annotations

import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.listing_repo import ListingRepository
from app.keyboards.keyboards import listing_actions_keyboard, main_menu
from app.locales.strings import t
from app.utils.helpers import (
    format_datetime,
    format_listing_status,
    format_price,
)

logger = logging.getLogger(__name__)
router = Router(name="my_listings")

PAGE_SIZE = 5


# ── Entry Point ────────────────────────────────────────────────────────────


@router.message(F.text.in_({"📋 My Listings", "📋 ማስታወቂያዎቼ"}))
async def my_listings_menu(
    message: Message, db_user: User, session, state: FSMContext
) -> None:
    await state.clear()
    await _send_listings_page(message, db_user, session, page=1, send_new=True)


async def _send_listings_page(
    message_or_callback,
    db_user: User,
    session,
    page: int,
    send_new: bool = False,
) -> None:
    """Render a paginated listing of the user's listings."""
    lang = db_user.language
    settings = get_settings()
    listing_repo = ListingRepository(session)

    total = await listing_repo.get_seller_listing_count(db_user.id)
    if total == 0:
        text = t("my_listings_empty", lang)
        if send_new or isinstance(message_or_callback, Message):
            await message_or_callback.answer(text=text, parse_mode="HTML")
        else:
            await message_or_callback.message.edit_text(text=text, parse_mode="HTML")
        return

    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    listings = await listing_repo.get_seller_listings(
        seller_id=db_user.id,
        offset=(page - 1) * PAGE_SIZE,
        limit=PAGE_SIZE,
    )

    admin_repo = AdminRepository(session)
    categories = {cat.id: cat for cat in await admin_repo.get_active_categories()}

    channel_username = get_settings().public_channel_username

    lines = [t("my_listings_header", lang, page=page, total_pages=total_pages)]
    for listing in listings:
        cat = categories.get(listing.category_id)
        cat_name = (
            (cat.name_am if lang == "am" else cat.name_en) if cat else "?"
        )
        price_str = format_price(listing.price, listing.currency)
        status_str = format_listing_status(listing.status)
        created = format_datetime(listing.created_at, include_time=False)
        lines.append(
            f"\n{t('listing_detail', lang, title=listing.title, status=status_str, price=price_str, category=cat_name, created_at=created)}"
        )

    text = "\n".join(lines)

    # Build inline keyboard with actions for each listing
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for listing in listings:
        builder.button(
            text=f"📌 {listing.title[:25]}",
            callback_data=f"my_listing:view:{listing.id}",
        )
    builder.adjust(1)

    # Pagination
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text=t("btn_prev", lang),
                callback_data=f"my_listings:page:{page - 1}",
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text=t("btn_next", lang),
                callback_data=f"my_listings:page:{page + 1}",
            )
        )
    if nav:
        builder.row(*nav)

    markup = builder.as_markup()

    if send_new or isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            text=text, parse_mode="HTML", reply_markup=markup
        )
    else:
        await message_or_callback.message.edit_text(
            text=text, parse_mode="HTML", reply_markup=markup
        )


# ── Pagination ─────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("my_listings:page:"))
async def my_listings_page(
    callback: CallbackQuery, db_user: User, session
) -> None:
    page = int(callback.data.split(":")[2])
    await _send_listings_page(callback, db_user, session, page=page)
    await callback.answer()


@router.callback_query(F.data == "my_listings:back")
async def my_listings_back(
    callback: CallbackQuery, db_user: User, session
) -> None:
    await _send_listings_page(callback, db_user, session, page=1)
    await callback.answer()


# ── View Single Listing ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("my_listing:view:"))
async def view_listing(
    callback: CallbackQuery, db_user: User, session
) -> None:
    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    listing_repo = ListingRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing or listing.seller_id != db_user.id:
        await callback.answer(t("listing_not_found", lang), show_alert=True)
        return

    admin_repo = AdminRepository(session)
    cat = await admin_repo.get_category_by_id(listing.category_id)
    cat_name = (
        (cat.name_am if lang == "am" else cat.name_en) if cat else "?"
    )
    price_str = format_price(listing.price, listing.currency)
    status_str = format_listing_status(listing.status)
    created = format_datetime(listing.created_at, include_time=False)

    text = t(
        "listing_detail",
        lang,
        title=listing.title,
        status=status_str,
        price=price_str,
        category=cat_name,
        created_at=created,
    )

    settings = get_settings()
    keyboard = listing_actions_keyboard(
        listing_id=listing.id,
        status=listing.status,
        channel_message_id=listing.channel_message_id,
        channel_username=settings.public_channel_username,
        lang=lang,
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    await callback.answer()


# ── Actions ────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("listing_action:withdraw:"))
async def withdraw_listing(
    callback: CallbackQuery, db_user: User, session
) -> None:
    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    listing_repo = ListingRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing or listing.seller_id != db_user.id:
        await callback.answer(t("listing_not_found", lang), show_alert=True)
        return

    if listing.status in ("sold", "withdrawn", "removed"):
        await callback.answer("Already in terminal state.", show_alert=True)
        return

    # Delete from channel if published
    if listing.channel_message_id:
        try:
            from app.bot.bot import create_bot
            bot = callback.bot
            settings = get_settings()
            await bot.delete_message(
                chat_id=settings.public_channel_id,
                message_id=listing.channel_message_id,
            )
        except Exception:
            pass  # Best effort

    await listing_repo.update_status(
        listing.id, "withdrawn", actor_id=db_user.id
    )
    await callback.message.edit_text(t("listing_withdrawn", lang))
    await callback.answer()


@router.callback_query(F.data.startswith("listing_action:sold:"))
async def mark_sold(
    callback: CallbackQuery, db_user: User, session
) -> None:
    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    listing_repo = ListingRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing or listing.seller_id != db_user.id:
        await callback.answer(t("listing_not_found", lang), show_alert=True)
        return

    await listing_repo.update_status(listing.id, "sold", actor_id=db_user.id)
    await callback.message.edit_text(t("listing_marked_sold", lang))
    await callback.answer()
