FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV TOKENIZERS_PARALLELISM=false

WORKDIR /app

# Install system dependencies including libgomp for llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    git curl libgomp1 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124

# Install llama-cpp-python from pre-built wheel (CUDA 12.4)
RUN pip install --no-cache-dir \
    llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# Install other dependencies
RUN pip install --no-cache-dir \
    transformers>=4.42.0 \
    huggingface-hub>=0.24.0 \
    accelerate>=0.25.0 \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    pyyaml>=6.0 \
    rich>=13.0.0 \
    typer>=0.12.0 \
    prompt-toolkit>=3.0.0 \
    regex \
    fastmcp

# Copy application code
COPY translategemma_cli/ translategemma_cli/
COPY app_fastapi.py mcp_server.py pyproject.toml ./
COPY templates/ templates/
COPY static/ static/

# Install the package
RUN pip install -e .

# Create directories
RUN mkdir -p /app/models /tmp/translategemma

# Expose port
EXPOSE 8022

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8022/health || exit 1

# Default command - run FastAPI server
CMD ["uvicorn", "app_fastapi:app", "--host", "0.0.0.0", "--port", "8022"]
