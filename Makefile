.PHONY: help install dev test build docker-build docker-up docker-down docker-logs lint format clean

help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies for both backend and frontend"
	@echo "  make dev             - Start backend and frontend in development mode"
	@echo "  make backend-dev     - Start backend in development mode only"
	@echo "  make frontend-dev    - Start frontend in development mode only"
	@echo "  make test            - Run all tests"
	@echo "  make backend-test    - Run backend tests"
	@echo "  make frontend-test   - Run frontend tests"
	@echo "  make lint            - Run linting checks"
	@echo "  make format          - Format code"
	@echo "  make type-check      - Run TypeScript type checking"
	@echo "  make build           - Build both backend and frontend"
	@echo "  make backend-build   - Build backend only"
	@echo "  make frontend-build  - Build frontend only"
	@echo "  make docker-build    - Build Docker images"
	@echo "  make docker-up       - Start Docker containers"
	@echo "  make docker-down     - Stop Docker containers"
	@echo "  make docker-logs     - Show Docker logs"
	@echo "  make clean           - Clean build artifacts and caches"

install:
	pip install -e backend[dev]
	cd frontend && npm install

dev:
	@echo "Starting backend and frontend (background processes)"
	cd backend && uvicorn app.main:app --reload &
	cd frontend && npm run dev &

backend-dev:
	cd backend && uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm run dev

test:
	pytest backend && cd frontend && npm run test

backend-test:
	pytest backend -v

frontend-test:
	cd frontend && npm run test

lint:
	@echo "Linting backend..."
	pylint backend/app || true
	@echo "Type checking frontend..."
	cd frontend && npm run type-check

format:
	@echo "Formatting frontend..."
	cd frontend && npx prettier --write src

type-check:
	cd frontend && npm run type-check

build: backend-build frontend-build

backend-build:
	@echo "Building backend..."
	cd backend && python setup.py sdist bdist_wheel

frontend-build:
	@echo "Building frontend..."
	cd frontend && npm run build

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Containers started. Access the application at:"
	@echo "  - Frontend: http://localhost"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-logs-backend:
	docker-compose logs -f backend

docker-logs-frontend:
	docker-compose logs -f frontend

docker-clean:
	docker-compose down -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/build backend/dist backend/*.egg-info
	rm -rf frontend/dist frontend/node_modules
	rm -rf backend/data backend/logs
	docker-compose down -v 2>/dev/null || true

.PHONY: db-migrate db-export db-restore

db-migrate:
	@echo "Running database migrations..."
	cd backend && python -m alembic upgrade head

db-export:
	@echo "Exporting database backup..."
	cd backend && python -m app.cli --export

db-restore:
	@echo "Restoring from backup..."
	cd backend && python -m app.cli --restore
