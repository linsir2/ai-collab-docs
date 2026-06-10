.PHONY: up down dev test types lint migrate

# ============================================================
# Docker Compose
# ============================================================
up:
	docker compose up -d postgres redis
	@echo "Waiting for services..."
	@sleep 3
	docker compose up -d backend yjs-server frontend
	@echo "Ready: http://localhost:5173"

down:
	docker compose down

restart: down up

# ============================================================
# Development (with hot reload)
# ============================================================
dev-backend:
	cd backend && uv run uvicorn src.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-yjs:
	cd yjs-server && npm run dev

# ============================================================
# Contracts → TypeScript 类型生成 (单一真相源)
# ============================================================
types:
	cd tools && python gen_ts_types.py ../contracts/contracts.py ../frontend/src/shared/types/contracts.ts
	@echo "TypeScript types generated from contracts.py"

# ============================================================
# Testing
# ============================================================
test:
	cd backend && uv run pytest tests/ -v

test-cov:
	cd backend && uv run pytest tests/ -v --cov=src --cov-report=term-missing

# ============================================================
# Linting & Formatting
# ============================================================
lint:
	cd backend && uv run ruff check src/ tests/
	cd backend && uv run mypy src/

fmt:
	cd backend && uv run ruff format src/ tests/

# ============================================================
# Database
# ============================================================
migrate:
	cd backend && uv run alembic upgrade head

migrate-new:
	@read -p "Migration name: " name; \
	cd backend && uv run alembic revision --autogenerate -m "$$name"
