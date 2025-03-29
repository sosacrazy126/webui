"""
Configuration module for Enhanced RA.Aid Server.

This module handles loading and validation of configuration settings from
environment variables and command-line arguments.
"""

import os
from typing import Dict, Any, Optional


# Default configuration values
DEFAULT_CONFIG = {
    # Server settings
    "host": "0.0.0.0",
    "port": 8000,
    
    # Model settings
    "model": os.environ.get("RA_AID_MODEL", "claude-3-haiku-20240307"),
    "research_only": False,
    "expert_enabled": True,
    "hil": True,  # Human-in-the-loop
    
    # Research model settings (can differ from main model)
    "research_model": os.environ.get("RA_AID_RESEARCH_MODEL", None),
    "research_provider": os.environ.get("RA_AID_RESEARCH_PROVIDER", None),
    
    # Planning model settings
    "planning_model": os.environ.get("RA_AID_PLANNING_MODEL", None),
    "planning_provider": os.environ.get("RA_AID_PLANNING_PROVIDER", None),
    
    # Expert model settings
    "expert_model": os.environ.get("RA_AID_EXPERT_MODEL", "claude-3-opus-20240229"),
    "expert_provider": os.environ.get("RA_AID_EXPERT_PROVIDER", "anthropic"),
    
    # Provider settings
    "provider": os.environ.get("RA_AID_PROVIDER", "anthropic"),
    
    # Memory settings
    "memory_path": os.environ.get("RA_AID_MEMORY_PATH", "~/.ra_aid/memory.db"),
    
    # API keys
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", None),
    "openai_api_key": os.environ.get("OPENAI_API_KEY", None),
    "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY", None),
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", None),
    "tavily_api_key": os.environ.get("TAVILY_API_KEY", None),
}


def load_config(**kwargs) -> Dict[str, Any]:
    """
    Load configuration by combining defaults, environment variables, and CLI arguments.
    
    Args:
        **kwargs: Keyword arguments from command-line parsing
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary
    
    Raises:
        ValueError: If configuration validation fails
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Update with provided arguments (from CLI)
    for key, value in kwargs.items():
        if value is not None:  # Only override if value is provided
            # Convert CLI arg format (dash-separated) to config format (underscore-separated)
            config_key = key.replace("-", "_")
            config[config_key] = value
    
    # Special handling for boolean flags with negative semantics
    if kwargs.get("no_expert"):
        config["expert_enabled"] = False
    
    if kwargs.get("no_hil"):
        config["hil"] = False
    
    # Validate configuration
    validate_config(config)
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration, raising an error if any issues are found.
    
    Args:
        config: Configuration dictionary to validate
    
    Raises:
        ValueError: If validation fails
    """
    # Validate API keys are available for selected providers
    provider = config.get("provider")
    if provider == "anthropic" and not config.get("anthropic_api_key"):
        raise ValueError("ANTHROPIC_API_KEY is required when using the Anthropic provider")
    
    if provider == "openai" and not config.get("openai_api_key"):
        raise ValueError("OPENAI_API_KEY is required when using the OpenAI provider")
        
    if provider == "openrouter" and not config.get("openrouter_api_key"):
        raise ValueError("OPENROUTER_API_KEY is required when using the OpenRouter provider")
        
    if provider == "gemini" and not config.get("gemini_api_key"):
        raise ValueError("GEMINI_API_KEY is required when using the Gemini provider")
    
    # Validate port is in valid range
    port = config.get("port")
    if not (1 <= port <= 65535):
        raise ValueError(f"Port must be between 1 and 65535, got {port}")


def get_model_config(config: Dict[str, Any], phase: Optional[str] = None) -> Dict[str, Any]:
    """
    Get model configuration for a specific phase.
    
    Args:
        config: Main configuration dictionary
        phase: Optional phase name ("research", "planning", or None for default)
    
    Returns:
        Dict containing relevant model configuration for the specified phase
    """
    if phase == "research" and (config.get("research_model") or config.get("research_provider")):
        return {
            "model": config.get("research_model") or config.get("model"),
            "provider": config.get("research_provider") or config.get("provider"),
        }
    elif phase == "planning" and (config.get("planning_model") or config.get("planning_provider")):
        return {
            "model": config.get("planning_model") or config.get("model"),
            "provider": config.get("planning_provider") or config.get("provider"),
        }
    else:
        return {
            "model": config.get("model"),
            "provider": config.get("provider"),
        } 