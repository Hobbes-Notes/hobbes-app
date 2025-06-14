# Use latest stable Python for consistency
# Update this periodically to latest stable version
FROM python:3.12-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development tools in separate layer for better caching
RUN pip install --no-cache-dir pre-commit

# Set PYTHONPATH to ensure imports work - matches volume mount at /code/backend/src
ENV PYTHONPATH=/code/backend/src

# Source code will be mounted via volume
# No COPY needed - docker-compose handles this

# Run as Python module to recognize package structure
CMD ["python", "-m", "uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8888", "--reload"] 