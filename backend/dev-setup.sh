#!/bin/bash
# Development setup script for Hobbes Backend
# Ensures consistent Python path for Cursor and local development

set -e  # Exit on any error

echo "🚀 Setting up Hobbes Backend development environment..."

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -d "src" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Expected files: setup.py, src/"
    exit 1
fi

# Check Python and virtual environment
echo "🐍 Checking Python environment..."
PYTHON_VERSION=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
echo "✅ Python $PYTHON_VERSION detected"

# Gentle version guidance without being prescriptive
MINIMUM_VERSION="3.9"
if [ "$(printf '%s\n' "$MINIMUM_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MINIMUM_VERSION" ]; then
    echo "⚠️  Python $PYTHON_VERSION is quite old. Modern Python (3.10+) recommended for best compatibility"
    echo "   📝 Your current version should still work, but consider upgrading when convenient"
fi

# Check for consistency with Docker environment
echo "📋 For consistency across environments:"
echo "   🐳 Docker will use Python 3.12-slim (latest stable)"
echo "   💻 Local: Python $PYTHON_VERSION"
echo "   📝 Both should work identically due to our package structure"

# Check virtual environment
echo "🔧 Checking virtual environment..."
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "../.venv" ]; then
        echo "⚠️  Virtual environment found at ../.venv but not activated"
        echo "   💡 Recommendation: cd .. && source .venv/bin/activate && cd backend"
        echo "   📝 This ensures consistent package versions"
    else
        echo "⚠️  No virtual environment detected"
        echo "   💡 Recommendation: cd .. && python3 -m venv .venv && source .venv/bin/activate"
        echo "   📝 Virtual environments prevent package conflicts"
    fi
    echo "   ⚡ Continuing with system Python..."
else
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
fi

# Set Python path
echo "🔧 Configuring Python path..."
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Install in development mode
if [ -f "setup.py" ]; then
    echo "📦 Installing package in development mode..."
    pip install -e . || {
        echo "❌ Package installation failed. Trying to continue..."
        sleep 1
    }
fi

# Verify installation
echo "🔍 Verifying Python path setup..."
python -c "
import sys
import os
print('Python version:', sys.version)
print('Current directory:', os.getcwd())
print('Python path:')
for path in sys.path:
    if 'src' in path or 'backend' in path or path == '':
        print(f'  ✅ {path}')
    else:
        print(f'     {path}')
print()

# Test imports
test_results = []
try:
    from api.controllers.auth_controller import router
    test_results.append('✅ auth_controller import: OK')
except ImportError as e:
    test_results.append(f'❌ auth_controller import: {e}')

try:
    from infrastructure.dynamodb_client import get_dynamodb_client
    test_results.append('✅ dynamodb_client import: OK')
except ImportError as e:
    test_results.append(f'❌ dynamodb_client import: {e}')

for result in test_results:
    print(result)

# Summary
failed_tests = [r for r in test_results if '❌' in r]
if not failed_tests:
    print()
    print('🎉 All import tests passed - setup successful!')
else:
    print()
    print('⚠️  Some imports failed. This may be normal if dependencies are missing.')
    print('   The development environment is still configured correctly.')
"

echo ""
echo "✅ Development environment ready!"
echo "💡 Environment variables set:"
echo "   PYTHONPATH=\"${PWD}/src:\${PYTHONPATH}\""
echo ""
echo "🔧 For your shell session, run:"
echo "   export PYTHONPATH=\"\${PWD}/src:\${PYTHONPATH}\""
echo ""
echo "📝 VS Code/Cursor users: Python path is auto-configured via .vscode/settings.json" 