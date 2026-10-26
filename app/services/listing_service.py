"""
Listing service — business logic for publishing listings to the channel.
"""

from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import get_settings
from app.database.models import Listing
from app.database.repositories.listing_repo import ListingRepository
from app.locales.strings import t
from app.utils.helpers import format_condition, format_price

logger = logging.getLogger(__name__)


class ListingService:
    """Handles listing publication, withdrawal, and channel message management."""

    def __init__(self, listing_repo: ListingRepository, bot: Bot):
        self.listing_repo = listing_repo
        self.bot = bot
        self.settings = get_settings()

    def _build_channel_post(self, listing: Listing, category_name: str) -> str:
        """Build the HTML text for a channel post."""
        contact_link = (
            f"https://t.me/{self.settings.bot_username}"
            f"?start=listing_{listing.public_token}"
        )
        condition = format_condition(listing.condition)
        price = format_price(listing.price, listing.currency)

        return t(
            "channel_post",
            lang="en",  # Channel posts always in English (default)
            title=listing.title,
            description=listing.description,
            price=price,
            location=listing.location,
            category=category_name,
            condition=condition,
            contact_link=contact_link,
        )

    async def publish_to_channel(
        self, listing: Listing, category_name: str
    ) -> Optional[int]:
        """
        Publish an approved listing to the public channel.

        Returns the channel message ID on success, or None on failure.
        """
        channel_id = self.settings.public_channel_id
        text = self._build_channel_post(listing, category_name)

        try:
            # Send with photos if available
            media = listing.media
            if media:
                if len(media) == 1:
                    # Single photo
                    msg = await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=media[0].file_id,
                        caption=text,
                        parse_mode="HTML",
                    )
                else:
                    # Media group (up to 10 photos)
                    from aiogram.types import InputMediaPhoto

                    media_group = []
                    for i, m in enumerate(media[:10]):
                        caption = text if i == 0 else None
                        media_group.append(
                            InputMediaPhoto(
                                media=m.file_id,
                                caption=caption,
                                parse_mode="HTML" if caption else None,
                            )
                        )
                    msgs = await self.bot.send_media_group(
                        chat_id=channel_id, media=media_group
                    )
                    msg = msgs[0]  # Use first message ID for reference
            else:
                # Text only
                msg = await self.bot.send_message(
                    chat_id=channel_id, text=text, parse_mode="HTML"
                )

            # Store the channel message ID
            await self.listing_repo.set_channel_message(
                listing_id=listing.id,
                channel_message_id=msg.message_id,
                channel_id=str(channel_id),
            )
            logger.info(
                "Published listing %d to channel as message %d",
                listing.id,
                msg.message_id,
            )
            return msg.message_id

        except TelegramForbiddenError:
            logger.error(
                "Bot is not a member of channel %s. Cannot publish listing %d.",
                channel_id,
                listing.id,
            )
        except TelegramBadRequest as e:
            logger.error(
                "Failed to publish listing %d to channel: %s", listing.id, e
            )
        except Exception as e:
            logger.error(
                "Unexpected error publishing listing %d: %s", listing.id, e
            )

        return None

    async def delete_from_channel(self, listing: Listing) -> bool:
        """
        Delete a listing's channel message (e.g. on withdrawal or removal).

        Returns True on success.
        """
        if not listing.channel_message_id or not listing.channel_id:
            return False

        try:
            await self.bot.delete_message(
                chat_id=listing.channel_id,
                message_id=listing.channel_message_id,
            )
            logger.info(
                "Deleted channel message %d for listing %d",
                listing.channel_message_id,
                listing.id,
            )
            return True
        except TelegramBadRequest:
            logger.warning(
                "Could not delete channel message %d (already deleted?)",
                listing.channel_message_id,
            )
        except Exception as e:
            logger.error(
                "Error deleting channel message for listing %d: %s", listing.id, e
            )

        return False

    async def notify_seller(
        self,
        seller_telegram_id: int,
        key: str,
        lang: str = "en",
        **kwargs,
    ) -> None:
        """Send a notification message to the seller."""
        try:
            await self.bot.send_message(
                chat_id=seller_telegram_id,
                text=t(key, lang, **kwargs),
                parse_mode="HTML",
            )
        except TelegramForbiddenError:
            logger.warning(
                "Cannot notify seller %s — bot was blocked.",
                seller_telegram_id,
            )
        except Exception as e:
            logger.error("Error notifying seller: %s", e)
