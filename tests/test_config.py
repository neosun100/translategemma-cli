"""Tests for configuration management."""

import pytest
import yaml
from pathlib import Path

from translategemma_cli.config import (
    Config,
    get_config,
    reset_config,
    get_model_path,
    get_hf_model_id,
    MODEL_SIZES,
    MODEL_INFO,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGES,
    CJK_LANGUAGES,
    DEFAULT_MODEL_SIZE,
)


class TestConfigConstants:
    """Test configuration constants."""
    
    def test_model_sizes(self):
        """Test that all model sizes are defined."""
        assert MODEL_SIZES == ("4b", "12b", "27b")
    
    def test_default_model_size(self):
        """Test default model size."""
        assert DEFAULT_MODEL_SIZE == "27b"
    
    def test_model_info_completeness(self):
        """Test that MODEL_INFO has entries for all sizes."""
        for size in MODEL_SIZES:
            assert size in MODEL_INFO
            assert "hf_id" in MODEL_INFO[size]
            assert "params" in MODEL_INFO[size]
            assert "quantized_size_gb" in MODEL_INFO[size]
    
    def test_supported_languages_count(self):
        """Test that we have 54 supported languages."""
        assert len(SUPPORTED_LANGUAGES) == 54
    
    def test_default_languages(self):
        """Test default language pair."""
        assert DEFAULT_LANGUAGES == ("yue", "en")
    
    def test_cjk_languages(self):
        """Test CJK language codes."""
        assert "yue" in CJK_LANGUAGES
        assert "zh" in CJK_LANGUAGES
        assert "ja" in CJK_LANGUAGES
        assert "ko" in CJK_LANGUAGES
        assert "en" not in CJK_LANGUAGES


class TestGetModelPath:
    """Test get_model_path function."""
    
    def test_default_quantization(self):
        """Test model path with default quantization."""
        path = get_model_path("27b")
        assert "translategemma-27b-it-4bit" in str(path)
    
    def test_custom_quantization(self):
        """Test model path with custom quantization."""
        path = get_model_path("12b", 8)
        assert "translategemma-12b-it-8bit" in str(path)
    
    def test_all_model_sizes(self):
        """Test paths for all model sizes."""
        for size in MODEL_SIZES:
            path = get_model_path(size)
            assert f"translategemma-{size}-it" in str(path)


class TestGetHfModelId:
    """Test get_hf_model_id function."""
    
    def test_all_model_sizes(self):
        """Test HuggingFace IDs for all model sizes."""
        assert get_hf_model_id("4b") == "google/translategemma-4b-it"
        assert get_hf_model_id("12b") == "google/translategemma-12b-it"
        assert get_hf_model_id("27b") == "google/translategemma-27b-it"


class TestConfig:
    """Test Config class."""
    
    def test_default_model_size(self, mock_config):
        """Test default model size."""
        assert mock_config.model_size == "27b"
    
    def test_set_model_size(self, mock_config):
        """Test setting model size."""
        mock_config.model_size = "4b"
        assert mock_config.model_size == "4b"
    
    def test_invalid_model_size(self, mock_config):
        """Test setting invalid model size raises error."""
        with pytest.raises(ValueError, match="Invalid model size"):
            mock_config.model_size = "invalid"
    
    def test_default_quantization_bits(self, mock_config):
        """Test default quantization bits."""
        assert mock_config.quantization_bits == 4
    
    def test_set_quantization_bits(self, mock_config):
        """Test setting quantization bits."""
        mock_config.quantization_bits = 8
        assert mock_config.quantization_bits == 8
    
    def test_invalid_quantization_bits(self, mock_config):
        """Test setting invalid quantization bits raises error."""
        with pytest.raises(ValueError, match="Quantization bits must be 4 or 8"):
            mock_config.quantization_bits = 16
    
    def test_default_languages(self, mock_config):
        """Test default language pair."""
        assert mock_config.languages == ("yue", "en")
    
    def test_set_languages(self, mock_config):
        """Test setting language pair."""
        mock_config.languages = ("ja", "en")
        assert mock_config.languages == ("ja", "en")
    
    def test_default_output_mode(self, mock_config):
        """Test default output mode."""
        assert mock_config.output_mode == "direct"
    
    def test_set_output_mode(self, mock_config):
        """Test setting output mode."""
        mock_config.output_mode = "explain"
        assert mock_config.output_mode == "explain"
    
    def test_invalid_output_mode(self, mock_config):
        """Test setting invalid output mode raises error."""
        with pytest.raises(ValueError, match="Output mode must be"):
            mock_config.output_mode = "invalid"
    
    def test_default_max_tokens(self, mock_config):
        """Test default max tokens."""
        assert mock_config.max_tokens == 512
    
    def test_default_show_language_indicator(self, mock_config):
        """Test default language indicator setting."""
        assert mock_config.show_language_indicator is True
    
    def test_default_colored_output(self, mock_config):
        """Test default colored output setting."""
        assert mock_config.colored_output is True
    
    def test_save_and_load(self, temp_config_dir):
        """Test saving and loading configuration."""
        config_path = temp_config_dir / "config.yaml"
        config = Config(config_path)
        
        # Modify settings
        config.model_size = "12b"
        config.languages = ("zh", "en")
        config.save()
        
        # Load and verify
        loaded_config = Config(config_path)
        assert loaded_config.model_size == "12b"
        assert loaded_config.languages == ("zh", "en")


class TestGlobalConfig:
    """Test global configuration functions."""
    
    def test_get_config_singleton(self, mock_config):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_reset_config(self, monkeypatch, temp_config_dir, temp_cache_dir):
        """Test resetting global config."""
        from translategemma_cli import config
        
        monkeypatch.setattr(config, "DEFAULT_CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(config, "DEFAULT_CACHE_DIR", temp_cache_dir)
        
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        # After reset, should be a new instance
        assert config1 is not config2
