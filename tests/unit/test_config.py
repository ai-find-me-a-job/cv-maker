"""
Unit tests for the configuration module.

Tests cover:
- Environment variable loading
- Default values
- Validation
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import ROOT_DIR, Config


@pytest.fixture
def clean_env(monkeypatch):
    """
    Fixture to clean environment variables before each test.
    Ensures tests don't interfere with each other.
    """
    # Remove common config environment variables
    env_vars_to_remove = [
        "LLAMA_PARSE_API_KEY",
        "GOOGLE_API_KEY",
        "QDRANT_KEY",
        "GEMINI_MODEL",
        "GEMINI_TEMPERATURE",
        "REDIS_DSN",
        "SCRAPPING_PAGE_CONTENT_LIMIT",
    ]

    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)

    yield


class TestConfigDefaults:
    """Test default configuration values."""

    def test_defaults(self, clean_env, monkeypatch):
        """Test that default values are set correctly."""
        monkeypatch.setenv("LLAMA_PARSE_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("QDRANT_KEY", "test-key")
        monkeypatch.setenv("QDRANT_ENDPOINT", "test-key")

        config = Config()

        # Test all defaults in one test
        assert config.gemini_model == "gemini-2.0-flash"
        assert config.gemini_temperature == 0.7
        assert str(config.redis_dsn) == "redis://localhost:6379/0"
        assert config.scrapping_page_content_limit == 15000
        assert config.supported_languages == {
            "en": "English",
            "pt": "Portuguese (Brazilian)",
        }


class TestConfigEnvironmentVariables:
    """Test loading configuration from environment variables."""

    def test_load_and_override_from_env_vars(self, clean_env, monkeypatch):
        """Test loading configuration from environment variables and overriding defaults."""
        monkeypatch.setenv("LLAMA_PARSE_API_KEY", "llama-test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "google-test-key")
        monkeypatch.setenv("QDRANT_KEY", "qdrant-test-key")
        monkeypatch.setenv("QDRANT_ENDPOINT", "test-key")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
        monkeypatch.setenv("GEMINI_TEMPERATURE", "0.3")
        monkeypatch.setenv("REDIS_DSN", "redis://redis:6379/1")

        config = Config()

        # Test environment variable loading
        assert config.llama_parser_api_key == "llama-test-key"
        assert config.google_api_key == "google-test-key"
        assert config.qdrant_key == "qdrant-test-key"

        # Test overriding defaults
        assert config.gemini_model == "gemini-1.5-pro"
        assert config.gemini_temperature == 0.3
        assert str(config.redis_dsn) == "redis://redis:6379/1"


class TestConfigValidation:
    """Test configuration validation."""

    def test_missing_required_fields(self, clean_env):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}

        # Field aliases use uppercase names
        assert "LLAMA_PARSE_API_KEY" in error_fields
        assert "GOOGLE_API_KEY" in error_fields
        assert "QDRANT_KEY" in error_fields

    def test_invalid_values(self, clean_env, monkeypatch):
        """Test that invalid values raise ValidationError."""
        monkeypatch.setenv("LLAMA_PARSE_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("QDRANT_KEY", "test-key")

        # Test invalid Redis DSN
        monkeypatch.setenv("REDIS_DSN", "invalid-url")
        with pytest.raises(ValidationError):
            Config()

        # Test invalid temperature type
        monkeypatch.setenv("REDIS_DSN", "redis://localhost:6379/0")
        monkeypatch.setenv("GEMINI_TEMPERATURE", "not-a-number")
        with pytest.raises(ValidationError):
            Config()


class TestConfigSingleton:
    """Test config singleton."""

    def test_config_singleton_accessible(self):
        """Test that config singleton is accessible."""
        from app.core.config import Config, config

        assert isinstance(config, Config)
        assert hasattr(config, "llama_parser_api_key")
        assert hasattr(config, "google_api_key")
