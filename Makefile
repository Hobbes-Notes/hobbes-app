.PHONY: start stop restart status logs clean build init check-docker install-backend clear-data ingest-data

# Check if Docker is running
check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "Error: Docker is not running or you don't have proper permissions"; \
		echo "Please make sure:"; \
		echo "1. Docker is installed and running"; \
		echo "2. You have permission to run Docker (try running 'docker ps' to test)"; \
		echo "3. If using Linux, your user is in the 'docker' group or you're using sudo"; \
		exit 1; \
	fi

# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

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
init: check-docker install-backend
	@echo "Initializing application..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		cp .env.example .env; \
		echo "Please update .env file with your credentials!"; \
	fi
	@if [ ! -f frontend/.env ]; then \
		echo "Creating frontend .env file..."; \
		echo "REACT_APP_API_URL=http://localhost:8888" > frontend/.env; \
	fi
	@echo "Building containers..."
	docker-compose build
	@echo "Starting application..."
	docker-compose up -d
	@echo "Initialization complete!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8888"
	@echo "Don't forget to update your .env file with proper credentials!" 