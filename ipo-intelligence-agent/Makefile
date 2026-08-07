# Makefile for IPO Intelligence Agent

.PHONY: help dev prod test lint format clean install

# Default target
help:
	@echo "IPO Intelligence Agent - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-backend  - Start backend only"
	@echo "  make dev-frontend - Start frontend only"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build production images"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-reset     - Reset database"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make logs         - View logs"
	@echo "  make shell        - Open backend shell"
	@echo "  make install      - Install dependencies"

# Development
dev:
	docker-compose up -d

dev-backend:
	docker-compose up -d postgres redis backend celery-worker celery-beat prefect jaeger prometheus grafana

dev-frontend:
	docker-compose up -d frontend

# Production
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Testing
test:
	cd backend && poetry run pytest -v --cov=app --cov-report=html
	cd frontend && npm run test

test-backend:
	cd backend && poetry run pytest -v --cov=app --cov-report=html

test-frontend:
	cd frontend && npm run test -- --coverage

# Linting
lint:
	cd backend && poetry run ruff check . && poetry run mypy app
	cd frontend && npm run lint

format:
	cd backend && poetry run ruff check --fix . && poetry run black .
	cd frontend && npm run format

# Database
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

db-reset:
	docker-compose exec backend alembic downgrade base && alembic upgrade head

# Database backup
db-backup:
	docker-compose exec postgres pg_dump -U postgres ipo_intelligence > backup_$(date +%Y%m%d_%H%M%S).sql

db-restore:
	@read -p "Enter backup file: " file; \
	cat $$file | docker-compose exec -T postgres psql -U postgres ipo_intelligence

# Logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f postgres

logs-celery:
	docker-compose logs -f celery-worker

# Shell access
shell:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U postgres ipo_intelligence

shell-redis:
	docker-compose exec redis redis-cli

# Installation
install:
	cd backend && poetry install
	cd frontend && npm install

# Cleanup
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all:
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af --volumes

# Production utilities
prod-logs:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-shell:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend bash

prod-shell-db:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres psql -U postgres ipo_intelligence

# CI/CD
ci-test:
	make lint
	make test

ci-build:
	make prod-build

# Monitoring
monitor:
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Jaeger: http://localhost:16686"
	@echo "Prefect: http://localhost:4200"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"

# Quick start
quickstart: install
	cp backend/.env.example backend/.env
	@echo "Edit backend/.env with your API keys"
	@echo "Then run: make dev"