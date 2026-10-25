"""
Application configuration with validation.

Loads settings from environment variables and validates them on startup.
Uses pydantic-settings for type-safe configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Required Settings ──────────────────────────────────────────
    bot_token: str = Field(
        ...,
        description="Telegram Bot Token from @BotFather",
    )
    bot_username: str = Field(
        ...,
        description="Telegram Bot Username (without @)",
    )
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string",
    )
    superadmin_telegram_id: int = Field(
        ...,
        description="Superadmin's numeric Telegram user ID",
    )
    public_channel_id: str = Field(
        ...,
        description="Public channel ID (numeric) or username (with @)",
    )
    public_channel_username: str = Field(
        ...,
        description="Public channel username (with @)",
    )

    # ── AI Configuration (Optional) ───────────────────────────────
    ai_provider: Optional[str] = Field(
        default=None,
        description="AI provider: openai, gemini, or None to disable",
    )
    ai_api_key: Optional[str] = Field(
        default=None,
        description="AI provider API key",
    )
    ai_model: Optional[str] = Field(
        default=None,
        description="AI model name",
    )

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # ── Localization ──────────────────────────────────────────────
    default_language: str = Field(
        default="en",
        description="Default language: en or am",
    )

    # ── Privacy ───────────────────────────────────────────────────
    privacy_notice_version: int = Field(
        default=1,
        description="Privacy notice version (increment on changes)",
    )

    # ── Marketplace Limits ────────────────────────────────────────
    max_active_listings_per_user: int = Field(
        default=10,
        description="Maximum active listings per seller",
    )
    max_photos_per_listing: int = Field(
        default=5,
        description="Maximum photos per listing",
    )
    max_description_length: int = Field(
        default=2000,
        description="Maximum description length in characters",
    )
    max_title_length: int = Field(
        default=100,
        description="Maximum title length in characters",
    )

    # ── Rate Limits ───────────────────────────────────────────────
    message_rate_limit: int = Field(
        default=30,
        description="Max messages per minute per user",
    )
    listing_rate_limit: int = Field(
        default=5,
        description="Max listing submissions per hour per user",
    )

    # ── Data Retention ────────────────────────────────────────────
    data_retention_days: int = Field(
        default=365,
        description="Data retention period in days (0 = keep forever)",
    )

    # ── Spam Detection ────────────────────────────────────────────
    spam_duplicate_window_seconds: int = Field(
        default=60,
        description="Time window to check for duplicate messages",
    )
    spam_max_duplicate_messages: int = Field(
        default=3,
        description="Max duplicate messages before spam flag",
    )

    # ── Validators ────────────────────────────────────────────────

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate bot token format without logging the actual value."""
        v = v.strip()
        if not v or len(v) < 20:
            raise ValueError(
                "BOT_TOKEN is required and must be a valid Telegram bot token. "
                "Get one from @BotFather."
            )
        # Basic format check: <numbers>:<alphanumeric>
        if ":" not in v:
            raise ValueError(
                "BOT_TOKEN format appears invalid. "
                "Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            )
        return v

    @field_validator("bot_username")
    @classmethod
    def validate_bot_username(cls, v: str) -> str:
        """Validate and clean bot username."""
        v = v.strip().lstrip("@")
        if not v:
            raise ValueError("BOT_USERNAME is required.")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        v = v.strip()
        if not v:
            raise ValueError("DATABASE_URL is required.")
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+asyncpg://' "
                "for production or 'sqlite+aiosqlite://' for testing."
            )
        return v

    @field_validator("superadmin_telegram_id")
    @classmethod
    def validate_superadmin_id(cls, v: int) -> int:
        """Validate superadmin ID is a positive integer."""
        if v <= 0:
            raise ValueError(
                "SUPERADMIN_TELEGRAM_ID must be a positive numeric Telegram user ID. "
                "Get yours from @userinfobot."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        v = v.upper().strip()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v

    @field_validator("default_language")
    @classmethod
    def validate_default_language(cls, v: str) -> str:
        """Validate default language."""
        v = v.lower().strip()
        if v not in ("en", "am"):
            raise ValueError("DEFAULT_LANGUAGE must be 'en' or 'am'.")
        return v

    @field_validator("public_channel_username")
    @classmethod
    def validate_channel_username(cls, v: str) -> str:
        """Ensure channel username starts with @."""
        v = v.strip()
        if v and not v.startswith("@"):
            v = f"@{v}"
        return v

    @model_validator(mode="after")
    def validate_ai_config(self) -> "Settings":
        """Validate AI configuration consistency."""
        if self.ai_provider and not self.ai_api_key:
            logging.warning(
                "AI_PROVIDER is set but AI_API_KEY is missing. "
                "AI features will be disabled."
            )
            self.ai_provider = None
        return self

    @property
    def ai_enabled(self) -> bool:
        """Check if AI features are properly configured."""
        return bool(self.ai_provider and self.ai_api_key)

    @property
    def bot_deep_link_base(self) -> str:
        """Base URL for bot deep links."""
        return f"https://t.me/{self.bot_username}"

    def get_numeric_log_level(self) -> int:
        """Get numeric logging level."""
        return getattr(logging, self.log_level, logging.INFO)


# ── Module-level singleton ──────────────────────────────────────────

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (for testing)."""
    global _settings
    _settings = None
