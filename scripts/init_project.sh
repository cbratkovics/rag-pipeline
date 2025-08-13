#!/bin/bash

set -e

echo "Initializing RAG Pipeline Project..."

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v poetry >/dev/null 2>&1 || { echo "Poetry is required but not installed. Installing..."; pip install poetry; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }

# Create virtual environment and install dependencies
echo "Installing Python dependencies..."
poetry install

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env with your API keys and configuration"
fi

# Download NLTK data
echo "Downloading NLTK data..."
poetry run python -c "import nltk; nltk.download('punkt', quiet=True)"

# Create necessary directories
echo "Creating directories..."
mkdir -p data logs mlruns

# Start services with Docker Compose
echo "Starting Docker services..."
docker-compose up -d postgres redis qdrant

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "Running database migrations..."
poetry run python -c "
import asyncio
from src.infrastructure.database import db_manager

async def init_db():
    await db_manager.initialize()
    await db_manager.create_tables()
    await db_manager.close()

asyncio.run(init_db())
"

echo "Initialization complete!"
echo ""
echo "To start the application, run:"
echo "  poetry run uvicorn src.api.main:app --reload"
echo ""
echo "Or with Docker:"
echo "  docker-compose up"
echo ""
echo "Access the application at:"
echo "  API Documentation: http://localhost:8000/docs"
echo "  Interactive Demo: http://localhost:8000/demo"
echo "  Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "  MLflow UI: http://localhost:5000"