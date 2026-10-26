"""
Messaging handler — anonymous buyer-seller messaging relay.

Features:
- Contact seller from a listing (deep link or inline button)
- Anonymous message relay (text, photo, video, voice, document)
- Conversation list with pagination
- End conversation
"""

from __future__ import annotations

import logging
import math

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.database.models import User
from app.database.repositories.conversation_repo import ConversationRepository
from app.database.repositories.listing_repo import ListingRepository
from app.keyboards.keyboards import (
    conversation_keyboard,
    conversations_list_keyboard,
    main_menu,
)
from app.locales.strings import t
from app.services.messaging_service import MessagingService
from app.database.repositories.admin_repo import AdminRepository

logger = logging.getLogger(__name__)
router = Router(name="messaging")

CONV_PAGE_SIZE = 7


# ── FSM States ─────────────────────────────────────────────────────────────


class MessagingStates(StatesGroup):
    in_conversation = State()


# ── Browse Conversations ───────────────────────────────────────────────────


@router.message(F.text.in_({"💬 Messages", "💬 መልዕክቶች"}))
async def messages_menu(
    message: Message, db_user: User, session, state: FSMContext
) -> None:
    """Show the user's conversation list."""
    await state.clear()
    await _send_conversations_page(message, db_user, session, page=1, send_new=True)


async def _send_conversations_page(
    message_or_cb,
    db_user: User,
    session,
    page: int,
    send_new: bool = False,
) -> None:
    lang = db_user.language
    conv_repo = ConversationRepository(session)

    total = await conv_repo.get_user_conversation_count(db_user.id, state="active")
    if total == 0:
        text = t("my_messages_empty", lang)
        if send_new or isinstance(message_or_cb, Message):
            await message_or_cb.answer(text=text)
        else:
            await message_or_cb.message.edit_text(text=text)
        return

    total_pages = max(1, math.ceil(total / CONV_PAGE_SIZE))
    page = max(1, min(page, total_pages))

    conversations = await conv_repo.get_user_conversations(
        user_id=db_user.id,
        state="active",
        offset=(page - 1) * CONV_PAGE_SIZE,
        limit=CONV_PAGE_SIZE,
    )

    markup = conversations_list_keyboard(conversations, page, total_pages, lang)

    if send_new or isinstance(message_or_cb, Message):
        await message_or_cb.answer(
            text=f"💬 <b>{'Messages' if lang == 'en' else 'መልዕክቶች'}</b> (Page {page}/{total_pages})",
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        await message_or_cb.message.edit_text(
            text=f"💬 <b>{'Messages' if lang == 'en' else 'መልዕክቶች'}</b> (Page {page}/{total_pages})",
            parse_mode="HTML",
            reply_markup=markup,
        )


@router.callback_query(F.data.startswith("conv_list:page:"))
async def conv_list_page(
    callback: CallbackQuery, db_user: User, session
) -> None:
    page = int(callback.data.split(":")[2])
    await _send_conversations_page(callback, db_user, session, page=page)
    await callback.answer()


# ── Contact Seller ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("contact_seller:"))
async def contact_seller(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    listing_id = int(callback.data.split(":")[1])
    lang = db_user.language

    listing_repo = ListingRepository(session)
    listing = await listing_repo.get_by_id(listing_id)

    if not listing or listing.status != "published":
        await callback.answer(t("listing_not_found", lang), show_alert=True)
        return

    if listing.seller_id == db_user.id:
        await callback.answer(
            t("cannot_message_own_listing", lang), show_alert=True
        )
        return

    conv_repo = ConversationRepository(session)
    conversation, created = await conv_repo.get_or_create(
        listing_id=listing.id,
        buyer_id=db_user.id,
        seller_id=listing.seller_id,
    )

    await state.set_state(MessagingStates.in_conversation)
    await state.update_data(conversation_id=conversation.id)

    await callback.message.answer(
        text=t("conversation_started", lang, listing_title=listing.title),
        parse_mode="HTML",
        reply_markup=conversation_keyboard(conversation.id, lang),
    )
    await callback.answer()


# ── Open Existing Conversation ─────────────────────────────────────────────


@router.callback_query(F.data.startswith("conv:open:"))
async def open_conversation(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    conv_id = int(callback.data.split(":")[2])
    lang = db_user.language

    conv_repo = ConversationRepository(session)
    conversation = await conv_repo.get_by_id(conv_id)

    if not conversation:
        await callback.answer("Conversation not found.", show_alert=True)
        return

    # Verify participant
    if db_user.id not in (conversation.buyer_id, conversation.seller_id):
        await callback.answer(t("not_authorized", lang), show_alert=True)
        return

    if conversation.state != "active":
        await callback.message.edit_text(t("conversation_ended", lang))
        await callback.answer()
        return

    other_party = (
        conversation.seller.first_name or conversation.seller.username or "Seller"
        if db_user.id == conversation.buyer_id
        else conversation.buyer.first_name or conversation.buyer.username or "Buyer"
    )

    await state.set_state(MessagingStates.in_conversation)
    await state.update_data(conversation_id=conversation.id)

    listing_title = (
        conversation.listing.title if conversation.listing else "?"
    )

    await callback.message.edit_text(
        text=t(
            "conversation_header",
            lang,
            listing_title=listing_title,
            other_party=other_party,
        ),
        parse_mode="HTML",
        reply_markup=conversation_keyboard(conv_id, lang),
    )
    await callback.answer()


# ── Message Relay ──────────────────────────────────────────────────────────


@router.message(
    MessagingStates.in_conversation,
    F.content_type.in_({"text", "photo", "video", "voice", "document"}),
)
async def relay_message(
    message: Message, db_user: User, session, state: FSMContext, bot: Bot
) -> None:
    lang = db_user.language
    data = await state.get_data()
    conv_id = data.get("conversation_id")

    if not conv_id:
        await state.clear()
        return

    conv_repo = ConversationRepository(session)
    conversation = await conv_repo.get_by_id(conv_id)

    if not conversation or conversation.state != "active":
        await message.answer(t("conversation_ended", lang))
        await state.clear()
        return

    svc = MessagingService(conv_repo, bot)
    success = await svc.relay_message(
        conversation=conversation,
        sender_id=db_user.id,
        sender_telegram_id=message.from_user.id,
        tg_message=message,
        lang=lang,
    )

    if success:
        await message.answer(t("message_relayed", lang))
    else:
        await message.answer(t("message_relay_failed", lang))


# ── End Conversation ───────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("conv:end:"))
async def end_conversation(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    conv_id = int(callback.data.split(":")[2])
    lang = db_user.language

    conv_repo = ConversationRepository(session)
    conversation = await conv_repo.get_by_id(conv_id)

    if not conversation:
        await callback.answer("Not found.", show_alert=True)
        return

    if db_user.id not in (conversation.buyer_id, conversation.seller_id):
        await callback.answer(t("not_authorized", lang), show_alert=True)
        return

    await conv_repo.update_state(conv_id, "ended")
    await state.clear()

    await callback.message.edit_text(t("conversation_ended", lang))

    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(callback.from_user.id)
    await callback.message.answer(
        text=t("welcome", lang),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang, is_admin=is_admin),
    )
    await callback.answer()
