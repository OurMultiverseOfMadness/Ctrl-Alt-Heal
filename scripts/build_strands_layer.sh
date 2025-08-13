#!/usr/bin/env bash
set -euo pipefail

# Build a Python 3.11 Lambda Layer containing the official AWS Strands SDK (strands-agents only).
# Output folder: infra/lambda_layers/strands

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LAYER_DIR="$ROOT_DIR/infra/lambda_layers/strands"
SITE_PKGS_DIR="$LAYER_DIR/python/lib/python3.11/site-packages"

# Clean output
rm -rf "$LAYER_DIR"
mkdir -p "$SITE_PKGS_DIR"

# Cross-platform build: download manylinux wheels for Python 3.11 x86_64 and extract
TMPDIR="$(mktemp -d)"
WHEEL_DIR="$TMPDIR/wheels"
mkdir -p "$WHEEL_DIR"
python3 -m pip download \
  --only-binary=:all: \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --abi cp311 \
  --python-version 3.11 \
  --dest "$WHEEL_DIR" \
  strands-agents

for whl in "$WHEEL_DIR"/*.whl; do
  unzip -q -o "$whl" -d "$SITE_PKGS_DIR"
done

rm -rf "$TMPDIR"

# Strip bytecode and caches to reduce size
find "$SITE_PKGS_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} + || true

echo "Strands layer built at: $LAYER_DIR"
