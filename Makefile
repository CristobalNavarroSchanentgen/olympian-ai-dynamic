# Olympian AI Makefile
# Divine automation for mortal tasks

.PHONY: help setup setup-backend setup-frontend dev dev-backend dev-frontend \
        test test-backend test-frontend test-coverage test-watch lint format \
        build deploy clean test-unit test-integration docker docker-down \
        docker-build docker-prod docker-logs docker-shell docker-clean \
        mongodb-shell redis-cli backup-mongodb

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
NPM := npm
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.prod.yml

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

## help: Display this help message
help:
	@echo "${BLUE}🏛️  Olympian AI Makefile${NC}"
	@echo "${BLUE}========================${NC}"
	@echo ""
	@echo "${YELLOW}Available commands:${NC}"
	@grep -E '^##' Makefile | sed -E 's/^## //' | column -t -s ':'

## setup: Complete setup for both frontend and backend
setup: setup-backend setup-frontend
	@echo "${GREEN}✓ Setup complete!${NC}"

## setup-backend: Setup Python backend environment
setup-backend:
	@echo "${BLUE}Setting up backend...${NC}"
	cd backend && \
	if [ ! -d ".venv" ]; then \
		uv venv; \
	fi && \
	. .venv/bin/activate && \
	uv pip install -r requirements.txt && \
	if [ ! -f ".env" ]; then \
		cp .env.example .env; \
	fi && \
	if [ ! -f "config.yaml" ]; then \
		cp config.yaml.example config.yaml; \
	fi && \
	mkdir -p data logs
	@echo "${GREEN}✓ Backend setup complete${NC}"

## setup-frontend: Setup Node.js frontend environment
setup-frontend:
	@echo "${BLUE}Setting up frontend...${NC}"
	cd frontend && \
	$(NPM) install && \
	if [ ! -f ".env" ]; then \
		cp .env.example .env; \
	fi
	@echo "${GREEN}✓ Frontend setup complete${NC}"

## dev: Run both frontend and backend in development mode
dev:
	@echo "${BLUE}Starting Olympian AI in development mode...${NC}"
	@make -j2 dev-backend dev-frontend

## dev-backend: Run backend in development mode
dev-backend:
	@echo "${BLUE}Starting backend...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

## dev-frontend: Run frontend in development mode
dev-frontend:
	@echo "${BLUE}Starting frontend...${NC}"
	cd frontend && $(NPM) run dev

## docker: Run application using Docker Compose (development)
docker:
	@echo "${BLUE}Starting Olympian AI with Docker...${NC}"
	$(DOCKER_COMPOSE) up

## docker-build: Build Docker images
docker-build:
	@echo "${BLUE}Building Docker images...${NC}"
	$(DOCKER_COMPOSE) build --no-cache

## docker-up: Start Docker services in background
docker-up:
	@echo "${BLUE}Starting Docker services in background...${NC}"
	$(DOCKER_COMPOSE) up -d

## docker-down: Stop Docker Compose services
docker-down:
	@echo "${BLUE}Stopping Docker services...${NC}"
	$(DOCKER_COMPOSE) down

## docker-prod: Run production Docker setup
docker-prod:
	@echo "${BLUE}Starting production Docker setup...${NC}"
	$(DOCKER_COMPOSE_PROD) up -d

## docker-prod-down: Stop production Docker services
docker-prod-down:
	@echo "${BLUE}Stopping production Docker services...${NC}"
	$(DOCKER_COMPOSE_PROD) down

## docker-logs: View Docker logs
docker-logs:
	$(DOCKER_COMPOSE) logs -f

## docker-logs-backend: View backend logs
docker-logs-backend:
	$(DOCKER_COMPOSE) logs -f backend

## docker-logs-frontend: View frontend logs
docker-logs-frontend:
	$(DOCKER_COMPOSE) logs -f frontend

## docker-shell-backend: Open shell in backend container
docker-shell-backend:
	$(DOCKER_COMPOSE) exec backend /bin/bash

## docker-shell-frontend: Open shell in frontend container
docker-shell-frontend:
	$(DOCKER_COMPOSE) exec frontend /bin/sh

## docker-clean: Clean Docker resources
docker-clean:
	@echo "${RED}Cleaning Docker resources...${NC}"
	$(DOCKER_COMPOSE) down -v
	docker system prune -af
	@echo "${GREEN}✓ Docker cleanup complete${NC}"

## mongodb-shell: Access MongoDB shell
mongodb-shell:
	@echo "${BLUE}Connecting to MongoDB...${NC}"
	$(DOCKER_COMPOSE) exec mongodb mongosh olympian_ai

## mongodb-backup: Backup MongoDB database
mongodb-backup:
	@echo "${BLUE}Backing up MongoDB...${NC}"
	mkdir -p backups/mongodb/$(shell date +%Y%m%d_%H%M%S)
	$(DOCKER_COMPOSE) exec mongodb mongodump --db olympian_ai --out /backup/$(shell date +%Y%m%d_%H%M%S)
	@echo "${GREEN}✓ MongoDB backup complete${NC}"

## mongodb-restore: Restore MongoDB from backup (usage: make mongodb-restore BACKUP=20240525_120000)
mongodb-restore:
	@echo "${BLUE}Restoring MongoDB from backup...${NC}"
	$(DOCKER_COMPOSE) exec mongodb mongorestore --db olympian_ai /backup/$(BACKUP)/olympian_ai
	@echo "${GREEN}✓ MongoDB restore complete${NC}"

## redis-cli: Access Redis CLI
redis-cli:
	@echo "${BLUE}Connecting to Redis...${NC}"
	$(DOCKER_COMPOSE) exec redis redis-cli

## redis-flush: Flush Redis cache
redis-flush:
	@echo "${RED}Flushing Redis cache...${NC}"
	$(DOCKER_COMPOSE) exec redis redis-cli FLUSHALL
	@echo "${GREEN}✓ Redis cache flushed${NC}"

## test: Run all tests with coverage
test: test-backend test-frontend
	@echo "${GREEN}✓ All tests passed!${NC}"

## test-backend: Run backend tests with coverage
test-backend:
	@echo "${BLUE}Running backend tests...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	python tests/run_tests.py

## test-unit: Run only unit tests
test-unit:
	@echo "${BLUE}Running unit tests...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	python tests/run_tests.py --unit

## test-integration: Run only integration tests
test-integration:
	@echo "${BLUE}Running integration tests...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	python tests/run_tests.py --integration

## test-coverage: Run tests and open coverage report
test-coverage:
	@echo "${BLUE}Running tests with coverage report...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	python tests/run_tests.py && \
	open htmlcov/index.html

## test-watch: Run tests in watch mode
test-watch:
	@echo "${BLUE}Running tests in watch mode...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	ptw -- -v

## test-file: Run a specific test file (usage: make test-file FILE=test_chat_api.py)
test-file:
	@echo "${BLUE}Running test file: $(FILE)${NC}"
	cd backend && \
	. .venv/bin/activate && \
	pytest tests/$(FILE) -v

## test-frontend: Run frontend tests
test-frontend:
	@echo "${BLUE}Running frontend tests...${NC}"
	cd frontend && $(NPM) test

## lint: Lint all code
lint: lint-backend lint-frontend
	@echo "${GREEN}✓ Linting complete!${NC}"

## lint-backend: Lint Python code
lint-backend:
	@echo "${BLUE}Linting backend code...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	ruff check . && \
	mypy .

## lint-frontend: Lint TypeScript/React code
lint-frontend:
	@echo "${BLUE}Linting frontend code...${NC}"
	cd frontend && $(NPM) run lint

## format: Format all code
format: format-backend format-frontend
	@echo "${GREEN}✓ Formatting complete!${NC}"

## format-backend: Format Python code
format-backend:
	@echo "${BLUE}Formatting backend code...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	black .

## format-frontend: Format TypeScript/React code
format-frontend:
	@echo "${BLUE}Formatting frontend code...${NC}"
	cd frontend && $(NPM) run format

## build: Build production images
build:
	@echo "${BLUE}Building production images...${NC}"
	docker build -t olympian-backend:latest ./backend
	docker build -t olympian-frontend:latest ./frontend
	@echo "${GREEN}✓ Build complete!${NC}"

## clean: Clean all generated files and dependencies
clean:
	@echo "${RED}Cleaning all generated files...${NC}"
	cd backend && rm -rf .venv __pycache__ .pytest_cache .mypy_cache data logs htmlcov .coverage
	cd frontend && rm -rf node_modules dist
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "${GREEN}✓ Clean complete!${NC}"

## scan-services: Trigger service discovery scan
scan-services:
	@echo "${BLUE}Triggering service discovery...${NC}"
	curl -X GET http://localhost:8000/api/discovery/scan

## health-check: Check health of all services
health-check:
	@echo "${BLUE}Checking service health...${NC}"
	@curl -s http://localhost:8000/health | jq . || echo "Backend: ${RED}Unhealthy${NC}"
	@curl -s http://localhost/ > /dev/null && echo "Frontend: ${GREEN}Healthy${NC}" || echo "Frontend: ${RED}Unhealthy${NC}"
	@$(DOCKER_COMPOSE) exec -T redis redis-cli ping > /dev/null && echo "Redis: ${GREEN}Healthy${NC}" || echo "Redis: ${RED}Unhealthy${NC}"
	@$(DOCKER_COMPOSE) exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null && echo "MongoDB: ${GREEN}Healthy${NC}" || echo "MongoDB: ${RED}Unhealthy${NC}"

## system-info: Display system information
system-info:
	@echo "${BLUE}System Information:${NC}"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Node: $(shell node --version)"
	@echo "NPM: $(shell $(NPM) --version)"
	@echo "Docker: $(shell docker --version)"
	@echo "OS: $(shell uname -s)"

## install-hooks: Install git hooks
install-hooks:
	@echo "${BLUE}Installing git hooks...${NC}"
	cp scripts/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "${GREEN}✓ Git hooks installed${NC}"

## docs: Generate documentation
docs:
	@echo "${BLUE}Generating documentation...${NC}"
	cd backend && \
	. .venv/bin/activate && \
	pdoc --html --output-dir docs app
	@echo "${GREEN}✓ Documentation generated${NC}"

## optimize: Run system optimization
optimize:
	@echo "${BLUE}Optimizing system...${NC}"
	curl -X POST http://localhost:8000/api/system/optimize

## backup: Create backup of all data
backup:
	@echo "${BLUE}Creating full backup...${NC}"
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@make mongodb-backup
	cp backend/config.yaml backups/$(shell date +%Y%m%d_%H%M%S)/
	tar -czf backups/$(shell date +%Y%m%d_%H%M%S)/data.tar.gz backend/data/
	@echo "${GREEN}✓ Full backup created in backups/$(shell date +%Y%m%d_%H%M%S)${NC}"

# Hidden targets for CI/CD
.PHONY: ci-test ci-build ci-deploy

ci-test:
	@make test

ci-build:
	@make build

ci-deploy:
	@echo "${BLUE}Deploying to production...${NC}"
	# Add deployment commands here