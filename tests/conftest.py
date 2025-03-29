import os
import pytest
from unittest.mock import patch

# Import pytest-mock which provides the 'mocker' fixture
pytest_plugins = ['pytest_mock']

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