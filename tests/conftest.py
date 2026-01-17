"""Shared fixtures for TranslateGemma CLI tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def temp_model_dir(temp_cache_dir):
    """Create a temporary model directory with fake model files."""
    model_dir = temp_cache_dir / "models" / "translategemma-27b-it-4bit"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Create fake model files
    (model_dir / "config.json").write_text('{"model_type": "gemma"}')
    (model_dir / "model.safetensors.index.json").write_text('{}')
    (model_dir / "tokenizer.json").write_text('{}')
    
    return model_dir


@pytest.fixture
def mock_config(temp_config_dir, temp_cache_dir, monkeypatch):
    """Patch config paths to use temp directories."""
    from translategemma_cli import config
    
    monkeypatch.setattr(config, "DEFAULT_CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr(config, "DEFAULT_CACHE_DIR", temp_cache_dir)
    
    # Reset global config
    config.reset_config()
    
    yield config.get_config()
    
    # Cleanup
    config.reset_config()


@pytest.fixture
def mock_model():
    """Create a mock model object."""
    model = MagicMock()
    model.parameters.return_value = iter([MagicMock()])
    return model


@pytest.fixture
def mock_tokenizer():
    """Create a mock tokenizer object."""
    tokenizer = MagicMock()
    tokenizer.apply_chat_template.return_value = "formatted prompt"
    tokenizer.eos_token_id = 0
    tokenizer.decode.return_value = "translated text"
    return tokenizer


@pytest.fixture
def sample_texts():
    """Sample texts in different languages for testing."""
    return {
        "cantonese": [
            "你好",
            "今日天氣好好",
            "我哋去食飯",
            "早晨",
            "多謝",
        ],
        "english": [
            "Hello",
            "The weather is nice today",
            "Let's go eat",
            "Good morning",
            "Thank you",
        ],
        "mixed": [
            "我想order一杯coffee",
            "Hello 你好",
            "今天very good",
        ],
        "japanese": [
            "こんにちは",
            "ありがとう",
        ],
        "korean": [
            "안녕하세요",
            "감사합니다",
        ],
    }


@pytest.fixture
def cli_runner():
    """Create a Typer CLI test runner."""
    from typer.testing import CliRunner
    return CliRunner()
