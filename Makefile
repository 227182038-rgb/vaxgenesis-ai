.PHONY: help install dev up down build logs test migrate seed clean

help:
	@echo "VaxGenesis AI - available commands:"
	@echo "  make install  - Install all dependencies"
	@echo "  make dev      - Run backend + frontend in dev mode"
	@echo "  make up       - Start full stack via docker-compose"
	@echo "  make down     - Stop the stack"
	@echo "  make test     - Run all tests"
	@echo "  make migrate  - Run database migrations"
	@echo "  make seed     - Seed reference data"

install:
	cd apps/backend && pip install -e ".[dev]"
	cd apps/frontend && npm install --legacy-peer-deps

dev:
	trap 'kill 0' EXIT; 	cd apps/backend && uvicorn vaxgenesis.main:app --reload --port 8000 & 	cd apps/frontend && npm run dev; wait

up:
	docker compose up -d

down:
	docker compose down

test:
	cd apps/backend && pytest -v --no-cov
	cd apps/frontend && npm test

migrate:
	cd apps/backend && alembic upgrade head

seed:
	cd apps/backend && python -m vaxgenesis.scripts.seed

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/frontend/.next
