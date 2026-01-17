# TranslateGemma CLI

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

> 🚀 Production-ready local translation powered by Google's TranslateGemma  
> Supporting 55 languages with smart chunking, streaming output, and batch processing

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model: TranslateGemma](https://img.shields.io/badge/Model-TranslateGemma-green.svg)](https://huggingface.co/collections/google/translategemma)

---

## ✨ Highlights

- **🌍 55 Languages** - Full TranslateGemma language support
- **📚 Unlimited Length** - Smart chunking with sliding window for texts of any length
- **⚡ Streaming Output** - Real-time translation progress
- **📦 Batch Processing** - Translate entire directories at once
- **🎯 Multiple Backends** - Local (MLX/PyTorch), vLLM, or Ollama
- **💻 Multi-platform** - macOS (Apple Silicon), Linux, Windows
- **🔧 Highly Configurable** - Flexible parameters for different use cases

---

## 🎬 Quick Start

### Installation

```bash
# Using uv (recommended)
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[mlx]"  # macOS Apple Silicon
# or
uv pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU

# Using pip
pip install -e ".[mlx]"  # macOS Apple Silicon
pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU
pip install -e ".[cpu]"  # CPU-only
```

### First Run

```bash
# Initialize configuration
translate init

# Download model (first time only)
translate model download 27b

# Start translating!
translate --text "Hello world"
# Output: 你好，世界。
```

---

## 🚀 Features

### 1. Smart Long Text Translation

**Problem**: TranslateGemma truncates long texts (>500 chars)

**Solution**: Smart chunking with sliding window

```bash
# Automatic chunking for long text
translate --file long_article.txt

# Custom chunk parameters
translate --file book.txt --chunk-size 80 --overlap 10

# Disable chunking for short text
translate --file short.txt --no-chunk
```

**How it works**:
```
Original: [AAAAA][BBBBB][CCCCC][DDDDD]

Sliding Window:
Chunk 1: [AAAAA]
Chunk 2:    [AA|BBBBB]    ← Overlap provides context
Chunk 3:         [BB|CCCCC]
Chunk 4:              [CC|DDDDD]

Result: Complete translation with context preservation
```

### 2. Streaming Output

Real-time translation progress for better UX:

```bash
# Stream output token by token
translate --file article.txt --stream

# Combine with chunking
translate --file book.txt --chunk-size 80 --stream
```

### 3. Batch Translation

Translate entire directories efficiently:

```bash
# Translate all .txt and .md files
translate --dir ./documents

# Output to ./documents/translated/
```

### 4. Interactive REPL

```bash
translate
```

```
TranslateGemma Interactive (yue ↔ en)
Model: 27b | Mode: direct | Type /help for commands

> 今日天氣好好
[yue→en] The weather is really nice today

> /to ja
Target language set to: ja

> Hello
[en→ja] こんにちは。

> /quit
再見！Goodbye!
```

---

## 📖 Usage

### Basic Translation

```bash
# Single text
translate --text "Hello world"

# From file
translate --file input.txt --output output.txt

# From stdin
echo "Bonjour" | translate

# Force target language
translate --text "Hello" --to ja
```

### Long Text Translation

```bash
# Auto-chunking (text > 300 chars)
translate --file article.txt

# Custom chunking
translate --file book.txt --chunk-size 80 --overlap 10

# Streaming for real-time feedback
translate --file long.txt --stream

# Disable chunking
translate --file short.txt --no-chunk
```

### Batch Processing

```bash
# Translate directory
translate --dir ./documents

# With custom parameters
translate --dir ./docs --chunk-size 100
```

### Model Management

```bash
# List models
translate model list

# Download model
translate model download 4b

# Check status
translate model status

# List supported languages
translate model langs
```

---

## ⚙️ Configuration

Config file: `~/.config/translate/config.yaml`

### Default Configuration (Optimized)

```yaml
model:
  name: 27b              # Model size: 4b, 12b, 27b
  quantization: 4        # 4-bit or 8-bit

backend:
  type: auto             # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434

translation:
  languages: [yue, en]   # Language pair
  mode: direct           # direct or explain
  max_tokens: 512        # Base max tokens (auto-adjusted for chunks)
  
  chunking:
    enabled: true        # Enable smart chunking
    chunk_size: 80       # Optimal for completeness
    overlap: 10          # Minimal repetition
    split_by: sentence   # sentence, paragraph, or char
    auto_threshold: 300  # Auto-enable for text > 300 chars

ui:
  show_detected_language: true
  colored_output: true
  show_progress: true
```

### Customization

```bash
# Initialize with defaults
translate init

# Force overwrite
translate init --force

# Edit manually
vim ~/.config/translate/config.yaml
```

---

## 🎯 Best Practices

### Chunk Size Selection

| Text Type | chunk_size | overlap | Reason |
|-----------|------------|---------|--------|
| Daily conversation | 60-80 | 10-15 | Short sentences |
| Technical docs | 80-100 | 15-20 | Term consistency |
| Literary works | 80-100 | 20-30 | Context preservation |
| Long articles | 80-100 | 10-20 | Balance quality & speed |

### When to Use Chunking

| Text Length | Recommendation |
|-------------|----------------|
| < 300 chars | Use `--no-chunk` for speed |
| 300-1000 chars | Auto-chunking (default) |
| 1000-5000 chars | `--chunk-size 80 --overlap 10` |
| 5000+ chars (books) | `--chunk-size 80 --stream` |

### Performance Tips

1. **Interactive mode** - Model loads once, faster for multiple translations
2. **Batch processing** - Use `--dir` instead of translating files one by one
3. **Streaming** - Use `--stream` for long texts to see progress
4. **Optimal chunks** - chunk_size=80, overlap=10 is the sweet spot

---

## 📊 Performance

**Test Environment**: MacBook Pro M2 Max, 96GB, MLX Backend

| Text Length | Chunks | Time | Throughput |
|-------------|--------|------|------------|
| 100 chars | 1 | 1.2s | 83 chars/s |
| 400 chars | 4 | 8.5s | 48 chars/s |
| 1000 chars | 12 | ~22s | ~45 chars/s |
| 5000 chars | 60 | ~110s | ~45 chars/s |

**Memory Usage**: 14.15 GB (stable across all text lengths)

---

## 🛠️ Requirements

### macOS (Apple Silicon)
- M1/M2/M3/M4 Mac
- 8GB+ unified memory (4b), 16GB+ (12b), 32GB+ (27b)
- macOS 14.0+

### Linux (NVIDIA GPU) ⚠️ Important

> **Note**: TranslateGemma-27b requires **multiple GPUs** on Linux due to quantization compatibility issues. See [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md) for details.

- **27b model**: 2x GPUs with ≥32GB VRAM each (e.g., A100, L40S, RTX 4090×3)
- **12b model**: 1x GPU with ≥24GB VRAM
- **4b model**: 1x GPU with ≥16GB VRAM
- CUDA 11.8+
- Python 3.11+

```bash
# Linux multi-GPU usage (required for 27b model)
CUDA_VISIBLE_DEVICES=1,2 translate --text "Hello world"
```

### Windows
- NVIDIA GPU with 16GB+ VRAM
- CUDA 11.8+ (for GPU)

### All Platforms
- Python 3.11+

---

## 📦 Installation Options

### Option 1: uv (Fastest, Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
uv venv .venv
source .venv/bin/activate

# macOS Apple Silicon
uv pip install -e ".[mlx]"

# Linux/Windows with NVIDIA GPU
uv pip install -e ".[cuda]"

# CPU-only
uv pip install -e ".[cpu]"
```

### Option 2: pipx (Isolated Installation)

```bash
# Install from local directory
pipx install /path/to/translategemma-cli[mlx]

# Or from git (when published)
pipx install git+https://github.com/jhkchan/translategemma-cli.git[mlx]
```

### Option 3: pip (Traditional)

```bash
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mlx]"  # or [cuda] or [cpu]
```

---

## 🌍 Supported Languages (55)

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `yue` | Cantonese |
| `zh` | Chinese (Simplified) | `zh-TW` | Chinese (Traditional) |
| `ja` | Japanese | `ko` | Korean |
| `fr` | French | `de` | German |
| `es` | Spanish | `pt` | Portuguese |
| `ru` | Russian | `ar` | Arabic |

...and 45 more. Run `translate model langs` for full list.

---

## 🎓 Advanced Usage

### Custom Language Pairs

Edit `~/.config/translate/config.yaml`:

```yaml
translation:
  languages: [ja, en]  # Japanese ↔ English
  # or
  languages: [zh, fr]  # Chinese ↔ French
```

### Backend Options

```bash
# Local (default)
translate --backend mlx  # macOS
translate --backend pytorch  # Linux/Windows

# vLLM (high throughput)
vllm serve google/translategemma-27b-it --quantization awq
translate --backend vllm --server http://localhost:8000

# Ollama (easy setup)
ollama pull translategemma:27b
translate --backend ollama
```

### Interactive Commands

| Command | Function |
|---------|----------|
| `/to <lang>` | Force target language |
| `/auto` | Enable auto-detection |
| `/mode direct` | Direct translation |
| `/mode explain` | With explanations |
| `/model <size>` | Switch model |
| `/backend <type>` | Switch backend |
| `/langs` | List languages |
| `/config` | Show configuration |
| `/quit` | Exit |

---

## 🔬 Technical Details

### Smart Chunking Algorithm

```python
# Sentence-based splitting with sliding window
TextChunker(
    chunk_size=80,      # Target chunk size
    overlap=10,         # Overlap for context
    split_by="sentence" # Split at sentence boundaries
)

# Process:
1. Split text at sentence boundaries
2. Group sentences into chunks (~80 chars)
3. Add overlap from previous chunk
4. Translate each chunk with context
5. Merge results (skip overlap)
```

### Adaptive max_tokens

```python
# Dynamically adjust based on input length
adaptive_max_tokens = min(
    2048,                      # Upper limit
    max(512, len(chunk) * 3)   # 3x input (safety buffer)
)

# Why 3x?
# - Chinese → English typically expands 1.5-2x
# - 3x provides safety buffer
# - Prevents truncation
```

### Merge Strategy

```python
# Simple concatenation (overlap provides context only)
def merge(chunks, translations):
    result = [translations[0]]  # Keep first complete
    for trans in translations[1:]:
        result.append(" " + trans)  # Add space between chunks
    return "".join(result)

# Note: Minimal overlap (10) reduces repetition
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main documentation (this file) |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick reference card |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | Usage best practices |
| [LONG_TEXT_FEATURE_REPORT.md](LONG_TEXT_FEATURE_REPORT.md) | Feature detailed report |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | Comprehensive test report |
| [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) | Development summary |
| [TRANSLATION_TEST_REPORT.md](TRANSLATION_TEST_REPORT.md) | Multi-language quality assessment |

---

## 🎯 Use Cases

### Use Case 1: Translate a Book

```bash
# With streaming for progress feedback
translate --file novel.txt --chunk-size 80 --overlap 10 --stream --output novel_en.txt
```

### Use Case 2: Batch Translate Documentation

```bash
# Translate all docs in directory
translate --dir ./docs

# Output to ./docs/translated/
```

### Use Case 3: Quick Translation

```bash
# Short text, no chunking
translate --text "Hello world" --no-chunk

# Or use interactive mode
translate
> Hello world
[en→yue] 你好，世界。
```

### Use Case 4: Multi-language Workflow

```bash
# English to multiple languages
translate --text "Welcome" --to ja  # Japanese
translate --text "Welcome" --to ko  # Korean
translate --text "Welcome" --to zh  # Chinese
translate --text "Welcome" --to fr  # French
```

---

## 🔧 Development Insights

### Key Learnings

1. **TranslateGemma Model Characteristics**:
   - Truncates long texts (>500 chars)
   - Stops at paragraph breaks (empty lines)
   - Requires small chunks (80-100 chars) for completeness

2. **Optimal Chunking Strategy**:
   - chunk_size=80: Best completeness (98%)
   - overlap=10: Minimal repetition (<5%)
   - split_by=sentence: Natural boundaries

3. **Adaptive max_tokens**:
   - Fixed 512 tokens insufficient for long chunks
   - 3x input length ensures completeness
   - Cap at 2048 to prevent over-generation

4. **Merge Strategy**:
   - Simple concatenation works best
   - Overlap provides context, not for deduplication
   - Smart deduplication is complex (future work)

### Architecture

```
User Input
    ↓
TextChunker (chunker.py)
    ↓
[Chunk 1] [Chunk 2] [Chunk 3] ...
    ↓         ↓         ↓
Translator.translate_long()
    ↓
Adaptive max_tokens (3x input)
    ↓
MLX/PyTorch/vLLM/Ollama Backend
    ↓
Merge Results
    ↓
Output (Complete Translation)
```

---

## 🧪 Testing

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=translategemma_cli

# Run specific test
pytest tests/test_chunker.py
```

### Manual Testing

```bash
# Comprehensive test suite
./tests/comprehensive_test.sh

# Or test individual features
translate --file test.txt --chunk-size 80
translate --dir ./test_docs
translate --text "Test" --stream
```

---

## 📊 Benchmarks

### Translation Completeness

| Method | Completeness | Speed | Recommendation |
|--------|--------------|-------|----------------|
| No chunking | 13% | Fast | ❌ Long text fails |
| chunk=150 | 70% | Medium | ⚠️ Not recommended |
| chunk=100 | 95% | Medium | ✅ Good |
| chunk=80 | 98% | Medium | ✅ **Best** |
| chunk=60 | 100% | Slow | ⚠️ Over-chunking |

### Overlap Impact

| Overlap | Repetition | Quality | Recommendation |
|---------|------------|---------|----------------|
| 0 | 0% | Medium | ⚠️ No context |
| 10 | <5% | High | ✅ **Best** |
| 20 | 5-10% | High | ✅ Good |
| 30 | 10-15% | Medium | ⚠️ Too much |
| 50 | 20-30% | Low | ❌ Not recommended |

---

## 🎨 Model Selection

| Model | Parameters | Disk Size | Memory | Use Case |
|-------|------------|-----------|--------|----------|
| **4b** | 5B | ~3.2 GB | 8GB+ | Fast translation, limited resources |
| **12b** | 13B | ~7.0 GB | 16GB+ | Balance performance & quality |
| **27b** | 29B | ~14.8 GB | 32GB+ | **Best quality** (recommended) |

---

## 🌟 What's New in v0.2.0

### Major Features

- ✅ **Smart Text Chunking** - Handle unlimited text length
- ✅ **Sliding Window** - Preserve context with overlap
- ✅ **Streaming Output** - Real-time translation progress
- ✅ **Batch Translation** - Process entire directories
- ✅ **Adaptive max_tokens** - Prevent truncation
- ✅ **Progress Display** - Visual feedback with rich

### New CLI Parameters

```bash
--chunk-size <int>    # Chunk size (default: 80)
--overlap <int>       # Overlap size (default: 10)
--no-chunk            # Disable chunking
--stream              # Enable streaming
--dir <path>          # Batch translate directory
```

### Performance Improvements

- **Translation completeness**: 13% → 98% (for long texts)
- **Throughput**: Stable 45-50 chars/sec
- **Memory**: Unchanged (14.15 GB)

---

## 🐛 Known Limitations

### 1. Model Behavior

- **Paragraph breaks**: Model stops at empty lines
  - **Solution**: Use small chunks (80 chars)
- **Long chunks**: Truncates if chunk > 150 chars
  - **Solution**: Adaptive max_tokens (3x input)

### 2. Overlap Repetition

- **Issue**: overlap > 10 causes slight repetition
- **Reason**: Overlapped region translated twice
- **Recommendation**: Use overlap=10-20

### 3. Not Yet Implemented

- Smart deduplication (planned for v0.3.0)
- Translation cache (planned for v0.3.0)
- Resume capability (planned for v0.4.0)
- Terminology support (under evaluation)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

**Note**: TranslateGemma models are subject to Google's model license terms. Please review and comply with the [model license](https://ai.google.dev/gemma/terms).

---

## 🙏 Acknowledgments

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - Base translation model
- [MLX](https://github.com/ml-explore/mlx) - Apple Silicon optimization
- [Cursor](https://cursor.com/) + [Claude](https://www.anthropic.com/claude) - Development tools
- [hy-mt](https://github.com/neosun100/hy-mt) - Inspiration for chunking strategy

---

## 🔗 Links

- **GitHub**: https://github.com/jhkchan/translategemma-cli
- **HuggingFace**: https://huggingface.co/collections/google/translategemma
- **Issues**: https://github.com/jhkchan/translategemma-cli/issues
- **Documentation**: See [docs](docs/) directory

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jhkchan/translategemma-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jhkchan/translategemma-cli/discussions)
- **Email**: [Your Email]

---

## 🗺️ Roadmap

### v0.3.0 (Next)
- [ ] Smart deduplication algorithm
- [ ] Translation cache system
- [ ] Improved language detection
- [ ] Terminology support

### v0.4.0 (Future)
- [ ] Resume capability
- [ ] Parallel translation (multi-GPU)
- [ ] Web UI
- [ ] REST API server

---

**Version**: 0.2.1  
**Last Updated**: 2026-01-17  
**Status**: Production Ready ✅
