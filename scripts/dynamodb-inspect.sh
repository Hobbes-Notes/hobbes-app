#!/bin/bash

# DynamoDB Inspector - Docker Wrapper Script
# 
# This script allows you to easily inspect DynamoDB tables from outside Docker
# by running the inspector utility inside the backend container.
#
# Usage:
#   ./scripts/dynamodb-inspect.sh list-tables
#   ./scripts/dynamodb-inspect.sh describe-table Notes
#   ./scripts/dynamodb-inspect.sh scan-table Notes --limit 5
#   ./scripts/dynamodb-inspect.sh table-status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if the backend container is running
CONTAINER_NAME="hobbes-app-backend-1"
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Backend container is not running. Please start it with:"
    echo "  docker compose up -d backend"
    exit 1
fi

# Check if no arguments provided
if [ $# -eq 0 ]; then
    print_info "DynamoDB Inspector - Available commands:"
    echo ""
    echo "  list-tables                    - List all DynamoDB tables"
    echo "  describe-table <table_name>    - Describe a specific table"
    echo "  scan-table <table_name>        - Scan items from a table"
    echo "  table-status                   - Show status summary of all tables"
    echo ""
    echo "Examples:"
    echo "  $0 list-tables"
    echo "  $0 describe-table Notes"
    echo "  $0 scan-table Notes --limit 5"
    echo "  $0 table-status"
    exit 0
fi

# Run the inspector inside the Docker container
print_info "Running DynamoDB inspector..."
docker exec -it ${CONTAINER_NAME} python utils/dynamodb_inspector.py "$@" 