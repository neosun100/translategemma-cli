"""Translation engine for TranslateGemma."""

from __future__ import annotations

import re
from typing import Any, Generator, Literal, Callable

from .config import get_config, OutputMode, SUPPORTED_LANGUAGES, BackendType
from .detector import detect_language, get_target_language
from .model import load_model, Backend, get_backend as get_local_backend
from .backends import VLLMBackend, OllamaBackend
from .chunker import TextChunker, Chunk


# Language code mapping to TranslateGemma's supported codes
LANG_CODE_MAP = {
    "yue": "zh-Hant-HK",  # Cantonese -> Hong Kong Traditional Chinese
    "zh-TW": "zh-Hant",   # Traditional Chinese
    # Most other codes match directly
}

# Extended backend type including server backends
ExtendedBackend = Literal["mlx", "pytorch", "vllm", "ollama"]


class Translator:
    """TranslateGemma translation engine with cross-platform support."""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._backend: ExtendedBackend | None = None
        self._force_target: str | None = None
        self._output_mode: OutputMode = "direct"
        self._current_model_size: str | None = None
        
        # Server backends
        self._vllm_backend: VLLMBackend | None = None
        self._ollama_backend: OllamaBackend | None = None

    def _resolve_backend(self, backend_type: BackendType) -> ExtendedBackend:
        """
        Resolve the actual backend to use based on configuration.
        
        Args:
            backend_type: Configured backend type (may be "auto")
            
        Returns:
            Resolved backend: mlx, pytorch, vllm, or ollama
        """
        if backend_type == "auto":
            return get_local_backend()  # Returns "mlx" or "pytorch"
        return backend_type

    def ensure_model_loaded(
        self,
        model_size: str | None = None,
        backend_type: BackendType | None = None,
    ) -> None:
        """
        Ensure the model is loaded.
        
        Args:
            model_size: Model size to load. If None, uses config default.
            backend_type: Backend to use. If None, uses config default.
        """
        config = get_config()
        size = model_size or config.model_size
        backend_cfg = backend_type or config.backend_type
        resolved_backend = self._resolve_backend(backend_cfg)
        
        # Check if we need to switch backends
        if self._backend != resolved_backend:
            self._model = None
            self._tokenizer = None
            self._vllm_backend = None
            self._ollama_backend = None
            self._current_model_size = None
        
        # For server backends, initialize the client
        if resolved_backend == "vllm":
            if self._vllm_backend is None:
                self._vllm_backend = VLLMBackend(
                    server_url=config.vllm_url,
                    model=None,  # Use server default
                )
                available, error = self._vllm_backend.is_available()
                if not available:
                    raise RuntimeError(f"vLLM server not available: {error}")
            self._backend = "vllm"
            self._current_model_size = size
            self._output_mode = config.output_mode
            return
        
        if resolved_backend == "ollama":
            if self._ollama_backend is None:
                ollama_model = OllamaBackend.MODEL_MAP.get(size, f"translategemma:{size}")
                self._ollama_backend = OllamaBackend(
                    server_url=config.ollama_url,
                    model=ollama_model,
                )
                available, error = self._ollama_backend.is_available()
                if not available:
                    raise RuntimeError(f"Ollama server not available: {error}")
                
                # Check if model is available, offer to pull if not
                if not self._ollama_backend.has_model():
                    from rich.console import Console
                    console = Console()
                    console.print(f"[yellow]Model {ollama_model} not found in Ollama.[/yellow]")
                    console.print("[dim]Pulling model...[/dim]")
                    self._ollama_backend.pull_model()
            
            self._backend = "ollama"
            self._current_model_size = size
            self._output_mode = config.output_mode
            return
        
        # Local backends (mlx, pytorch)
        # Check if we need to switch models
        if self._model is not None and self._current_model_size == size:
            return
        
        # Unload current model if switching
        if self._model is not None and self._current_model_size != size:
            self._model = None
            self._tokenizer = None
        
        self._model, self._tokenizer, self._backend = load_model(size)
        self._current_model_size = size
        self._output_mode = config.output_mode

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    @property
    def current_model_size(self) -> str | None:
        """Get the currently loaded model size."""
        return self._current_model_size

    @property
    def backend(self) -> ExtendedBackend | None:
        """Get the current backend."""
        return self._backend
    
    @property
    def is_server_backend(self) -> bool:
        """Check if using a server backend (vLLM or Ollama)."""
        return self._backend in ("vllm", "ollama")

    def set_force_target(self, target: str | None) -> None:
        """
        Force translations to a specific target language.
        
        Args:
            target: Target language code, or None for auto-detect
        """
        if target is not None and target not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {target}")
        self._force_target = target

    def get_force_target(self) -> str | None:
        """Get the current forced target language."""
        return self._force_target

    def set_output_mode(self, mode: OutputMode) -> None:
        """Set the output mode (direct or explain)."""
        if mode not in ("direct", "explain"):
            raise ValueError("Mode must be 'direct' or 'explain'")
        self._output_mode = mode

    def get_output_mode(self) -> OutputMode:
        """Get the current output mode."""
        return self._output_mode

    def _map_lang_code(self, code: str) -> str:
        """Map internal language code to TranslateGemma's format."""
        return LANG_CODE_MAP.get(code, code)

    def _format_messages(
        self, text: str, source_lang: str, target_lang: str
    ) -> list[dict]:
        """
        Format input for TranslateGemma's chat template.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Messages list for chat template
        """
        source_code = self._map_lang_code(source_lang)
        target_code = self._map_lang_code(target_lang)
        
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_code,
                        "target_lang_code": target_code,
                        "text": text,
                    }
                ],
            }
        ]

    def _format_messages_for_server(
        self, text: str, source_lang: str, target_lang: str
    ) -> list[dict]:
        """
        Format input for server backends (vLLM/Ollama).
        
        Server backends use the OpenAI-style message format.
        We construct a prompt that mimics TranslateGemma's expected input.
        """
        source_code = self._map_lang_code(source_lang)
        target_code = self._map_lang_code(target_lang)
        
        # Construct a translation prompt for server backends
        prompt = f"Translate the following text from {source_code} to {target_code}:\n\n{text}"
        
        return [
            {"role": "user", "content": prompt}
        ]

    def translate(
        self,
        text: str,
        force_target: str | None = None,
        mode: OutputMode | None = None,
    ) -> tuple[str, str, str]:
        """
        Translate text with automatic language detection.
        
        Args:
            text: Text to translate
            force_target: Override target language (optional)
            mode: Override output mode (optional)
            
        Returns:
            Tuple of (translation, source_lang, target_lang)
            
        Note:
            The model must be loaded before calling this method.
            Call ensure_model_loaded() once at session start.
        """
        if not self.is_loaded:
            self.ensure_model_loaded()
        config = get_config()
        output_mode = mode or self._output_mode
        
        # Detect source language
        source_lang = detect_language(text, config.languages)
        
        # Determine target language
        target_lang = force_target or self._force_target or get_target_language(source_lang, config.languages)
        
        # Generate based on backend
        if self._backend == "vllm":
            response = self._generate_vllm(text, source_lang, target_lang, config.max_tokens)
        elif self._backend == "ollama":
            response = self._generate_ollama(text, source_lang, target_lang, config.max_tokens)
        else:
            # Local backends (mlx, pytorch)
            # Format messages
            messages = self._format_messages(text, source_lang, target_lang)
            
            # Apply chat template
            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            
            if self._backend == "mlx":
                response = self._generate_mlx(prompt, config.max_tokens)
            else:
                response = self._generate_pytorch(prompt, config.max_tokens)
        
        # Clean response based on mode
        if output_mode == "direct":
            response = self._clean_response(response)
        else:
            # Explain mode - just clean special tokens
            response = self._clean_special_tokens(response)
        
        return response, source_lang, target_lang

    def translate_long(
        self,
        text: str,
        force_target: str | None = None,
        mode: OutputMode | None = None,
        chunk_size: int = 200,
        overlap: int = 50,
        split_by: Literal["sentence", "paragraph", "char"] = "sentence",
        stream: bool = False,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> str | Generator[str, None, None]:
        """
        Translate long text using chunking with sliding window.
        
        Args:
            text: Text to translate
            force_target: Override target language (optional)
            mode: Override output mode (optional)
            chunk_size: Target size for each chunk (in characters)
            overlap: Overlap size between chunks (in characters)
            split_by: How to split text - "sentence", "paragraph", or "char"
            stream: Whether to stream output
            progress_callback: Callback function(current, total, chunk_text)
            
        Returns:
            Translated text (string) or generator if stream=True
        """
        if not self.is_loaded:
            self.ensure_model_loaded()
        
        config = get_config()
        output_mode = mode or self._output_mode
        
        # Detect source and target languages
        source_lang = detect_language(text, config.languages)
        target_lang = force_target or self._force_target or get_target_language(source_lang, config.languages)
        
        # Create chunker
        chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=overlap,
            split_by=split_by,
        )
        
        # Split into chunks
        chunks = chunker.chunk(text)
        
        if not chunks:
            return "" if not stream else iter([])
        
        # If only one chunk, use regular translate
        if len(chunks) == 1:
            if stream:
                return self.translate_stream(text, force_target)
            else:
                result, _, _ = self.translate(text, force_target, mode)
                return result
        
        # Translate each chunk
        if stream:
            return self._translate_long_stream(
                chunks, source_lang, target_lang, output_mode, progress_callback
            )
        else:
            return self._translate_long_batch(
                chunks, source_lang, target_lang, output_mode, progress_callback
            )
    
    def _translate_long_batch(
        self,
        chunks: list[Chunk],
        source_lang: str,
        target_lang: str,
        output_mode: OutputMode,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> str:
        """Translate chunks in batch mode."""
        config = get_config()
        translations = []
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(i + 1, len(chunks), chunk.text[:50])
            
            # Adaptive max_tokens based on chunk length
            # Rule: Chinese to English typically expands 1.5-2x
            # Use 3x for safety buffer, cap at 2048
            adaptive_max_tokens = min(2048, max(config.max_tokens, int(len(chunk.text) * 3)))
            
            # Generate based on backend
            if self._backend == "vllm":
                response = self._generate_vllm(chunk.text, source_lang, target_lang, adaptive_max_tokens)
            elif self._backend == "ollama":
                response = self._generate_ollama(chunk.text, source_lang, target_lang, adaptive_max_tokens)
            else:
                # Local backends
                messages = self._format_messages(chunk.text, source_lang, target_lang)
                prompt = self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                
                if self._backend == "mlx":
                    response = self._generate_mlx(prompt, adaptive_max_tokens)
                else:
                    response = self._generate_pytorch(prompt, adaptive_max_tokens)
            
            # Clean response
            if output_mode == "direct":
                response = self._clean_response(response)
            else:
                response = self._clean_special_tokens(response)
            
            translations.append(response)
        
        # Merge translations
        chunker = TextChunker()  # Create instance for merge method
        return chunker.merge(chunks, translations)
    
    def _translate_long_stream(
        self,
        chunks: list[Chunk],
        source_lang: str,
        target_lang: str,
        output_mode: OutputMode,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> Generator[str, None, None]:
        """Translate chunks in streaming mode."""
        config = get_config()
        translations = []
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(i + 1, len(chunks), chunk.text[:50])
            
            # Adaptive max_tokens
            adaptive_max_tokens = min(2048, max(config.max_tokens, int(len(chunk.text) * 3)))
            
            # Collect streamed tokens for this chunk
            chunk_translation = ""
            
            if self._backend == "vllm":
                for token, _, _ in self._stream_vllm(chunk.text, source_lang, target_lang, adaptive_max_tokens):
                    chunk_translation += token
                    yield token
            elif self._backend == "ollama":
                for token, _, _ in self._stream_ollama(chunk.text, source_lang, target_lang, adaptive_max_tokens):
                    chunk_translation += token
                    yield token
            else:
                # Local backends
                messages = self._format_messages(chunk.text, source_lang, target_lang)
                prompt = self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                
                if self._backend == "mlx":
                    for token, _, _ in self._stream_mlx(prompt, adaptive_max_tokens, source_lang, target_lang):
                        chunk_translation += token
                        yield token
                else:
                    for token, _, _ in self._stream_pytorch(prompt, adaptive_max_tokens, source_lang, target_lang):
                        chunk_translation += token
                        yield token
            
            # Clean and store translation
            if output_mode == "direct":
                chunk_translation = self._clean_response(chunk_translation)
            else:
                chunk_translation = self._clean_special_tokens(chunk_translation)
            
            translations.append(chunk_translation)


    def _generate_mlx(self, prompt: str, max_tokens: int) -> str:
        """Generate response using MLX backend."""
        from mlx_lm import generate
        
        # Note: Current MLX version doesn't support sampling parameters
        # They are only used for PyTorch/vLLM/Ollama backends
        response = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False,
        )
        
        # Handle GenerationResponse object (newer mlx_lm versions)
        if hasattr(response, 'text'):
            response = response.text
        
        return response

    def _generate_pytorch(self, prompt: str, max_tokens: int) -> str:
        """Generate response using PyTorch backend."""
        import torch
        
        config = get_config()
        inputs = self._tokenizer(prompt, return_tensors="pt")
        
        # Move to same device as model
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Prepare generation kwargs
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        
        # Add sampling parameters
        if config.temperature > 0.0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = config.temperature
            if config.top_p < 1.0:
                gen_kwargs["top_p"] = config.top_p
            if config.top_k > 0:
                gen_kwargs["top_k"] = config.top_k
        else:
            gen_kwargs["do_sample"] = False
        
        if config.repetition_penalty != 1.0:
            gen_kwargs["repetition_penalty"] = config.repetition_penalty
        
        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)
        
        # Decode only the new tokens
        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        return response

    def _generate_vllm(
        self, text: str, source_lang: str, target_lang: str, max_tokens: int
    ) -> str:
        """Generate response using vLLM server backend."""
        messages = self._format_messages_for_server(text, source_lang, target_lang)
        return self._vllm_backend.generate(messages, max_tokens=max_tokens)

    def _generate_ollama(
        self, text: str, source_lang: str, target_lang: str, max_tokens: int
    ) -> str:
        """Generate response using Ollama server backend."""
        messages = self._format_messages_for_server(text, source_lang, target_lang)
        return self._ollama_backend.generate(messages, max_tokens=max_tokens)

    def _clean_special_tokens(self, text: str) -> str:
        """Remove special tokens from response."""
        special_tokens = [
            "<end_of_turn>",
            "<eos>",
            "<bos>",
            "<pad>",
            "</s>",
            "<s>",
        ]
        for token in special_tokens:
            text = text.replace(token, "")
        return text.strip()

    def _clean_response(self, text: str) -> str:
        """Remove special tokens and extract direct translation only."""
        text = self._clean_special_tokens(text)
        
        # Explanation markers - lines starting with these are skipped
        explanation_markers = [
            "This phrase",
            "This is",
            "This term",
            "This expression",
            "This word",
            "However,",
            "Note:",
            "Note that",
            "It's important",
            "A direct",
            "A neutral",
            "A literal",
            "A more",
            "Alternatively",
            "The phrase",
            "The term",
            "The word",
            "[Translate",
            "Given the",
            "In this context",
            "Without context",
            "Depending on",
            "Please note",
            "Be aware",
            "Warning:",
            "Caution:",
            "literally",
            "would be:",
            "could be:",
            "might be:",
        ]
        
        # Patterns that indicate the whole response is an explanation (no direct translation)
        refusal_patterns = [
            "I cannot",
            "I can't",
            "I won't",
            "I'm unable",
            "inappropriate",
            "offensive",
            "vulgar",
            "not appropriate",
            "cannot translate",
            "unable to translate",
        ]
        
        # Check if the response is a refusal/explanation without translation
        text_lower = text.lower()
        is_refusal = any(pattern.lower() in text_lower for pattern in refusal_patterns)
        
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that start with explanation markers (case-insensitive check)
            line_lower = line.lower()
            is_explanation = any(line_lower.startswith(marker.lower()) for marker in explanation_markers)
            if is_explanation:
                continue
            
            # Skip lines that are clearly meta-commentary
            if line.startswith('(') and line.endswith(')'):
                continue
            if line.startswith('[') and line.endswith(']'):
                continue
            
            clean_lines.append(line)
        
        if clean_lines:
            # Return the first non-explanation line (usually the actual translation)
            result = clean_lines[0]
            
            # Remove markdown bold markers
            result = result.replace("**", "")
            result = result.strip()
            
            # Remove quotes if the translation is wrapped in them
            quote_pairs = [
                ('"', '"'),
                ("'", "'"),
                ('\u201c', '\u201d'),  # curly double quotes
                ('\u2018', '\u2019'),  # curly single quotes
                ('「', '」'),          # CJK brackets
                ('『', '』'),          # CJK double brackets
            ]
            if len(result) >= 2:
                for start_q, end_q in quote_pairs:
                    if result.startswith(start_q) and result.endswith(end_q):
                        result = result[len(start_q):-len(end_q)]
                        break
            
            # Remove parenthetical explanations at the end
            result = re.sub(r'\s*\([^)]+\)\s*$', '', result)
            result = re.sub(r'\s*（[^）]+）\s*$', '', result)  # Chinese parentheses
            
            # If the result still looks like an explanation, try to extract quoted text
            result_lower = result.lower()
            if any(marker.lower() in result_lower for marker in explanation_markers[:10]):
                # Try to find quoted translation within the text
                quoted = re.search(r'["\u201c]([^"\u201d]+)["\u201d]', text)
                if quoted:
                    result = quoted.group(1)
            
            return result.strip()
        
        # If no clean lines found but there's quoted text, extract it
        quoted = re.search(r'["\u201c]([^"\u201d]+)["\u201d]', text)
        if quoted:
            return quoted.group(1).strip()
        
        return text

    def translate_stream(
        self,
        text: str,
        force_target: str | None = None,
    ) -> Generator[tuple[str, str, str], None, None]:
        """
        Translate text with streaming output (explain mode only).
        
        Note: Streaming is only available in explain mode. For direct mode,
        use translate() which returns the complete cleaned response.
        
        The model must be loaded before calling this method.
        Call ensure_model_loaded() once at session start.
        
        Args:
            text: Text to translate
            force_target: Override target language (optional)
            
        Yields:
            Tuples of (token, source_lang, target_lang)
        """
        if not self.is_loaded:
            self.ensure_model_loaded()
        config = get_config()
        
        # Detect source language
        source_lang = detect_language(text, config.languages)
        
        # Determine target language
        target_lang = force_target or self._force_target or get_target_language(source_lang, config.languages)
        
        # Stream based on backend
        if self._backend == "vllm":
            yield from self._stream_vllm(text, source_lang, target_lang, config.max_tokens)
        elif self._backend == "ollama":
            yield from self._stream_ollama(text, source_lang, target_lang, config.max_tokens)
        else:
            # Local backends (mlx, pytorch)
            # Format messages
            messages = self._format_messages(text, source_lang, target_lang)
            
            # Apply chat template
            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            
            if self._backend == "mlx":
                yield from self._stream_mlx(prompt, config.max_tokens, source_lang, target_lang)
            else:
                yield from self._stream_pytorch(prompt, config.max_tokens, source_lang, target_lang)

    def _stream_mlx(
        self, prompt: str, max_tokens: int, source_lang: str, target_lang: str
    ) -> Generator[tuple[str, str, str], None, None]:
        """Stream generation using MLX backend."""
        from mlx_lm import stream_generate
        
        # Note: Current MLX version doesn't support sampling parameters
        # They are only used for PyTorch/vLLM/Ollama backends
        for response in stream_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
        ):
            token = response.text if hasattr(response, 'text') else str(response)
            
            # Stop on special tokens
            if "<end_of_turn>" in token or "<eos>" in token:
                break
            yield token, source_lang, target_lang

    def _stream_pytorch(
        self, prompt: str, max_tokens: int, source_lang: str, target_lang: str
    ) -> Generator[tuple[str, str, str], None, None]:
        """Stream generation using PyTorch backend."""
        import torch
        from transformers import TextIteratorStreamer
        from threading import Thread
        
        config = get_config()
        inputs = self._tokenizer(prompt, return_tensors="pt")
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": max_tokens,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        
        # Add sampling parameters
        if config.temperature > 0.0:
            generation_kwargs["do_sample"] = True
            generation_kwargs["temperature"] = config.temperature
            if config.top_p < 1.0:
                generation_kwargs["top_p"] = config.top_p
            if config.top_k > 0:
                generation_kwargs["top_k"] = config.top_k
        else:
            generation_kwargs["do_sample"] = False
        
        if config.repetition_penalty != 1.0:
            generation_kwargs["repetition_penalty"] = config.repetition_penalty
        
        thread = Thread(target=self._model.generate, kwargs=generation_kwargs)
        thread.start()
        
        for token in streamer:
            if "<end_of_turn>" in token or "<eos>" in token:
                break
            yield token, source_lang, target_lang
        
        thread.join()

    def _stream_vllm(
        self, text: str, source_lang: str, target_lang: str, max_tokens: int
    ) -> Generator[tuple[str, str, str], None, None]:
        """Stream generation using vLLM server backend."""
        messages = self._format_messages_for_server(text, source_lang, target_lang)
        
        for token in self._vllm_backend.generate_stream(messages, max_tokens=max_tokens):
            if "<end_of_turn>" in token or "<eos>" in token:
                break
            yield token, source_lang, target_lang

    def _stream_ollama(
        self, text: str, source_lang: str, target_lang: str, max_tokens: int
    ) -> Generator[tuple[str, str, str], None, None]:
        """Stream generation using Ollama server backend."""
        messages = self._format_messages_for_server(text, source_lang, target_lang)
        
        for token in self._ollama_backend.generate_stream(messages, max_tokens=max_tokens):
            if "<end_of_turn>" in token or "<eos>" in token:
                break
            yield token, source_lang, target_lang


# Global translator instance
_translator: Translator | None = None


def get_translator() -> Translator:
    """Get the global translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def reset_translator() -> None:
    """Reset the global translator instance."""
    global _translator
    _translator = None
