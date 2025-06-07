# Hobbes Backend

## 🚀 Quick Start

### For Docker Development
```bash
# From project root
make start
```

### For Cursor Development
```bash
# From project root
make dev-setup

# Or manually:
cd backend
./dev-setup.sh
```

## 📁 Project Structure

```
backend/
├── src/                    # Source code
│   ├── api/               # API layer (controllers, services, repositories)
│   ├── infrastructure/    # External dependencies (DynamoDB, S3, etc.)
│   └── main.py           # FastAPI application
├── setup.py              # Package configuration
└── dev-setup.sh          # Development environment setup
```

## 🔧 Import Structure

**Always use absolute imports from the `src` directory:**

```python
# ✅ Correct
from api.controllers.auth_controller import router
from infrastructure.dynamodb_client import get_dynamodb_client

# ❌ Avoid
from ....infrastructure.dynamodb_client import get_dynamodb_client
```

## 🐛 Troubleshooting

### Import Errors
If you see `ImportError: attempted relative import beyond top-level package`:

1. Run the development setup: `./dev-setup.sh`
2. Ensure PYTHONPATH includes the `src` directory
3. Use absolute imports as shown above

### Docker Issues
```bash
# Rebuild containers
make build

# Check logs
make logs

# Reset everything
make clean && make init
```

## 🎯 Key Features

- **Consistent Imports**: Works identically in Docker, local, and Cursor environments
- **Self-Healing Setup**: `dev-setup.sh` configures everything automatically
- **VS Code Integration**: Automatic Python path configuration for Cursor
- **Hot Reload**: Changes reflect immediately in development mode 