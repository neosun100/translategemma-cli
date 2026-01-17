"""
TranslateGemma Translation Service - FastAPI Version
Supports UI, REST API, and MCP integration
"""
import os
import time
import threading
import gc
import json
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, AsyncGenerator

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ==================== Configuration ====================
DEFAULT_MODEL = os.getenv("MODEL_NAME", "27b")
DEFAULT_QUANTIZATION = int(os.getenv("QUANTIZATION", "8"))
DEFAULT_BACKEND = os.getenv("BACKEND", "gguf")
GPU_IDLE_TIMEOUT = int(os.getenv("GPU_IDLE_TIMEOUT", "0"))  # 0 = unload immediately after use
MAX_CHUNK_LENGTH = int(os.getenv("MAX_CHUNK_LENGTH", "100"))  # 100 is safe, 150+ may cause truncation
DEFAULT_OVERLAP = int(os.getenv("DEFAULT_OVERLAP", "0"))  # 0 = no sliding window, >0 = overlap chars
REPETITION_PENALTY = float(os.getenv("REPETITION_PENALTY", "1.0"))  # 1.0 = no penalty, 1.1+ = reduce repetition

# Supported languages (55 from TranslateGemma)
LANGUAGES = {
    "af": "Afrikaans", "ar": "Arabic", "bn": "Bengali", "bg": "Bulgarian",
    "ca": "Catalan", "cs": "Czech", "cy": "Welsh", "da": "Danish",
    "de": "German", "el": "Greek", "en": "English", "es": "Spanish",
    "et": "Estonian", "fa": "Persian", "fi": "Finnish", "fr": "French",
    "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi", "hr": "Croatian",
    "hu": "Hungarian", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "kk": "Kazakh", "kn": "Kannada", "ko": "Korean", "lt": "Lithuanian",
    "lv": "Latvian", "ml": "Malayalam", "mr": "Marathi", "ms": "Malay",
    "nl": "Dutch", "no": "Norwegian", "pa": "Punjabi", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sk": "Slovak",
    "sl": "Slovenian", "sr": "Serbian", "sv": "Swedish", "sw": "Swahili",
    "ta": "Tamil", "te": "Telugu", "th": "Thai", "tr": "Turkish",
    "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese", "yue": "Cantonese",
    "zh": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)",
}

# Model configurations
AVAILABLE_MODELS = {
    "4B-Q4": {"name": "TranslateGemma 4B Q4", "size": "4B", "quantization": "Q4", "quant": 4, "vram": "~3GB", "quality": "Good", "description": "最快速度，适合日常翻译"},
    "4B-Q8": {"name": "TranslateGemma 4B Q8", "size": "4B", "quantization": "Q8", "quant": 8, "vram": "~5GB", "quality": "Better", "description": "平衡速度与质量"},
    "12B-Q4": {"name": "TranslateGemma 12B Q4", "size": "12B", "quantization": "Q4", "quant": 4, "vram": "~7GB", "quality": "High", "description": "中等模型，高质量翻译"},
    "12B-Q8": {"name": "TranslateGemma 12B Q8", "size": "12B", "quantization": "Q8", "quant": 8, "vram": "~12GB", "quality": "Higher", "description": "更高精度，推荐使用"},
    "27B-Q4": {"name": "TranslateGemma 27B Q4", "size": "27B", "quantization": "Q4", "quant": 4, "vram": "~15GB", "quality": "Best", "description": "大模型，最佳翻译质量"},
    "27B-Q8": {"name": "TranslateGemma 27B Q8", "size": "27B", "quantization": "Q8", "quant": 8, "vram": "~28GB", "quality": "Best+", "description": "最高质量，专业翻译首选"},
}


# ==================== GPU Manager ====================
class GPUManager:
    """Manages GPU resources with auto-unload on idle."""
    
    def __init__(self):
        self.translator = None
        self.current_model = None
        self.current_quant = None
        self.lock = threading.Lock()
        self.last_used = 0
        self.unload_timer = None
        self.loading = False

    def load(self, model_size: str = None, quantization: int = None):
        """Load model, reusing if same config."""
        model_size = model_size or DEFAULT_MODEL
        quantization = quantization or DEFAULT_QUANTIZATION
        
        with self.lock:
            # Return existing if same config
            if (self.translator is not None and 
                self.current_model == model_size and 
                self.current_quant == quantization):
                self.last_used = time.time()
                self._schedule_unload()
                return self.translator
            
            # Unload existing if different
            if self.translator is not None:
                self._do_unload()
            
            self.loading = True
            try:
                # Import here to avoid startup delay
                from translategemma_cli.translator import Translator
                from translategemma_cli.config import get_config
                
                # Update config
                config = get_config()
                config.model_size = model_size
                config.quantization_bits = quantization
                config.backend_type = DEFAULT_BACKEND
                
                # Create and load translator
                self.translator = Translator()
                self.translator.ensure_model_loaded(
                    model_size=model_size,
                    backend_type=DEFAULT_BACKEND
                )
                
                self.current_model = model_size
                self.current_quant = quantization
                self.last_used = time.time()
                self._schedule_unload()
                
            finally:
                self.loading = False
            
            return self.translator

    def _schedule_unload(self):
        """Schedule unload after idle timeout. If timeout is 0, unload immediately after use."""
        if self.unload_timer:
            self.unload_timer.cancel()
            self.unload_timer = None
        
        if GPU_IDLE_TIMEOUT <= 0:
            # Immediate unload mode - will be called after translation completes
            return
        
        self.unload_timer = threading.Timer(GPU_IDLE_TIMEOUT, self._auto_unload)
        self.unload_timer.daemon = True
        self.unload_timer.start()

    def unload_if_immediate(self):
        """Unload immediately if GPU_IDLE_TIMEOUT is 0."""
        if GPU_IDLE_TIMEOUT <= 0:
            with self.lock:
                self._do_unload()

    def _auto_unload(self):
        with self.lock:
            if self.translator and time.time() - self.last_used >= GPU_IDLE_TIMEOUT:
                self._do_unload()

    def _do_unload(self):
        if self.translator:
            del self.translator
            self.translator = None
            self.current_model = None
            self.current_quant = None
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def force_unload(self):
        with self.lock:
            self._do_unload()

    def status(self):
        gpu_info = {"available": False}
        try:
            import torch
            if torch.cuda.is_available():
                # 只有在模型加载后才显示显存信息
                if self.translator is not None:
                    free, total = torch.cuda.mem_get_info()
                    used = total - free
                    gpu_info = {
                        "available": True,
                        "device": torch.cuda.get_device_name(0),
                        "free_mb": int(free / 1024 / 1024),
                        "total_mb": int(total / 1024 / 1024),
                        "used_mb": int(used / 1024 / 1024),
                    }
                else:
                    gpu_info = {
                        "available": True,
                        "device": torch.cuda.get_device_name(0),
                    }
        except:
            pass
        
        return {
            "loaded": self.translator is not None,
            "loading": self.loading,
            "current_model": f"{self.current_model}-Q{self.current_quant}" if self.current_model else None,
            "idle_seconds": int(time.time() - self.last_used) if self.last_used else 0,
            "gpu": gpu_info,
            "default_model": f"{DEFAULT_MODEL}-Q{DEFAULT_QUANTIZATION}",
        }


gpu = GPUManager()


# ==================== Text Processing ====================
def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    import re
    sentence_pattern = r'([。！？.!?]+[\s]*)'
    parts = re.split(sentence_pattern, text)
    
    sentences = []
    for i in range(0, len(parts), 2):
        sent = parts[i]
        if i + 1 < len(parts):
            sent += parts[i + 1]
        if sent.strip():
            sentences.append(sent)
    return sentences


def split_text(text: str, max_length: int = MAX_CHUNK_LENGTH, overlap: int = 0) -> List[dict]:
    """
    Smart text splitting with optional sliding window overlap.
    
    Args:
        text: Input text
        max_length: Maximum chunk size
        overlap: Overlap size for sliding window (0 = disabled)
    
    Returns:
        List of dicts with 'text' and 'overlap_chars' (chars to skip in merge)
    """
    import re
    
    # First split by paragraph (double newline or single newline)
    paragraphs = re.split(r'\n\s*\n|\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return [{"text": text, "overlap_chars": 0}] if text.strip() else []
    
    chunks = []
    
    for para in paragraphs:
        if len(para) <= max_length:
            chunks.append({"text": para, "overlap_chars": 0})
        else:
            # Split long paragraph by sentences
            sentences = split_sentences(para)
            
            if not sentences:
                # No sentence boundaries, split by length
                for i in range(0, len(para), max_length):
                    chunk_text = para[i:i+max_length].strip()
                    chunks.append({"text": chunk_text, "overlap_chars": 0})
            else:
                # Group sentences into chunks with optional overlap
                current = ""
                prev_overlap_text = ""  # Text to prepend for context
                
                for sent in sentences:
                    if len(current) + len(sent) <= max_length:
                        current += sent
                    else:
                        if current:
                            # Add chunk with overlap prefix if enabled
                            if overlap > 0 and prev_overlap_text:
                                chunk_text = prev_overlap_text + current
                                overlap_chars = len(prev_overlap_text)
                            else:
                                chunk_text = current
                                overlap_chars = 0
                            chunks.append({"text": chunk_text.strip(), "overlap_chars": overlap_chars})
                            
                            # Prepare overlap for next chunk
                            if overlap > 0:
                                prev_overlap_text = _get_overlap_text(current, overlap)
                        
                        if len(sent) > max_length:
                            # Handle very long sentence
                            for i in range(0, len(sent), max_length):
                                chunks.append({"text": sent[i:i+max_length].strip(), "overlap_chars": 0})
                            current = ""
                            prev_overlap_text = ""
                        else:
                            current = sent
                
                if current.strip():
                    if overlap > 0 and prev_overlap_text:
                        chunk_text = prev_overlap_text + current
                        overlap_chars = len(prev_overlap_text)
                    else:
                        chunk_text = current
                        overlap_chars = 0
                    chunks.append({"text": chunk_text.strip(), "overlap_chars": overlap_chars})
    
    # Mark first chunk as having no overlap to skip
    if chunks:
        chunks[0]["overlap_chars"] = 0
    
    return chunks if chunks else [{"text": text, "overlap_chars": 0}]


def _get_overlap_text(text: str, overlap: int) -> str:
    """Get the last N characters for overlap, preferring sentence boundaries."""
    if len(text) <= overlap:
        return text
    
    # Try to find a sentence boundary within the overlap region
    overlap_region = text[-overlap * 2:]  # Look in a larger region
    sentences = split_sentences(overlap_region)
    
    if sentences and len(sentences) > 1:
        # Use the last complete sentence(s) that fit within overlap
        result = ""
        for sent in reversed(sentences):
            if len(result) + len(sent) <= overlap * 1.5:  # Allow some flexibility
                result = sent + result
            else:
                break
        if result:
            return result
    
    # Fallback: just take last N chars
    return text[-overlap:]


# ==================== Translation Functions ====================
def translate(
    text: str,
    target_lang: str,
    source_lang: str = None,
    model_size: str = None,
    quantization: int = None,
    chunk_size: int = MAX_CHUNK_LENGTH,
    overlap: int = DEFAULT_OVERLAP,
    repetition_penalty: float = REPETITION_PENALTY,
    auto_split: bool = True,
) -> dict:
    """Translate text with chunking and optional sliding window support."""
    start_time = time.time()
    
    # Parse model key if provided (e.g., "27B-Q8" -> "27b", 8)
    actual_model = model_size
    actual_quant = quantization
    if model_size and "-Q" in model_size.upper():
        parts = model_size.upper().split("-Q")
        actual_model = parts[0].lower()
        actual_quant = int(parts[1]) if len(parts) > 1 else quantization
    elif model_size:
        actual_model = model_size.lower()
    
    translator = gpu.load(actual_model, actual_quant)
    
    # Set target language
    if target_lang:
        translator.set_force_target(target_lang)
    
    # Split text with optional overlap
    if auto_split:
        chunk_data = split_text(text, chunk_size, overlap)
    else:
        chunk_data = [{"text": text, "overlap_chars": 0}]
    
    results = []
    
    for chunk_info in chunk_data:
        chunk_text = chunk_info["text"]
        overlap_chars = chunk_info["overlap_chars"]
        
        result, src, tgt = translator.translate(chunk_text, force_target=target_lang)
        
        # If overlap was used, we need to handle potential duplicate content
        # The overlap is in source text for context, but translation may have duplicates
        results.append({
            "text": result,
            "overlap_chars": overlap_chars,
            "source_overlap": overlap_chars > 0,
        })
        
        if not source_lang:
            source_lang = src
    
    # Unload immediately if configured
    gpu.unload_if_immediate()
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Merge results
    final_result = _merge_translations(results, text, overlap > 0)
    
    # Store model info before potential unload
    model_info = f"{actual_model}-Q{actual_quant}" if actual_model else f"{DEFAULT_MODEL}-Q{DEFAULT_QUANTIZATION}"
    
    return {
        "result": final_result,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "elapsed_ms": elapsed_ms,
        "chunks": len(chunk_data),
        "input_length": len(text),
        "output_length": len(final_result),
        "model": model_info,
        "overlap_used": overlap,
        "chars_per_sec": round(len(text) / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
    }


def _merge_translations(results: List[dict], original_text: str, has_overlap: bool) -> str:
    """
    Merge translated chunks, handling overlap if present.
    
    Strategy:
    - First chunk: keep complete
    - Subsequent chunks with overlap: the overlap provided context for translation,
      but we keep the full translation (overlap helps quality, not for deduplication)
    """
    if not results:
        return ""
    
    if len(results) == 1:
        return results[0]["text"]
    
    # Check if original has newlines
    use_newline = '\n' in original_text
    separator = "\n" if use_newline else ""
    
    merged = [results[0]["text"]]
    
    for r in results[1:]:
        merged.append(r["text"])
    
    return separator.join(merged)


async def translate_stream(
    text: str,
    target_lang: str,
    source_lang: str = None,
    model_size: str = None,
    quantization: int = None,
    chunk_size: int = MAX_CHUNK_LENGTH,
    overlap: int = DEFAULT_OVERLAP,
) -> AsyncGenerator[str, None]:
    """Stream translation results chunk by chunk."""
    start_time = time.time()
    chunk_data = split_text(text, chunk_size, overlap)
    total_chunks = len(chunk_data)
    
    yield f"data: {json.dumps({'event': 'start', 'total_chunks': total_chunks, 'input_length': len(text), 'overlap': overlap})}\n\n"
    
    # Parse model key if provided (e.g., "27B-Q8" -> "27b", 8)
    actual_model = model_size
    actual_quant = quantization
    if model_size and "-Q" in model_size.upper():
        parts = model_size.upper().split("-Q")
        actual_model = parts[0].lower()
        actual_quant = int(parts[1]) if len(parts) > 1 else quantization
    elif model_size:
        actual_model = model_size.lower()
    
    translator = gpu.load(actual_model, actual_quant)
    if target_lang:
        translator.set_force_target(target_lang)
    
    results = []
    
    for i, chunk_info in enumerate(chunk_data):
        chunk_text = chunk_info["text"]
        chunk_start = time.time()
        
        yield f"data: {json.dumps({'event': 'progress', 'chunk': i + 1, 'total': total_chunks})}\n\n"
        
        loop = asyncio.get_event_loop()
        result, src, tgt = await loop.run_in_executor(
            None, lambda c=chunk_text: translator.translate(c, force_target=target_lang)
        )
        results.append({"text": result, "overlap_chars": chunk_info["overlap_chars"]})
        
        chunk_elapsed = int((time.time() - chunk_start) * 1000)
        yield f"data: {json.dumps({'event': 'chunk', 'chunk': i + 1, 'total': total_chunks, 'result': result, 'elapsed_ms': chunk_elapsed})}\n\n"
    
    # Store model info before potential unload
    model_info = f"{actual_model}-Q{actual_quant}" if actual_model else f"{DEFAULT_MODEL}-Q{DEFAULT_QUANTIZATION}"
    
    # Unload immediately if configured
    gpu.unload_if_immediate()
    
    total_elapsed = int((time.time() - start_time) * 1000)
    
    # Merge results
    final_result = _merge_translations(results, text, overlap > 0)
    
    yield f"data: {json.dumps({'event': 'done', 'result': final_result, 'elapsed_ms': total_elapsed, 'output_length': len(final_result), 'model': model_info, 'overlap_used': overlap})}\n\n"


# ==================== FastAPI App ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if gpu.unload_timer:
        gpu.unload_timer.cancel()


app = FastAPI(
    title="TranslateGemma API",
    description="Local translation powered by Google's TranslateGemma - 55 languages supported",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================
class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_lang: str = Field(..., description="Target language code (e.g., en, zh, ja)")
    source_lang: Optional[str] = Field(None, description="Source language (auto-detect if not provided)")
    model: Optional[str] = Field(None, description="Model size: 4b, 12b, 27b")
    quantization: Optional[int] = Field(None, description="Quantization: 4 or 8")
    chunk_size: int = Field(MAX_CHUNK_LENGTH, description="Chunk size for long text")
    overlap: int = Field(DEFAULT_OVERLAP, description="Overlap size for sliding window (0=disabled)")
    auto_split: bool = Field(True, description="Auto-split long text")
    stream: bool = Field(False, description="Stream results")


class TranslateResponse(BaseModel):
    status: str
    result: Optional[str] = None
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    elapsed_ms: Optional[int] = None
    chunks: Optional[int] = None
    input_length: Optional[int] = None
    output_length: Optional[int] = None
    model: Optional[str] = None
    chars_per_sec: Optional[float] = None
    error: Optional[str] = None


class BatchRequest(BaseModel):
    texts: List[str]
    target_lang: str
    source_lang: Optional[str] = None
    model: Optional[str] = None
    quantization: Optional[int] = None


class SwitchModelRequest(BaseModel):
    model: str = Field(..., description="Model key like '12b-Q4' or just '12b'")


# ==================== API Endpoints ====================
@app.get("/health")
async def health():
    return {"status": "ok", "gpu": gpu.status()}


@app.get("/api/config")
async def api_config():
    return {
        "default_model": DEFAULT_MODEL,
        "default_quantization": DEFAULT_QUANTIZATION,
        "default_backend": DEFAULT_BACKEND,
        "gpu_idle_timeout": GPU_IDLE_TIMEOUT,
        "max_chunk_length": MAX_CHUNK_LENGTH,
        "default_overlap": DEFAULT_OVERLAP,
        "repetition_penalty": REPETITION_PENALTY,
        "supported_languages": len(LANGUAGES),
    }


@app.get("/api/languages")
async def api_languages():
    return LANGUAGES


@app.get("/api/models")
async def api_models():
    return {
        "models": AVAILABLE_MODELS,
        "current": f"{gpu.current_model.upper()}-Q{gpu.current_quant}" if gpu.current_model else None,
        "default": f"{DEFAULT_MODEL.upper()}-Q{DEFAULT_QUANTIZATION}",
    }


@app.post("/api/models/switch")
async def api_switch_model(req: SwitchModelRequest):
    """Switch to a different model."""
    # Parse model key - normalize to uppercase
    model_key = req.model.upper()
    
    if model_key in AVAILABLE_MODELS:
        info = AVAILABLE_MODELS[model_key]
        model_size = info["size"].lower()  # GPUManager expects lowercase
        quant = info["quant"]
    elif req.model.lower() in ["4b", "12b", "27b"]:
        model_size = req.model.lower()
        quant = DEFAULT_QUANTIZATION
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model: {req.model}")
    
    try:
        start = time.time()
        gpu.load(model_size, quant)
        elapsed = int((time.time() - start) * 1000)
        return {
            "status": "success",
            "model": f"{model_size.upper()}-Q{quant}",
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/translate", response_model=TranslateResponse)
async def api_translate(req: TranslateRequest):
    """Translate text."""
    try:
        if req.stream:
            return StreamingResponse(
                translate_stream(
                    text=req.text,
                    target_lang=req.target_lang,
                    source_lang=req.source_lang,
                    model_size=req.model,
                    quantization=req.quantization,
                    chunk_size=req.chunk_size,
                    overlap=req.overlap,
                ),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        
        result = translate(
            text=req.text,
            target_lang=req.target_lang,
            source_lang=req.source_lang,
            model_size=req.model,
            quantization=req.quantization,
            chunk_size=req.chunk_size,
            overlap=req.overlap,
            auto_split=req.auto_split,
        )
        return TranslateResponse(status="success", **result)
    except Exception as e:
        return TranslateResponse(status="error", error=str(e))


@app.post("/api/translate/stream")
async def api_translate_stream(req: TranslateRequest):
    """Stream translation endpoint."""
    return StreamingResponse(
        translate_stream(
            text=req.text,
            target_lang=req.target_lang,
            source_lang=req.source_lang,
            model_size=req.model,
            quantization=req.quantization,
            chunk_size=req.chunk_size,
            overlap=req.overlap,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/translate/batch")
async def api_translate_batch(req: BatchRequest):
    """Batch translate multiple texts."""
    start_time = time.time()
    results = []
    
    for text in req.texts:
        try:
            r = translate(
                text=text,
                target_lang=req.target_lang,
                source_lang=req.source_lang,
                model_size=req.model,
                quantization=req.quantization,
            )
            results.append({"status": "success", "result": r["result"], "elapsed_ms": r["elapsed_ms"]})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
    
    return {
        "status": "success",
        "results": results,
        "total_elapsed_ms": int((time.time() - start_time) * 1000),
        "count": len(results),
    }


@app.post("/api/translate/file")
async def api_translate_file(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    source_lang: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    stream: bool = Form(False),
):
    """Translate uploaded text file."""
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        if stream:
            return StreamingResponse(
                translate_stream(text=text, target_lang=target_lang, source_lang=source_lang, model_size=model),
                media_type="text/event-stream",
            )
        
        result = translate(text=text, target_lang=target_lang, source_lang=source_lang, model_size=model)
        return TranslateResponse(status="success", **result)
    except UnicodeDecodeError:
        return TranslateResponse(status="error", error="File encoding error. Please use UTF-8.")
    except Exception as e:
        return TranslateResponse(status="error", error=str(e))


@app.get("/api/gpu/status")
async def api_gpu_status():
    return gpu.status()


@app.post("/api/gpu/offload")
async def api_gpu_offload():
    gpu.force_unload()
    return {"status": "ok", "message": "GPU memory released"}


# ==================== Static Files & UI ====================
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")


# Mount static files if directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==================== Swagger Docs ====================
# FastAPI auto-generates /docs (Swagger UI) and /redoc
