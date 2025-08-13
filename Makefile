.PHONY: help install test lint format clean run docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies with Poetry"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Clean up cache and build files"
	@echo "  make run        - Run the application locally"
	@echo "  make docker-up  - Start all services with Docker Compose"
	@echo "  make docker-down - Stop all Docker services"

install:
	poetry install
	poetry run python -c "import nltk; nltk.download('punkt', quiet=True)"

test:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	poetry run ruff check src/
	poetry run mypy src/
	poetry run bandit -r src/

format:
	poetry run black src/
	poetry run ruff check --fix src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

run:
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker build -t rag-pipeline:latest .

docker-logs:
	docker-compose logs -f rag-pipeline