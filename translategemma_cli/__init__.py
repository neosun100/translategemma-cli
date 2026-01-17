"""TranslateGemma CLI - Multi-platform local translation powered by TranslateGemma."""

__version__ = "0.1.0"

from .config import (
    SUPPORTED_LANGUAGES,
    MODEL_SIZES,
    DEFAULT_LANGUAGES,
    get_config,
)
from .detector import (
    detect_language,
    get_target_language,
    get_language_name,
    is_valid_language,
)
from .model import (
    get_backend,
    is_model_ready,
    load_model,
    get_model_info,
)
from .translator import (
    Translator,
    get_translator,
)
from .backends import (
    VLLMBackend,
    OllamaBackend,
    check_vllm_server,
    check_ollama_server,
)

__all__ = [
    # Version
    "__version__",
    # Config
    "SUPPORTED_LANGUAGES",
    "MODEL_SIZES",
    "DEFAULT_LANGUAGES",
    "get_config",
    # Detection
    "detect_language",
    "get_target_language",
    "get_language_name",
    "is_valid_language",
    # Model
    "get_backend",
    "is_model_ready",
    "load_model",
    "get_model_info",
    # Translation
    "Translator",
    "get_translator",
    # Backends
    "VLLMBackend",
    "OllamaBackend",
    "check_vllm_server",
    "check_ollama_server",
]
