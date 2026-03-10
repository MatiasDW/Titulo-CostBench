# CostBench - Quantitative Real Estate & Banking Dashboard

.PHONY: help build up down restart logs logs-app logs-db clean dev frontend db-shell shell seed-db run-pipeline lint format test

help:
	@echo "CostBench Dashboard"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev         - Start backend environment (Docker)"
	@echo "  make frontend    - Start local React frontend server"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show logs from all services"
	@echo "  make logs-app    - Show app logs"
	@echo "  make logs-db     - Show database logs"
	@echo ""
	@echo "Data & Shell Tools:"
	@echo "  make shell       - Open bash shell in app container"
	@echo "  make db-shell    - Open PostgreSQL shell"
	@echo "  make seed-db     - Seed Real Estate DB with CChC data"
	@echo "  make run-pipeline- Run Banking Data Pipeline"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run linting (flake8/black)"
	@echo "  make format      - Format code (black)"
	@echo "  make test        - Run tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove containers and volumes"

# Development environment
dev: build up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app

logs-db:
	docker compose logs -f db

# Frontend
frontend:
	cd frontend && npm run dev

# App Tools
shell:
	docker compose exec app bash

db-shell:
	docker compose exec db psql -U postgres -d costbench

seed-db:
	docker compose exec app python scripts/seed_real_estate.py

run-pipeline:
	docker compose exec app python scripts/run_pipeline.py

# Code quality
lint:
	docker compose exec app flake8 app scripts

format:
	docker compose exec app black app scripts

test:
	docker compose exec app pytest

# Cleanup
clean:
	docker compose down -v
