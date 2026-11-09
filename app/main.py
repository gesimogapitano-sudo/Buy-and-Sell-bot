"""
Application entry point for the Buy & Sell Telegram Marketplace Bot.

Initializes configuration, database, bot, and starts polling or webhook mode.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiohttp import web
from app.config import get_settings
from app.bot.bot import create_bot, create_dispatcher
from app.bot.middleware import (
    DatabaseSessionMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    UserRegistrationMiddleware,
)
from app.database.engine import close_engine, get_engine, get_session_factory
from app.database.models import Base
from app.database.repositories.admin_repo import AdminRepository
from app.database.repositories.user_repo import UserRepository
from app.utils.redis_client import close_redis
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Reduce noise from third-party libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


async def initialize_superadmin(settings) -> None:
    """
    Ensure the superadmin user exists in the database.

    The superadmin is configured via the SUPERADMIN_TELEGRAM_ID
    environment variable and cannot be granted through bot commands alone.
    """
    logger = logging.getLogger(__name__)
    factory = get_session_factory()
    async with factory() as session:
        try:
            user_repo = UserRepository(session)
            admin_repo = AdminRepository(session)

            # Get or create the superadmin user
            user, created = await user_repo.get_or_create(
                telegram_id=settings.superadmin_telegram_id,
                language=settings.default_language,
            )
            if created:
                logger.info("Created superadmin user record.")

            # Check if already an admin
            admin = await admin_repo.get_admin_by_user_id(user.id)
            if admin:
                if admin.role != "superadmin" or not admin.is_active:
                    await admin_repo.update_admin_role(admin.id, "superadmin")
                    await admin_repo.update_admin_status(admin.id, True)
                    logger.info("Updated existing admin to active superadmin.")
            else:
                await admin_repo.create_admin(
                    user_id=user.id,
                    role="superadmin",
                    created_by=None,
                )
                logger.info("Superadmin administrator record created.")

            # Seed default categories
            await admin_repo.seed_default_categories()

            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Failed to initialize superadmin: %s", e)
            raise


def register_routers(dp) -> None:
    """Register all handler routers with the dispatcher."""
    # Import handlers here to avoid circular imports
    from app.handlers.start import router as start_router
    from app.handlers.listings import router as listings_router
    from app.handlers.my_listings import router as my_listings_router
    from app.handlers.messaging import router as messaging_router
    from app.handlers.admin import router as admin_router
    from app.handlers.admin_conversations import router as admin_conv_router
    from app.handlers.reports import router as reports_router
    from app.handlers.settings import router as settings_router

    dp.include_router(start_router)
    dp.include_router(listings_router)
    dp.include_router(my_listings_router)
    dp.include_router(messaging_router)
    dp.include_router(admin_router)
    dp.include_router(admin_conv_router)
    dp.include_router(reports_router)
    dp.include_router(settings_router)


def register_middleware(dp) -> None:
    """Register middleware stack in correct order."""
    # Middleware runs in registration order (outermost first)
    # 1. Logging (outermost — wraps everything)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    # 2. Rate limiting
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())

    # 3. Database session (needed by user registration)
    dp.message.middleware(DatabaseSessionMiddleware())
    dp.callback_query.middleware(DatabaseSessionMiddleware())

    # 4. User registration (innermost — needs session)
    dp.message.middleware(UserRegistrationMiddleware())
    dp.callback_query.middleware(UserRegistrationMiddleware())


async def run_webhook(settings, bot, dp) -> None:
    """Run the bot behind an HTTP webhook server."""
    logger = logging.getLogger(__name__)
    if not settings.webhook_url:
        raise ValueError("WEBHOOK_URL is required for webhook mode.")

    webhook_url = f"{settings.webhook_url}{settings.webhook_path}"
    app = web.Application()
    app.router.add_get("/health", lambda _: web.json_response({"status": "ok"}))
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret_token,
    ).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.port)
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        secret_token=settings.webhook_secret_token,
    )
    await site.start()
    logger.info("Webhook server listening on port %s.", settings.port)
    logger.info("Telegram webhook configured at %s.", webhook_url)

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def main() -> None:
    """Main application entry point."""
    logger = logging.getLogger(__name__)

    # Load and validate configuration
    try:
        settings = get_settings()
    except Exception as e:
        print(f"\n❌ Configuration Error:\n{e}\n")
        print("Please check your .env file. See .env.example for reference.")
        sys.exit(1)

    # Set up logging
    setup_logging(settings.log_level)
    logger.info("=" * 60)
    logger.info("Buy & Sell Marketplace Bot starting...")
    logger.info("Bot: @%s", settings.bot_username)
    logger.info("AI: %s", "enabled" if settings.ai_enabled else "disabled")
    logger.info("Language: %s", settings.default_language)
    logger.info("=" * 60)

    # Initialize database engine
    get_engine()

    # Initialize superadmin and seed data
    await initialize_superadmin(settings)

    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    # Register middleware and handlers
    register_middleware(dp)
    register_routers(dp)

    try:
        if settings.webhook_url:
            await run_webhook(settings, bot, dp)
        else:
            # Delete any pending webhook to ensure long polling works locally.
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Starting long polling...")
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
            )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal.")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await close_engine()
        await close_redis()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
