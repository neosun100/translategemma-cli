# TranslateGemma CLI

Local translation powered by [TranslateGemma](https://huggingface.co/collections/google/translategemma), supporting 55 languages with configurable language pairs (default: Cantonese ↔ English).

## Features

- **Multi-platform** - Works on macOS (Apple Silicon), Linux, and Windows
- **Multiple model sizes** - Choose from 4b, 12b, or 27b based on your hardware
- **Multiple backends** - Local (MLX/PyTorch), vLLM, or Ollama
- **Interactive REPL** - Just run `translate` and start typing
- **Auto language detection** - No need to specify source/target languages
- **Two output modes** - Direct (clean translation) or Explain (with context)
- **55 languages** - Full TranslateGemma language support
- **🆕 Long text support** - Smart chunking with sliding window for texts of any length
- **🆕 Streaming output** - Real-time translation progress
- **🆕 Batch translation** - Translate entire directories at once

## Requirements

### macOS (Apple Silicon)
- M1/M2/M3/M4 Mac
- 8GB+ unified memory (4b), 16GB+ (12b), 32GB+ (27b)
- macOS 14.0+

### Linux / Windows
- NVIDIA GPU with 8GB+ VRAM (or CPU with 16GB+ RAM)
- CUDA 11.8+ (for GPU)

### All Platforms
- Python 3.11+

## Installation

```bash
# Clone the repository
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Option 1: Install with pip (recommended)

```bash
# macOS (Apple Silicon)
pip install -e ".[mlx]"

# Linux/Windows with NVIDIA GPU
pip install -e ".[cuda]"

# Linux/Windows CPU-only
pip install -e ".[cpu]"
```

### Option 2: Install with requirements files

```bash
# macOS (Apple Silicon)
pip install -r requirements-mlx.txt && pip install -e .

# Linux/Windows with NVIDIA GPU
pip install -r requirements-cuda.txt && pip install -e .

# Linux/Windows CPU-only
pip install -r requirements-cpu.txt && pip install -e .

# Development (any platform, add tests/linting)
pip install -r requirements-dev.txt && pip install -e .
```

## Usage

### Interactive Mode (Default)

```bash
translate
```

This opens an interactive REPL with auto-detection:

```
TranslateGemma Interactive (yue ↔ en)
Model: 27b | Mode: direct | Type /help for commands

> 今日天氣好好
[yue→en] The weather is really nice today

> That's great!
[en→yue] 太好啦！

> /mode explain
Switched to explanation mode (streaming enabled)

> 你食咗飯未？
[yue→en] Have you eaten yet?

This is a common Cantonese greeting, literally "Have you eaten rice yet?"...

> /quit
再見！Goodbye!
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/to <lang>` | Force output to language (e.g., `/to en`, `/to ja`) |
| `/auto` | Enable auto-detection (default) |
| `/mode direct` | Direct translation only |
| `/mode explain` | Include explanations (streaming) |
| `/langs` | List all 55 supported languages |
| `/model <size>` | Switch model (4b, 12b, 27b) |
| `/model` | Show current model info |
| `/backend <type>` | Switch backend (auto, mlx, pytorch, vllm, ollama) |
| `/backend` | Show backend info |
| `/config` | Show configuration |
| `/clear` | Clear screen |
| `/help` | Show help |
| `/quit` | Exit |

### Single-Shot Mode

```bash
# Translate text (use --text option)
translate --text "早晨"
# Output: Good morning

# Or use the text subcommand
translate text "早晨"

# Force target language
translate --to en --text "早晨"

# Use explanation mode
translate --explain --text "你好"

# Select model size
translate --model 4b --text "Hello"

# From file
translate --file input.txt --output output.txt

# From stdin
echo "Hello world" | translate

# 🆕 Long text with chunking
translate --file long_article.txt --chunk-size 80 --overlap 20

# 🆕 Streaming output
translate --file article.txt --stream

# 🆕 Batch translate directory
translate --dir ./documents

# 🆕 Disable chunking for short text
translate --file short.txt --no-chunk
```

### Model Management

```bash
# List all models
translate model list

# Check model status
translate model status

# Download specific model
translate model download 4b

# Remove a model
translate model remove 4b

# List supported languages
translate model langs
```

### Configuration

```bash
# Initialize config file with defaults (~/.config/translate/config.yaml)
translate init

# Force overwrite existing config with defaults
translate init --force
```

## First Run

On first run, the CLI will:

1. Download your selected TranslateGemma model
2. Convert to optimized format with 4-bit quantization
3. Save to `~/.cache/translate/models/`

Download sizes:
- **4b**: ~10GB → ~3GB quantized
- **12b**: ~26GB → ~7GB quantized
- **27b**: ~54GB → ~15GB quantized

## Configuration

Config file: `~/.config/translate/config.yaml`

```yaml
model:
  name: 27b                    # Model size: 4b, 12b, or 27b
  quantization: 4              # 4-bit or 8-bit

translation:
  languages: [yue, en]         # Language pair (configurable)
  mode: direct                 # direct or explain
  max_tokens: 512

ui:
  show_detected_language: true
  colored_output: true
```

### Language Pair Examples

```yaml
# Japanese ↔ English
translation:
  languages: [ja, en]

# Chinese (Simplified) ↔ French
translation:
  languages: [zh, fr]
```

## Supported Languages

The CLI supports all 55 TranslateGemma languages. Run `translate model langs` to see the full list.

Key languages:
| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `yue` | Cantonese |
| `zh` | Chinese (Simplified) | `zh-TW` | Chinese (Traditional) |
| `ja` | Japanese | `ko` | Korean |
| `es` | Spanish | `fr` | French |
| `de` | German | `pt` | Portuguese |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=translategemma_cli

# Run specific test file
pytest tests/test_detector.py

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── conftest.py         # Shared fixtures
├── test_config.py      # Configuration tests
├── test_detector.py    # Language detection tests
├── test_model.py       # Model management tests
├── test_translator.py  # Translation engine tests
└── test_cli.py         # CLI command tests
```

## Notes

> TranslateGemma doesn't have a dedicated Cantonese (`yue`) language code. This CLI uses `zh-Hant-HK` (Traditional Chinese, Hong Kong) for the Chinese side of translations when `yue` is specified.

## Backend Options

The CLI supports multiple inference backends:

### Local Backends (Default)

- **MLX** (macOS Apple Silicon) - Native Metal optimization, superior memory efficiency
- **PyTorch** (Linux/Windows) - CUDA acceleration or CPU fallback

### vLLM Backend

[vLLM](https://docs.vllm.ai/) provides high-throughput inference with continuous batching and PagedAttention for up to 24x faster inference.

```bash
# Start vLLM server
pip install vllm
vllm serve google/translategemma-27b-it --quantization awq

# Use with CLI
translate --backend vllm --server http://localhost:8000
# Or in interactive mode
> /backend vllm
```

### Ollama Backend

[Ollama](https://ollama.ai/) provides a simple interface for running LLMs locally with one-command model downloads.

```bash
# Install Ollama from https://ollama.ai/download
# Pull the model
ollama pull translategemma:27b

# Use with CLI
translate --backend ollama
# Or in interactive mode
> /backend ollama
```

### Backend Management

```bash
# Check backend status
translate backend status

# Configure vLLM backend
translate backend vllm --url http://localhost:8000

# Configure Ollama backend
translate backend ollama

# Switch back to local
translate backend local
```

## Acknowledgements

This project was vibe-coded with [Cursor](https://cursor.com/) and [Claude Opus 4.5](https://www.anthropic.com/claude) by Anthropic. 🤖✨

## Disclaimer

**This project is not affiliated with, endorsed by, or sponsored by Google.**

TranslateGemma is an open-source model released by Google under its own license terms. This CLI tool is an independent, community-developed wrapper that provides a convenient interface for running TranslateGemma models locally. Please refer to the [TranslateGemma model cards](https://huggingface.co/collections/google/translategemma) on HuggingFace for the official model documentation and license terms.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Note: The TranslateGemma models themselves are subject to Google's model license terms. Please review and comply with the model license when using the models.
