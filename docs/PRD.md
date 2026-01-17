# Product Requirements Document: TranslateGemma Local CLI

## Overview

This document outlines the requirements for running [TranslateGemma](https://huggingface.co/collections/google/translategemma) models locally through a command-line interface, with configurable language pairs (default: Cantonese 粵語 ↔ English).

### Background

TranslateGemma is Google's state-of-the-art open translation model family based on Gemma 3, supporting 55 languages including Cantonese (yue). The model family includes three parameter sizes:

| Model | Parameters | HuggingFace |
|-------|------------|-------------|
| TranslateGemma-4b-it | 5B | [google/translategemma-4b-it](https://huggingface.co/google/translategemma-4b-it) |
| TranslateGemma-12b-it | 13B | [google/translategemma-12b-it](https://huggingface.co/google/translategemma-12b-it) |
| TranslateGemma-27b-it | 29B | [google/translategemma-27b-it](https://huggingface.co/google/translategemma-27b-it) |

Running this model locally enables:

- **Privacy**: No data leaves the device
- **Offline capability**: Translation without internet connectivity
- **Cost efficiency**: No API costs for high-volume translation
- **Low latency**: Direct hardware access without network round-trips

### Goals

1. Enable local execution of TranslateGemma models on multiple platforms (macOS, Linux, Windows)
2. Provide an **interactive-first CLI** with automatic language detection
3. Support **multiple model sizes** (4b, 12b, 27b) for different hardware capabilities
4. Optimize memory usage through quantization for consumer hardware
5. Deliver acceptable inference speed for conversational use

---

## System Requirements

### Platform Support

| Platform | Backend | Status |
|----------|---------|--------|
| macOS (Apple Silicon M1/M2/M3/M4) | MLX (Metal) | Supported |
| Linux (NVIDIA GPU) | PyTorch + CUDA | Supported |
| Linux (CPU) | PyTorch | Supported |
| Windows (NVIDIA GPU) | PyTorch + CUDA | Supported |
| Windows (CPU) | PyTorch | Supported |
| Any (with vLLM server) | vLLM | Supported |
| Any (with Ollama) | Ollama | Supported |

### Hardware Requirements by Model Size

#### TranslateGemma-27b-it (Default)

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| macOS Apple Silicon | M4 32GB (4-bit) | M4 Pro/Max 64GB+ |
| Linux/Windows NVIDIA | RTX 3090 24GB | RTX 4090 / A100 |
| Linux/Windows CPU | 64GB RAM | 128GB RAM |

#### TranslateGemma-12b-it

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| macOS Apple Silicon | M1/M2/M3/M4 16GB | M4 32GB |
| Linux/Windows NVIDIA | RTX 3080 12GB | RTX 4080+ |
| Linux/Windows CPU | 32GB RAM | 64GB RAM |

#### TranslateGemma-4b-it

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| macOS Apple Silicon | M1/M2/M3/M4 8GB | M4 16GB+ |
| Linux/Windows NVIDIA | RTX 3060 8GB | RTX 3070+ |
| Linux/Windows CPU | 16GB RAM | 32GB RAM |

### Memory Considerations (4-bit Quantization)

| Model | Native Size | 4-bit Size | Peak Memory |
|-------|-------------|------------|-------------|
| TranslateGemma-4b-it | ~10GB | ~3GB | ~5GB |
| TranslateGemma-12b-it | ~26GB | ~7GB | ~10GB |
| TranslateGemma-27b-it | ~54GB | ~15GB | ~20GB |

**Recommendation**: 
- Use 4b model for systems with 8-16GB memory
- Use 12b model for systems with 16-32GB memory  
- Use 27b model for systems with 32GB+ memory (default)

---

## Technical Architecture

### Framework Selection

**Platform-Adaptive Backend**:

| Platform | Framework | Rationale |
|----------|-----------|-----------|
| macOS Apple Silicon | MLX + mlx-lm | Native Metal optimization, superior memory efficiency |
| Linux/Windows NVIDIA | PyTorch + transformers | CUDA acceleration, broad compatibility |
| Linux/Windows CPU | PyTorch + transformers | Fallback with optimizations |

### Model Availability

> **Note**: As of January 2026, TranslateGemma models are only available in **safetensors format** on HuggingFace. This project handles the conversion to platform-specific optimized formats as part of the setup process.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Interactive CLI (Default)                   │
│  $ translate                                                 │
│  > 你好世界                                                   │
│  Hello world                                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Translation Engine                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Language   │  │ Prompt Fmt  │  │ Response Parser     │  │
│  │  Detector   │  │             │  │ (Direct/Explain)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Platform-Adaptive Runtime                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  TranslateGemma (4b/12b/27b, quantized)             │    │
│  │  - MLX backend (macOS) / PyTorch (Linux/Windows)    │    │
│  │  - Lazy loading for memory efficiency               │    │
│  │  - Hardware acceleration (Metal/CUDA)               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     Hardware: Apple Silicon / NVIDIA GPU / CPU               │
└─────────────────────────────────────────────────────────────┘
```

---

## Functional Requirements

### FR-1: CLI Interface

The CLI is invoked using the `translate` command.

#### FR-1.1: Interactive Mode (Default)

The CLI launches in interactive mode by default with two output modes:

**Direct Mode (Default)**: Returns only the translation without explanation. No streaming—output is post-processed to extract clean translation.

**Explanation Mode**: Raw model output with streaming, may include translation notes or alternatives.

```bash
$ translate
Loading TranslateGemma-27b-it... done (18.2s)

TranslateGemma Interactive (yue ↔ en, auto-detect)
Mode: direct | Type /help for commands, /quit to exit

> 今日天氣好好
The weather is really nice today

> That's great, let's go to the park
太好啦，不如去公園啦

> /mode explain
Switched to explanation mode (streaming enabled)

> 你食咗飯未？
Have you eaten yet?

This is a common Cantonese greeting, literally "Have you eaten rice yet?"
It's often used as a casual hello rather than a literal question about meals.

> /mode direct
Switched to direct mode

> /quit
再見！
```

#### FR-1.2: Automatic Language Detection

The system automatically detects the input language and translates to the target language based on the configured language pair (default: yue ↔ en).

| Input Language | Detected As | Output Language |
|----------------|-------------|-----------------|
| Chinese characters (粵語) | `yue` | `en` |
| Latin alphabet (English) | `en` | `yue` |
| Mixed content | Majority language | Opposite |

**Detection Strategy**:
1. **Primary**: Character script analysis (Han vs Latin)
2. **Fallback**: Use `langdetect` or `lingua` library for ambiguous cases
3. **Override**: User can force direction with `/to <lang>` command

#### FR-1.3: Single-Shot Mode (Optional)

For scripting or one-off translations, pass text as an argument:

```bash
# Auto-detect and translate
$ translate "早晨"
Good morning

$ translate "Good morning"
早晨

# Force specific direction if needed
$ translate --to en "早晨"
Good morning

# Use explanation mode
$ translate --explain "你食咗飯未？"
Have you eaten yet?

This is a common Cantonese greeting...
```

#### FR-1.4: File/Pipe Translation

```bash
# Translate file contents (auto-detect)
$ translate --file input.txt --output output.txt

# Translate from stdin
$ echo "你好" | translate
Hello

# Process multiple lines
$ cat phrases.txt | translate > translated.txt
```

#### FR-1.5: Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/to <lang>` | Force translations to specified language (e.g., `/to en`, `/to yue`, `/to zh`) |
| `/auto` | Return to auto-detect mode |
| `/mode direct` | Switch to direct translation mode (no streaming) |
| `/mode explain` | Switch to explanation mode (with streaming) |
| `/langs` | List all supported languages |
| `/model <name>` | Switch to a different model (e.g., `/model 4b`, `/model 12b`) |
| `/model` | Show current model info |
| `/config` | Show current configuration |
| `/clear` | Clear conversation history |
| `/quit` or `/exit` | Exit the CLI |

### FR-2: Language Configuration

The CLI supports configurable language pairs with 55 supported languages. Default pair: **Cantonese ↔ English**.

#### FR-2.1: Supported Languages

TranslateGemma supports the following 55 languages:

| Language | Code | Language | Code |
|----------|------|----------|------|
| Afrikaans | `af` | Korean | `ko` |
| Arabic | `ar` | Latvian | `lv` |
| Bengali | `bn` | Lithuanian | `lt` |
| Bulgarian | `bg` | Malay | `ms` |
| Cantonese | `yue` | Malayalam | `ml` |
| Catalan | `ca` | Marathi | `mr` |
| Chinese (Simplified) | `zh` | Norwegian | `no` |
| Chinese (Traditional) | `zh-TW` | Persian | `fa` |
| Croatian | `hr` | Polish | `pl` |
| Czech | `cs` | Portuguese | `pt` |
| Danish | `da` | Punjabi | `pa` |
| Dutch | `nl` | Romanian | `ro` |
| English | `en` | Russian | `ru` |
| Estonian | `et` | Serbian | `sr` |
| Finnish | `fi` | Slovak | `sk` |
| French | `fr` | Slovenian | `sl` |
| German | `de` | Spanish | `es` |
| Greek | `el` | Swahili | `sw` |
| Gujarati | `gu` | Swedish | `sv` |
| Hebrew | `he` | Tamil | `ta` |
| Hindi | `hi` | Telugu | `te` |
| Hungarian | `hu` | Thai | `th` |
| Indonesian | `id` | Turkish | `tr` |
| Italian | `it` | Ukrainian | `uk` |
| Japanese | `ja` | Urdu | `ur` |
| Kannada | `kn` | Vietnamese | `vi` |
| Kazakh | `kk` | Welsh | `cy` |

#### FR-2.2: Default Language Pair

| Language | Code | Variant Used |
|----------|------|--------------|
| Cantonese | `yue` | `yue-HK` (Hong Kong Traditional Chinese) |
| English | `en` | `en` (General English) |

### FR-3: Configuration Management

Configuration stored in `~/.config/translate/config.yaml`:

```yaml
# Default configuration
model:
  name: 27b                    # Model size: "4b", "12b", or "27b"
  path: ~/.cache/translate/models
  quantization: 4bit
  
translation:
  languages: [yue, en]         # Configurable language pair
  max_tokens: 512
  mode: direct                 # "direct" or "explain"
  
detection:
  strategy: script             # "script" (fast) or "model" (accurate)
  
performance:
  lazy_load: true
  
ui:
  show_detected_language: true # Show "[yue→en]" prefix
  colored_output: true
```

### FR-4: Model Management

The CLI supports multiple model sizes and handles conversion automatically:

#### FR-4.1: First Run Setup

```bash
$ translate
Model not found locally.
Available models:
  - translategemma-4b-it  (~3GB quantized)
  - translategemma-12b-it (~7GB quantized)  
  - translategemma-27b-it (~15GB quantized) [default]

Downloading google/translategemma-27b-it (safetensors)... 54GB
Converting to optimized format with 4-bit quantization...
This may take 10-15 minutes on first run.
[████████████████████████████████] 100%
Model ready!

> _
```

#### FR-4.2: Model Switching

```bash
# In interactive mode
> /model 4b
Switching to translategemma-4b-it...
Loading model... done (5.2s)
Now using: TranslateGemma-4b-it (3.2GB)

> /model
Current model: TranslateGemma-27b-it
Size: 14.8GB (4-bit quantized)
Location: ~/.cache/translate/models/translategemma-27b-it-4bit

# Command line model selection
$ translate --model 12b "早晨"
Good morning
```

#### FR-4.3: Model Management Commands

```bash
# List available/downloaded models
$ translate model list
Available models:
  ✓ translategemma-4b-it   [downloaded] 3.2GB
  ✗ translategemma-12b-it  [not downloaded]
  ✓ translategemma-27b-it  [downloaded] 14.8GB

# Download specific model
$ translate model download 12b

# Check model status
$ translate model status
Current: google/translategemma-27b-it
Format: MLX (converted from safetensors)
Quantization: 4-bit
Location: ~/.cache/translate/models/translategemma-27b-it-4bit
Size: 14.8GB

# Remove a model
$ translate model remove 4b
```

---

## Non-Functional Requirements

### NFR-1: Performance

| Metric | 4b Model | 12b Model | 27b Model |
|--------|----------|-----------|-----------|
| Cold start time | < 10s | < 20s | < 30s |
| Warm inference (50 tokens) | < 1s | < 1.5s | < 2s |
| Memory footprint | < 5GB | < 10GB | < 20GB |
| Tokens/second (Apple Silicon) | > 30 tok/s | > 20 tok/s | > 15 tok/s |
| Tokens/second (NVIDIA RTX) | > 40 tok/s | > 25 tok/s | > 18 tok/s |

### NFR-2: Reliability

- Graceful handling of out-of-memory conditions
- Automatic fallback to smaller model on memory pressure
- Clear error messages for unsupported configurations
- Platform-specific optimizations applied automatically

### NFR-3: Usability

- **Zero-configuration**: Just run `translate` - everything else is automatic
- **No language specification required**: Auto-detect input language by default
- **Interactive-first**: REPL mode is the default, single-shot available via arguments
- **Cross-platform**: Same CLI experience on macOS, Linux, and Windows
- Progress indicators for model download, conversion, and loading
- Colored terminal output with language direction indicators (e.g., `[yue→en]`)

---

## Implementation Plan

### Phase 1: Core Pipeline (Week 1)

1. **Platform Detection & Backend Selection**
   - Detect platform (macOS/Linux/Windows)
   - Select appropriate backend (MLX/PyTorch)
   - Configure hardware acceleration (Metal/CUDA/CPU)

2. **Model Conversion Pipeline**
   - Download TranslateGemma safetensors from HuggingFace
   - Convert to platform-optimized format
   - Apply quantization based on available memory

3. **Basic Inference Pipeline**
   - Implement TranslateGemma chat template formatter
   - Create unified inference wrapper across backends
   - Support both direct and explanation modes

### Phase 2: Language & CLI (Week 2)

1. **Language Detection Module**
   - Implement script-based detection
   - Support 55 languages
   - Handle mixed-language input

2. **Interactive CLI**
   - Build CLI using `typer` as `translate` command
   - Implement interactive REPL with all commands
   - Support model switching
   - Support language listing and configuration

### Phase 3: Multi-Model & Polish (Week 3)

1. **Multi-Model Support**
   - Support 4b, 12b, 27b models
   - Model download/switch management
   - Automatic model recommendation based on hardware

2. **User Experience**
   - Direct vs explanation mode
   - Cross-platform testing
   - Configuration file support
   - Error messages and recovery suggestions

---

## Technical Implementation Details

### Language Detection Algorithm

```python
import re
from typing import Literal

def detect_language(text: str, configured_langs: tuple[str, str] = ("yue", "en")) -> str:
    """
    Detect input language from configured pair.
    
    Strategy:
    1. Count Han (Chinese) characters vs Latin characters
    2. If >50% Han characters → first CJK language in pair
    3. Otherwise → first non-CJK language in pair
    """
    clean_text = re.sub(r'[\s\p{P}]', '', text)
    
    if not clean_text:
        return configured_langs[1]  # Default to second language
    
    # Count Han characters (CJK Unified Ideographs)
    han_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
    han_count = len(han_pattern.findall(clean_text))
    han_ratio = han_count / len(clean_text)
    
    # Determine which language in pair is CJK
    cjk_langs = {"yue", "zh", "zh-TW", "ja", "ko"}
    lang1, lang2 = configured_langs
    
    if han_ratio > 0.5:
        return lang1 if lang1 in cjk_langs else lang2
    else:
        return lang2 if lang2 not in cjk_langs else lang1


def get_target_language(source: str, configured_langs: tuple[str, str]) -> str:
    """Return the opposite language in the configured pair."""
    return configured_langs[1] if source == configured_langs[0] else configured_langs[0]
```

### TranslateGemma Prompt Format

```python
def format_translation_request(
    text: str, 
    source_lang: str, 
    target_lang: str,
    mode: str = "direct"
) -> list:
    """Format input for TranslateGemma's chat template."""
    
    # For direct mode, add instruction to return only translation
    if mode == "direct":
        instruction = f"Translate the following text from {source_lang} to {target_lang}. Return ONLY the translation, nothing else."
    else:
        instruction = None
    
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "source_lang_code": source_lang,
                    "target_lang_code": target_lang,
                    "text": text,
                }
            ],
        }
    ]
```

### Platform-Adaptive Model Loading

```python
import platform
from pathlib import Path

def get_backend():
    """Detect platform and return appropriate backend."""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Darwin" and machine == "arm64":
        return "mlx"
    else:
        return "pytorch"


def load_model(model_name: str = "27b", quantization: str = "4bit"):
    """Load model with platform-appropriate backend."""
    backend = get_backend()
    
    model_map = {
        "4b": "google/translategemma-4b-it",
        "12b": "google/translategemma-12b-it",
        "27b": "google/translategemma-27b-it",
    }
    
    hf_path = model_map[model_name]
    cache_path = Path.home() / ".cache/translate/models" / f"translategemma-{model_name}-it-{quantization}"
    
    if backend == "mlx":
        from mlx_lm import load
        return load(str(cache_path), lazy=True)
    else:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = AutoModelForCausalLM.from_pretrained(
            str(cache_path),
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(str(cache_path))
        return model, tokenizer
```

### Translation with Mode Support

```python
def translate(
    text: str, 
    model, 
    tokenizer,
    source_lang: str,
    target_lang: str,
    mode: str = "direct",
    stream: bool = False
) -> str:
    """
    Translate text with support for direct/explain modes.
    
    Direct mode: No streaming, post-process to extract clean translation
    Explain mode: Streaming enabled, raw model output
    """
    messages = format_translation_request(text, source_lang, target_lang, mode)
    
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    if mode == "direct":
        # No streaming for direct mode - need to post-process
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=256,
            verbose=False
        )
        # Post-process: extract only the translation
        return extract_translation(response)
    else:
        # Explanation mode: stream raw output
        if stream:
            return generate_streaming(model, tokenizer, prompt)
        else:
            return generate(model, tokenizer, prompt, max_tokens=512)


def extract_translation(response: str) -> str:
    """Extract clean translation from model response."""
    # Remove any explanatory text, notes, or alternatives
    lines = response.strip().split('\n')
    # Return first non-empty line as the translation
    for line in lines:
        line = line.strip()
        if line and not line.startswith(('Note:', 'Alternative:', '(')):
            return line
    return response.strip()
```

---

## Dependencies

### Python Dependencies

```txt
# requirements.txt

# Core
transformers>=4.45.0
huggingface-hub>=0.24.0
torch>=2.0.0               # PyTorch backend (Linux/Windows)

# Apple Silicon (optional, auto-detected)
mlx>=0.22.0; sys_platform == "darwin" and platform_machine == "arm64"
mlx-lm>=0.20.0; sys_platform == "darwin" and platform_machine == "arm64"

# CLI
typer>=0.12.0              # CLI framework with REPL support
pyyaml>=6.0
rich>=13.0.0               # Colored terminal output & progress bars
prompt-toolkit>=3.0.0      # Interactive REPL enhancements

# Language detection
regex>=2024.0.0            # Unicode-aware regex
langdetect>=1.0.9          # Fallback language detection
```

### System Dependencies

**macOS (Apple Silicon)**:
- Xcode Command Line Tools
- Python 3.11+

**Linux**:
- Python 3.11+
- CUDA 11.8+ (for NVIDIA GPU acceleration)

**Windows**:
- Python 3.11+
- CUDA 11.8+ (for NVIDIA GPU acceleration)

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Insufficient memory | High | Medium | Support multiple model sizes (4b/12b/27b); auto-recommend based on hardware |
| Platform compatibility issues | High | Medium | Extensive testing on all platforms; fallback to CPU |
| Quantization degrades quality | Medium | Medium | Benchmark all model sizes; document quality tradeoffs |
| Model download failures | Medium | Medium | Implement resume capability; support manual download |
| Language detection errors | Medium | Medium | Provide `/to` override; support `/langs` listing |
| Backend framework conflicts | Medium | Low | Isolate backend-specific code; clean abstractions |

---

## Success Metrics

1. **Functional**: Successfully translate 100 test sentences with >90% semantic accuracy across all model sizes
2. **Language Detection**: Correctly detect language direction in >95% of cases
3. **Performance**: Meet token/second targets for each model size and platform
4. **Cross-Platform**: Same CLI experience on macOS, Linux, and Windows
5. **Usability**: First translation within 1 command from fresh install (`translate` → auto-setup → ready)
6. **Reliability**: Zero crashes in 1000 consecutive translations

---

## Open Questions

1. **Cantonese variant**: Should we use `yue` or `yue-HK` as default?
   - *Recommendation*: Use `yue-HK` for Hong Kong Traditional Chinese orthography

2. **Language detection edge cases**: How to handle Cantonese written in romanization (Jyutping)?
   - *Consideration*: Could be detected as English; may need special handling or user override

3. **Mixed language input**: How to handle code-switching (e.g., "我想 order 一杯咖啡")?
   - *Recommendation*: Detect majority language; provide `/to` command for user override

4. **Direct mode prompt engineering**: Should we use prompt instructions or post-processing for clean output?
   - *Recommendation*: Use both - prompt for cleaner output + post-processing as safety net

---

## Appendix

### A. Sample Usage Session

```bash
# First run - automatic setup
$ translate
Model not found locally.

Available models:
  - translategemma-4b-it  (~3GB)
  - translategemma-12b-it (~7GB)
  - translategemma-27b-it (~15GB) [default]

Downloading google/translategemma-27b-it from HuggingFace...
[████████████████████████████████] 54.2GB / 54.2GB

Converting to optimized format (4-bit quantization)...
[████████████████████████████████] 100%

Model ready! (14.8GB)

TranslateGemma Interactive (yue ↔ en)
Mode: direct | Language auto-detection enabled
Type /help for commands.

> 我哋今晚去邊度食飯？
Where shall we go for dinner tonight?

> Let's go to a cha chaan teng
不如我哋去茶餐廳啦

> /mode explain
Switched to explanation mode (streaming enabled)

> 香港係一個好靚嘅城市
Hong Kong is a beautiful city.

"靚" (leng) is a Cantonese word meaning beautiful/pretty,
commonly used in Hong Kong to describe places and people.

> /mode direct
Switched to direct mode

> /langs
Supported languages (55):
  af (Afrikaans)    ar (Arabic)       bn (Bengali)    ...
  yue (Cantonese)   zh (Chinese)      en (English)    ...

> /to ja
Output language set to: Japanese (ja)

> 早晨
おはようございます

> /auto
Auto-detection re-enabled (yue ↔ en)

> /model 4b
Switching to translategemma-4b-it...
Loading model... done (5.2s)
Now using: TranslateGemma-4b-it (3.2GB)

> /model
Current model: TranslateGemma-4b-it
Size: 3.2GB (4-bit quantized)
Location: ~/.cache/translate/models/translategemma-4b-it-4bit

> /help
Commands:
  /to <lang>     - Force translation to language (e.g., /to en, /to yue)
  /auto          - Enable auto-detection (default)
  /mode direct   - Direct translation only (no streaming)
  /mode explain  - Include explanations (with streaming)
  /langs         - List supported languages
  /model <size>  - Switch model (4b, 12b, 27b)
  /model         - Show current model info
  /config        - Show current configuration
  /clear         - Clear conversation
  /quit          - Exit

> /quit
再見！Goodbye!

# Subsequent runs - model already cached
$ translate
Loading TranslateGemma-27b-it... done (12.3s)

TranslateGemma Interactive (yue ↔ en)
> _

# Single-shot mode for scripting
$ translate "早晨"
Good morning

$ echo "Hello world" | translate
你好世界

# Use specific model
$ translate --model 4b "Good morning"
早晨

# Explanation mode from command line
$ translate --explain "你食咗飯未？"
Have you eaten yet?

This is a common Cantonese greeting...
```

### B. Configuration Examples

```yaml
# ~/.config/translate/config.yaml

# Example: Japanese ↔ English translator
model:
  name: 12b
  quantization: 4bit
  
translation:
  languages: [ja, en]
  mode: direct
```

```yaml
# Example: Multi-language setup with explanations
model:
  name: 27b
  quantization: 8bit
  
translation:
  languages: [zh, en]
  mode: explain
  
ui:
  colored_output: true
  show_detected_language: true
```

### C. Backend Support: vLLM and Ollama

The CLI supports multiple inference backends beyond local execution:

#### vLLM Integration

[vLLM](https://docs.vllm.ai/) provides high-throughput inference with features like:
- Continuous batching for parallel requests
- PagedAttention for efficient memory management
- Up to 24x higher throughput than HuggingFace Transformers

```bash
# Start vLLM server
pip install vllm
vllm serve google/translategemma-27b-it --quantization awq

# CLI connects to server
translate --backend vllm --server http://localhost:8000

# Or configure via command
translate backend vllm --url http://localhost:8000
```

#### Ollama Integration

[Ollama](https://ollama.ai/) provides a simple interface for running LLMs locally with:
- One-command model downloads
- Cross-platform support (macOS, Linux, Windows)
- OpenAI-compatible API

```bash
# Install Ollama from https://ollama.ai/download
# Pull model via Ollama
ollama pull translategemma:27b

# CLI uses Ollama backend
translate --backend ollama

# Or configure via command
translate backend ollama
```

#### Backend Selection

The CLI automatically selects the best available backend:
1. If `--backend` is specified, use that backend
2. If configured in `config.yaml`, use that backend
3. Otherwise, use local backend (MLX on macOS Apple Silicon, PyTorch elsewhere)

```yaml
# config.yaml backend configuration
backend:
  type: auto         # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434
```

Interactive commands for backend switching:
- `/backend` - Show current backend info
- `/backend vllm` - Switch to vLLM
- `/backend ollama` - Switch to Ollama
- `/backend auto` - Switch to auto (local)

### D. References

- [TranslateGemma Collection](https://huggingface.co/collections/google/translategemma)
- [TranslateGemma Technical Report](https://arxiv.org/pdf/2601.09012)
- [TranslateGemma-27b-it Model Card](https://huggingface.co/google/translategemma-27b-it)
- [TranslateGemma-12b-it Model Card](https://huggingface.co/google/translategemma-12b-it)
- [TranslateGemma-4b-it Model Card](https://huggingface.co/google/translategemma-4b-it)
- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Ollama Documentation](https://ollama.ai/)
- [Gemma 3 Technical Report](https://arxiv.org/abs/2503.19786)
