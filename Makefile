.PHONY: help setup ingest run eval loadtest evidence quality up down clean

help:  ## Show this help message
	@echo "RAG Pipeline Makefile"
	@echo "===================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Install dependencies and pre-commit hooks
	@echo "Setting up RAG pipeline..."
	@echo "Installing dependencies with uv..."
	@uv sync
	@echo "Creating necessary directories..."
	@mkdir -p data/seed data/eval results/ragas benchmarks/locust mlruns .chroma
	@echo "Setup complete!"

ingest:  ## Build local Chroma index from data/seed
	@echo "Ingesting documents into Chroma..."
	@mkdir -p data/seed .chroma
	uv run python -m src.rag.ingest --data-dir data/seed --reset
	@echo "Ingestion complete!"

run:  ## Run API locally with uvicorn
	@echo "Starting RAG API server..."
	@mkdir -p /tmp/prometheus_multiproc
	uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000

eval:  ## Run RAGAS evaluation and log to MLflow
	@echo "Running RAGAS evaluation..."
	@mkdir -p results/ragas mlruns
	uv run python -m src.eval.ragas_runner
	@echo "Evaluation complete! Check results/ragas/ for reports"

loadtest:  ## Run Locust headless and save artifacts
	@echo "Running load tests..."
	@mkdir -p benchmarks/locust
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p benchmarks/locust/$$TIMESTAMP && \
	uv run locust \
		-f benchmarks/locust/locustfile.py \
		--host http://localhost:8000 \
		--users 10 \
		--spawn-rate 2 \
		--run-time 2m \
		--headless \
		--html benchmarks/locust/$$TIMESTAMP/report.html \
		--csv benchmarks/locust/$$TIMESTAMP/stats
	@echo "Load test complete! Check benchmarks/locust/ for reports"

evidence:  ## Generate README evidence snippet from latest artifacts
	@echo "Generating evidence summary..."
	@mkdir -p results
	uv run python scripts/summarize_evidence.py
	@echo "Evidence summary generated!"

quality:  ## Run ruff, mypy, pytest
	@echo "Running quality checks..."
	./scripts/ci.sh

up:  ## docker compose up -d api prometheus grafana mlflow
	@echo "Starting Docker services..."
	docker compose up -d api prometheus grafana mlflow
	@echo "Services started!"
	@echo "  API: http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"
	@echo "  MLflow: http://localhost:5000"

down:  ## docker compose down
	@echo "Stopping Docker services..."
	docker compose down
	@echo "Services stopped!"

clean:  ## Clean up cache and temporary files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

# Development helpers
dev-run:  ## Run with hot reload for development
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

docker-build:  ## Build Docker image
	docker build -t rag-pipeline:latest .

docker-logs:  ## Show Docker logs
	docker compose logs -f api

test:  ## Run pytest with coverage
	uv run pytest tests/ -v --cov=src --cov=api --cov-report=term-missing

lint:  ## Run linting
	uv run ruff check .

format:  ## Format code
	uv run ruff check --fix .

ci-test:  ## Run CI tests locally
	@echo "Running CI tests locally..."
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src api --ignore-missing-imports
	uv run pytest tests/ -m "not integration" --cov=src --cov=api --cov-report=term
	@echo "CI tests passed!"

ci-fix:  ## Fix CI issues automatically
	@echo "Fixing CI issues..."
	uv run ruff format .
	uv run ruff check . --fix
	@echo "CI issues fixed!"

# UV management
install:  ## Install dependencies with uv
	@echo "Installing dependencies with uv..."
	@uv sync
	@echo "Dependencies installed!"

update:  ## Update dependencies
	@echo "Updating dependencies..."
	@uv lock --upgrade
	@uv sync
	@echo "Dependencies updated!"

lock:  ## Regenerate uv.lock
	@echo "Regenerating uv.lock..."
	@uv lock
	@echo "Lock file regenerated!"

shell:  ## Enter Python shell with uv
	@uv run python

show-deps:  ## Show dependency tree
	@uv tree