"""
Admin handler — admin panel with listing review, user management, and stats.

Access is restricted to users with active administrator records.
"""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.listing_repo import ListingRepository
from app.database.repositories.user_repo import UserRepository
from app.keyboards.keyboards import (
    admin_panel_keyboard,
    cancel_keyboard,
    listing_review_keyboard,
    main_menu,
)
from app.locales.strings import t
from app.services.listing_service import ListingService
from app.utils.helpers import (
    format_condition,
    format_datetime,
    format_listing_status,
    format_price,
)

logger = logging.getLogger(__name__)
router = Router(name="admin")


# ── FSM States ─────────────────────────────────────────────────────────────


class AdminReviewStates(StatesGroup):
    awaiting_reject_reason = State()
    awaiting_changes_reason = State()


# ── Guards ─────────────────────────────────────────────────────────────────


async def _require_admin(callback_or_msg, db_user: User, session) -> bool:
    """Return True if the user is an active admin, else send error and return False."""
    admin_repo = AdminRepository(session)
    if not await admin_repo.is_admin(db_user.telegram_id):
        lang = db_user.language
        if isinstance(callback_or_msg, CallbackQuery):
            await callback_or_msg.answer(t("not_authorized", lang), show_alert=True)
        else:
            await callback_or_msg.answer(t("not_authorized", lang))
        return False
    return True


# ── Entry Points ───────────────────────────────────────────────────────────


@router.message(F.text.in_({"🔑 Admin Panel", "🔑 የአስተዳዳሪ ፓነል"}))
@router.message(Command("admin"))
async def admin_panel(
    message: Message, db_user: User, session, state: FSMContext
) -> None:
    await state.clear()
    if not await _require_admin(message, db_user, session):
        return

    lang = db_user.language
    admin_repo = AdminRepository(session)
    user_repo = UserRepository(session)
    listing_repo = ListingRepository(session)
    from app.database.repositories.conversation_repo import ConversationRepository
    conv_repo = ConversationRepository(session)

    users = await user_repo.get_user_count()
    listings = await listing_repo.get_total_listing_count()
    pending = await listing_repo.get_pending_count()
    conversations = await conv_repo.get_total_conversation_count()

    text = t(
        "admin_panel",
        lang,
        users=users,
        listings=listings,
        pending=pending,
        conversations=conversations,
    )

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard(lang),
    )


# ── Review Listings ────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin:review_listings")
async def review_listings_start(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    await state.clear()
    if not await _require_admin(callback, db_user, session):
        return
    await _show_next_pending(callback, db_user, session, offset=0)
    await callback.answer()


async def _show_next_pending(
    callback_or_msg,
    db_user: User,
    session,
    offset: int = 0,
) -> None:
    lang = db_user.language
    listing_repo = ListingRepository(session)
    total = await listing_repo.get_pending_count()

    if total == 0:
        text = t("no_pending_listings", lang)
        if isinstance(callback_or_msg, CallbackQuery):
            await callback_or_msg.message.edit_text(text)
        else:
            await callback_or_msg.answer(text)
        return

    offset = min(offset, total - 1)
    listings = await listing_repo.get_pending_listings(offset=offset, limit=1)
    if not listings:
        text = t("no_pending_listings", lang)
        if isinstance(callback_or_msg, CallbackQuery):
            await callback_or_msg.message.edit_text(text)
        else:
            await callback_or_msg.answer(text)
        return

    listing = listings[0]
    admin_repo = AdminRepository(session)
    cat = await admin_repo.get_category_by_id(listing.category_id)
    cat_name = (cat.name_am if lang == "am" else cat.name_en) if cat else "?"

    seller_name = (
        listing.seller.first_name or listing.seller.username or f"user_{listing.seller_id}"
        if listing.seller else "?"
    )
    price_str = format_price(listing.price, listing.currency)
    condition_str = format_condition(listing.condition)
    photos_count = len(listing.media) if listing.media else 0
    submitted = format_datetime(listing.created_at)

    text = t(
        "review_listing",
        lang,
        listing_id=listing.id,
        seller=seller_name,
        listing_type=listing.listing_type,
        category=cat_name,
        title=listing.title,
        description=listing.description[:500] + ("..." if len(listing.description) > 500 else ""),
        brand=listing.brand or "N/A",
        condition=condition_str,
        price=price_str,
        location=listing.location,
        photos=photos_count,
        submitted_at=submitted,
        current=offset + 1,
        total=total,
    )

    keyboard = listing_review_keyboard(
        listing_id=listing.id,
        current=offset + 1,
        total=total,
        lang=lang,
    )

    # Send with photos if available
    if listing.media:
        try:
            if isinstance(callback_or_msg, CallbackQuery):
                # Edit existing message — can't easily change to photo, send new
                await callback_or_msg.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            else:
                if len(listing.media) == 1:
                    await callback_or_msg.answer_photo(
                        photo=listing.media[0].file_id,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    from aiogram.types import InputMediaPhoto
                    media_group = [
                        InputMediaPhoto(media=m.file_id) for m in listing.media[:10]
                    ]
                    media_group[0] = InputMediaPhoto(
                        media=listing.media[0].file_id,
                        caption=text,
                        parse_mode="HTML",
                    )
                    await callback_or_msg.answer_media_group(media=media_group)
                    await callback_or_msg.answer(
                        "👆 Use the buttons above to moderate:",
                        reply_markup=keyboard,
                    )
        except Exception:
            if isinstance(callback_or_msg, CallbackQuery):
                await callback_or_msg.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            else:
                await callback_or_msg.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        if isinstance(callback_or_msg, CallbackQuery):
            await callback_or_msg.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback_or_msg.answer(text, parse_mode="HTML", reply_markup=keyboard)

    # Store the offset for "next" button
    return listing.id, offset


@router.callback_query(F.data == "admin_review:next")
async def review_next(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    if not await _require_admin(callback, db_user, session):
        return
    data = await state.get_data()
    offset = data.get("review_offset", 0) + 1
    await state.update_data(review_offset=offset)
    await _show_next_pending(callback, db_user, session, offset=offset)
    await callback.answer()


# ── Approve ────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin_review:approve:"))
async def approve_listing(
    callback: CallbackQuery, db_user: User, session, state: FSMContext, bot: Bot
) -> None:
    if not await _require_admin(callback, db_user, session):
        return

    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language

    listing_repo = ListingRepository(session)
    admin_repo = AdminRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing:
        await callback.answer("Listing not found.", show_alert=True)
        return

    # Update status to approved then publish
    await listing_repo.update_status(
        listing_id=listing.id,
        new_status="approved",
        actor_id=db_user.id,
    )

    # Get category name for channel post
    cat = await admin_repo.get_category_by_id(listing.category_id)
    cat_name = (cat.name_am if lang == "am" else cat.name_en) if cat else "?"

    # Publish to channel
    listing_svc = ListingService(listing_repo, bot)
    msg_id = await listing_svc.publish_to_channel(listing, cat_name)

    if msg_id:
        await listing_repo.update_status(
            listing.id, "published", actor_id=db_user.id
        )

    # Notify seller
    if listing.seller:
        await listing_svc.notify_seller(
            seller_telegram_id=listing.seller.telegram_id,
            key="listing_approved_seller",
            lang=listing.seller.language,
            title=listing.title,
        )

    # Log admin action
    admin_record = await admin_repo.get_admin_by_user_id(db_user.id)
    if admin_record:
        await admin_repo.log_action(
            administrator_id=admin_record.id,
            action="approve_listing",
            target_type="listing",
            target_id=listing.id,
        )

    await callback.message.edit_text(
        t("listing_approved_admin", lang, listing_id=listing_id)
    )
    await callback.answer()


# ── Reject ─────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin_review:reject:"))
async def reject_listing_prompt(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    if not await _require_admin(callback, db_user, session):
        return

    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    await state.set_state(AdminReviewStates.awaiting_reject_reason)
    await state.update_data(target_listing_id=listing_id)
    await callback.message.answer(
        text=t("reject_reason_prompt", lang),
        reply_markup=cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(AdminReviewStates.awaiting_reject_reason)
async def reject_listing_confirm(
    message: Message, db_user: User, session, state: FSMContext, bot: Bot
) -> None:
    lang = db_user.language
    data = await state.get_data()
    listing_id = data.get("target_listing_id")
    reason = message.text or "No reason provided."
    await state.clear()

    listing_repo = ListingRepository(session)
    admin_repo = AdminRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing:
        await message.answer("Listing not found.")
        return

    await listing_repo.update_status(
        listing.id, "rejected", actor_id=db_user.id, reason=reason
    )

    # Notify seller
    if listing.seller:
        listing_svc = ListingService(listing_repo, bot)
        await listing_svc.notify_seller(
            seller_telegram_id=listing.seller.telegram_id,
            key="listing_rejected_seller",
            lang=listing.seller.language,
            title=listing.title,
            reason=reason,
        )

    admin_record = await admin_repo.get_admin_by_user_id(db_user.id)
    if admin_record:
        await admin_repo.log_action(
            administrator_id=admin_record.id,
            action="reject_listing",
            target_type="listing",
            target_id=listing.id,
            details=reason,
        )

    await message.answer(
        t("listing_rejected_admin", lang, listing_id=listing_id)
    )


# ── Request Changes ────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin_review:changes:"))
async def changes_listing_prompt(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    if not await _require_admin(callback, db_user, session):
        return

    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    await state.set_state(AdminReviewStates.awaiting_changes_reason)
    await state.update_data(target_listing_id=listing_id)
    await callback.message.answer(
        text=t("changes_reason_prompt", lang),
        reply_markup=cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(AdminReviewStates.awaiting_changes_reason)
async def changes_listing_confirm(
    message: Message, db_user: User, session, state: FSMContext, bot: Bot
) -> None:
    lang = db_user.language
    data = await state.get_data()
    listing_id = data.get("target_listing_id")
    reason = message.text or "Please review and resubmit."
    await state.clear()

    listing_repo = ListingRepository(session)
    admin_repo = AdminRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing:
        await message.answer("Listing not found.")
        return

    await listing_repo.update_status(
        listing.id, "changes_requested", actor_id=db_user.id, reason=reason
    )

    if listing.seller:
        listing_svc = ListingService(listing_repo, bot)
        await listing_svc.notify_seller(
            seller_telegram_id=listing.seller.telegram_id,
            key="listing_changes_requested_seller",
            lang=listing.seller.language,
            title=listing.title,
            reason=reason,
        )

    admin_record = await admin_repo.get_admin_by_user_id(db_user.id)
    if admin_record:
        await admin_repo.log_action(
            administrator_id=admin_record.id,
            action="request_changes",
            target_type="listing",
            target_id=listing.id,
            details=reason,
        )

    await message.answer(f"🔄 Changes requested for listing #{listing_id}.")


# ── Cancel Admin Review ────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_review:cancel")
async def cancel_admin_review(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    await state.clear()
    lang = db_user.language
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.answer()
