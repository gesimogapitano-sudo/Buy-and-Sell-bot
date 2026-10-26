"""
Listings handler — multi-step FSM for creating a new listing.

Steps:
1. listing_type  (product / service)
2. category      (from DB)
3. title         (text)
4. description   (text)
5. brand         (text, optional)
6. condition     (new / like_new / used / refurbished)  — skipped for services
7. price         (decimal)
8. currency      (ETB / USD / EUR / GBP)
9. location      (text)
10. photos       (one or more)
11. preview & submit
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.database.models import User
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.listing_repo import ListingRepository
from app.keyboards.keyboards import (
    categories_keyboard,
    condition_keyboard,
    currency_keyboard,
    done_cancel_keyboard,
    listing_confirm_keyboard,
    listing_type_keyboard,
    main_menu,
    skip_cancel_keyboard,
)
from app.locales.strings import t
from app.utils.helpers import format_condition, format_price
from app.utils.validators import (
    ValidationError,
    validate_brand,
    validate_description,
    validate_location,
    validate_price,
    validate_title,
)

logger = logging.getLogger(__name__)
router = Router(name="listings")


# ── FSM States ─────────────────────────────────────────────────────────────


class NewListingStates(StatesGroup):
    listing_type = State()
    category = State()
    title = State()
    description = State()
    brand = State()
    condition = State()
    price = State()
    currency = State()
    location = State()
    photos = State()
    preview = State()


# ── Entry Point ────────────────────────────────────────────────────────────


@router.message(F.text.in_({"🏷️ Sell Something", "🏷️ ሽያጭ ጀምር"}))
async def start_listing(message: Message, db_user: User, state: FSMContext) -> None:
    """Begin the listing creation flow."""
    lang = db_user.language

    if not db_user.consent_given:
        await message.answer(t("consent_required", lang), parse_mode="HTML")
        return

    settings = get_settings()
    # Check listing limit using session from state
    # We'll do the check inside FSM data after we have session
    await state.set_state(NewListingStates.listing_type)
    await state.update_data(lang=lang)
    await message.answer(
        text=t("listing_type_prompt", lang),
        parse_mode="HTML",
        reply_markup=listing_type_keyboard(lang),
    )


# ── Cancel ─────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "listing:cancel")
async def cancel_listing(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    await state.clear()
    lang = db_user.language
    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(callback.from_user.id)
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.message.answer(
        text=t("welcome", lang),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang, is_admin=is_admin),
    )
    await callback.answer()


# ── Step 1: Listing Type ───────────────────────────────────────────────────


@router.callback_query(
    NewListingStates.listing_type, F.data.startswith("listing_type:")
)
async def step_listing_type(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    listing_type = callback.data.split(":")[1]
    lang = db_user.language

    # Check active listing limit
    settings = get_settings()
    listing_repo = ListingRepository(session)
    active_count = await listing_repo.get_active_listing_count(db_user.id)
    if active_count >= settings.max_active_listings_per_user:
        await callback.message.edit_text(
            t("listing_limit_reached", lang, limit=settings.max_active_listings_per_user)
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(listing_type=listing_type)

    # Fetch categories
    admin_repo = AdminRepository(session)
    categories = await admin_repo.get_active_categories()

    await state.set_state(NewListingStates.category)
    await callback.message.edit_text(
        text=t("category_prompt", lang),
        reply_markup=categories_keyboard(categories, lang),
    )
    await callback.answer()


# ── Step 2: Category ───────────────────────────────────────────────────────


@router.callback_query(NewListingStates.category, F.data.startswith("category:"))
async def step_category(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    category_id = int(callback.data.split(":")[1])
    lang = db_user.language
    await state.update_data(category_id=category_id)
    await state.set_state(NewListingStates.title)
    await callback.message.edit_text(
        text=t("title_prompt", lang), parse_mode="HTML"
    )
    await callback.answer()


# ── Step 3: Title ──────────────────────────────────────────────────────────


@router.message(NewListingStates.title)
async def step_title(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    try:
        title = validate_title(message.text or "")
    except ValidationError as e:
        await message.answer(f"⚠️ {e.message}")
        return

    await state.update_data(title=title)
    await state.set_state(NewListingStates.description)
    await message.answer(text=t("description_prompt", lang), parse_mode="HTML")


# ── Step 4: Description ────────────────────────────────────────────────────


@router.message(NewListingStates.description)
async def step_description(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    try:
        description = validate_description(message.text or "")
    except ValidationError as e:
        await message.answer(f"⚠️ {e.message}")
        return

    await state.update_data(description=description)
    await state.set_state(NewListingStates.brand)
    await message.answer(
        text=t("brand_prompt", lang),
        reply_markup=skip_cancel_keyboard(lang),
    )


# ── Step 5: Brand (optional) ───────────────────────────────────────────────


@router.callback_query(NewListingStates.brand, F.data == "listing:skip")
async def step_brand_skip(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    await state.update_data(brand=None)
    await _ask_condition_or_price(callback.message, db_user, state, edit=True)
    await callback.answer()


@router.message(NewListingStates.brand)
async def step_brand(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    try:
        brand = validate_brand(message.text or "")
    except ValidationError as e:
        await message.answer(f"⚠️ {e.message}")
        return

    await state.update_data(brand=brand if brand else None)
    await _ask_condition_or_price(message, db_user, state, edit=False)


async def _ask_condition_or_price(
    message_or_msg, db_user: User, state: FSMContext, edit: bool = False
) -> None:
    """Go to condition step for products, skip to price for services."""
    data = await state.get_data()
    lang = db_user.language
    listing_type = data.get("listing_type", "product")

    if listing_type == "product":
        await state.set_state(NewListingStates.condition)
        text = t("condition_prompt", lang)
        kb = condition_keyboard(lang)
        if edit:
            await message_or_msg.edit_text(text=text, reply_markup=kb)
        else:
            await message_or_msg.answer(text=text, reply_markup=kb)
    else:
        # Service — skip condition
        await state.update_data(condition=None)
        await state.set_state(NewListingStates.price)
        text = t("price_prompt", lang)
        if edit:
            await message_or_msg.edit_text(text=text)
        else:
            await message_or_msg.answer(text=text)


# ── Step 6: Condition ──────────────────────────────────────────────────────


@router.callback_query(NewListingStates.condition, F.data.startswith("condition:"))
async def step_condition(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    condition = callback.data.split(":")[1]
    lang = db_user.language
    await state.update_data(condition=condition)
    await state.set_state(NewListingStates.price)
    await callback.message.edit_text(text=t("price_prompt", lang))
    await callback.answer()


# ── Step 7: Price ──────────────────────────────────────────────────────────


@router.message(NewListingStates.price)
async def step_price(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    try:
        price = validate_price(message.text or "")
    except ValidationError as e:
        await message.answer(f"⚠️ {e.message}")
        return

    await state.update_data(price=str(price))
    await state.set_state(NewListingStates.currency)
    await message.answer(
        text=t("currency_prompt", lang),
        reply_markup=currency_keyboard(lang),
    )


# ── Step 8: Currency ───────────────────────────────────────────────────────


@router.callback_query(NewListingStates.currency, F.data.startswith("currency:"))
async def step_currency(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    currency = callback.data.split(":")[1]
    lang = db_user.language
    await state.update_data(currency=currency)
    await state.set_state(NewListingStates.location)
    await callback.message.edit_text(text=t("location_prompt", lang))
    await callback.answer()


# ── Step 9: Location ───────────────────────────────────────────────────────


@router.message(NewListingStates.location)
async def step_location(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    from app.utils.validators import validate_location
    try:
        location = validate_location(message.text or "")
    except ValidationError as e:
        await message.answer(f"⚠️ {e.message}")
        return

    settings = get_settings()
    await state.update_data(location=location, photos=[])
    await state.set_state(NewListingStates.photos)
    await message.answer(
        text=t("photos_prompt", lang, max=settings.max_photos_per_listing),
        parse_mode="HTML",
        reply_markup=done_cancel_keyboard(lang),
    )


# ── Step 10: Photos ────────────────────────────────────────────────────────


@router.message(NewListingStates.photos, F.photo)
async def step_photo(
    message: Message, db_user: User, state: FSMContext
) -> None:
    lang = db_user.language
    settings = get_settings()
    data = await state.get_data()
    photos: list = data.get("photos", [])

    if len(photos) >= settings.max_photos_per_listing:
        await message.answer(
            t("photos_max_reached", lang, max=settings.max_photos_per_listing)
        )
        return

    # Store highest resolution file_id and unique_id
    photo = message.photo[-1]
    photos.append(
        {
            "file_id": photo.file_id,
            "file_unique_id": photo.file_unique_id,
            "file_size": photo.file_size,
        }
    )
    await state.update_data(photos=photos)

    if len(photos) >= settings.max_photos_per_listing:
        await message.answer(
            t("photos_max_reached", lang, max=settings.max_photos_per_listing),
            reply_markup=done_cancel_keyboard(lang),
        )
    else:
        await message.answer(
            t(
                "photo_added",
                lang,
                current=len(photos),
                max=settings.max_photos_per_listing,
            ),
            reply_markup=done_cancel_keyboard(lang),
        )


@router.callback_query(NewListingStates.photos, F.data == "listing:done_photos")
async def step_photos_done(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    lang = db_user.language
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await callback.answer(t("photos_required", lang), show_alert=True)
        return

    # Build preview
    admin_repo = AdminRepository(session)
    category = await admin_repo.get_category_by_id(data["category_id"])
    category_name = (
        (category.name_am if lang == "am" else category.name_en) if category else "?"
    )

    price_str = format_price(Decimal(data["price"]), data["currency"])
    condition_str = format_condition(data.get("condition"))
    listing_type_str = (
        t("btn_type_product", lang)
        if data["listing_type"] == "product"
        else t("btn_type_service", lang)
    )

    preview_text = t(
        "listing_preview",
        lang,
        listing_type=listing_type_str,
        category=category_name,
        title=data["title"],
        description=data["description"][:300]
        + ("..." if len(data["description"]) > 300 else ""),
        brand=data.get("brand") or "N/A",
        condition=condition_str,
        price=price_str,
        location=data["location"],
    )

    await state.set_state(NewListingStates.preview)
    await callback.message.edit_text(
        text=preview_text,
        parse_mode="HTML",
        reply_markup=listing_confirm_keyboard(lang),
    )
    await callback.answer()


# ── Step 11: Submit ────────────────────────────────────────────────────────


@router.callback_query(NewListingStates.preview, F.data == "listing:submit")
async def step_submit(
    callback: CallbackQuery, db_user: User, session, state: FSMContext
) -> None:
    lang = db_user.language
    data = await state.get_data()
    await state.clear()

    listing_repo = ListingRepository(session)

    # Create the listing
    listing = await listing_repo.create(
        seller_id=db_user.id,
        category_id=data["category_id"],
        listing_type=data["listing_type"],
        title=data["title"],
        description=data["description"],
        price=Decimal(data["price"]),
        currency=data["currency"],
        location=data["location"],
        brand=data.get("brand"),
        condition=data.get("condition"),
    )

    # Attach photos
    for i, photo_data in enumerate(data.get("photos", [])):
        await listing_repo.add_media(
            listing_id=listing.id,
            file_id=photo_data["file_id"],
            file_unique_id=photo_data["file_unique_id"],
            media_type="photo",
            file_size=photo_data.get("file_size"),
            sort_order=i,
        )

    # Move to pending
    await listing_repo.update_status(listing.id, "pending", actor_id=db_user.id)

    admin_repo = AdminRepository(session)
    is_admin = await admin_repo.is_admin(callback.from_user.id)

    await callback.message.edit_text(
        text=t("listing_submitted", lang), parse_mode="HTML"
    )
    await callback.message.answer(
        text=t("welcome", lang),
        parse_mode="HTML",
        reply_markup=main_menu(lang=lang, is_admin=is_admin),
    )
    await callback.answer()
    logger.info(
        "User %d submitted listing %d for review.", db_user.id, listing.id
    )
