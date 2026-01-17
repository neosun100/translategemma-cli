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
DEFAULT_MODEL = os.getenv("MODEL_NAME", "12b")
DEFAULT_QUANTIZATION = int(os.getenv("QUANTIZATION", "4"))
DEFAULT_BACKEND = os.getenv("BACKEND", "gguf")
GPU_IDLE_TIMEOUT = int(os.getenv("GPU_IDLE_TIMEOUT", "300"))
MAX_CHUNK_LENGTH = int(os.getenv("MAX_CHUNK_LENGTH", "80"))

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
    "4b-Q4": {"size": "4b", "quant": 4, "vram": "~3GB", "speed": "fastest", "quality": "good"},
    "4b-Q8": {"size": "4b", "quant": 8, "vram": "~5GB", "speed": "fast", "quality": "better"},
    "12b-Q4": {"size": "12b", "quant": 4, "vram": "~7GB", "speed": "balanced", "quality": "high"},
    "12b-Q8": {"size": "12b", "quant": 8, "vram": "~12GB", "speed": "medium", "quality": "higher"},
    "27b-Q4": {"size": "27b", "quant": 4, "vram": "~15GB", "speed": "slow", "quality": "best"},
    "27b-Q8": {"size": "27b", "quant": 8, "vram": "~28GB", "speed": "slowest", "quality": "best+"},
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
        if self.unload_timer:
            self.unload_timer.cancel()
        self.unload_timer = threading.Timer(GPU_IDLE_TIMEOUT, self._auto_unload)
        self.unload_timer.daemon = True
        self.unload_timer.start()

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
                gpu_info = {
                    "available": True,
                    "device": torch.cuda.get_device_name(0),
                    "free_mb": int(torch.cuda.mem_get_info()[0] / 1024 / 1024),
                    "total_mb": int(torch.cuda.mem_get_info()[1] / 1024 / 1024),
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
def split_text(text: str, max_length: int = MAX_CHUNK_LENGTH) -> List[str]:
    """Smart text splitting by sentences."""
    import re
    
    if len(text) <= max_length:
        return [text]
    
    # Split by sentence endings
    sentence_pattern = r'([。！？.!?]+[\s]*)'
    parts = re.split(sentence_pattern, text)
    
    sentences = []
    for i in range(0, len(parts), 2):
        sent = parts[i]
        if i + 1 < len(parts):
            sent += parts[i + 1]
        if sent.strip():
            sentences.append(sent)
    
    if not sentences:
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    chunks = []
    current = ""
    
    for sent in sentences:
        if len(current) + len(sent) <= max_length:
            current += sent
        else:
            if current:
                chunks.append(current.strip())
            current = sent if len(sent) <= max_length else ""
            if len(sent) > max_length:
                for i in range(0, len(sent), max_length):
                    chunks.append(sent[i:i+max_length].strip())
    
    if current.strip():
        chunks.append(current.strip())
    
    return chunks


# ==================== Translation Functions ====================
def translate(
    text: str,
    target_lang: str,
    source_lang: str = None,
    model_size: str = None,
    quantization: int = None,
    chunk_size: int = MAX_CHUNK_LENGTH,
    auto_split: bool = True,
) -> dict:
    """Translate text with chunking support."""
    start_time = time.time()
    
    translator = gpu.load(model_size, quantization)
    
    # Set target language
    if target_lang:
        translator.set_force_target(target_lang)
    
    chunks = split_text(text, chunk_size) if auto_split else [text]
    results = []
    
    for chunk in chunks:
        result, src, tgt = translator.translate(chunk, force_target=target_lang)
        results.append(result)
        if not source_lang:
            source_lang = src
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    final_result = " ".join(results) if len(results) > 1 else results[0]
    
    return {
        "result": final_result,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "elapsed_ms": elapsed_ms,
        "chunks": len(chunks),
        "input_length": len(text),
        "output_length": len(final_result),
        "model": f"{gpu.current_model}-Q{gpu.current_quant}",
        "chars_per_sec": round(len(text) / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
    }


async def translate_stream(
    text: str,
    target_lang: str,
    source_lang: str = None,
    model_size: str = None,
    quantization: int = None,
    chunk_size: int = MAX_CHUNK_LENGTH,
) -> AsyncGenerator[str, None]:
    """Stream translation results chunk by chunk."""
    start_time = time.time()
    chunks = split_text(text, chunk_size)
    total_chunks = len(chunks)
    
    yield f"data: {json.dumps({'event': 'start', 'total_chunks': total_chunks, 'input_length': len(text)})}\n\n"
    
    translator = gpu.load(model_size, quantization)
    if target_lang:
        translator.set_force_target(target_lang)
    
    results = []
    
    for i, chunk in enumerate(chunks):
        chunk_start = time.time()
        
        yield f"data: {json.dumps({'event': 'progress', 'chunk': i + 1, 'total': total_chunks})}\n\n"
        
        loop = asyncio.get_event_loop()
        result, src, tgt = await loop.run_in_executor(
            None, lambda c=chunk: translator.translate(c, force_target=target_lang)
        )
        results.append(result)
        
        chunk_elapsed = int((time.time() - chunk_start) * 1000)
        yield f"data: {json.dumps({'event': 'chunk', 'chunk': i + 1, 'result': result, 'elapsed_ms': chunk_elapsed})}\n\n"
    
    total_elapsed = int((time.time() - start_time) * 1000)
    final_result = " ".join(results)
    
    yield f"data: {json.dumps({'event': 'done', 'result': final_result, 'elapsed_ms': total_elapsed})}\n\n"


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
        "supported_languages": len(LANGUAGES),
    }


@app.get("/api/languages")
async def api_languages():
    return LANGUAGES


@app.get("/api/models")
async def api_models():
    return {
        "models": AVAILABLE_MODELS,
        "current": f"{gpu.current_model}-Q{gpu.current_quant}" if gpu.current_model else None,
        "default": f"{DEFAULT_MODEL}-Q{DEFAULT_QUANTIZATION}",
    }


@app.post("/api/models/switch")
async def api_switch_model(req: SwitchModelRequest):
    """Switch to a different model."""
    # Parse model key
    model_key = req.model.upper() if "-Q" in req.model.upper() else req.model
    
    if model_key in AVAILABLE_MODELS:
        info = AVAILABLE_MODELS[model_key]
        model_size = info["size"]
        quant = info["quant"]
    elif req.model in ["4b", "12b", "27b"]:
        model_size = req.model
        quant = DEFAULT_QUANTIZATION
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model: {req.model}")
    
    try:
        start = time.time()
        gpu.load(model_size, quant)
        elapsed = int((time.time() - start) * 1000)
        return {
            "status": "success",
            "model": f"{model_size}-Q{quant}",
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
