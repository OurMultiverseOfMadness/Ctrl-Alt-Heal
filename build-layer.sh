#!/bin/bash
set -e

PROJECT_ROOT=$(git rev-parse --show-toplevel)
LAYER_DIR="$PROJECT_ROOT/cdk/lambda_layer"
DOCKER_IMAGE_NAME="ctrl-alt-heal-layer-builder"

echo "Building Lambda layer using multi-stage Dockerfile..."

# Clean up previous build
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"

# Build the Docker image
docker build -t "$DOCKER_IMAGE_NAME" -f Dockerfile.layer .

# Create a container from the image
CONTAINER_ID=$(docker create "$DOCKER_IMAGE_NAME")

# Copy the built layer from the container to the host
docker cp "$CONTAINER_ID:/opt/." "$LAYER_DIR/"

# Remove the container
docker rm "$CONTAINER_ID"

# Clean up Docker image
docker rmi "$DOCKER_IMAGE_NAME"

echo "Lambda layer built successfully!"
echo "Layer size:"
du -sh "$LAYER_DIR"
echo ""
echo "Layer contents:"
ls -la "$LAYER_DIR"
