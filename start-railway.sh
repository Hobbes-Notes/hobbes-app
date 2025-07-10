#!/bin/bash
set -e

echo "🚀 Starting Hobbes App on Railway..."

# Set Python path
export PYTHONPATH=/app/src:$PYTHONPATH

# Initialize database if needed
echo "🗄️ Setting up database..."
python -c "
import asyncio
from src.infrastructure.postgresql_client import PostgreSQLClient
from src.database.init_tables import create_tables

async def init_db():
    try:
        await create_tables()
        print('✅ Database tables created successfully')
    except Exception as e:
        print(f'⚠️ Database setup: {e}')

asyncio.run(init_db())
"

# Start the FastAPI server with static file serving
echo "🌐 Starting server..."
cd /app/src
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 