"""
Messaging service — relays messages between buyers and sellers anonymously.
"""

from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message as TGMessage

from app.database.models import Conversation
from app.database.repositories.conversation_repo import ConversationRepository
from app.locales.strings import t

logger = logging.getLogger(__name__)


class MessagingService:
    """Handles anonymous message relay between conversation participants."""

    def __init__(self, conv_repo: ConversationRepository, bot: Bot):
        self.conv_repo = conv_repo
        self.bot = bot

    async def relay_message(
        self,
        conversation: Conversation,
        sender_id: int,         # internal DB user id
        sender_telegram_id: int,
        tg_message: TGMessage,
        lang: str = "en",
    ) -> bool:
        """
        Relay a message from sender to the other party.

        Returns True if successfully delivered.
        """
        # Determine recipient
        if sender_id == conversation.buyer_id:
            recipient_telegram_id = conversation.seller.telegram_id
            direction = "buyer_to_seller"
        else:
            recipient_telegram_id = conversation.buyer.telegram_id
            direction = "seller_to_buyer"

        # Determine message type and relay accordingly
        try:
            relayed_msg_id: Optional[int] = None

            if tg_message.text:
                relayed = await self.bot.send_message(
                    chat_id=recipient_telegram_id,
                    text=tg_message.text,
                    parse_mode=None,
                )
                relayed_msg_id = relayed.message_id

            elif tg_message.photo:
                photo = tg_message.photo[-1]  # Highest resolution
                relayed = await self.bot.send_photo(
                    chat_id=recipient_telegram_id,
                    photo=photo.file_id,
                    caption=tg_message.caption,
                )
                relayed_msg_id = relayed.message_id

            elif tg_message.video:
                relayed = await self.bot.send_video(
                    chat_id=recipient_telegram_id,
                    video=tg_message.video.file_id,
                    caption=tg_message.caption,
                )
                relayed_msg_id = relayed.message_id

            elif tg_message.voice:
                relayed = await self.bot.send_voice(
                    chat_id=recipient_telegram_id,
                    voice=tg_message.voice.file_id,
                )
                relayed_msg_id = relayed.message_id

            elif tg_message.document:
                relayed = await self.bot.send_document(
                    chat_id=recipient_telegram_id,
                    document=tg_message.document.file_id,
                    caption=tg_message.caption,
                )
                relayed_msg_id = relayed.message_id

            else:
                # Unsupported message type
                await self.bot.send_message(
                    chat_id=sender_telegram_id,
                    text="⚠️ This message type is not supported for relay.",
                )
                return False

            # Record message in DB
            content = tg_message.text or tg_message.caption
            file_id = None
            message_type = "text"
            if tg_message.photo:
                file_id = tg_message.photo[-1].file_id
                message_type = "photo"
            elif tg_message.video:
                file_id = tg_message.video.file_id
                message_type = "video"
            elif tg_message.voice:
                file_id = tg_message.voice.file_id
                message_type = "voice"
            elif tg_message.document:
                file_id = tg_message.document.file_id
                message_type = "document"

            db_msg = await self.conv_repo.add_message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                direction=direction,
                message_type=message_type,
                content=content,
                file_id=file_id,
                original_message_id=tg_message.message_id,
                delivery_status="delivered",
            )

            if relayed_msg_id:
                await self.conv_repo.update_message_delivery(
                    message_id=db_msg.id,
                    delivery_status="delivered",
                    relayed_message_id=relayed_msg_id,
                )

            return True

        except TelegramForbiddenError:
            logger.warning(
                "Cannot relay message — recipient %s blocked the bot.",
                recipient_telegram_id,
            )
            # Mark as failed
            await self.conv_repo.add_message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                direction=direction,
                message_type="text",
                content=tg_message.text or "[media]",
                original_message_id=tg_message.message_id,
                delivery_status="failed",
            )
            return False

        except TelegramBadRequest as e:
            logger.error("TelegramBadRequest relaying message: %s", e)
            return False

        except Exception as e:
            logger.error("Unexpected error relaying message: %s", e, exc_info=True)
            return False
