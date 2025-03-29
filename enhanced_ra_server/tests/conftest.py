"""
PyTest configuration for Enhanced RA.Aid Server tests.

This module contains shared fixtures and configuration for tests.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the Python path to help with imports
# This is necessary when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def pytest_configure(config):
    """Configure pytest."""
    # Register marks
    config.addinivalue_line("markers", "asyncio: mark test as asyncio coroutine")


@pytest.fixture
def temp_dir():
    """Create and return a temporary directory."""
    import tempfile
    
    # Create temp directory
    temp_path = tempfile.mkdtemp()
    yield temp_path
    
    # Clean up (if directory still exists)
    try:
        import shutil
        shutil.rmtree(temp_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture(autouse=True)
def mock_api_keys(monkeypatch):
    """Mock API keys for all providers in the test environment."""
    # Create a copy of the current environment
    mock_env = os.environ.copy()
    
    # Add mock API keys for all supported providers
    mock_env.update({
        "ANTHROPIC_API_KEY": "mock-anthropic-key",
        "OPENAI_API_KEY": "mock-openai-key",
        "OPENROUTER_API_KEY": "mock-openrouter-key",
        "GEMINI_API_KEY": "mock-gemini-key",
        "DEEPSEEK_API_KEY": "mock-deepseek-key",
        
        # Also add expert versions
        "EXPERT_ANTHROPIC_API_KEY": "mock-expert-anthropic-key",
        "EXPERT_OPENAI_API_KEY": "mock-expert-openai-key",
        "EXPERT_OPENROUTER_API_KEY": "mock-expert-openrouter-key",
        "EXPERT_GEMINI_API_KEY": "mock-expert-gemini-key",
        "EXPERT_DEEPSEEK_API_KEY": "mock-expert-deepseek-key",
    })
    
    # Apply the patched environment
    for key, value in mock_env.items():
        monkeypatch.setenv(key, value) 