"""Interactive CLI for TranslateGemma."""

import os
import sys
import warnings
import logging
from typing import Optional

# Suppress tokenizer warnings before any imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"
warnings.filterwarnings("ignore", message=".*tokenizer.*")
warnings.filterwarnings("ignore", message=".*incorrect regex.*")
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress transformers logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from .config import (
    get_config,
    create_default_config,
    DEFAULT_CONFIG_DIR,
    SUPPORTED_LANGUAGES,
    MODEL_SIZES,
    MODEL_INFO,
    BackendType,
)
from .detector import (
    detect_language,
    get_target_language,
    format_language_indicator,
    get_language_name,
    is_valid_language,
)
from .model import (
    is_model_ready,
    download_and_convert_model,
    get_model_info,
    list_downloaded_models,
    remove_model,
    get_backend,
)
from .translator import get_translator
from .backends import check_vllm_server, check_ollama_server, OllamaBackend

app = typer.Typer(
    name="translate",
    help="Local translation powered by TranslateGemma (multi-platform)",
    no_args_is_help=False,
)
console = Console()

# Prompt style
prompt_style = Style.from_dict({
    "prompt": "#00aa00 bold",
})


def print_welcome(translator):
    """Print welcome message."""
    config = get_config()
    lang1, lang2 = config.languages
    mode = translator.get_output_mode()
    model_size = translator.current_model_size or config.model_size
    
    console.print()
    console.print(
        Panel(
            f"[bold]TranslateGemma Interactive[/bold] ({lang1} ↔ {lang2})\n"
            f"[dim]Model: {model_size} | Mode: {mode} | Type /help for commands[/dim]",
            border_style="cyan",
        )
    )
    console.print()


def print_help():
    """Print help message."""
    help_text = """
[bold]Commands:[/bold]
  [cyan]/to <lang>[/cyan]       - Force translation to language (e.g., /to en, /to yue, /to ja)
  [cyan]/auto[/cyan]            - Enable auto-detection (default)
  [cyan]/mode direct[/cyan]     - Direct translation only (no streaming)
  [cyan]/mode explain[/cyan]    - Include explanations (with streaming)
  [cyan]/langs[/cyan]           - List all supported languages
  [cyan]/model <size>[/cyan]    - Switch model (4b, 12b, 27b)
  [cyan]/model[/cyan]           - Show current model info
  [cyan]/backend <type>[/cyan]  - Switch backend (auto, mlx, pytorch, gguf, vllm, ollama)
  [cyan]/backend[/cyan]         - Show backend info
  [cyan]/config[/cyan]          - Show current configuration
  [cyan]/clear[/cyan]           - Clear screen
  [cyan]/help[/cyan]            - Show this help
  [cyan]/quit[/cyan]            - Exit (or /exit, Ctrl+D)
"""
    console.print(help_text)


def print_languages():
    """Print all supported languages in a table."""
    table = Table(title="Supported Languages (55)")
    table.add_column("Code", style="cyan")
    table.add_column("Language", style="white")
    table.add_column("Code", style="cyan")
    table.add_column("Language", style="white")
    
    # Sort and pair languages for two-column display
    langs = sorted(SUPPORTED_LANGUAGES.items())
    mid = (len(langs) + 1) // 2
    
    for i in range(mid):
        code1, name1 = langs[i]
        if i + mid < len(langs):
            code2, name2 = langs[i + mid]
            table.add_row(code1, name1, code2, name2)
        else:
            table.add_row(code1, name1, "", "")
    
    console.print(table)


def print_config():
    """Print current configuration."""
    config = get_config()
    translator = get_translator()
    
    console.print("\n[bold]Current Configuration:[/bold]")
    console.print(f"  Model size: [cyan]{config.model_size}[/cyan]")
    console.print(f"  Quantization: [cyan]{config.quantization_bits}-bit[/cyan]")
    console.print(f"  Languages: [cyan]{config.languages[0]} ↔ {config.languages[1]}[/cyan]")
    console.print(f"  Output mode: [cyan]{translator.get_output_mode()}[/cyan]")
    
    # Backend info
    backend_type = config.backend_type
    actual_backend = translator.backend or get_backend()
    if backend_type == "auto":
        console.print(f"  Backend: [cyan]auto[/cyan] → [cyan]{actual_backend}[/cyan]")
    else:
        console.print(f"  Backend: [cyan]{backend_type}[/cyan]")
    
    # Server URLs if using server backends
    if backend_type in ("vllm", "auto"):
        console.print(f"  vLLM URL: [dim]{config.vllm_url}[/dim]")
    if backend_type in ("ollama", "auto"):
        console.print(f"  Ollama URL: [dim]{config.ollama_url}[/dim]")
    
    force_target = translator.get_force_target()
    if force_target:
        console.print(f"  Force target: [cyan]{force_target} ({get_language_name(force_target)})[/cyan]")
    else:
        console.print(f"  Force target: [dim]auto-detect[/dim]")
    
    console.print(f"\n  Config file: [dim]{config.config_path}[/dim]")
    console.print()


def handle_command(command: str, translator) -> bool:
    """
    Handle slash commands.
    
    Returns:
        True if should continue REPL, False to exit
    """
    cmd = command.strip()
    cmd_lower = cmd.lower()
    
    if cmd_lower in ("/quit", "/exit", "/q"):
        console.print("[dim]再見！Goodbye![/dim]")
        return False
    
    elif cmd_lower == "/help":
        print_help()
    
    elif cmd_lower.startswith("/to "):
        lang = cmd[4:].strip()
        if not lang:
            console.print("[yellow]Usage: /to <language_code>[/yellow]")
            console.print("[dim]Example: /to en, /to yue, /to ja[/dim]")
        elif not is_valid_language(lang):
            console.print(f"[yellow]Unknown language: {lang}[/yellow]")
            console.print("[dim]Use /langs to see supported languages.[/dim]")
        else:
            translator.set_force_target(lang)
            console.print(f"[green]Output language set to: {get_language_name(lang)} ({lang})[/green]")
    
    elif cmd_lower == "/auto":
        translator.set_force_target(None)
        config = get_config()
        console.print(f"[green]Auto-detection re-enabled ({config.languages[0]} ↔ {config.languages[1]})[/green]")
    
    elif cmd_lower.startswith("/mode "):
        mode = cmd[6:].strip().lower()
        if mode == "direct":
            translator.set_output_mode("direct")
            console.print("[green]Switched to direct mode (no streaming)[/green]")
        elif mode == "explain":
            translator.set_output_mode("explain")
            console.print("[green]Switched to explanation mode (streaming enabled)[/green]")
        else:
            console.print(f"[yellow]Unknown mode: {mode}[/yellow]")
            console.print("[dim]Available modes: direct, explain[/dim]")
    
    elif cmd_lower == "/langs":
        print_languages()
    
    elif cmd_lower.startswith("/model "):
        size = cmd[7:].strip().lower()
        if size not in MODEL_SIZES:
            console.print(f"[yellow]Unknown model size: {size}[/yellow]")
            console.print(f"[dim]Available sizes: {', '.join(MODEL_SIZES)}[/dim]")
        else:
            console.print(f"[cyan]Switching to translategemma-{size}-it...[/cyan]")
            try:
                translator.ensure_model_loaded(size)
                info = MODEL_INFO[size]
                console.print(f"[green]Now using: TranslateGemma-{size}-it ({info['params']} params)[/green]")
            except Exception as e:
                console.print(f"[red]Error loading model: {e}[/red]")
    
    elif cmd_lower == "/model":
        info = get_model_info()
        console.print(f"\n[bold]Current Model:[/bold] TranslateGemma-{info['size']}-it")
        console.print(f"  Parameters: {info['params']}")
        console.print(f"  Quantization: {info['quantization_bits']}-bit")
        console.print(f"  Backend: {info['backend']}")
        if info.get("gguf_ready"):
            console.print(f"  Location: [dim]{info['gguf_path']}[/dim]")
        elif info.get("hf_ready"):
            console.print(f"  Location: [dim]{info['hf_path']}[/dim]")
        else:
            console.print(f"  Location: [dim]{info['hf_path']} (not downloaded)[/dim]")
        if info.get("size_gb"):
            console.print(f"  Size on disk: {info['size_gb']} GB")
        console.print(f"  Status: {'[green]Ready[/green]' if info['ready'] else '[yellow]Not downloaded[/yellow]'}")
        console.print()
    
    elif cmd_lower == "/config":
        print_config()
    
    elif cmd_lower.startswith("/backend "):
        backend = cmd[9:].strip().lower()
        valid_backends = ("auto", "mlx", "pytorch", "gguf", "vllm", "ollama")
        if backend not in valid_backends:
            console.print(f"[yellow]Unknown backend: {backend}[/yellow]")
            console.print(f"[dim]Available backends: {', '.join(valid_backends)}[/dim]")
        else:
            # Check server availability for vllm/ollama
            if backend == "vllm":
                available, error = check_vllm_server(get_config().vllm_url)
                if not available:
                    console.print(f"[yellow]⚠ vLLM server not available: {error}[/yellow]")
                    console.print("[dim]Start vLLM: vllm serve google/translategemma-27b-it[/dim]")
                    return True
            elif backend == "ollama":
                available, error = check_ollama_server(get_config().ollama_url)
                if not available:
                    console.print(f"[yellow]⚠ Ollama not available: {error}[/yellow]")
                    console.print("[dim]Install: https://ollama.ai/download[/dim]")
                    return True
            elif backend == "gguf":
                # Check if llama-cpp-python is installed
                try:
                    from llama_cpp import Llama
                except ImportError:
                    console.print("[yellow]⚠ llama-cpp-python not installed[/yellow]")
                    console.print("[dim]Install: pip install llama-cpp-python[/dim]")
                    return True
            
            config = get_config()
            config.backend_type = backend
            try:
                translator.ensure_model_loaded(backend_type=backend)
                console.print(f"[green]Switched to {backend} backend[/green]")
            except Exception as e:
                console.print(f"[red]Error switching backend: {e}[/red]")
    
    elif cmd_lower == "/backend":
        config = get_config()
        translator = get_translator()
        actual = translator.backend or get_backend()
        
        console.print(f"\n[bold]Backend Configuration:[/bold]")
        console.print(f"  Configured: [cyan]{config.backend_type}[/cyan]")
        console.print(f"  Active: [cyan]{actual}[/cyan]")
        
        if config.backend_type in ("vllm", "auto"):
            available, _ = check_vllm_server(config.vllm_url)
            status = "[green]✓ Connected[/green]" if available else "[dim]Not connected[/dim]"
            console.print(f"  vLLM: {status} ({config.vllm_url})")
        
        if config.backend_type in ("ollama", "auto"):
            available, _ = check_ollama_server(config.ollama_url)
            status = "[green]✓ Running[/green]" if available else "[dim]Not running[/dim]"
            console.print(f"  Ollama: {status} ({config.ollama_url})")
        
        console.print()
    
    elif cmd_lower == "/clear":
        console.clear()
        print_welcome(translator)
    
    else:
        console.print(f"[yellow]Unknown command: {command}[/yellow]")
        console.print("[dim]Type /help for available commands.[/dim]")
    
    return True


def run_interactive():
    """Run the interactive REPL."""
    config = get_config()
    translator = get_translator()
    
    # Ensure model is ready
    if not is_model_ready():
        download_and_convert_model()
    
    # Load model
    translator.ensure_model_loaded()
    
    print_welcome(translator)
    
    # Set up prompt with history
    history_file = DEFAULT_CONFIG_DIR / "history.txt"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    session: PromptSession = PromptSession(
        history=FileHistory(str(history_file)),
        style=prompt_style,
    )
    
    while True:
        try:
            # Get input
            text = session.prompt("> ")
            
            if not text.strip():
                continue
            
            # Handle commands
            if text.startswith("/"):
                if not handle_command(text, translator):
                    break
                continue
            
            # Translate
            try:
                # Detect language for indicator
                source = detect_language(text, config.languages)
                target = translator.get_force_target() or get_target_language(source, config.languages)
                
                # Show language indicator
                if config.show_language_indicator:
                    indicator = format_language_indicator(source, target)
                    console.print(f"[dim]{indicator}[/dim] ", end="")
                
                # Use streaming for explain mode, direct generation for direct mode
                if translator.get_output_mode() == "explain":
                    # Stream output
                    for token, _, _ in translator.translate_stream(text):
                        console.print(token, end="")
                    console.print()  # Newline after streaming
                else:
                    # Direct mode - no streaming, cleaned output
                    translation, _, _ = translator.translate(text)
                    console.print(translation)
                
            except Exception as e:
                console.print(f"[red]Translation error: {e}[/red]")
        
        except KeyboardInterrupt:
            console.print()  # Newline
            continue
        
        except EOFError:
            # Ctrl+D
            console.print("\n[dim]再見！Goodbye![/dim]")
            break


def translate_single(
    text: str,
    force_target: Optional[str] = None,
    model_size: Optional[str] = None,
    explain: bool = False,
    stream: bool = False,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    no_chunk: bool = False,
) -> str:
    """Translate a single text and return result."""
    translator = get_translator()
    config = get_config()
    
    if model_size:
        if not is_model_ready(model_size):
            download_and_convert_model(model_size)
        translator.ensure_model_loaded(model_size)
    else:
        if not is_model_ready():
            download_and_convert_model()
        translator.ensure_model_loaded()
    
    mode = "explain" if explain else "direct"
    
    # Determine if we should use chunking
    # Force chunking if user explicitly set chunk_size or overlap
    force_chunking = chunk_size is not None or overlap is not None
    use_chunking = not no_chunk and (
        force_chunking or 
        (config.chunking_enabled and len(text) > config.auto_chunk_threshold)
    )
    
    if use_chunking:
        # Use long text translation with chunking
        _chunk_size = chunk_size or config.chunk_size
        _overlap = overlap or config.chunk_overlap
        
        if stream:
            # Stream output
            result = []
            for item in translator.translate_long(
                text,
                force_target=force_target,
                mode=mode,
                chunk_size=_chunk_size,
                overlap=_overlap,
                split_by=config.chunk_split_by,
                stream=True,
            ):
                # Handle both string tokens and tuples
                if isinstance(item, tuple):
                    token = item[0]  # Extract token from (token, src, tgt) tuple
                else:
                    token = item
                print(token, end="", flush=True)
                result.append(token)
            print()  # Newline at end
            return "".join(result)
        else:
            # Batch mode with progress
            from rich.progress import Progress, SpinnerColumn, TextColumn
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Translating...", total=None)
                
                def progress_callback(current, total, chunk_text):
                    progress.update(task, description=f"[cyan]Chunk {current}/{total}")
                
                translation = translator.translate_long(
                    text,
                    force_target=force_target,
                    mode=mode,
                    chunk_size=_chunk_size,
                    overlap=_overlap,
                    split_by=config.chunk_split_by,
                    stream=False,
                    progress_callback=progress_callback,
                )
            return translation
    else:
        # Regular translation (no chunking)
        translation, source, target = translator.translate(text, force_target, mode)
        return translation


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    text: Optional[str] = typer.Option(
        None,
        help="Text to translate",
    ),
    to: Optional[str] = typer.Option(
        None,
        "--to", "-t",
        help="Force target language (e.g., en, yue, ja)",
    ),
    model_size: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="Model size to use (4b, 12b, 27b)",
    ),
    backend: Optional[str] = typer.Option(
        None,
        "--backend", "-b",
        help="Backend to use (auto, mlx, pytorch, gguf, vllm, ollama)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server", "-s",
        help="Server URL for vLLM/Ollama (e.g., http://localhost:8000)",
    ),
    explain: bool = typer.Option(
        False,
        "--explain", "-e",
        help="Include explanations in output",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file", "-f",
        help="Read text from file",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Write translation to file",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        help="Enable streaming output for long text",
    ),
    chunk_size: Optional[int] = typer.Option(
        None,
        "--chunk-size",
        help="Chunk size for long text translation (default: 200)",
    ),
    overlap: Optional[int] = typer.Option(
        None,
        "--overlap",
        help="Overlap size between chunks (default: 50)",
    ),
    no_chunk: bool = typer.Option(
        False,
        "--no-chunk",
        help="Disable chunking (translate entire text at once)",
    ),
    dir_path: Optional[str] = typer.Option(
        None,
        "--dir",
        help="Translate all text files in directory",
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature",
        help="Sampling temperature (0.0=deterministic, higher=more random)",
    ),
    top_p: Optional[float] = typer.Option(
        None,
        "--top-p",
        help="Nucleus sampling threshold (0.0-1.0, 1.0=disabled)",
    ),
    top_k: Optional[int] = typer.Option(
        None,
        "--top-k",
        help="Top-k sampling (0=disabled)",
    ),
    repetition_penalty: Optional[float] = typer.Option(
        None,
        "--repetition-penalty",
        help="Repetition penalty (1.0=disabled, >1.0=penalize)",
    ),
):
    """
    Translate text using TranslateGemma.
    
    Run without arguments for interactive mode.
    
    Examples:
    
        translate                           # Interactive mode
        
        translate "Hello world"             # Translate text (use quotes)
        
        translate --to ja "Hello"           # Translate to Japanese
        
        translate model list                # List available models
    """
    # If a subcommand is being invoked, skip the main logic
    if ctx.invoked_subcommand is not None:
        return
    
    # Validate --to option
    force_target: str | None = None
    if to:
        if not is_valid_language(to):
            console.print(f"[red]Invalid target language: {to}[/red]")
            console.print("[dim]Use 'translate model langs' to see supported languages.[/dim]")
            raise typer.Exit(1)
        force_target = to
    
    # Validate --model option
    if model_size and model_size not in MODEL_SIZES:
        console.print(f"[red]Invalid model size: {model_size}[/red]")
        console.print(f"[dim]Available sizes: {', '.join(MODEL_SIZES)}[/dim]")
        raise typer.Exit(1)
    
    # Validate --backend option
    valid_backends = ("auto", "mlx", "pytorch", "gguf", "vllm", "ollama")
    if backend and backend not in valid_backends:
        console.print(f"[red]Invalid backend: {backend}[/red]")
        console.print(f"[dim]Available backends: {', '.join(valid_backends)}[/dim]")
        raise typer.Exit(1)
    
    # Apply backend and server settings
    config = get_config()
    if backend:
        config.backend_type = backend
    if server:
        # Determine which server URL to set based on backend
        if backend == "vllm" or (not backend and "8000" in server):
            config.vllm_url = server
        elif backend == "ollama" or (not backend and "11434" in server):
            config.ollama_url = server
        else:
            # Default to vllm
            config.vllm_url = server
    
    # Apply generation parameters if specified
    if temperature is not None:
        config.temperature = temperature
    if top_p is not None:
        config.top_p = top_p
    if top_k is not None:
        config.top_k = top_k
    if repetition_penalty is not None:
        config.repetition_penalty = repetition_penalty
    
    # Handle directory batch translation
    if dir_path:
        from pathlib import Path
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        
        dir_path_obj = Path(dir_path)
        if not dir_path_obj.exists() or not dir_path_obj.is_dir():
            console.print(f"[red]Directory not found: {dir_path}[/red]")
            raise typer.Exit(1)
        
        # Find all text files
        text_files = list(dir_path_obj.glob("*.txt")) + list(dir_path_obj.glob("*.md"))
        if not text_files:
            console.print(f"[yellow]No .txt or .md files found in {dir_path}[/yellow]")
            raise typer.Exit(1)
        
        # Create output directory
        output_dir = dir_path_obj / "translated"
        output_dir.mkdir(exist_ok=True)
        
        console.print(f"[cyan]Found {len(text_files)} files to translate[/cyan]")
        console.print(f"[dim]Output directory: {output_dir}[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Translating files...", total=len(text_files))
            
            for file_path in text_files:
                progress.update(task, description=f"[cyan]{file_path.name}")
                
                try:
                    with open(file_path) as f:
                        file_text = f.read().strip()
                    
                    translation = translate_single(
                        file_text, force_target, model_size, explain,
                        False, chunk_size, overlap, no_chunk  # No stream for batch
                    )
                    
                    output_file = output_dir / file_path.name
                    with open(output_file, "w") as f:
                        f.write(translation + "\n")
                    
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error translating {file_path.name}: {e}[/red]")
        
        console.print(f"\n[green]✓ Translated {len(text_files)} files to {output_dir}[/green]")
        return
    
    # Handle file input
    if file:
        try:
            with open(file) as f:
                text = f.read().strip()
        except FileNotFoundError:
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)
    
    # Handle stdin
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    
    # Single-shot mode
    if text:
        translation = translate_single(
            text, force_target, model_size, explain,
            stream, chunk_size, overlap, no_chunk
        )
        
        if output:
            with open(output, "w") as f:
                f.write(translation + "\n")
            console.print(f"[green]Translation written to {output}[/green]")
        else:
            if not stream:  # Only print if not already streamed
                print(translation)
        return
    
    # Interactive mode (default)
    if not sys.stdin.isatty():
        console.print("[yellow]Interactive mode requires a terminal.[/yellow]")
        console.print("[dim]Usage: translate \"text to translate\"[/dim]")
        raise typer.Exit(1)
    
    run_interactive()


# Create a separate command for single-shot translation with positional argument
@app.command("text", hidden=False)
def translate_cmd(
    text: str = typer.Argument(..., help="Text to translate"),
    to: Optional[str] = typer.Option(
        None,
        "--to", "-t",
        help="Force target language (e.g., en, yue, ja)",
    ),
    model_size: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="Model size to use (4b, 12b, 27b)",
    ),
    explain: bool = typer.Option(
        False,
        "--explain", "-e",
        help="Include explanations in output",
    ),
):
    """Translate text (alternative to using quotes with main command)."""
    # Validate --to option
    force_target: str | None = None
    if to:
        if not is_valid_language(to):
            console.print(f"[red]Invalid target language: {to}[/red]")
            raise typer.Exit(1)
        force_target = to
    
    # Validate --model option
    if model_size and model_size not in MODEL_SIZES:
        console.print(f"[red]Invalid model size: {model_size}[/red]")
        raise typer.Exit(1)
    
    translation = translate_single(text, force_target, model_size, explain)
    print(translation)


@app.command("model")
def model_cmd(
    action: str = typer.Argument(
        "status",
        help="Action: status, list, download, remove, langs",
    ),
    size: Optional[str] = typer.Argument(
        None,
        help="Model size for download/remove (4b, 12b, 27b)",
    ),
    bits: int = typer.Option(
        4,
        "--bits", "-b",
        help="Quantization bits for download (4 or 8)",
    ),
):
    """Manage TranslateGemma models."""
    if action == "status":
        info = get_model_info(size)
        console.print(f"\n[bold]Model:[/bold] TranslateGemma-{info['size']}-it")
        console.print(f"[bold]Parameters:[/bold] {info['params']}")
        console.print(f"[bold]HuggingFace:[/bold] {info['hf_source']}")
        console.print(f"[bold]Format:[/bold] {info['backend'].upper()}")
        console.print(f"[bold]Quantization:[/bold] {info['quantization_bits']}-bit")
        if info.get("gguf_ready"):
            console.print(f"[bold]Location:[/bold] {info['gguf_path']}")
        else:
            console.print(f"[bold]Location:[/bold] {info['hf_path']}")
        
        if info["ready"]:
            console.print(f"[bold]Size:[/bold] {info.get('size_gb', 'N/A')} GB")
            console.print("[bold]Status:[/bold] [green]Ready[/green]")
        else:
            console.print("[bold]Status:[/bold] [yellow]Not downloaded[/yellow]")
        console.print()
    
    elif action == "list":
        models = list_downloaded_models()
        
        table = Table(title="TranslateGemma Models")
        table.add_column("Size", style="cyan")
        table.add_column("Parameters")
        table.add_column("Status")
        table.add_column("Disk Size")
        
        for m in models:
            status = "[green]✓ Downloaded[/green]" if m["downloaded"] else "[dim]Not downloaded[/dim]"
            disk_size = f"{m.get('actual_size_gb', m['quantized_size_gb'])} GB" if m["downloaded"] else f"~{m['quantized_size_gb']} GB"
            table.add_row(m["size"], m["params"], status, disk_size)
        
        console.print(table)
    
    elif action == "download":
        if not size:
            console.print("[yellow]Please specify model size: 4b, 12b, or 27b[/yellow]")
            console.print("[dim]Example: translate model download 12b[/dim]")
            raise typer.Exit(1)
        
        if size not in MODEL_SIZES:
            console.print(f"[red]Invalid model size: {size}[/red]")
            console.print(f"[dim]Available sizes: {', '.join(MODEL_SIZES)}[/dim]")
            raise typer.Exit(1)
        
        download_and_convert_model(size, bits)
    
    elif action == "remove":
        if not size:
            console.print("[yellow]Please specify model size: 4b, 12b, or 27b[/yellow]")
            console.print("[dim]Example: translate model remove 4b[/dim]")
            raise typer.Exit(1)
        
        if size not in MODEL_SIZES:
            console.print(f"[red]Invalid model size: {size}[/red]")
            raise typer.Exit(1)
        
        if remove_model(size):
            console.print(f"[green]Removed translategemma-{size}-it[/green]")
        else:
            console.print(f"[yellow]Model not found: translategemma-{size}-it[/yellow]")
    
    elif action == "langs":
        print_languages()
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("[dim]Available actions: status, list, download, remove, langs[/dim]")
        raise typer.Exit(1)


@app.command("init")
def init_cmd(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing config file",
    ),
):
    """Initialize configuration file with defaults."""
    config_path = DEFAULT_CONFIG_DIR / "config.yaml"
    
    if config_path.exists() and not force:
        console.print(f"[yellow]Config file already exists:[/yellow] {config_path}")
        console.print("[dim]Use --force to overwrite with defaults.[/dim]")
        raise typer.Exit(0)
    
    # Remove existing config if force is set
    if config_path.exists() and force:
        config_path.unlink()
    
    create_default_config(config_path)
    console.print(f"[green]✓ Created config file:[/green] {config_path}")
    console.print("\n[bold]Default configuration:[/bold]")
    console.print("  Model: 27b (4-bit quantization)")
    console.print("  Languages: yue ↔ en (Cantonese ↔ English)")
    console.print("  Mode: direct")
    console.print(f"\n[dim]Edit {config_path} to customize.[/dim]")


@app.command("backend")
def backend_cmd(
    action: str = typer.Argument(
        "status",
        help="Action: status, vllm, ollama",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url", "-u",
        help="Server URL (for vllm/ollama actions)",
    ),
):
    """Manage inference backends (local, vLLM, Ollama)."""
    config = get_config()
    
    if action == "status":
        console.print("\n[bold]Backend Status:[/bold]")
        console.print(f"  Configured: [cyan]{config.backend_type}[/cyan]")
        
        # Local backends
        local_backend = get_backend()
        console.print(f"\n  [bold]Local:[/bold] {local_backend}")
        
        # vLLM
        vllm_url = url or config.vllm_url
        available, error = check_vllm_server(vllm_url)
        if available:
            console.print(f"  [bold]vLLM:[/bold] [green]✓ Running[/green] at {vllm_url}")
        else:
            console.print(f"  [bold]vLLM:[/bold] [dim]Not connected[/dim] ({vllm_url})")
        
        # Ollama
        ollama_url = url if url and "11434" in url else config.ollama_url
        available, error = check_ollama_server(ollama_url)
        if available:
            console.print(f"  [bold]Ollama:[/bold] [green]✓ Running[/green] at {ollama_url}")
            # List available TranslateGemma models
            backend = OllamaBackend(server_url=ollama_url)
            models = backend.get_models()
            tg_models = [m for m in models if "translategemma" in m.lower()]
            if tg_models:
                console.print(f"    Models: {', '.join(tg_models)}")
        else:
            console.print(f"  [bold]Ollama:[/bold] [dim]Not running[/dim] ({ollama_url})")
        
        console.print()
    
    elif action == "vllm":
        vllm_url = url or config.vllm_url
        available, error = check_vllm_server(vllm_url)
        
        if available:
            console.print(f"[green]✓ vLLM server running at {vllm_url}[/green]")
            config.backend_type = "vllm"
            config.vllm_url = vllm_url
            config.save()
            console.print("[dim]Backend set to vLLM. Config saved.[/dim]")
        else:
            console.print(f"[red]✗ Cannot connect to vLLM at {vllm_url}[/red]")
            console.print(f"[dim]Error: {error}[/dim]")
            console.print("\n[bold]To start vLLM:[/bold]")
            console.print("  pip install vllm")
            console.print("  vllm serve google/translategemma-27b-it")
            raise typer.Exit(1)
    
    elif action == "ollama":
        ollama_url = url or config.ollama_url
        available, error = check_ollama_server(ollama_url)
        
        if available:
            console.print(f"[green]✓ Ollama running at {ollama_url}[/green]")
            
            # Check for TranslateGemma models
            backend = OllamaBackend(server_url=ollama_url)
            models = backend.get_models()
            tg_models = [m for m in models if "translategemma" in m.lower()]
            
            if tg_models:
                console.print(f"  Available models: {', '.join(tg_models)}")
            else:
                console.print("\n[yellow]TranslateGemma not found in Ollama.[/yellow]")
                console.print("[dim]Pull with: ollama pull translategemma:27b[/dim]")
            
            config.backend_type = "ollama"
            config.ollama_url = ollama_url
            config.save()
            console.print("\n[dim]Backend set to Ollama. Config saved.[/dim]")
        else:
            console.print(f"[red]✗ Cannot connect to Ollama at {ollama_url}[/red]")
            console.print(f"[dim]Error: {error}[/dim]")
            console.print("\n[bold]To install Ollama:[/bold]")
            console.print("  https://ollama.ai/download")
            console.print("\n[bold]Then pull the model:[/bold]")
            console.print("  ollama pull translategemma:27b")
            raise typer.Exit(1)
    
    elif action == "local":
        config.backend_type = "auto"
        config.save()
        console.print(f"[green]Backend set to local ({get_backend()})[/green]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("[dim]Available actions: status, vllm, ollama, local[/dim]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
