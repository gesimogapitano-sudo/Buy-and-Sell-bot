"""
Admin conversations handler — admin view into buyer-seller conversations.

Allows admins to search and monitor conversations for moderation purposes.
"""

from __future__ import annotations

import logging
import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.conversation_repo import ConversationRepository
from app.locales.strings import t
from app.utils.helpers import format_datetime

logger = logging.getLogger(__name__)
router = Router(name="admin_conversations")

PAGE_SIZE = 5


async def _require_admin(callback_or_msg, db_user: User, session) -> bool:
    admin_repo = AdminRepository(session)
    if not await admin_repo.is_admin(db_user.telegram_id):
        lang = db_user.language
        if isinstance(callback_or_msg, CallbackQuery):
            await callback_or_msg.answer(t("not_authorized", lang), show_alert=True)
        else:
            await callback_or_msg.answer(t("not_authorized", lang))
        return False
    return True


@router.callback_query(F.data == "admin:manage_users")
async def manage_users_stub(
    callback: CallbackQuery, db_user: User, session
) -> None:
    if not await _require_admin(callback, db_user, session):
        return
    lang = db_user.language
    from app.database.repositories.user_repo import UserRepository
    user_repo = UserRepository(session)
    count = await user_repo.get_user_count()
    active = await user_repo.get_active_user_count()

    await callback.message.edit_text(
        f"👥 <b>User Management</b>\n\n"
        f"Total users: {count}\n"
        f"Active users: {active}\n\n"
        f"<i>Use /suspend &lt;telegram_id&gt; or /unsuspend &lt;telegram_id&gt; to manage users.</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("suspend"))
async def suspend_user(
    message: Message, db_user: User, session
) -> None:
    if not await _require_admin(message, db_user, session):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /suspend <telegram_id>")
        return

    try:
        target_tid = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID.")
        return

    from app.database.repositories.user_repo import UserRepository
    user_repo = UserRepository(session)
    target = await user_repo.get_by_telegram_id(target_tid)

    if not target:
        await message.answer("User not found.")
        return

    await user_repo.update_status(target.id, "suspended")
    admin_repo = AdminRepository(session)
    admin_record = await admin_repo.get_admin_by_user_id(db_user.id)
    if admin_record:
        await admin_repo.log_action(
            administrator_id=admin_record.id,
            action="suspend_user",
            target_type="user",
            target_id=target.id,
        )
    await message.answer(f"✅ User {target_tid} suspended.")


@router.message(Command("unsuspend"))
async def unsuspend_user(
    message: Message, db_user: User, session
) -> None:
    if not await _require_admin(message, db_user, session):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /unsuspend <telegram_id>")
        return

    try:
        target_tid = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID.")
        return

    from app.database.repositories.user_repo import UserRepository
    user_repo = UserRepository(session)
    target = await user_repo.get_by_telegram_id(target_tid)

    if not target:
        await message.answer("User not found.")
        return

    await user_repo.update_status(target.id, "active")
    admin_repo = AdminRepository(session)
    admin_record = await admin_repo.get_admin_by_user_id(db_user.id)
    if admin_record:
        await admin_repo.log_action(
            administrator_id=admin_record.id,
            action="unsuspend_user",
            target_type="user",
            target_id=target.id,
        )
    await message.answer(f"✅ User {target_tid} unsuspended.")


@router.callback_query(F.data == "admin:manage_admins")
async def manage_admins(
    callback: CallbackQuery, db_user: User, session
) -> None:
    if not await _require_admin(callback, db_user, session):
        return

    admin_repo = AdminRepository(session)
    admins = await admin_repo.get_all_admins()

    lines = ["👮 <b>Administrators</b>\n"]
    for adm in admins:
        u = adm.user
        name = u.first_name or u.username or f"id:{u.telegram_id}" if u else "?"
        status = "✅" if adm.is_active else "❌"
        lines.append(f"{status} {name} — {adm.role}")

    lines.append(
        "\n<i>Use /grant_admin &lt;telegram_id&gt; or /revoke_admin &lt;telegram_id&gt;</i>"
    )
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML")
    await callback.answer()


@router.message(Command("grant_admin"))
async def grant_admin(
    message: Message, db_user: User, session
) -> None:
    admin_repo = AdminRepository(session)
    if not await admin_repo.is_superadmin(db_user.telegram_id):
        await message.answer(t("not_authorized", db_user.language))
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /grant_admin <telegram_id>")
        return

    try:
        target_tid = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID.")
        return

    from app.database.repositories.user_repo import UserRepository
    user_repo = UserRepository(session)
    target = await user_repo.get_by_telegram_id(target_tid)

    if not target:
        # Create a stub user
        target, _ = await user_repo.get_or_create(telegram_id=target_tid)

    existing = await admin_repo.get_admin_by_user_id(target.id)
    if existing:
        await admin_repo.update_admin_status(existing.id, True)
        await admin_repo.update_admin_role(existing.id, "moderator")
        await message.answer(f"✅ User {target_tid} granted moderator role.")
    else:
        await admin_repo.create_admin(
            user_id=target.id,
            role="moderator",
            created_by=db_user.id,
        )
        await message.answer(f"✅ User {target_tid} is now a moderator.")


@router.message(Command("revoke_admin"))
async def revoke_admin(
    message: Message, db_user: User, session
) -> None:
    admin_repo = AdminRepository(session)
    if not await admin_repo.is_superadmin(db_user.telegram_id):
        await message.answer(t("not_authorized", db_user.language))
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /revoke_admin <telegram_id>")
        return

    try:
        target_tid = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID.")
        return

    existing = await admin_repo.get_admin_by_telegram_id(target_tid)
    if not existing:
        await message.answer("User is not an admin.")
        return

    if existing.role == "superadmin":
        await message.answer("❌ Cannot revoke superadmin role.")
        return

    await admin_repo.update_admin_status(existing.id, False)
    await message.answer(f"✅ Admin access revoked for user {target_tid}.")
