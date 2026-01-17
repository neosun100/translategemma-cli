"""Backend implementations for vLLM and Ollama inference servers."""

from __future__ import annotations

import json
from typing import Any, Generator
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from rich.console import Console

console = Console()


class VLLMBackend:
    """
    vLLM backend using OpenAI-compatible API.
    
    vLLM provides high-throughput inference with:
    - Continuous batching for parallel requests
    - PagedAttention for efficient memory management
    - Up to 24x higher throughput than HuggingFace Transformers
    
    Usage:
        # Start vLLM server
        vllm serve google/translategemma-27b-it --port 8000
        
        # Or with quantization
        vllm serve google/translategemma-27b-it --quantization awq
    """
    
    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        model: str | None = None,
    ):
        """
        Initialize vLLM backend.
        
        Args:
            server_url: URL of the vLLM server (default: http://localhost:8000)
            model: Model name to use (optional, uses server default)
        """
        self.server_url = server_url.rstrip("/")
        self.model = model
        self._available_models: list[str] | None = None
    
    def is_available(self) -> tuple[bool, str | None]:
        """
        Check if the vLLM server is available.
        
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            req = Request(f"{self.server_url}/v1/models", method="GET")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                self._available_models = [m["id"] for m in data.get("data", [])]
                return True, None
        except URLError as e:
            return False, f"Cannot connect to vLLM server at {self.server_url}: {e.reason}"
        except HTTPError as e:
            return False, f"vLLM server error: {e.code} {e.reason}"
        except Exception as e:
            return False, f"vLLM connection error: {e}"
    
    def get_models(self) -> list[str]:
        """Get list of available models on the server."""
        if self._available_models is None:
            self.is_available()
        return self._available_models or []
    
    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate a response using the vLLM server.
        
        Args:
            messages: Chat messages in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0 for deterministic)
            
        Returns:
            Generated text response
        """
        # Get model from server if not specified
        model = self.model
        if not model:
            models = self.get_models()
            if models:
                model = models[0]
            else:
                raise RuntimeError("No models available on vLLM server")
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        req = Request(
            f"{self.server_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        
        try:
            with urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode())
                return data["choices"][0]["message"]["content"]
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"vLLM API error {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"vLLM generation error: {e}")
    
    def generate_stream(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response using the vLLM server.
        
        Args:
            messages: Chat messages in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Token strings as they are generated
        """
        model = self.model
        if not model:
            models = self.get_models()
            if models:
                model = models[0]
            else:
                raise RuntimeError("No models available on vLLM server")
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        req = Request(
            f"{self.server_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "text/event-stream")
        
        try:
            with urlopen(req, timeout=120) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
                        
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"vLLM streaming error {e.code}: {error_body}")


class OllamaBackend:
    """
    Ollama backend for local LLM inference.
    
    Ollama provides:
    - One-command model downloads
    - Cross-platform support
    - Simple REST API
    
    Usage:
        # Pull the model
        ollama pull translategemma:27b
        
        # Model runs automatically when called
    """
    
    # Map model sizes to Ollama model names
    MODEL_MAP = {
        "4b": "translategemma:4b",
        "12b": "translategemma:12b",
        "27b": "translategemma:27b",
    }
    
    def __init__(
        self,
        server_url: str = "http://localhost:11434",
        model: str = "translategemma:27b",
    ):
        """
        Initialize Ollama backend.
        
        Args:
            server_url: URL of the Ollama server (default: http://localhost:11434)
            model: Model name to use (default: translategemma:27b)
        """
        self.server_url = server_url.rstrip("/")
        self.model = model
        self._available_models: list[str] | None = None
    
    def is_available(self) -> tuple[bool, str | None]:
        """
        Check if Ollama is running and the model is available.
        
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            # Check if Ollama is running
            req = Request(f"{self.server_url}/api/tags", method="GET")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                self._available_models = [m["name"] for m in data.get("models", [])]
                return True, None
        except URLError as e:
            return False, f"Cannot connect to Ollama at {self.server_url}: {e.reason}"
        except HTTPError as e:
            return False, f"Ollama server error: {e.code} {e.reason}"
        except Exception as e:
            return False, f"Ollama connection error: {e}"
    
    def get_models(self) -> list[str]:
        """Get list of available models on Ollama."""
        if self._available_models is None:
            self.is_available()
        return self._available_models or []
    
    def has_model(self, model: str | None = None) -> bool:
        """Check if a specific model is available."""
        model = model or self.model
        models = self.get_models()
        # Check both exact match and partial match (e.g., "translategemma:27b" in "translategemma:27b-q4_K_M")
        return any(model in m or m.startswith(model.split(":")[0]) for m in models)
    
    def pull_model(self, model: str | None = None) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model to pull (default: self.model)
            
        Returns:
            True if successful
        """
        model = model or self.model
        
        payload = {"name": model, "stream": False}
        
        req = Request(
            f"{self.server_url}/api/pull",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        
        try:
            console.print(f"[cyan]Pulling {model} via Ollama...[/cyan]")
            console.print("[dim]This may take a while for first download.[/dim]\n")
            
            with urlopen(req, timeout=3600) as response:  # 1 hour timeout for large models
                # Ollama streams progress updates
                for line in response:
                    try:
                        data = json.loads(line.decode())
                        status = data.get("status", "")
                        if "pulling" in status.lower():
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)
                            if total > 0:
                                pct = (completed / total) * 100
                                console.print(f"\r[dim]Progress: {pct:.1f}%[/dim]", end="")
                    except json.JSONDecodeError:
                        continue
                
                console.print("\n[green]✓ Model pulled successfully[/green]\n")
                return True
                
        except HTTPError as e:
            console.print(f"[red]Failed to pull model: {e.code} {e.reason}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error pulling model: {e}[/red]")
            return False
    
    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate a response using Ollama.
        
        Args:
            messages: Chat messages in OpenAI-like format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        
        req = Request(
            f"{self.server_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        
        try:
            with urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode())
                return data["message"]["content"]
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"Ollama API error {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"Ollama generation error: {e}")
    
    def generate_stream(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response using Ollama.
        
        Args:
            messages: Chat messages in OpenAI-like format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Token strings as they are generated
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        
        req = Request(
            f"{self.server_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        
        try:
            with urlopen(req, timeout=120) as response:
                for line in response:
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode())
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"Ollama streaming error {e.code}: {error_body}")


def check_vllm_server(url: str = "http://localhost:8000") -> tuple[bool, str | None]:
    """Quick check if vLLM server is available."""
    backend = VLLMBackend(server_url=url)
    return backend.is_available()


def check_ollama_server(url: str = "http://localhost:11434") -> tuple[bool, str | None]:
    """Quick check if Ollama server is available."""
    backend = OllamaBackend(server_url=url)
    return backend.is_available()
