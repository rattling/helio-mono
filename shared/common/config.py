"""Configuration management for Helionyx.

Supports environment-specific configuration via ENV variable:
- dev: Development environment (.env.dev)
- staging: Staging environment (.env.staging)
- live: Production environment (.env.live)

Loading strategy:
1. Load base .env file (if exists)
2. Overlay environment-specific .env.{ENV} file (if exists)
3. Environment variables override file values
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import dotenv_values, load_dotenv


class Config:
    """Configuration loaded from environment variables with environment-specific overlays."""

    def __init__(self):
        # Event Store
        self.EVENT_STORE_PATH = os.getenv("EVENT_STORE_PATH", "./data/events")

        # Projections Database
        self.PROJECTIONS_DB_PATH = os.getenv(
            "PROJECTIONS_DB_PATH", "./data/projections/helionyx.db"
        )

        # OpenAI
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        # OpenAI Rate Limiting
        self.OPENAI_RATE_LIMIT_RPM = int(os.getenv("OPENAI_RATE_LIMIT_RPM", "10"))
        self.OPENAI_RATE_LIMIT_TPM = int(os.getenv("OPENAI_RATE_LIMIT_TPM", "150000"))

        # LLM Error Handling
        self.LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.LLM_RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.0"))

        # LLM Cost Control
        self.LLM_DAILY_COST_WARNING_USD = float(os.getenv("LLM_DAILY_COST_WARNING_USD", "1.0"))
        self.LLM_DAILY_COST_LIMIT_USD = float(os.getenv("LLM_DAILY_COST_LIMIT_USD", "10.0"))

        # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        self.NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true")
        self.DAILY_SUMMARY_HOUR = int(os.getenv("DAILY_SUMMARY_HOUR", "20"))
        self.WEEKLY_SUMMARY_DAY = int(os.getenv("WEEKLY_SUMMARY_DAY", "0"))
        self.WEEKLY_SUMMARY_HOUR = int(os.getenv("WEEKLY_SUMMARY_HOUR", "9"))
        self.REMINDER_WINDOW_START = int(os.getenv("REMINDER_WINDOW_START", "8"))
        self.REMINDER_WINDOW_END = int(os.getenv("REMINDER_WINDOW_END", "21"))
        self.REMINDER_ADVANCE_HOURS = int(os.getenv("REMINDER_ADVANCE_HOURS", "24"))
        self.ATTENTION_URGENT_THRESHOLD = float(os.getenv("ATTENTION_URGENT_THRESHOLD", "60"))

        # Learning / shadow ranking (M6)
        self.SHADOW_RANKER_ENABLED = os.getenv("SHADOW_RANKER_ENABLED", "true").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        self.SHADOW_RANKER_CONFIDENCE_THRESHOLD = float(
            os.getenv("SHADOW_RANKER_CONFIDENCE_THRESHOLD", "0.6")
        )
        self.ATTENTION_BOUNDED_PERSONALIZATION_ENABLED = os.getenv(
            "ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", "false"
        ).lower() in ("1", "true", "yes", "on")

        # API Server
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # Environment (set by from_env or defaults to dev)
        self.ENV = os.getenv("ENV", "dev")

    @classmethod
    def from_env(cls, env: Optional[str] = None):
        """Create config with environment-specific loading.

        Args:
            env: Environment name ('dev', 'staging', 'live').
                 If None, reads from ENV environment variable or defaults to 'dev'.

        Returns:
            Config instance with environment-specific configuration loaded.

        Loading order (later overrides earlier):
        1. Base .env file
        2. Environment-specific .env.{env} file
        3. System environment variables
        """
        # Determine environment
        if env is None:
            env = os.getenv("ENV", "dev")

        # Validate environment
        valid_envs = ["dev", "staging", "live"]
        if env not in valid_envs:
            raise ValueError(f"Invalid environment: {env}. Must be one of {valid_envs}")

        # Set ENV before loading
        os.environ["ENV"] = env

        # Load base .env file first.
        # OS environment variables must always win over file values.
        base_env_path = Path(".env")
        base_values = dotenv_values(base_env_path) if base_env_path.exists() else {}

        set_from_base: set[str] = set()
        for key, value in base_values.items():
            if value is None:
                continue
            if key not in os.environ:
                os.environ[key] = value
                set_from_base.add(key)

        # Load environment-specific file (overlays base file values, but not OS env vars)
        env_file_path = Path(f".env.{env}")
        env_values = dotenv_values(env_file_path) if env_file_path.exists() else {}
        for key, value in env_values.items():
            if value is None:
                continue
            if key not in os.environ or key in set_from_base:
                os.environ[key] = value

        # Create and return config instance
        return cls()

    def validate_required(self):
        """Validate required configuration variables are present.

        Raises:
            ValueError: If required variables are missing.
        """
        required = {
            "EVENT_STORE_PATH": self.EVENT_STORE_PATH,
            "PROJECTIONS_DB_PATH": self.PROJECTIONS_DB_PATH,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    def validate_telegram(self):
        """Validate Telegram configuration.

        Raises:
            ValueError: If required Telegram variables are missing.
        """
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")

    def validate_telegram_notifications(self):
        """Validate Telegram notification configuration.

        Use this when the system needs to send proactive messages (reminders/summaries)
        that require a configured chat ID.

        Raises:
            ValueError: If required Telegram variables are missing.
        """
        self.validate_telegram()
        if not self.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID not set")
