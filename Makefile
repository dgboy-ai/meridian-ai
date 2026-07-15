.PHONY: install dev test lint format clean docker-build docker-up docker-down

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

all:
	pip install -e ".[all]"

test:
	python -m pytest tests/ -q

test-verbose:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=backend --cov-report=term-missing

lint:
	ruff check backend/

format:
	ruff format backend/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f backend-api

health:
	curl -s http://localhost:8000/health | python -m json.tool

investigate:
	meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"

cleanup-data:
	python scripts/cleanup_data.py

examples:
	python scripts/regenerate_examples.py
