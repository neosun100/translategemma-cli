"""TranslateGemma MCP Server - Model Context Protocol Integration"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP

mcp = FastMCP("translategemma")

# Import from FastAPI app (shared GPU manager)
from app_fastapi import gpu, translate, LANGUAGES, AVAILABLE_MODELS, split_text, MAX_CHUNK_LENGTH


@mcp.tool()
def translate_text(
    text: str,
    target_lang: str,
    source_lang: str = None,
    model: str = None,
    quantization: int = None,
    chunk_size: int = 80,
    auto_split: bool = True,
) -> dict:
    """
    Translate text to target language using TranslateGemma.
    
    Args:
        text: Text to translate
        target_lang: Target language code (e.g., en, zh, ja, ko, fr, de, es, yue)
        source_lang: Source language code (optional, auto-detected if not provided)
        model: Model size - 4b, 12b, or 27b (default: 12b)
        quantization: Quantization bits - 4 or 8 (default: 4)
        chunk_size: Chunk size for long text (default: 80)
        auto_split: Auto-split long text into chunks (default: True)
    
    Returns:
        dict with result, source_lang, target_lang, elapsed_ms, model info
    """
    try:
        data = translate(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            model_size=model,
            quantization=quantization,
            chunk_size=chunk_size,
            auto_split=auto_split,
        )
        return {"status": "success", **data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def translate_batch(
    texts: list,
    target_lang: str,
    source_lang: str = None,
    model: str = None,
) -> dict:
    """
    Batch translate multiple texts.
    
    Args:
        texts: List of texts to translate
        target_lang: Target language code
        source_lang: Source language code (optional)
        model: Model size (optional)
    
    Returns:
        dict with results list and total elapsed time
    """
    import time
    start = time.time()
    results = []
    
    for text in texts:
        try:
            data = translate(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                model_size=model,
            )
            results.append({
                "status": "success",
                "result": data["result"],
                "elapsed_ms": data["elapsed_ms"],
            })
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
    
    return {
        "status": "success",
        "results": results,
        "total_elapsed_ms": int((time.time() - start) * 1000),
        "count": len(results),
    }


@mcp.tool()
def translate_file(
    file_path: str,
    target_lang: str,
    source_lang: str = None,
    model: str = None,
    output_path: str = None,
) -> dict:
    """
    Translate a text file.
    
    Args:
        file_path: Path to input text file
        target_lang: Target language code
        source_lang: Source language code (optional)
        model: Model size (optional)
        output_path: Path to save translated file (optional)
    
    Returns:
        dict with translation result and file info
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        data = translate(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            model_size=model,
        )
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(data["result"])
            data["output_file"] = output_path
        
        data["input_file"] = file_path
        return {"status": "success", **data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_gpu_status() -> dict:
    """
    Get GPU status including memory usage and loaded model info.
    
    Returns:
        dict with GPU status, loaded model, idle time, memory info
    """
    return gpu.status()


@mcp.tool()
def release_gpu() -> dict:
    """
    Release GPU memory by unloading the model.
    
    Returns:
        dict with status message
    """
    gpu.force_unload()
    return {"status": "ok", "message": "GPU memory released"}


@mcp.tool()
def switch_model(model: str, quantization: int = 4) -> dict:
    """
    Switch to a different model.
    
    Args:
        model: Model size - 4b, 12b, or 27b
        quantization: Quantization bits - 4 or 8 (default: 4)
    
    Returns:
        dict with new model info and load time
    """
    import time
    
    if model not in ["4b", "12b", "27b"]:
        return {"status": "error", "error": f"Invalid model: {model}. Use 4b, 12b, or 27b"}
    
    if quantization not in [4, 8]:
        return {"status": "error", "error": f"Invalid quantization: {quantization}. Use 4 or 8"}
    
    try:
        start = time.time()
        gpu.load(model, quantization)
        elapsed = int((time.time() - start) * 1000)
        return {
            "status": "success",
            "model": f"{model}-Q{quantization}",
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def list_languages() -> dict:
    """
    Get list of all 55 supported languages.
    
    Returns:
        dict mapping language codes to language names
    """
    return LANGUAGES


@mcp.tool()
def list_models() -> dict:
    """
    Get list of available models with their specifications.
    
    Returns:
        dict with model configurations and current model info
    """
    return {
        "models": AVAILABLE_MODELS,
        "current": f"{gpu.current_model}-Q{gpu.current_quant}" if gpu.current_model else None,
    }


@mcp.tool()
def get_config() -> dict:
    """
    Get current service configuration.
    
    Returns:
        dict with configuration settings
    """
    from app_fastapi import (
        DEFAULT_MODEL, DEFAULT_QUANTIZATION, DEFAULT_BACKEND,
        GPU_IDLE_TIMEOUT, MAX_CHUNK_LENGTH
    )
    
    return {
        "default_model": DEFAULT_MODEL,
        "default_quantization": DEFAULT_QUANTIZATION,
        "default_backend": DEFAULT_BACKEND,
        "gpu_idle_timeout": GPU_IDLE_TIMEOUT,
        "max_chunk_length": MAX_CHUNK_LENGTH,
        "supported_languages": len(LANGUAGES),
        "current_model": f"{gpu.current_model}-Q{gpu.current_quant}" if gpu.current_model else None,
    }


if __name__ == "__main__":
    mcp.run()
