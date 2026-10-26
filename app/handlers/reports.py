"""
Reports handler — user reporting of listings and other users.

Features:
- Report a listing (via callback button on listing detail)
- Report a user
- Admin viewing of reports
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.report_repo import ReportRepository
from app.keyboards.keyboards import cancel_keyboard, report_type_keyboard
from app.locales.strings import t

logger = logging.getLogger(__name__)
router = Router(name="reports")


# ── FSM States ─────────────────────────────────────────────────────────────


class ReportStates(StatesGroup):
    awaiting_details = State()


# ── Trigger: Report Listing ────────────────────────────────────────────────


@router.callback_query(F.data.startswith("report:listing:"))
async def report_listing_start(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    listing_id = int(callback.data.split(":")[2])
    lang = db_user.language
    await callback.message.answer(
        text=t("report_reason_prompt", lang),
        reply_markup=report_type_keyboard(listing_id=listing_id, lang=lang),
    )
    await callback.answer()


# ── Trigger: Report User ───────────────────────────────────────────────────


@router.callback_query(F.data.startswith("report:user:"))
async def report_user_start(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    user_id = int(callback.data.split(":")[2])
    lang = db_user.language
    await callback.message.answer(
        text=t("report_reason_prompt", lang),
        reply_markup=report_type_keyboard(user_id=user_id, lang=lang),
    )
    await callback.answer()


# ── Cancel ─────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "report:cancel")
async def report_cancel(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    await state.clear()
    lang = db_user.language
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.answer()


# ── Report Type Selected ───────────────────────────────────────────────────


@router.callback_query(F.data.startswith("report_type:"))
async def report_type_selected(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    """
    Callback data format: report_type:<reason>:listing:<id>
                      or: report_type:<reason>:user:<id>
    """
    parts = callback.data.split(":")
    # parts[0] = "report_type", parts[1] = reason, parts[2] = "listing"/"user", parts[3] = id
    if len(parts) < 4:
        await callback.answer("Invalid report data.", show_alert=True)
        return

    reason = parts[1]
    target_type = parts[2]
    target_id = int(parts[3])
    lang = db_user.language

    await state.set_state(ReportStates.awaiting_details)
    await state.update_data(
        report_reason=reason,
        report_target_type=target_type,
        report_target_id=target_id,
    )

    await callback.message.edit_text(
        text=t("report_details_prompt", lang),
        reply_markup=cancel_keyboard(lang),
    )
    await callback.answer()


# ── Report Details Received ────────────────────────────────────────────────


@router.message(ReportStates.awaiting_details)
async def report_details_received(
    message: Message, db_user: User, session, state: FSMContext
) -> None:
    lang = db_user.language
    data = await state.get_data()
    await state.clear()

    reason_type = data.get("report_reason", "other")
    target_type = data.get("report_target_type")
    target_id = data.get("report_target_id")
    details = message.text or "No details provided."

    full_reason = f"[{reason_type}] {details}"

    report_repo = ReportRepository(session)

    reported_listing_id = target_id if target_type == "listing" else None
    reported_user_id = target_id if target_type == "user" else None

    await report_repo.create_report(
        reporter_id=db_user.id,
        reported_listing_id=reported_listing_id,
        reported_user_id=reported_user_id,
        reason=full_reason,
        report_type=reason_type,
    )

    await message.answer(t("report_submitted", lang))
    logger.info(
        "User %d filed report: type=%s target=%s id=%s",
        db_user.id,
        reason_type,
        target_type,
        target_id,
    )


# ── Admin: View Reports ────────────────────────────────────────────────────


@router.callback_query(F.data == "admin:view_reports")
async def admin_view_reports(
    callback: CallbackQuery, db_user: User, session
) -> None:
    admin_repo = AdminRepository(session)
    if not await admin_repo.is_admin(db_user.telegram_id):
        await callback.answer(t("not_authorized", db_user.language), show_alert=True)
        return

    report_repo = ReportRepository(session)
    reports = await report_repo.get_open_reports(limit=10)

    if not reports:
        await callback.message.edit_text("✅ No open reports.")
        await callback.answer()
        return

    lines = ["🚩 <b>Open Reports</b>\n"]
    for r in reports:
        lines.append(
            f"• Report #{r.id} — {r.report_type}\n"
            f"  {r.reason[:100]}...\n"
            f"  Reported: {r.created_at.strftime('%Y-%m-%d')}"
        )

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML")
    await callback.answer()
