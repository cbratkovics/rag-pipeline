#!/usr/bin/env bash
set -euo pipefail

echo "🐳 Testing Docker build..."

# Clean up any existing containers/images
docker rm -f rag-pipeline-test 2>/dev/null || true

# Build the image
docker build -t rag-pipeline:test .

# Test that it starts
docker run -d --name rag-pipeline-test -p 8000:8000 rag-pipeline:test

# Wait for health check
sleep 5

# Test health endpoint
curl -f http://localhost:8000/healthz || exit 1

# Clean up
docker rm -f rag-pipeline-test

echo "✅ Docker build successful!"
