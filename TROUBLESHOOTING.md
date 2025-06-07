# Hobbes App Troubleshooting Guide

## 🚨 Quick Fixes

### Step 0: Run System Check First
**Before anything else:**
```bash
make system-check
```
This validates Docker, Python, virtual environment, and all requirements. Follow any recommendations it provides.

### Problem: Backend won't start / Import errors
**Solution:**
```bash
make dev-reset
```
This nuclear option fixes 90% of issues by rebuilding everything from scratch.

### Problem: "Failed to load projects" in frontend
**Symptoms:** Login works but projects page shows error
**Root Cause:** Backend import issues (now fixed!)
**Solution:**
```bash
make dev-start
curl http://localhost:8888/health  # Should return {"status":"healthy"}
```

### Problem: Docker context errors
**Solution:**
```bash
make fix-docker-context
```

### Problem: Environment validation fails
**Solution:**
```bash
make validate-env  # Comprehensive check of Python, venv, Docker, .env files
```

### Problem: Virtual environment issues
**Symptoms:**
- Package conflicts
- "Module not found" errors
- Different behavior than expected

**Solutions:**
```bash
make setup-venv          # Create virtual environment
source .venv/bin/activate # Activate it
make dev-setup           # Configure for development
```

## 🔧 Common Issues

### Import Errors in Cursor/VS Code
**Symptoms:**
- `ImportError: attempted relative import beyond top-level package`
- Python can't find modules

**Solution:**
```bash
cd backend
./dev-setup.sh
```

This configures the Python path correctly for Cursor development.

### Docker Issues
**Symptoms:**
- "Cannot connect to Docker daemon"
- "Docker is not running"

**Solutions:**
1. Start Docker Desktop
2. Run `make check-docker` to verify
3. If still issues: `make fix-docker-context`

### Database Issues
**Symptoms:**
- "Table doesn't exist"
- DynamoDB connection errors

**Solution:**
```bash
make dev-reset  # Recreates all tables
```

### Missing Environment Variables
**Symptoms:**
- "OPENAI_API_KEY not found"
- AWS credential errors

**Check:**
```bash
make validate-env  # Shows what's missing
```

**Fix:**
Ensure your `.env` file in the root directory contains:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-southeast-1
OPENAI_API_KEY=your_openai_key
```

## 🐛 Development Workflow Issues

### Problem: Changes not reflecting
**For Docker development:**
```bash
make restart
```

**For Cursor development:**
- Ensure you ran `make dev-setup`
- Python should auto-reload changes

### Problem: Port already in use
**Solution:**
```bash
make stop  # Stop all services
make dev-start  # Restart cleanly
```

### Problem: Inconsistent behavior between environments
**Root Cause:** Different Python paths
**Solution:** Use the standardized setup:
```bash
make dev-setup  # For Cursor
make dev-start  # For Docker
```

## 🏥 Health Checks

### Backend Health
```bash
curl http://localhost:8888/health
# Should return: {"status":"healthy","service":"backend"}
```

### DynamoDB Health
```bash
curl http://localhost:7777/  # Should not error
```

### Full System Check
```bash
make status  # Shows all container statuses
```

## 🆘 When All Else Fails

### Nuclear Reset (Clears Everything)
```bash
make dev-reset
```

This will:
1. Stop all services
2. Remove all containers and volumes
3. Clear local data
4. Rebuild from scratch
5. Start services with health checks

### Get Help
1. Run `make validate-env` and share the output
2. Run `make logs` to see error messages
3. Check if the issue is listed above

## 📋 Pre-Deployment Checklist

Before deploying or sharing with team:
- [ ] `make validate-env` passes
- [ ] `make dev-start` works
- [ ] Backend health check passes: `curl http://localhost:8888/health`
- [ ] Frontend loads: `http://localhost:3000`
- [ ] Can login and see projects

## 🎯 Performance Tips

- Use `make dev-start` instead of `make start` for better error handling
- Use `make dev-setup` for Cursor development (faster than Docker)
- Use `make dev-reset` sparingly (it's slow but thorough)
- Check `make logs` first before resetting everything 