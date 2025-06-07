# Use latest stable Python for consistency
# Update this periodically to latest stable version
FROM python:3.12-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH to ensure imports work - simpler approach for Docker
ENV PYTHONPATH=/code/src

# Source code will be mounted via volume
# No COPY needed - docker-compose handles this

# Run as Python module to recognize package structure
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888", "--reload"] 