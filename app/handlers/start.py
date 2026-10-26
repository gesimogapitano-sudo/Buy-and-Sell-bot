"""
Start handler — /start command and main menu.

Handles:
- /start (with optional deep link for listing contact)
- Main menu navigation
- Privacy consent flow
- /help command
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.listing_repo import ListingRepository
from app.database.repositories.user_repo import UserRepository
from app.keyboards.keyboards import (
    consent_keyboard,
    contact_seller_keyboard,
    main_menu,
)
from app.locales.strings import t
from app.utils.helpers import parse_deep_link_payload

logger = logging.getLogger(__name__)
router = Router(name="start")


# ── Helpers ────────────────────────────────────────────────────────────────


async def _send_main_menu(message: Message, db_user: User, is_admin: bool) -> None:
    """Send the main menu with the welcome message."""
    lang = db_user.language
    await message.answer(
        text=t("welcome", lang),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang, is_admin=is_admin),
    )


async def _send_consent_prompt(message: Message, lang: str) -> None:
    """Send the privacy consent prompt."""
    await message.answer(
        text=t("consent_required", lang),
        parse_mode="HTML",
        reply_markup=consent_keyboard(lang),
    )


# ── /start ─────────────────────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    db_user: User,
    session,
    state: FSMContext,
) -> None:
    """Handle /start command, optionally with deep link payload."""
    await state.clear()
    lang = db_user.language

    # Check consent
    if not db_user.consent_given:
        # Store any deep link payload for after consent
        start_param = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
        if start_param:
            await state.update_data(pending_start_param=start_param)
        await _send_consent_prompt(message, lang)
        return

    # Handle deep link (e.g., listing contact)
    start_param = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if start_param:
        token = parse_deep_link_payload(start_param)
        if token:
            listing_repo = ListingRepository(session)
            listing = await listing_repo.get_by_token(token)
            if listing and listing.status == "published":
                # Check if user is trying to contact their own listing
                if listing.seller_id == db_user.id:
                    await message.answer(t("cannot_message_own_listing", lang))
                else:
                    # Show listing contact button
                    from app.utils.helpers import format_price
                    price = format_price(listing.price, listing.currency)
                    text = (
                        f"📌 <b>{listing.title}</b>\n"
                        f"💰 {price}\n"
                        f"📍 {listing.location}\n\n"
                        f"{listing.description[:300]}{'...' if len(listing.description) > 300 else ''}"
                    )
                    await message.answer(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=contact_seller_keyboard(listing.id, lang),
                    )
                    return

    # Normal start — show main menu
    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(message.from_user.id)
    await _send_main_menu(message, db_user, is_admin)


# ── Consent Flow ───────────────────────────────────────────────────────────


@router.callback_query(F.data == "consent:accept")
async def consent_accept(
    callback: CallbackQuery,
    db_user: User,
    session,
    state: FSMContext,
) -> None:
    """User accepted the privacy notice."""
    settings = get_settings()
    user_repo = UserRepository(session)
    await user_repo.update_consent(db_user.id, settings.privacy_notice_version)
    db_user.consent_given = True
    db_user.consent_version = settings.privacy_notice_version

    lang = db_user.language
    await callback.message.edit_text(t("consent_accepted", lang))

    # Handle pending deep link if any
    data = await state.get_data()
    pending = data.get("pending_start_param", "")
    await state.clear()

    if pending:
        token = parse_deep_link_payload(pending)
        if token:
            listing_repo = ListingRepository(session)
            listing = await listing_repo.get_by_token(token)
            if listing and listing.status == "published":
                if listing.seller_id != db_user.id:
                    await callback.message.answer(
                        text=f"📌 <b>{listing.title}</b>",
                        parse_mode="HTML",
                        reply_markup=contact_seller_keyboard(listing.id, lang),
                    )
                    return

    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(callback.from_user.id)
    await callback.message.answer(
        text=t("welcome", lang),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang, is_admin=is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == "consent:decline")
async def consent_decline(callback: CallbackQuery, db_user: User) -> None:
    """User declined the privacy notice."""
    lang = db_user.language
    await callback.message.edit_text(t("consent_declined", lang))
    await callback.answer()


# ── Help ───────────────────────────────────────────────────────────────────


@router.message(Command("help"))
@router.message(F.text.func(lambda t: t in ("❓ Help", "❓ እርዳታ")))
async def cmd_help(message: Message, db_user: User) -> None:
    """Show help text."""
    lang = db_user.language
    await message.answer(
        text=t("help_text", lang),
        parse_mode="HTML",
    )
