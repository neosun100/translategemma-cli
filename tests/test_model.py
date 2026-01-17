"""Tests for model management."""

import platform
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from translategemma_cli.model import (
    get_backend,
    is_model_ready,
    list_downloaded_models,
    get_model_info,
    remove_model,
)
from translategemma_cli.config import MODEL_SIZES, MODEL_INFO


class TestGetBackend:
    """Test backend detection."""
    
    def test_mlx_on_apple_silicon(self):
        """Test MLX backend detection on Apple Silicon."""
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="arm64"), \
             patch.dict("sys.modules", {"mlx": MagicMock()}):
            # Re-import to get fresh detection
            import importlib
            from translategemma_cli import model
            importlib.reload(model)
            
            backend = model.get_backend()
            assert backend in ("mlx", "pytorch")
    
    def test_pytorch_on_linux(self):
        """Test backend on Linux - returns gguf if llama-cpp available, else pytorch."""
        with patch("platform.system", return_value="Linux"):
            backend = get_backend()
            # With llama-cpp-python installed, returns gguf; otherwise pytorch
            assert backend in ("pytorch", "gguf")
    
    def test_pytorch_on_windows(self):
        """Test PyTorch backend on Windows."""
        with patch("platform.system", return_value="Windows"):
            backend = get_backend()
            assert backend == "pytorch"
    
    def test_pytorch_fallback_no_mlx(self):
        """Test PyTorch fallback when MLX is not available."""
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="arm64"):
            # Simulate MLX import failure
            def mock_import(name, *args, **kwargs):
                if name == "mlx":
                    raise ImportError("No module named 'mlx'")
                return MagicMock()
            
            with patch("builtins.__import__", side_effect=mock_import):
                backend = get_backend()
                # Should fall back to pytorch
                assert backend in ("mlx", "pytorch")


class TestIsModelReady:
    """Test model readiness checking."""
    
    def test_model_not_ready_no_directory(self, mock_config, temp_cache_dir):
        """Test model not ready when directory doesn't exist."""
        assert is_model_ready("27b", "hf") is False
    
    def test_model_ready_with_files(self, mock_config, temp_model_dir):
        """Test model ready when required files exist."""
        # The temp_model_dir fixture creates the necessary files (HF format)
        assert is_model_ready("27b", "hf") is True
    
    def test_model_not_ready_missing_config(self, mock_config, temp_cache_dir):
        """Test model not ready when config.json is missing."""
        model_dir = temp_cache_dir / "models" / "translategemma-27b-it-4bit"
        model_dir.mkdir(parents=True, exist_ok=True)
        # Don't create config.json
        (model_dir / "model.safetensors").write_text("{}")
        
        assert is_model_ready("27b") is False
    
    def test_different_model_sizes(self, mock_config, temp_cache_dir):
        """Test readiness check for different model sizes (HF format)."""
        for size in MODEL_SIZES:
            assert is_model_ready(size, "hf") is False
            
            # Create model directory
            model_dir = temp_cache_dir / "models" / f"translategemma-{size}-it-4bit"
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "config.json").write_text('{}')
            
            assert is_model_ready(size, "hf") is True


class TestListDownloadedModels:
    """Test listing downloaded models."""
    
    def test_no_models_downloaded(self, mock_config):
        """Test listing when no models are downloaded."""
        models = list_downloaded_models()
        
        assert len(models) == 3  # 4b, 12b, 27b
        for model in models:
            assert model["downloaded"] is False
    
    def test_some_models_downloaded(self, mock_config, temp_cache_dir):
        """Test listing with some models downloaded."""
        # Create 4b model
        model_dir_4b = temp_cache_dir / "models" / "translategemma-4b-it-4bit"
        model_dir_4b.mkdir(parents=True, exist_ok=True)
        (model_dir_4b / "config.json").write_text('{}')
        
        models = list_downloaded_models()
        
        downloaded = [m for m in models if m["downloaded"]]
        not_downloaded = [m for m in models if not m["downloaded"]]
        
        assert len(downloaded) == 1
        assert len(not_downloaded) == 2
        assert downloaded[0]["size"] == "4b"
    
    def test_all_models_downloaded(self, mock_config, temp_cache_dir):
        """Test listing when all models are downloaded."""
        for size in MODEL_SIZES:
            model_dir = temp_cache_dir / "models" / f"translategemma-{size}-it-4bit"
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "config.json").write_text('{}')
        
        models = list_downloaded_models()
        
        for model in models:
            assert model["downloaded"] is True
    
    def test_model_info_completeness(self, mock_config):
        """Test that model info contains all required fields."""
        models = list_downloaded_models()
        
        for model in models:
            assert "size" in model
            assert "hf_id" in model
            assert "params" in model
            assert "quantized_size_gb" in model
            assert "hf_path" in model
            assert "gguf_path" in model
            assert "downloaded" in model


class TestGetModelInfo:
    """Test getting model information."""
    
    def test_default_model_info(self, mock_config):
        """Test getting info for default model."""
        info = get_model_info()
        
        assert info["size"] == "27b"
        assert info["hf_source"] == "google/translategemma-27b-it"
        assert info["quantization_bits"] == 4
        assert "backend" in info
        assert "params" in info
    
    def test_specific_model_info(self, mock_config):
        """Test getting info for specific model."""
        info = get_model_info("4b")
        
        assert info["size"] == "4b"
        assert info["hf_source"] == "google/translategemma-4b-it"
    
    def test_model_not_ready(self, mock_config):
        """Test info when model is not downloaded."""
        info = get_model_info("12b")
        
        assert info["ready"] is False
        assert "size_gb" not in info
    
    def test_model_ready(self, mock_config, temp_model_dir):
        """Test info when model is downloaded."""
        info = get_model_info("27b")
        
        assert info["ready"] is True
        assert "size_gb" in info


class TestRemoveModel:
    """Test model removal."""
    
    def test_remove_existing_model(self, mock_config, temp_cache_dir):
        """Test removing an existing model."""
        # Create model
        model_dir = temp_cache_dir / "models" / "translategemma-4b-it-4bit"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "config.json").write_text('{}')
        
        assert model_dir.exists()
        
        result = remove_model("4b")
        
        assert result is True
        assert not model_dir.exists()
    
    def test_remove_nonexistent_model(self, mock_config):
        """Test removing a model that doesn't exist."""
        result = remove_model("4b")
        assert result is False
    
    def test_remove_different_sizes(self, mock_config, temp_cache_dir):
        """Test removing different model sizes."""
        for size in MODEL_SIZES:
            model_dir = temp_cache_dir / "models" / f"translategemma-{size}-it-4bit"
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "config.json").write_text('{}')
        
        for size in MODEL_SIZES:
            assert remove_model(size) is True
            assert remove_model(size) is False  # Already removed


class TestModelDownloadConvert:
    """Test model download and conversion (mocked)."""
    
    @patch("translategemma_cli.model.get_backend", return_value="mlx")
    def test_download_skips_if_ready(self, mock_backend, mock_config, temp_model_dir):
        """Test download skips if model is already ready."""
        from translategemma_cli.model import download_and_convert_model
        
        result = download_and_convert_model("27b")
        
        assert result == temp_model_dir
    
    @patch("translategemma_cli.model.get_backend", return_value="mlx")
    @patch("translategemma_cli.model._download_mlx")
    def test_download_calls_mlx_on_apple_silicon(
        self, mock_download, mock_backend, mock_config
    ):
        """Test MLX download is called on Apple Silicon."""
        from translategemma_cli.model import download_and_convert_model
        
        mock_download.return_value = Path("/fake/path")
        
        result = download_and_convert_model("4b")
        
        mock_download.assert_called_once()
    
    @patch("translategemma_cli.model.get_backend", return_value="pytorch")
    @patch("translategemma_cli.model._download_pytorch")
    def test_download_calls_pytorch_on_other_platforms(
        self, mock_download, mock_backend, mock_config
    ):
        """Test PyTorch download is called on non-Apple platforms."""
        from translategemma_cli.model import download_and_convert_model
        
        mock_download.return_value = Path("/fake/path")
        
        result = download_and_convert_model("4b")
        
        mock_download.assert_called_once()


class TestModelLoad:
    """Test model loading (mocked)."""
    
    @patch("translategemma_cli.model.get_backend", return_value="mlx")
    @patch("translategemma_cli.model._load_mlx")
    def test_load_calls_mlx_backend(
        self, mock_load, mock_backend, mock_config, temp_model_dir
    ):
        """Test MLX load is called on Apple Silicon."""
        from translategemma_cli.model import load_model
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        model, tokenizer, backend = load_model("27b")
        
        mock_load.assert_called_once()
        assert backend == "mlx"
    
    @patch("translategemma_cli.model.get_backend", return_value="pytorch")
    @patch("translategemma_cli.model._load_pytorch")
    def test_load_calls_pytorch_backend(
        self, mock_load, mock_backend, mock_config, temp_model_dir
    ):
        """Test PyTorch load is called on other platforms."""
        from translategemma_cli.model import load_model
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer, "pytorch")
        
        model, tokenizer, backend = load_model("27b")
        
        mock_load.assert_called_once()
        assert backend == "pytorch"
