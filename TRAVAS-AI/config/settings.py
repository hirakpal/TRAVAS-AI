"""Application Settings

Load and manage configuration from environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # ========================================================================
    # LLM Configuration
    # ========================================================================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # LLM Hyperparameters
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))
    LLM_FREQUENCY_PENALTY: float = float(os.getenv("LLM_FREQUENCY_PENALTY", "0"))
    LLM_PRESENCE_PENALTY: float = float(os.getenv("LLM_PRESENCE_PENALTY", "0"))

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # ========================================================================
    # Logging
    # ========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/travas.log")
    LOG_TO_CONSOLE: bool = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"
    LOG_JSON: bool = os.getenv("LOG_JSON", "False").lower() == "true"

    # ========================================================================
    # Database
    # ========================================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./travas.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"

    # ========================================================================
    # Hotel Data
    # ========================================================================
    HOTEL_DATA_SOURCE: str = os.getenv("HOTEL_DATA_SOURCE", "local")
    HOTEL_API_KEY: str = os.getenv("HOTEL_API_KEY", "")

    # ========================================================================
    # Agent Settings
    # ========================================================================
    ATITHI_CONVERSATION_HISTORY_LIMIT: int = int(
        os.getenv("ATITHI_CONVERSATION_HISTORY_LIMIT", "100")
    )
    ATITHI_VERIFY_HOTEL_INFO: bool = (
        os.getenv("ATITHI_VERIFY_HOTEL_INFO", "True").lower() == "true"
    )
    ATITHI_REQUIRE_BOOKING_DISCLAIMER: bool = (
        os.getenv("ATITHI_REQUIRE_BOOKING_DISCLAIMER", "True").lower() == "true"
    )

    # ========================================================================
    # Cache Settings
    # ========================================================================
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "memory")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ========================================================================
    # API Timeouts
    # ========================================================================
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
    DB_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "30"))

    # ========================================================================
    # Retry Policy
    # ========================================================================
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF: float = float(os.getenv("RETRY_BACKOFF", "2"))

    # ========================================================================
    # Security
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_RPM", "60"))

    # ========================================================================
    # Email
    # ========================================================================
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # ========================================================================
    # Monitoring
    # ========================================================================
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    GA_ID: str = os.getenv("GA_ID", "")

    # ========================================================================
    # Feature Flags
    # ========================================================================
    FEATURE_ATITHI_AGENT: bool = (
        os.getenv("FEATURE_ATITHI_AGENT", "True").lower() == "true"
    )
    FEATURE_MULTI_LANGUAGE: bool = (
        os.getenv("FEATURE_MULTI_LANGUAGE", "False").lower() == "true"
    )
    FEATURE_HOTEL_COMPARISON: bool = (
        os.getenv("FEATURE_HOTEL_COMPARISON", "True").lower() == "true"
    )
    FEATURE_BOOKING_INTEGRATION: bool = (
        os.getenv("FEATURE_BOOKING_INTEGRATION", "False").lower() == "true"
    )

    @classmethod
    def get_llm_api_key(cls, provider: str) -> str:
        """
        Get API key for specified LLM provider.

        Args:
            provider: Provider name (openai, anthropic, gemini)

        Returns:
            API key for the provider
        """
        provider = provider.lower()
        if provider == "openai":
            return cls.OPENAI_API_KEY
        elif provider == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif provider == "gemini":
            return cls.GOOGLE_API_KEY
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @classmethod
    def get_llm_model(cls, provider: str) -> str:
        """
        Get default model for specified LLM provider.

        Args:
            provider: Provider name

        Returns:
            Model name for the provider
        """
        provider = provider.lower()
        if provider == "openai":
            return cls.OPENAI_MODEL
        elif provider == "anthropic":
            return cls.ANTHROPIC_MODEL
        elif provider == "gemini":
            return cls.GEMINI_MODEL
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.APP_ENV == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.APP_ENV == "development"

    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration"""
        if not cls.get_llm_api_key(cls.DEFAULT_LLM_PROVIDER):
            raise ValueError(
                f"API key not configured for provider: {cls.DEFAULT_LLM_PROVIDER}"
            )

    @classmethod
    def to_dict(cls) -> dict:
        """Get all settings as dictionary"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and isinstance(value, (str, int, float, bool))
        }


# Initialize logger
def setup_logging():
    """Setup application logging"""
    log_level = getattr(logging, Settings.LOG_LEVEL.upper())

    logger = logging.getLogger("travas")
    logger.setLevel(log_level)

    # File handler
    os.makedirs(os.path.dirname(Settings.LOG_FILE), exist_ok=True)
    file_handler = logging.FileHandler(Settings.LOG_FILE)
    file_handler.setLevel(log_level)

    # Console handler
    if Settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


# Initialize settings and logging
logger = setup_logging()
logger.info(f"TRAVAS-AI initialized in {Settings.APP_ENV} mode")
