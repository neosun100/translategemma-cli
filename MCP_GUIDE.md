# TranslateGemma MCP Guide

## Overview

TranslateGemma provides MCP (Model Context Protocol) integration, allowing AI assistants like Claude to directly use translation capabilities.

## Available Tools

### 1. `translate_text`
Translate text to target language.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text | string | ✅ | - | Text to translate |
| target_lang | string | ✅ | - | Target language code (e.g., en, zh, ja) |
| source_lang | string | ❌ | auto | Source language code |
| model | string | ❌ | 12b | Model size: 4b, 12b, 27b |
| quantization | int | ❌ | 4 | Quantization: 4 or 8 |
| chunk_size | int | ❌ | 80 | Chunk size for long text |
| auto_split | bool | ❌ | true | Auto-split long text |

**Example:**
```json
{
  "text": "Hello, how are you?",
  "target_lang": "zh"
}
```

### 2. `translate_batch`
Batch translate multiple texts.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| texts | list[str] | ✅ | List of texts to translate |
| target_lang | string | ✅ | Target language code |
| source_lang | string | ❌ | Source language code |
| model | string | ❌ | Model size |

### 3. `translate_file`
Translate a text file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | ✅ | Path to input file |
| target_lang | string | ✅ | Target language code |
| output_path | string | ❌ | Path to save translation |

### 4. `get_gpu_status`
Get GPU status and loaded model info.

**Returns:** GPU memory, loaded model, idle time

### 5. `release_gpu`
Release GPU memory by unloading model.

### 6. `switch_model`
Switch to a different model.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| model | string | ✅ | - | Model size: 4b, 12b, 27b |
| quantization | int | ❌ | 4 | Quantization: 4 or 8 |

### 7. `list_languages`
Get all 55 supported languages.

### 8. `list_models`
Get available models and current model info.

### 9. `get_config`
Get current service configuration.

## MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "translategemma": {
      "command": "python",
      "args": ["/path/to/translategemma-cli/mcp_server.py"],
      "env": {
        "MODEL_NAME": "12b",
        "QUANTIZATION": "4",
        "GPU_IDLE_TIMEOUT": "300"
      }
    }
  }
}
```

## Docker MCP Configuration

When running in Docker:

```json
{
  "mcpServers": {
    "translategemma": {
      "command": "docker",
      "args": ["exec", "-i", "translategemma", "python", "mcp_server.py"]
    }
  }
}
```

## Supported Languages (55)

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | zh | Chinese (Simplified) |
| zh-TW | Chinese (Traditional) | yue | Cantonese |
| ja | Japanese | ko | Korean |
| fr | French | de | German |
| es | Spanish | pt | Portuguese |
| ru | Russian | ar | Arabic |
| it | Italian | nl | Dutch |
| pl | Polish | vi | Vietnamese |
| th | Thai | id | Indonesian |
| ... | ... | ... | (55 total) |

Run `list_languages` tool for complete list.

## Model Recommendations

| Model | VRAM | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| 4b-Q4 | ~3GB | ⚡⚡⚡ | ★★★ | Quick translations |
| 12b-Q4 | ~7GB | ⚡⚡ | ★★★★ | **Recommended** |
| 27b-Q4 | ~15GB | ⚡ | ★★★★★ | Best quality |

## API vs MCP

| Feature | API | MCP |
|---------|-----|-----|
| Access | HTTP REST | Direct function call |
| Use case | Web apps, integrations | AI assistants |
| Streaming | ✅ SSE | ❌ |
| Batch | ✅ | ✅ |
| File upload | ✅ | ✅ (local path) |

Both share the same GPU manager and model instance.
