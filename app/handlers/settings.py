"""
Settings handler — language switching and data management.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.user_repo import UserRepository
from app.keyboards.keyboards import (
    confirm_delete_keyboard,
    language_keyboard,
    main_menu,
    settings_keyboard,
)
from app.locales.strings import t

logger = logging.getLogger(__name__)
router = Router(name="settings")


# ── Entry ──────────────────────────────────────────────────────────────────


@router.message(F.text.in_({"⚙️ Settings", "⚙️ ቅንብሮች"}))
@router.message(Command("settings"))
async def settings_menu(
    message: Message, db_user: User, state: FSMContext
) -> None:
    await state.clear()
    lang = db_user.language
    await message.answer(
        text=t("settings_menu", lang),
        parse_mode="HTML",
        reply_markup=settings_keyboard(lang),
    )


# ── Language ───────────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings:language")
async def change_language(callback: CallbackQuery, db_user: User) -> None:
    await callback.message.edit_text(
        text="🌐 Select your language / ቋንቋ ይምረጡ:",
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def set_language(
    callback: CallbackQuery, db_user: User, session
) -> None:
    lang_code = callback.data.split(":")[1]
    user_repo = UserRepository(session)
    await user_repo.update_language(db_user.id, lang_code)
    db_user.language = lang_code

    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(callback.from_user.id)

    await callback.message.edit_text(
        text=t("language_changed", lang_code),
        parse_mode="HTML",
    )
    await callback.message.answer(
        text=t("welcome", lang_code),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang_code, is_admin=is_admin),
    )
    await callback.answer()


# ── Delete Data ────────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings:delete_data")
async def delete_data_prompt(
    callback: CallbackQuery, db_user: User
) -> None:
    lang = db_user.language
    await callback.message.edit_text(
        text=t("delete_data_confirm", lang),
        parse_mode="HTML",
        reply_markup=confirm_delete_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:delete_confirm")
async def delete_data_confirm(
    callback: CallbackQuery, db_user: User, session
) -> None:
    lang = db_user.language
    user_repo = UserRepository(session)

    # Mark user as deleted (soft delete)
    await user_repo.update_status(db_user.id, "deleted")

    # Remove consent
    from sqlalchemy import delete
    from app.database.models import ConsentRecord
    await session.execute(
        delete(ConsentRecord).where(ConsentRecord.user_id == db_user.id)
    )

    await callback.message.edit_text(t("data_deleted", lang))
    await callback.answer()
    logger.info("User %d requested account deletion.", db_user.id)


@router.callback_query(F.data == "settings:delete_cancel")
async def delete_data_cancel(
    callback: CallbackQuery, db_user: User
) -> None:
    lang = db_user.language
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.answer()
