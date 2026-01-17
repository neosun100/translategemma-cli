"""Configuration management for TranslateGemma CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
import yaml

# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "translate"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "translate"

# Model configurations
MODEL_SIZES = ("4b", "12b", "27b")
DEFAULT_MODEL_SIZE = "27b"

# Backend types
BackendType = Literal["auto", "mlx", "pytorch", "vllm", "ollama"]
DEFAULT_BACKEND = "auto"

# Default server URLs
DEFAULT_VLLM_URL = "http://localhost:8000"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

MODEL_INFO = {
    "4b": {
        "hf_id": "google/translategemma-4b-it",
        "params": "5B",
        "quantized_size_gb": 3.2,
    },
    "12b": {
        "hf_id": "google/translategemma-12b-it",
        "params": "13B",
        "quantized_size_gb": 7.0,
    },
    "27b": {
        "hf_id": "google/translategemma-27b-it",
        "params": "29B",
        "quantized_size_gb": 14.8,
    },
}

# Output modes
OutputMode = Literal["direct", "explain"]

# All 55 supported languages with their codes
SUPPORTED_LANGUAGES = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kk": "Kazakh",
    "kn": "Kannada",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "yue": "Cantonese",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
}

# Default language pair
DEFAULT_LANGUAGES = ("yue", "en")

# CJK language codes (for script-based detection)
CJK_LANGUAGES = {"yue", "zh", "zh-TW", "ja", "ko"}


def get_model_path(model_size: str, quantization_bits: int = 4) -> Path:
    """Get the path for a specific model size and quantization."""
    return DEFAULT_CACHE_DIR / "models" / f"translategemma-{model_size}-it-{quantization_bits}bit"


def get_hf_model_id(model_size: str) -> str:
    """Get the HuggingFace model ID for a model size."""
    return MODEL_INFO[model_size]["hf_id"]


def get_default_config_data() -> dict:
    """Return the default configuration as a dictionary."""
    return {
        "model": {
            "name": DEFAULT_MODEL_SIZE,
            "quantization": 4,
        },
        "backend": {
            "type": DEFAULT_BACKEND,  # auto, mlx, pytorch, vllm, ollama
            "vllm_url": DEFAULT_VLLM_URL,
            "ollama_url": DEFAULT_OLLAMA_URL,
        },
        "translation": {
            "languages": list(DEFAULT_LANGUAGES),
            "mode": "direct",
            "max_tokens": 512,
            "chunking": {
                "enabled": True,
                "chunk_size": 80,   # Optimal for complete translation
                "overlap": 10,      # Minimal overlap to reduce repetition
                "split_by": "sentence",  # sentence, paragraph, char
                "auto_threshold": 300,  # Auto-enable chunking for text longer than this
            },
            "generation": {
                "temperature": 0.0,        # 0.0 = deterministic (recommended for translation)
                "top_p": 1.0,              # 1.0 = disabled (recommended for translation)
                "top_k": 0,                # 0 = disabled (recommended for translation)
                "min_p": 0.0,              # 0.0 = disabled
                "repetition_penalty": 1.0, # 1.0 = disabled (avoid affecting terminology)
            },
        },
        "ui": {
            "show_detected_language": True,
            "colored_output": True,
            "show_progress": True,
        },
    }


def create_default_config(config_path: Path | None = None) -> Path:
    """
    Create the default config file if it doesn't exist.
    
    Args:
        config_path: Path to config file. Defaults to ~/.config/translate/config.yaml
        
    Returns:
        Path to the config file
    """
    path = config_path or (DEFAULT_CONFIG_DIR / "config.yaml")
    
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(get_default_config_data(), f, default_flow_style=False, sort_keys=False)
    
    return path


class Config:
    """Configuration for TranslateGemma CLI."""

    def __init__(self, config_path: Path | None = None, auto_create: bool = True):
        self.config_path = config_path or (DEFAULT_CONFIG_DIR / "config.yaml")
        
        # Auto-create config file with defaults on first run
        if auto_create and not self.config_path.exists():
            create_default_config(self.config_path)
        
        self._data = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file or return defaults."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return get_default_config_data()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False)

    @property
    def model_size(self) -> str:
        """Current model size (4b, 12b, or 27b)."""
        size = self._data.get("model", {}).get("name", DEFAULT_MODEL_SIZE)
        return size if size in MODEL_SIZES else DEFAULT_MODEL_SIZE

    @model_size.setter
    def model_size(self, value: str) -> None:
        if value not in MODEL_SIZES:
            raise ValueError(f"Invalid model size: {value}. Must be one of {MODEL_SIZES}")
        if "model" not in self._data:
            self._data["model"] = {}
        self._data["model"]["name"] = value

    @property
    def model_path(self) -> Path:
        """Path to the converted model."""
        path = self._data.get("model", {}).get("path")
        if path:
            return Path(path)
        return get_model_path(self.model_size, self.quantization_bits)

    @model_path.setter
    def model_path(self, value: Path) -> None:
        if "model" not in self._data:
            self._data["model"] = {}
        self._data["model"]["path"] = str(value)

    @property
    def quantization_bits(self) -> int:
        """Quantization bits (4 or 8)."""
        return self._data.get("model", {}).get("quantization", 4)

    @quantization_bits.setter
    def quantization_bits(self, value: int) -> None:
        if value not in (4, 8):
            raise ValueError("Quantization bits must be 4 or 8")
        if "model" not in self._data:
            self._data["model"] = {}
        self._data["model"]["quantization"] = value

    @property
    def languages(self) -> tuple[str, str]:
        """Configured language pair."""
        langs = self._data.get("translation", {}).get("languages", list(DEFAULT_LANGUAGES))
        if isinstance(langs, list) and len(langs) >= 2:
            return (langs[0], langs[1])
        return DEFAULT_LANGUAGES

    @languages.setter
    def languages(self, value: tuple[str, str]) -> None:
        if "translation" not in self._data:
            self._data["translation"] = {}
        self._data["translation"]["languages"] = list(value)

    @property
    def output_mode(self) -> OutputMode:
        """Output mode: direct or explain."""
        mode = self._data.get("translation", {}).get("mode", "direct")
        return mode if mode in ("direct", "explain") else "direct"

    @output_mode.setter
    def output_mode(self, value: OutputMode) -> None:
        if value not in ("direct", "explain"):
            raise ValueError("Output mode must be 'direct' or 'explain'")
        if "translation" not in self._data:
            self._data["translation"] = {}
        self._data["translation"]["mode"] = value

    @property
    def max_tokens(self) -> int:
        """Maximum tokens to generate."""
        return self._data.get("translation", {}).get("max_tokens", 512)

    @property
    def backend_type(self) -> BackendType:
        """Backend type: auto, mlx, pytorch, vllm, or ollama."""
        backend = self._data.get("backend", {}).get("type", DEFAULT_BACKEND)
        valid_backends = ("auto", "mlx", "pytorch", "vllm", "ollama")
        return backend if backend in valid_backends else DEFAULT_BACKEND

    @backend_type.setter
    def backend_type(self, value: BackendType) -> None:
        if value not in ("auto", "mlx", "pytorch", "vllm", "ollama"):
            raise ValueError("Backend must be 'auto', 'mlx', 'pytorch', 'vllm', or 'ollama'")
        if "backend" not in self._data:
            self._data["backend"] = {}
        self._data["backend"]["type"] = value

    @property
    def vllm_url(self) -> str:
        """vLLM server URL."""
        return self._data.get("backend", {}).get("vllm_url", DEFAULT_VLLM_URL)

    @vllm_url.setter
    def vllm_url(self, value: str) -> None:
        if "backend" not in self._data:
            self._data["backend"] = {}
        self._data["backend"]["vllm_url"] = value

    @property
    def ollama_url(self) -> str:
        """Ollama server URL."""
        return self._data.get("backend", {}).get("ollama_url", DEFAULT_OLLAMA_URL)

    @ollama_url.setter
    def ollama_url(self, value: str) -> None:
        if "backend" not in self._data:
            self._data["backend"] = {}
        self._data["backend"]["ollama_url"] = value

    @property
    def show_language_indicator(self) -> bool:
        """Whether to show [yue→en] prefix in output."""
        return self._data.get("ui", {}).get("show_detected_language", True)

    @property
    def colored_output(self) -> bool:
        """Whether to use colored terminal output."""
        return self._data.get("ui", {}).get("colored_output", True)
    
    @property
    def show_progress(self) -> bool:
        """Whether to show progress bars."""
        return self._data.get("ui", {}).get("show_progress", True)
    
    # Chunking configuration
    @property
    def chunking_enabled(self) -> bool:
        """Whether chunking is enabled by default."""
        return self._data.get("translation", {}).get("chunking", {}).get("enabled", True)
    
    @chunking_enabled.setter
    def chunking_enabled(self, value: bool) -> None:
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "chunking" not in self._data["translation"]:
            self._data["translation"]["chunking"] = {}
        self._data["translation"]["chunking"]["enabled"] = value
    
    @property
    def chunk_size(self) -> int:
        """Default chunk size for long text translation."""
        return self._data.get("translation", {}).get("chunking", {}).get("chunk_size", 200)
    
    @chunk_size.setter
    def chunk_size(self, value: int) -> None:
        if value <= 0:
            raise ValueError("chunk_size must be positive")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "chunking" not in self._data["translation"]:
            self._data["translation"]["chunking"] = {}
        self._data["translation"]["chunking"]["chunk_size"] = value
    
    @property
    def chunk_overlap(self) -> int:
        """Default overlap size for chunking."""
        return self._data.get("translation", {}).get("chunking", {}).get("overlap", 50)
    
    @chunk_overlap.setter
    def chunk_overlap(self, value: int) -> None:
        if value < 0:
            raise ValueError("overlap cannot be negative")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "chunking" not in self._data["translation"]:
            self._data["translation"]["chunking"] = {}
        self._data["translation"]["chunking"]["overlap"] = value
    
    @property
    def chunk_split_by(self) -> Literal["sentence", "paragraph", "char"]:
        """How to split text for chunking."""
        split_by = self._data.get("translation", {}).get("chunking", {}).get("split_by", "sentence")
        return split_by if split_by in ("sentence", "paragraph", "char") else "sentence"
    
    @chunk_split_by.setter
    def chunk_split_by(self, value: Literal["sentence", "paragraph", "char"]) -> None:
        if value not in ("sentence", "paragraph", "char"):
            raise ValueError("split_by must be 'sentence', 'paragraph', or 'char'")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "chunking" not in self._data["translation"]:
            self._data["translation"]["chunking"] = {}
        self._data["translation"]["chunking"]["split_by"] = value
    
    @property
    def auto_chunk_threshold(self) -> int:
        """Auto-enable chunking for text longer than this."""
        return self._data.get("translation", {}).get("chunking", {}).get("auto_threshold", 500)
    
    # Generation parameters
    @property
    def temperature(self) -> float:
        """Sampling temperature (0.0 = deterministic)."""
        return self._data.get("translation", {}).get("generation", {}).get("temperature", 0.0)
    
    @temperature.setter
    def temperature(self, value: float) -> None:
        if value < 0.0 or value > 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "generation" not in self._data["translation"]:
            self._data["translation"]["generation"] = {}
        self._data["translation"]["generation"]["temperature"] = value
    
    @property
    def top_p(self) -> float:
        """Nucleus sampling threshold (1.0 = disabled)."""
        return self._data.get("translation", {}).get("generation", {}).get("top_p", 1.0)
    
    @top_p.setter
    def top_p(self, value: float) -> None:
        if value < 0.0 or value > 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "generation" not in self._data["translation"]:
            self._data["translation"]["generation"] = {}
        self._data["translation"]["generation"]["top_p"] = value
    
    @property
    def top_k(self) -> int:
        """Top-k sampling (0 = disabled)."""
        return self._data.get("translation", {}).get("generation", {}).get("top_k", 0)
    
    @top_k.setter
    def top_k(self, value: int) -> None:
        if value < 0:
            raise ValueError("top_k must be non-negative")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "generation" not in self._data["translation"]:
            self._data["translation"]["generation"] = {}
        self._data["translation"]["generation"]["top_k"] = value
    
    @property
    def min_p(self) -> float:
        """Minimum probability threshold (0.0 = disabled)."""
        return self._data.get("translation", {}).get("generation", {}).get("min_p", 0.0)
    
    @min_p.setter
    def min_p(self, value: float) -> None:
        if value < 0.0 or value > 1.0:
            raise ValueError("min_p must be between 0.0 and 1.0")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "generation" not in self._data["translation"]:
            self._data["translation"]["generation"] = {}
        self._data["translation"]["generation"]["min_p"] = value
    
    @property
    def repetition_penalty(self) -> float:
        """Repetition penalty (1.0 = disabled)."""
        return self._data.get("translation", {}).get("generation", {}).get("repetition_penalty", 1.0)
    
    @repetition_penalty.setter
    def repetition_penalty(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("repetition_penalty must be non-negative")
        if "translation" not in self._data:
            self._data["translation"] = {}
        if "generation" not in self._data["translation"]:
            self._data["translation"]["generation"] = {}
        self._data["translation"]["generation"]["repetition_penalty"] = value


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None
