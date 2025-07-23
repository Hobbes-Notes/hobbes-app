.PHONY: start stop restart status logs clean build init check-docker dev-start dev-start-backend dev-reset validate-env fix-docker-context deploy setup-venv system-check frontend-start frontend-logs frontend-shell frontend-rebuild frontend-install frontend-clean-install frontend-test frontend-build backend-debug frontend-debug debug-all health-check wait-for-services

# Check if Docker is running
check-docker:
	@echo "🐳 Checking Docker environment..."
	@if ! command -v docker > /dev/null 2>&1; then \
		echo "❌ Docker not installed"; \
		echo "   Install Docker Desktop: https://www.docker.com/products/docker-desktop"; \
		exit 1; \
	fi
	@if ! docker info > /dev/null 2>&1; then \
		echo "❌ Docker is not running or you don't have proper permissions"; \
		echo ""; \
		echo "📋 Troubleshooting steps:"; \
		echo "1. 🚀 Start Docker Desktop application"; \
		echo "2. ⏳ Wait for Docker engine to start (whale icon in menu bar)"; \
		echo "3. 🔐 Ensure you have permission to run Docker"; \
		echo "4. 🧪 Test with: docker ps"; \
		echo "5. 🔧 If on Linux, add user to docker group: sudo usermod -aG docker $$USER"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ Docker is running"
	@DOCKER_VERSION=$$(docker --version | grep -o '[0-9]\+\.[0-9]\+' | head -1); \
	echo "✅ Docker version: $$DOCKER_VERSION"; \
	if [ "$$(printf '%s\n' "20.0" "$$DOCKER_VERSION" | sort -V | head -n1)" != "20.0" ]; then \
		echo "⚠️  Docker $$DOCKER_VERSION is quite old. Consider updating for better performance"; \
	fi
	@if ! docker-compose --version > /dev/null 2>&1; then \
		echo "✅ Using Docker Compose plugin (modern approach)"; \
	else \
		COMPOSE_VERSION=$$(docker-compose --version | grep -o '[0-9]\+\.[0-9]\+' | head -1); \
		echo "✅ Docker Compose version: $$COMPOSE_VERSION"; \
	fi

# Start the application (with error handling)
start: check-docker
	@echo "🚀 Starting the full application..."
	@echo "Building containers if needed..."
	@docker-compose build 2>/dev/null || (echo "⚠️  Build failed, trying to continue..."; sleep 1)
	@echo "Starting core services..."
	@docker-compose up dynamodb-local -d
	@sleep 2
	@echo "Starting backend..."
	@docker-compose up backend -d
	@sleep 3
	@echo "Starting frontend..."
	@docker-compose up frontend -d
	@sleep 5
	@echo "Starting additional services..."
	@docker-compose up localstack -d 2>/dev/null || echo "⚠️  Localstack failed to start, continuing without it..."
	@echo "⏳ Waiting for services and performing health checks..."
	@make wait-for-services
	@make health-check
	@echo "✅ Application startup complete and verified!"

# Stop the application
stop: check-docker
	@echo "Stopping the application..."
	docker-compose down
	@echo "Application stopped!"

# Restart the application
restart: stop start

# Check application status
status: check-docker
	@echo "Container Status:"
	docker-compose ps

# View application logs
logs: check-docker
	docker-compose logs -f

# Clean up everything
clean: check-docker
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f
	rm -rf frontend/node_modules
	rm -rf backend/src/__pycache__
	rm -rf backend/src/api/__pycache__
	@echo "Cleanup complete!"

# Clear all data
clear-data: stop
	@echo "Clearing all data..."
	rm -rf .dynamodb/*
	rm -rf localstack/*
	@echo "Data cleared successfully!"

# Ingest sample data
ingest-data:
	@echo "Ingesting sample data..."
	python3 scripts/ingest_notes.py

# Build containers
build: check-docker
	@echo "Building containers..."
	docker-compose build
	@echo "Build complete!"

# Initialize the application (first time setup)
init: check-docker
	@echo "🚀 Initializing Hobbes application..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		cp .env.example .env 2>/dev/null || echo "# Add your environment variables here" > .env; \
		echo "Please update .env file with your credentials!"; \
	fi
	@if [ ! -f frontend/.env ]; then \
		echo "Creating frontend .env file..."; \
		echo "REACT_APP_API_URL=http://localhost:8888" > frontend/.env; \
	fi
	@echo "📦 Building containers..."
	docker-compose build
	@echo "🔧 Setting up development environment..."
	@if [ -f backend/dev-setup.sh ]; then \
		cd backend && chmod +x dev-setup.sh; \
	fi
	@echo "🚀 Starting application..."
	@make start
	@echo "✅ Initialization complete!"
	@echo ""
	@echo "💡 For Cursor development:"
	@echo "   cd backend && ./dev-setup.sh"
	@echo ""
	@echo "🔍 Quick health check available:"
	@echo "   make health-check"

# Development setup for Cursor users
dev-setup:
	@echo "🔧 Setting up development environment for Cursor..."
	@cd backend && ./dev-setup.sh
	@echo "✅ Development environment ready!"
	@echo "💡 Your Python path is configured for absolute imports"

# Validate development environment
validate-env:
	@echo "🔍 Validating development environment..."
	@echo ""
	@echo "🐍 Checking Python environment..."
	@which python3 > /dev/null || (echo "❌ Python3 not found. Please install latest Python 3.x"; exit 1)
	@python3 --version | grep -q "3\." || (echo "❌ Python 3 required"; exit 1)
	@PYTHON_VERSION=$$(python3 --version | grep -o '[0-9]\+\.[0-9]\+' | head -1); \
	echo "✅ Python $$PYTHON_VERSION detected"; \
	if [ "$$(printf '%s\n' "3.9" "$$PYTHON_VERSION" | sort -V | head -n1)" != "3.9" ]; then \
		echo "⚠️  Python $$PYTHON_VERSION is quite old. Consider upgrading to latest stable"; \
	fi
	@echo ""
	@echo "🔧 Checking virtual environment..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		if [ -d ".venv" ]; then \
			echo "⚠️  Virtual environment found at .venv but not activated"; \
			echo "   Run: source .venv/bin/activate"; \
		else \
			echo "⚠️  No virtual environment detected"; \
			echo "   Recommendation: python3 -m venv .venv && source .venv/bin/activate"; \
		fi; \
	else \
		echo "✅ Virtual environment active: $$VIRTUAL_ENV"; \
	fi
	@echo ""
	@echo "🔐 Checking environment variables..."
	@test -f .env || (echo "❌ Main .env file missing. Run: make init"; exit 1)
	@grep -q "OPENAI_API_KEY" .env || (echo "❌ OPENAI_API_KEY not found in .env"; exit 1)
	@grep -q "AWS_ACCESS_KEY_ID" .env || (echo "❌ AWS_ACCESS_KEY_ID not found in .env"; exit 1)
	@echo "✅ Environment variables OK"
	@echo ""
	@echo "📁 Checking project structure..."
	@test -d backend/src || (echo "❌ Backend src directory missing"; exit 1)
	@test -f backend/src/main.py || (echo "❌ Backend main.py missing"; exit 1)
	@test -f backend/setup.py || (echo "❌ Backend setup.py missing"; exit 1)
	@echo "✅ Project structure OK"
	@echo ""
	@echo "🎉 Environment validation complete!"

# Fix common Docker issues
fix-docker-context:
	@echo "🔧 Fixing Docker context issues..."
	@docker context use default 2>/dev/null || echo "Docker context already set"
	@echo "✅ Docker context fixed"

# Self-healing development start (full stack)
dev-start: validate-env fix-docker-context check-docker
	@echo "🚀 Starting full development environment with self-healing..."
	@echo "Building containers if needed..."
	@docker-compose build backend frontend 2>/dev/null || (echo "⚠️  Build failed, trying to continue..."; sleep 1)
	@echo "Starting core services..."
	@docker-compose up dynamodb-local -d
	@sleep 2
	@echo "Starting backend..."
	@docker-compose up backend -d
	@sleep 3
	@echo "Starting frontend..."
	@docker-compose up frontend -d
	@sleep 5
	@echo "⏳ Performing comprehensive health checks..."
	@if make health-check 2>/dev/null; then \
		echo "🎉 Full development environment ready!"; \
	else \
		echo "❌ DEVELOPMENT ENVIRONMENT ISSUES DETECTED"; \
		echo ""; \
		echo "🛠️  Quick diagnostics:"; \
		echo "   Backend debug:  make backend-debug"; \
		echo "   Frontend debug: make frontend-debug"; \
		echo "   Full reset:     make dev-reset"; \
		echo ""; \
		echo "🔍 Checking backend logs for obvious errors:"; \
		docker-compose logs --tail=10 backend | grep -E "(Error|Exception|ImportError|ModuleNotFoundError|Failed|Traceback)" || echo "No obvious Python errors found"; \
	fi

# Backend-only development start (for pure API work)
dev-start-backend: validate-env fix-docker-context check-docker
	@echo "🚀 Starting backend-only development environment..."
	@echo "Building backend container if needed..."
	@docker-compose build backend 2>/dev/null || (echo "⚠️  Build failed, trying to continue..."; sleep 1)
	@echo "Starting core services..."
	@docker-compose up dynamodb-local -d
	@sleep 2
	@echo "Starting backend..."
	@docker-compose up backend -d
	@sleep 3
	@echo "🏥 Health check..."
	@curl -s http://localhost:8888/health > /dev/null && echo "✅ Backend healthy!" || echo "⚠️  Backend may still be starting..."
	@echo "🎉 Backend development environment ready!"
	@echo "📊 Status:"
	@make status 2>/dev/null || echo "Checking status..."
	@echo ""
	@echo "🔗 Quick links:"
	@echo "   Backend: http://localhost:8888"
	@echo "   Health:  http://localhost:8888/health"
	@echo "   DynamoDB: http://localhost:7777"

# ⚠️  DESTRUCTIVE: Nuclear option - reset everything (DELETES ALL LOCAL DATA)
dev-reset: stop clean
	@echo "🚨🚨🚨 DANGER: DESTRUCTIVE OPERATION AHEAD 🚨🚨🚨"
	@echo ""
	@echo "⚠️  This command will PERMANENTLY DELETE ALL LOCAL DATA:"
	@echo "   • All Projects, Notes, Action Items in DynamoDB Local"
	@echo "   • All Docker containers and volumes"
	@echo "   • All local development database data"
	@echo "   • Cache and temporary files"
	@echo ""
	@echo "💡 ALTERNATIVES: Try these less destructive options first:"
	@echo "   • make stop && make dev-start    (restart containers)"
	@echo "   • docker-compose restart backend (restart just backend)"
	@echo "   • docker-compose down && docker-compose up -d (rebuild containers)"
	@echo ""
	@echo "🔥 ONLY use dev-reset if you need to completely start fresh"
	@echo "   (like switching between different database schemas)"
	@echo ""
	@read -p "⚠️  Type 'DELETE_ALL_DATA' to confirm you want to proceed: " confirm; \
	if [ "$$confirm" != "DELETE_ALL_DATA" ]; then \
		echo "❌ Operation cancelled - your data is safe!"; \
		exit 1; \
	fi
	@echo ""
	@echo "💥 Nuclear reset in progress..."
	@echo "Removing containers and volumes..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f --volumes
	@echo "🗑️  Cleaning local data (THIS DELETES YOUR DEVELOPMENT DATABASE)..."
	@rm -rf .dynamodb/* 2>/dev/null || true
	@rm -rf localstack/* 2>/dev/null || true
	@rm -rf backend/src/__pycache__ 2>/dev/null || true
	@find backend -name "*.pyc" -delete 2>/dev/null || true
	@echo "Rebuilding from scratch..."
	@make dev-start
	@echo "🎉 Complete reset finished! (All previous local data has been deleted)"

# Set up virtual environment
setup-venv:
	@echo "🔧 Setting up Python virtual environment..."
	@if [ ! -d ".venv" ]; then \
		echo "📦 Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo "✅ Virtual environment created at .venv"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi
	@echo ""
	@echo "🚀 To activate the virtual environment:"
	@echo "   source .venv/bin/activate"
	@echo ""
	@echo "💡 Then run: make dev-setup"

# Comprehensive system check
system-check:
	@echo "🔍 Comprehensive System Check"
	@echo "=============================="
	@echo ""
	@make check-docker
	@echo ""
	@make validate-env
	@echo ""
	@echo "🔄 Consistency Check:"
	@DOCKER_PYTHON=$$(docker run --rm python:3.12-slim python --version | grep -o '[0-9]\+\.[0-9]\+' | head -1 2>/dev/null || echo "unknown"); \
	LOCAL_PYTHON=$$(python3 --version | grep -o '[0-9]\+\.[0-9]\+' | head -1); \
	echo "   🐳 Docker Python: $$DOCKER_PYTHON"; \
	echo "   💻 Local Python:  $$LOCAL_PYTHON"; \
	if [ "$$DOCKER_PYTHON" != "unknown" ] && [ "$$DOCKER_PYTHON" != "$$LOCAL_PYTHON" ]; then \
		echo "   📝 Different versions detected - this is normal and handled by our package structure"; \
	else \
		echo "   ✅ Versions aligned for optimal consistency"; \
	fi
	@echo ""
	@echo "🎯 Summary:"
	@echo "If all checks passed, you're ready for development!"
	@echo "If any failed, follow the recommendations above."

# Wait for services to be ready
wait-for-services:
	@echo "⏳ Waiting for services to be ready..."
	@echo "   Waiting for backend startup..."
	@for i in $$(seq 1 30); do \
		if curl -s http://localhost:8888/health > /dev/null 2>&1; then \
			echo "   ✅ Backend ready!"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "   ❌ Backend failed to start within 30 seconds"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "   Waiting for frontend startup..."
	@for i in $$(seq 1 20); do \
		if curl -s http://localhost:3000 > /dev/null 2>&1; then \
			echo "   ✅ Frontend ready!"; \
			break; \
		fi; \
		if [ $$i -eq 20 ]; then \
			echo "   ❌ Frontend failed to start within 20 seconds"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

# Comprehensive health check
health-check: check-docker
	@echo "🏥 Application Health Check"
	@echo "==========================="
	@echo ""
	@echo "📊 Service Status:"
	@make status 2>/dev/null || echo "Could not get container status"
	@echo ""
	@echo "🌐 Endpoint Health:"
	@BACKEND_STATUS=$$(curl -s http://localhost:8888/health 2>/dev/null || echo "failed"); \
	FRONTEND_STATUS=$$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo "failed"); \
	DYNAMODB_STATUS=$$(curl -s -o /dev/null -w '%{http_code}' http://localhost:7777 2>/dev/null || echo "failed"); \
	echo "   🔧 Backend:   $$BACKEND_STATUS"; \
	echo "   🎨 Frontend:  HTTP $$FRONTEND_STATUS"; \
	echo "   💾 DynamoDB:  HTTP $$DYNAMODB_STATUS"; \
	echo ""; \
	if echo "$$BACKEND_STATUS" | grep -q "healthy"; then \
		echo "✅ Backend: HEALTHY"; \
	else \
		echo "❌ Backend: FAILED - Check logs with: make backend-debug"; \
		exit 1; \
	fi; \
	if [ "$$FRONTEND_STATUS" = "200" ]; then \
		echo "✅ Frontend: HEALTHY"; \
	else \
		echo "❌ Frontend: FAILED - Check logs with: make frontend-debug"; \
		exit 1; \
	fi; \
	if [ "$$DYNAMODB_STATUS" = "400" ]; then \
		echo "✅ DynamoDB: HEALTHY"; \
	else \
		echo "❌ DynamoDB: FAILED - Check with: docker-compose logs dynamodb-local"; \
		exit 1; \
	fi
	@echo ""
	@echo "🎉 All services are healthy!"
	@echo ""
	@echo "🔗 Ready to work:"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8888"
	@echo "   Health:   http://localhost:8888/health"

# Production-ready deployment
deploy:
	@echo "🚀 Starting production deployment..."
	@./deploy.sh 

# Frontend Development Commands
# ============================

# Start frontend only (for frontend-focused development)
frontend-start: check-docker
	@echo "🎨 Starting frontend development environment..."
	@echo "Building frontend container if needed..."
	@docker-compose build frontend 2>/dev/null || (echo "⚠️  Build failed, trying to continue..."; sleep 1)
	@echo "Starting frontend..."
	@docker-compose up frontend -d
	@sleep 5
	@echo "🏥 Frontend health check..."
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend healthy!" || echo "⚠️  Frontend may still be starting..."
	@echo "🎉 Frontend development ready!"
	@echo "🔗 Frontend: http://localhost:3000"

# Frontend logs (for debugging React issues)
frontend-logs:
	@echo "📋 Frontend logs (press Ctrl+C to exit):"
	@docker-compose logs -f frontend

# Frontend shell access (for debugging inside container)
frontend-shell:
	@echo "🐚 Accessing frontend container shell..."
	@docker-compose exec frontend /bin/sh

# Rebuild frontend (when package.json changes)
frontend-rebuild: check-docker
	@echo "🔄 Rebuilding frontend container..."
	@docker-compose stop frontend
	@docker-compose build --no-cache frontend
	@docker-compose up frontend -d
	@echo "✅ Frontend rebuilt and started!"

# Frontend dependency install (when adding new packages)
frontend-install: check-docker
	@echo "📦 Installing frontend dependencies..."
	@docker-compose exec frontend npm install
	@echo "✅ Dependencies installed!"

# Frontend clean install (when node_modules is corrupted)
frontend-clean-install: check-docker
	@echo "🧹 Clean installing frontend dependencies..."
	@docker-compose exec frontend rm -rf node_modules package-lock.json
	@docker-compose exec frontend npm install
	@echo "✅ Clean install completed!"

# Frontend test (run React tests)
frontend-test: check-docker
	@echo "🧪 Running frontend tests..."
	@docker-compose exec frontend npm test

# Frontend build (production build test)
frontend-build: check-docker
	@echo "🏗️  Testing frontend production build..."
	@docker-compose exec frontend npm run build
	@echo "✅ Frontend build successful!"

# Debug backend issues (comprehensive troubleshooting)
backend-debug: check-docker
	@echo "🔍 Backend Debug Information"
	@echo "============================"
	@echo ""
	@echo "📊 Container Status:"
	@docker-compose ps backend
	@echo ""
	@echo "🔍 Backend Environment:"
	@docker-compose exec backend env | grep -E "(PYTHON|PATH|AWS_|OPENAI_)" 2>/dev/null || echo "Cannot access backend environment"
	@echo ""
	@echo "📁 Backend File Structure:"
	@docker-compose exec backend ls -la /code 2>/dev/null || echo "Cannot access backend filesystem"
	@echo ""
	@echo "🐍 Python Path Issues:"
	@docker-compose exec backend python -c "import sys; print('\\n'.join(sys.path))" 2>/dev/null || echo "Python not accessible"
	@echo ""
	@echo "🌐 Port Check:"
	@netstat -an | grep 8888 || echo "Port 8888 not in use"
	@echo ""
	@echo "📋 Full Backend Error Log:"
	@docker-compose logs --tail=30 backend
	@echo ""
	@echo "🛠️  Common fixes:"
	@echo "   1. Import issues: Check Python path and relative imports"
	@echo "   2. Missing dependencies: Rebuild container"
	@echo "   3. Environment issues: Check .env files"
	@echo "   4. Nuclear option: make dev-reset"

# Debug frontend issues (comprehensive troubleshooting)
frontend-debug: check-docker
	@echo "🔍 Frontend Debug Information"
	@echo "============================="
	@echo ""
	@echo "📊 Container Status:"
	@docker-compose ps frontend
	@echo ""
	@echo "🔍 Frontend Environment:"
	@docker-compose exec frontend env | grep -E "(REACT_|NODE_|npm_)" || echo "No React/Node env vars found"
	@echo ""
	@echo "📁 Frontend File Structure:"
	@docker-compose exec frontend ls -la /app
	@echo ""
	@echo "📦 Package.json dependencies:"
	@docker-compose exec frontend npm list --depth=0 2>/dev/null || echo "Dependencies not installed"
	@echo ""
	@echo "🌐 Port Check:"
	@netstat -an | grep 3000 || echo "Port 3000 not in use"
	@echo ""
	@echo "📋 Recent Frontend Logs:"
	@docker-compose logs --tail=20 frontend

# System-wide debugging (backend + frontend)
debug-all: check-docker
	@echo "🔍 Full System Debug Information"
	@echo "================================"
	@echo ""
	@make status
	@echo ""
	@echo "🏥 Health Checks & Diagnostics:"
	@if curl -s http://localhost:8888/health > /dev/null; then \
		echo "✅ Backend: http://localhost:8888 (healthy)"; \
	else \
		echo "❌ Backend: http://localhost:8888 (FAILED)"; \
		echo "   🔍 Error: $$(docker-compose logs --tail=3 backend | grep -E "(Error|Exception)" | tail -1 || echo 'Container may not be running properly')"; \
	fi
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend: http://localhost:3000 (healthy)" || echo "❌ Frontend: http://localhost:3000 (FAILED)"
	@curl -s http://localhost:7777 > /dev/null && echo "✅ DynamoDB: http://localhost:7777 (healthy)" || echo "❌ DynamoDB: http://localhost:7777 (FAILED)"
	@echo ""
	@echo "🌐 Port Usage:"
	@netstat -an | grep -E ":(3000|8888|7777)" || echo "No services detected on expected ports"
	@echo ""
	@echo "📋 Recent Logs (Backend):"
	@docker-compose logs --tail=10 backend
	@echo ""
	@echo "📋 Recent Logs (Frontend):"
	@docker-compose logs --tail=10 frontend

# Phase 3 - Architecture & Quality Gates
# =====================================

# Import Linter - Architecture Validation
.PHONY: lint-imports
lint-imports:
	@echo "🔍 Running Import Linter - Architecture Validation..."
	@./scripts/lint-imports.sh 

# Fly.io Deployment Commands
fly-deploy-backend:
	@echo "🚀 Deploying backend to Fly.dev..."
	cd backend && ../scripts/fly deploy

fly-deploy-frontend:
	@echo "🚀 Deploying frontend to Fly.dev..."
	cd frontend && ../scripts/fly deploy

fly-deploy-all:
	@echo "🚀 Deploying both backend and frontend to Fly.dev..."
	@$(MAKE) fly-deploy-backend
	@$(MAKE) fly-deploy-frontend

fly-status:
	@echo "📊 Checking Fly.dev app status..."
	@./scripts/fly status --app hobbes-backend
	@./scripts/fly status --app hobbes-frontend

fly-logs-backend:
	@echo "📝 Showing backend logs..."
	@./scripts/fly logs --app hobbes-backend

fly-logs-frontend:
	@echo "📝 Showing frontend logs..."
	@./scripts/fly logs --app hobbes-frontend 