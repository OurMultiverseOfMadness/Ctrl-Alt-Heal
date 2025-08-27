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
# Note the path inside the container is now /opt/python
docker cp "$CONTAINER_ID:/opt/." "$LAYER_DIR/"

# Remove the container
docker rm "$CONTAINER_ID"

echo "Lambda layer built successfully!"
du -sh "$LAYER_DIR"
