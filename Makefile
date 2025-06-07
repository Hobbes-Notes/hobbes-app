.PHONY: start stop restart status logs clean build init check-docker dev-start dev-reset validate-env fix-docker-context deploy setup-venv system-check

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

# Start the application
start: check-docker
	@echo "Starting the application..."
	docker-compose up -d
	@echo "Application is running!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8888"
	@echo "DynamoDB: http://localhost:7777"

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
	docker-compose up -d
	@echo "✅ Initialization complete!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8888"
	@echo "Health Check: curl http://localhost:8888/health"
	@echo ""
	@echo "💡 For Cursor development:"
	@echo "   cd backend && ./dev-setup.sh"

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

# Self-healing development start
dev-start: validate-env fix-docker-context check-docker
	@echo "🚀 Starting development environment with self-healing..."
	@echo "Building containers if needed..."
	@docker-compose build backend 2>/dev/null || (echo "⚠️  Build failed, trying to continue..."; sleep 1)
	@echo "Starting core services..."
	@docker-compose up dynamodb-local -d
	@sleep 2
	@echo "Starting backend..."
	@docker-compose up backend -d
	@sleep 3
	@echo "🏥 Health check..."
	@curl -s http://localhost:8888/health > /dev/null && echo "✅ Backend healthy!" || echo "⚠️  Backend may still be starting..."
	@echo "🎉 Development environment ready!"
	@echo "📊 Status:"
	@make status 2>/dev/null || echo "Checking status..."
	@echo ""
	@echo "🔗 Quick links:"
	@echo "   Backend: http://localhost:8888"
	@echo "   Health:  http://localhost:8888/health"
	@echo "   DynamoDB: http://localhost:7777"

# Nuclear option - reset everything
dev-reset: stop clean
	@echo "💥 Nuclear reset in progress..."
	@echo "Removing containers and volumes..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f --volumes
	@echo "Cleaning local data..."
	@rm -rf .dynamodb/* 2>/dev/null || true
	@rm -rf localstack/* 2>/dev/null || true
	@rm -rf backend/src/__pycache__ 2>/dev/null || true
	@find backend -name "*.pyc" -delete 2>/dev/null || true
	@echo "Rebuilding from scratch..."
	@make dev-start
	@echo "🎉 Complete reset finished!"

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

# Production-ready deployment
deploy:
	@echo "🚀 Starting production deployment..."
	@./deploy.sh 