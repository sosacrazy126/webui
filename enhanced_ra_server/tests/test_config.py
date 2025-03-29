"""
Unit tests for the configuration module.
"""

import os
import pytest
from unittest.mock import patch

from enhanced_ra_server.config import load_config, validate_config, get_model_config


class TestConfig:
    """Test cases for the configuration module."""

    def test_default_config(self):
        """Test that default configuration values are correctly set."""
        config = load_config()
        
        # Check that default values are set
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 8000
        assert "model" in config
        assert isinstance(config["expert_enabled"], bool)
        assert isinstance(config["hil"], bool)

    def test_cli_arguments_override_defaults(self):
        """Test that CLI arguments override default values."""
        config = load_config(host="127.0.0.1", port=9000, model="custom-model")
        
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 9000
        assert config["model"] == "custom-model"

    def test_boolean_flag_handling(self):
        """Test handling of boolean flags with negative semantics."""
        config = load_config(no_expert=True, no_hil=True)
        
        assert config["expert_enabled"] is False
        assert config["hil"] is False

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = {
            "provider": "anthropic",
            "anthropic_api_key": "test-key",
            "port": 8000
        }
        
        # Should not raise an exception
        validate_config(config)

    def test_config_validation_missing_api_key(self):
        """Test validation fails when API key is missing."""
        config = {
            "provider": "anthropic",
            "anthropic_api_key": None,
            "port": 8000
        }
        
        with pytest.raises(ValueError) as excinfo:
            validate_config(config)
        
        assert "ANTHROPIC_API_KEY is required" in str(excinfo.value)

    def test_config_validation_invalid_port(self):
        """Test validation fails with invalid port."""
        config = {
            "provider": "anthropic",
            "anthropic_api_key": "test-key",
            "port": 70000  # Invalid port
        }
        
        with pytest.raises(ValueError) as excinfo:
            validate_config(config)
        
        assert "Port must be between 1 and 65535" in str(excinfo.value)

    def test_get_model_config_default(self):
        """Test getting default model configuration."""
        config = {
            "model": "default-model",
            "provider": "default-provider"
        }
        
        model_config = get_model_config(config)
        
        assert model_config["model"] == "default-model"
        assert model_config["provider"] == "default-provider"

    def test_get_model_config_research(self):
        """Test getting research-specific model configuration."""
        config = {
            "model": "default-model",
            "provider": "default-provider",
            "research_model": "research-model",
            "research_provider": "research-provider"
        }
        
        model_config = get_model_config(config, phase="research")
        
        assert model_config["model"] == "research-model"
        assert model_config["provider"] == "research-provider"

    def test_get_model_config_planning(self):
        """Test getting planning-specific model configuration."""
        config = {
            "model": "default-model",
            "provider": "default-provider",
            "planning_model": "planning-model",
            "planning_provider": "planning-provider"
        }
        
        model_config = get_model_config(config, phase="planning")
        
        assert model_config["model"] == "planning-model"
        assert model_config["provider"] == "planning-provider" 