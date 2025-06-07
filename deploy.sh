#!/bin/bash
# Hobbes App Deployment Script
# Ensures consistent deployment process

set -e  # Exit on any error

echo "🚀 Hobbes App Deployment Process"
echo "================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -f "Makefile" ]; then
    echo "❌ Error: Please run this script from the project root"
    echo "   Expected files: docker-compose.yml, Makefile"
    exit 1
fi

# Environment validation
echo "🔍 Step 1: Environment validation..."
make validate-env || {
    echo "❌ Environment validation failed"
    exit 1
}

# Clean build
echo "🧹 Step 2: Clean build..."
make clean
make build

# Health check function
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Deploy
echo "🚀 Step 3: Deployment..."
make start

# Health checks
echo "🏥 Step 4: Health checks..."
wait_for_service "Backend" "http://localhost:8888/health" || {
    echo "❌ Backend health check failed"
    echo "Checking logs..."
    make logs
    exit 1
}

# Deployment verification
echo "🔍 Step 5: Deployment verification..."
echo "Checking services..."
make status

echo ""
echo "🎉 Deployment successful!"
echo "================================="
echo "📊 Service Status:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8888"
echo "   Health:    http://localhost:8888/health"
echo "   DynamoDB:  http://localhost:7777"
echo ""
echo "🔧 Useful commands:"
echo "   make logs     - View logs"
echo "   make status   - Check status"
echo "   make stop     - Stop services"
echo "   make restart  - Restart services" 