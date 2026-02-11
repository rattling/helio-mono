"""Tests for environment-aware configuration system."""

import os
import pytest
from pathlib import Path
from shared.common.config import Config


class TestEnvironmentConfig:
    """Test environment-specific configuration loading."""
    
    def test_from_env_defaults_to_dev(self, monkeypatch, tmp_path):
        """Test that from_env defaults to dev environment when ENV not set."""
        # Clear ENV if set
        monkeypatch.delenv('ENV', raising=False)
        
        config = Config.from_env()
        assert config.ENV == 'dev'
    
    def test_from_env_explicit_environment(self, monkeypatch):
        """Test from_env with explicitly specified environment."""
        monkeypatch.delenv('ENV', raising=False)
        
        config = Config.from_env('staging')
        assert config.ENV == 'staging'
    
    def test_from_env_reads_env_variable(self, monkeypatch):
        """Test from_env reads from ENV environment variable."""
        monkeypatch.setenv('ENV', 'live')
        
        config = Config.from_env()
        assert config.ENV == 'live'
    
    def test_from_env_invalid_environment(self):
        """Test from_env raises ValueError for invalid environment."""
        with pytest.raises(ValueError, match="Invalid environment"):
            Config.from_env('production')
    
    def test_from_env_valid_environments(self, monkeypatch):
        """Test all valid environment names are accepted."""
        monkeypatch.delenv('ENV', raising=False)
        
        for env in ['dev', 'staging', 'live']:
            config = Config.from_env(env)
            assert config.ENV == env
    
    def test_environment_overlay_priority(self, monkeypatch, tmp_path):
        """Test that environment-specific file overlays base .env."""
        # Change to temp directory for this test
        monkeypatch.chdir(tmp_path)
        
        # Create base .env
        base_env = tmp_path / '.env'
        base_env.write_text('LOG_LEVEL=INFO\nOPENAI_MODEL=gpt-4\n')
        
        # Create .env.dev that overrides LOG_LEVEL
        dev_env = tmp_path / '.env.dev'
        dev_env.write_text('LOG_LEVEL=DEBUG\n')
        
        # Clear any existing env vars
        monkeypatch.delenv('LOG_LEVEL', raising=False)
        monkeypatch.delenv('OPENAI_MODEL', raising=False)
        monkeypatch.delenv('ENV', raising=False)
        
        config = Config.from_env('dev')
        
        # LOG_LEVEL should be from .env.dev (overlay)
        assert config.LOG_LEVEL == 'DEBUG'
        # OPENAI_MODEL should be from .env (base)
        assert config.OPENAI_MODEL == 'gpt-4'
    
    def test_validate_required(self):
        """Test validate_required checks for required variables."""
        config = Config()
        # Should not raise - defaults are provided
        config.validate_required()
        
        # Test with missing required field
        config.EVENT_STORE_PATH = None
        with pytest.raises(ValueError, match="Missing required configuration"):
            config.validate_required()
    
    def test_validate_telegram(self, monkeypatch):
        """Test validate_telegram checks for Telegram bot configuration."""
        # Clear any existing env vars
        monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
        monkeypatch.delenv('TELEGRAM_CHAT_ID', raising=False)
        
        config = Config()
        
        # Should raise - no credentials set
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            config.validate_telegram()
        
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_token')
        config = Config()
        # Should not raise now (chat id is optional for bot startup)
        config.validate_telegram()

        # Notifications require chat id
        with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID"):
            config.validate_telegram_notifications()

        monkeypatch.setenv('TELEGRAM_CHAT_ID', '12345')
        config = Config()
        config.validate_telegram_notifications()
    
    def test_config_defaults(self, monkeypatch):
        """Test that Config has sensible defaults."""
        # Clear all relevant env vars to ensure we test defaults
        monkeypatch.delenv('EVENT_STORE_PATH', raising=False)
        monkeypatch.delenv('PROJECTIONS_DB_PATH', raising=False)
        monkeypatch.delenv('OPENAI_MODEL', raising=False)
        monkeypatch.delenv('OPENAI_MAX_TOKENS', raising=False)
        monkeypatch.delenv('LOG_LEVEL', raising=False)
        monkeypatch.delenv('ENV', raising=False)
        
        config = Config()
        
        assert config.EVENT_STORE_PATH == './data/events'
        assert config.PROJECTIONS_DB_PATH == './data/projections/helionyx.db'
        assert config.OPENAI_MODEL == 'gpt-4o-mini'
        assert config.OPENAI_MAX_TOKENS == 1000
        assert config.LOG_LEVEL == 'INFO'
        assert config.ENV == 'dev'
    
    def test_backwards_compatibility(self):
        """Test that existing code using Config() still works."""
        # This tests backwards compatibility for code that does:
        # config = Config()
        config = Config()
        assert config is not None
        assert hasattr(config, 'EVENT_STORE_PATH')
        assert hasattr(config, 'ENV')
