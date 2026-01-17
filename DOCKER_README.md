# TranslateGemma Docker Deployment Guide

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
