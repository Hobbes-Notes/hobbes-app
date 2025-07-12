#!/bin/bash
set -e

echo "🚀 Starting Hobbes App on Railway (Simple Mode)..."

# Set Python path
export PYTHONPATH=/app/src:$PYTHONPATH

# Set environment for Railway
export RAILWAY_ENVIRONMENT_NAME=production
export ENVIRONMENT=production

# Start the FastAPI server directly without complex DB setup
echo "🌐 Starting server on port $PORT..."
cd /app/src

# Use Railway's PORT environment variable
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8888} --workers 1 