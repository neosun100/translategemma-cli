#!/bin/bash
# Build all-in-one Docker image with embedded models

set -e

VERSION="v1.0.0"
IMAGE_NAME="neosun/translategemma"
MODEL_DIR="$HOME/.cache/translate/models"

echo "=== TranslateGemma All-in-One Docker Build ==="
echo "Version: $VERSION"
echo "Model directory: $MODEL_DIR"

# Check if models exist
if [ ! -f "$MODEL_DIR/translategemma-27b-it-Q8.gguf" ]; then
    echo "Error: Models not found in $MODEL_DIR"
    echo "Please download models first using: translate model download"
    exit 1
fi

# Create temporary build context with models
BUILD_DIR=$(mktemp -d)
echo "Build directory: $BUILD_DIR"

# Copy application files
cp -r translategemma_cli "$BUILD_DIR/"
cp app_fastapi.py mcp_server.py pyproject.toml "$BUILD_DIR/"
cp -r templates static "$BUILD_DIR/"
cp Dockerfile.allinone "$BUILD_DIR/Dockerfile"

# Create models directory and copy GGUF files only
mkdir -p "$BUILD_DIR/models"
echo "Copying models (this may take a while)..."
cp "$MODEL_DIR"/*.gguf "$BUILD_DIR/models/"

# Show what we're building
echo ""
echo "Files to include:"
ls -lh "$BUILD_DIR/models/"

# Build the image
echo ""
echo "Building Docker image..."
cd "$BUILD_DIR"
docker build -t "$IMAGE_NAME:$VERSION-allinone" .

# Tag as latest-allinone
docker tag "$IMAGE_NAME:$VERSION-allinone" "$IMAGE_NAME:latest-allinone"

# Cleanup
echo "Cleaning up build directory..."
rm -rf "$BUILD_DIR"

echo ""
echo "=== Build Complete ==="
echo "Images created:"
echo "  - $IMAGE_NAME:$VERSION-allinone"
echo "  - $IMAGE_NAME:latest-allinone"
echo ""
echo "To push to Docker Hub:"
echo "  docker push $IMAGE_NAME:$VERSION-allinone"
echo "  docker push $IMAGE_NAME:latest-allinone"
