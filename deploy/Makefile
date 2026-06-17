.PHONY: up down dev test types lint migrate

# ============================================================
# Docker Compose
# ============================================================
up:
	docker compose up -d postgres redis
	@echo "Waiting for services..."
	@sleep 3
	docker compose up -d api yjs web
	@echo "Ready: http://localhost:5173"

down:
	docker compose down

restart: down up

# ============================================================
# Development (with hot reload)
# ============================================================
dev-api:
	cd services/api && uv run uvicorn src.main:app --reload --port 8000

dev-web:
	cd services/web && npm run dev

dev-yjs:
	cd services/yjs && npm run dev

# ============================================================
# Contracts → TypeScript 类型生成 (单一真相源)
# ============================================================
types:
	python contracts/gen_ts_types.py contracts/contracts.py services/web/src/shared/types/contracts.ts
	@echo "TypeScript types generated from contracts.py"

# ============================================================
# Testing
# ============================================================
test:
	cd services/api && uv run pytest ../../tests/api/ -v

test-cov:
	cd services/api && uv run pytest ../../tests/api/ -v --cov=src --cov-report=term-missing

# ============================================================
# Linting & Formatting
# ============================================================
lint:
	cd services/api && uv run ruff check src/ ../../tests/api/
	cd services/api && uv run mypy src/

fmt:
	cd services/api && uv run ruff format src/ ../../tests/api/

# ============================================================
# Database
# ============================================================
migrate:
	cd services/api && uv run alembic upgrade head

migrate-new:
	@read -p "Migration name: " name; \
	cd services/api && uv run alembic revision --autogenerate -m "$$name"
