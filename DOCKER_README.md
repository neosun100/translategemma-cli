# TranslateGemma Docker Deployment Guide

## Docker Images

| Image | Size | Description |
|-------|------|-------------|
| `neosun/translategemma:v1.0.0-allinone` | ~82GB | **All-in-One** - includes all 6 models (4B/12B/27B × Q4/Q8) |
| `neosun/translategemma:latest-allinone` | ~82GB | Same as above, latest tag |
| `neosun/translategemma:v1.0.0` | ~10GB | Lightweight - models downloaded on first use |
| `neosun/translategemma:latest` | ~10GB | Same as above, latest tag |

## Quick Start (All-in-One)

```bash
# Pull the all-in-one image (includes all models)
docker pull neosun/translategemma:v1.0.0-allinone

# Run with GPU
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -e MODEL_NAME=27b \
  -e QUANTIZATION=8 \
  --name translategemma \
  neosun/translategemma:v1.0.0-allinone

# Test
curl -X POST http://localhost:8022/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "target_lang": "zh"}'
```

## Docker Compose (Recommended)

### All-in-One Version

```yaml
# docker-compose.allinone.yml
services:
  translategemma:
    image: neosun/translategemma:v1.0.0-allinone
    container_name: translategemma
    ports:
      - "8022:8022"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - MODEL_NAME=27b
      - QUANTIZATION=8
      - BACKEND=gguf
      - GPU_IDLE_TIMEOUT=0
      - MAX_CHUNK_LENGTH=100
      - DEFAULT_OVERLAP=0
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: [gpu]
```

### Lightweight Version (Models Downloaded on Demand)

```yaml
# docker-compose.yml
services:
  translategemma:
    image: neosun/translategemma:latest
    container_name: translategemma
    ports:
      - "8022:8022"
    environment:
      - MODEL_NAME=27b
      - QUANTIZATION=8
    volumes:
      - ~/.cache/translate/models:/root/.cache/translate/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: [gpu]
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `27b` | Model size: `4b`, `12b`, `27b` |
| `QUANTIZATION` | `8` | Quantization: `4` or `8` |
| `BACKEND` | `gguf` | Backend: `gguf`, `pytorch` |
| `GPU_IDLE_TIMEOUT` | `0` | Seconds before unloading model (0=immediate) |
| `MAX_CHUNK_LENGTH` | `100` | Max characters per chunk |
| `DEFAULT_OVERLAP` | `0` | Sliding window overlap (0=disabled) |

## GPU Memory Requirements

| Model | VRAM Required |
|-------|---------------|
| 4B-Q4 | ~3GB |
| 4B-Q8 | ~5GB |
| 12B-Q4 | ~7GB |
| 12B-Q8 | ~12GB |
| 27B-Q4 | ~15GB |
| 27B-Q8 | ~28GB |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/config` | GET | Get configuration |
| `/api/models` | GET | List available models |
| `/api/translate` | POST | Translate text |
| `/api/translate/stream` | POST | Stream translation |
| `/api/gpu/status` | GET | GPU status |

## Web UI

Access the web interface at: `http://localhost:8022`

## MCP Server

The container also includes an MCP server for integration with AI assistants:

```bash
# Run MCP server
docker exec translategemma python mcp_server.py
```

## Troubleshooting

### Out of Memory Error
- Use a smaller model (4B or 12B)
- Use Q4 quantization instead of Q8
- Check GPU memory with `nvidia-smi`

### Model Loading Slow
- First load takes time to initialize CUDA
- Subsequent loads are faster

### Translation Truncated
- Ensure `MAX_CHUNK_LENGTH=100` (not higher)
- This is a known TranslateGemma model limitation

## Quick Start

```bash
# Clone and start
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
./start.sh
```

The script will:
1. Check nvidia-docker environment
2. Auto-select GPU with most free memory
3. Find available port (default: 8022)
4. Start the service

## Access Points

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8022 |
| API Docs (Swagger) | http://localhost:8022/docs |
| Health Check | http://localhost:8022/health |

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
vim .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8022 | Service port |
| NVIDIA_VISIBLE_DEVICES | auto | GPU ID (auto-selected) |
| MODEL_NAME | 12b | Model size: 4b, 12b, 27b |
| QUANTIZATION | 4 | Quantization: 4 or 8 |
| BACKEND | gguf | Backend: gguf, pytorch |
| GPU_IDLE_TIMEOUT | 300 | Auto-unload after N seconds |
| MAX_CHUNK_LENGTH | 80 | Text chunk size |
| MODEL_PATH | ~/.cache/translate/models | Model cache directory |

## Model Selection

| Model | VRAM | Speed | Quality |
|-------|------|-------|---------|
| 4b-Q4 | ~3GB | 665 chars/s | Good |
| 4b-Q8 | ~5GB | 544 chars/s | Better |
| 12b-Q4 | ~7GB | 319 chars/s | High ⭐ |
| 12b-Q8 | ~12GB | 223 chars/s | Higher |
| 27b-Q4 | ~15GB | 159 chars/s | Best |
| 27b-Q8 | ~28GB | 102 chars/s | Best+ |

**Recommendation:** 12b-Q4 for best balance of speed and quality.

## API Usage

### Translate Text

```bash
curl -X POST http://localhost:8022/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "target_lang": "zh"
  }'
```

### Stream Translation

```bash
curl -X POST http://localhost:8022/api/translate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long text here...",
    "target_lang": "ja"
  }'
```

### Batch Translation

```bash
curl -X POST http://localhost:8022/api/translate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World", "How are you?"],
    "target_lang": "zh"
  }'
```

### GPU Management

```bash
# Check status
curl http://localhost:8022/api/gpu/status

# Release GPU memory
curl -X POST http://localhost:8022/api/gpu/offload

# Switch model
curl -X POST http://localhost:8022/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model": "27b-Q4"}'
```

## Docker Commands

```bash
# Start with build
./start.sh --build

# View logs
docker logs -f translategemma

# Stop service
docker compose down

# Restart
docker compose restart

# Shell access
docker exec -it translategemma bash
```

## MCP Integration

See [MCP_GUIDE.md](MCP_GUIDE.md) for MCP configuration.

## Troubleshooting

### GPU Not Detected
```bash
# Check NVIDIA driver
nvidia-smi

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Out of Memory
- Use smaller model (4b or 12b)
- Use Q4 quantization instead of Q8
- Release GPU: `curl -X POST http://localhost:8022/api/gpu/offload`

### Model Download Slow
Set HuggingFace mirror:
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### Port Already in Use
The start.sh script auto-finds available port, or set manually:
```bash
PORT=8023 ./start.sh
```

## Building Custom Image

```bash
# Build
docker build -t translategemma:custom .

# Run
docker run --gpus all -p 8022:8022 translategemma:custom
```

## Production Deployment

For production, consider:
1. Use specific GPU: `NVIDIA_VISIBLE_DEVICES=1`
2. Increase timeout: `GPU_IDLE_TIMEOUT=3600`
3. Use reverse proxy (nginx) for HTTPS
4. Set up monitoring for `/health` endpoint
