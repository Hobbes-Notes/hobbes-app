#!/bin/bash
set -e

# Import Linter - Architecture Validation
# Always run from repo root with consistent PYTHONPATH

echo "🔍 Running Import Linter - Architecture Validation"
echo "Working directory: $(pwd)"
echo "PYTHONPATH: /code/backend/src"
echo ""

docker-compose exec backend bash -c "cd /code && PYTHONPATH=/code/backend/src lint-imports --config .importlinter" 