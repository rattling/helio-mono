"""Configuration management for Helionyx."""

import os
from pathlib import Path


class Config:
    """Configuration loaded from environment variables."""
    
    def __init__(self):
        # Event Store
        self.EVENT_STORE_PATH = os.getenv('EVENT_STORE_PATH', './data/events')
        
        # Projections Database
        self.PROJECTIONS_DB_PATH = os.getenv('PROJECTIONS_DB_PATH', './data/projections/helionyx.db')
        
        # OpenAI
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        # OpenAI Rate Limiting
        self.OPENAI_RATE_LIMIT_RPM = int(os.getenv('OPENAI_RATE_LIMIT_RPM', '10'))
        self.OPENAI_RATE_LIMIT_TPM = int(os.getenv('OPENAI_RATE_LIMIT_TPM', '150000'))
        
        # LLM Error Handling
        self.LLM_MAX_RETRIES = int(os.getenv('LLM_MAX_RETRIES', '3'))
        self.LLM_RETRY_BASE_DELAY = float(os.getenv('LLM_RETRY_BASE_DELAY', '1.0'))
        
        # LLM Cost Control
        self.LLM_DAILY_COST_WARNING_USD = float(os.getenv('LLM_DAILY_COST_WARNING_USD', '1.0'))
        self.LLM_DAILY_COST_LIMIT_USD = float(os.getenv('LLM_DAILY_COST_LIMIT_USD', '10.0'))
        
        # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        self.NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'true')
        self.DAILY_SUMMARY_HOUR = int(os.getenv('DAILY_SUMMARY_HOUR', '20'))
        self.REMINDER_WINDOW_START = int(os.getenv('REMINDER_WINDOW_START', '8'))
        self.REMINDER_WINDOW_END = int(os.getenv('REMINDER_WINDOW_END', '21'))
        self.REMINDER_ADVANCE_HOURS = int(os.getenv('REMINDER_ADVANCE_HOURS', '24'))
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables."""
        return cls()
    
    def validate_telegram(self):
        """Validate Telegram configuration."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        if not self.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID not set")
