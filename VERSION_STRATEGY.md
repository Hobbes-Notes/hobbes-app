# Hobbes App Version Strategy

## 🎯 Core Philosophy

**Latest Stable + Consistency > Specific Versions**

We prioritize:
1. **Latest stable versions** for security and performance
2. **Consistency across environments** (Docker, local, Cursor)
3. **Forward compatibility** - no hard version locks
4. **Easy updates** when new versions are available

## 🐍 Python Strategy

### Current Approach
- **Docker**: Python 3.12-slim (latest stable)
- **Local**: Any Python 3.9+ (with gentle upgrade suggestions)
- **Package Structure**: Ensures identical behavior across versions

### Version Updates
```bash
# Check current versions
make system-check

# When updating Docker Python version:
# 1. Update backend/Dockerfile
# 2. Test with: make dev-reset
# 3. Update this guide
```

### Compatibility Promise
- **Minimum**: Python 3.9+ (for broad compatibility)
- **Recommended**: Latest stable (currently 3.12+)
- **Docker**: Always latest stable

## 🐳 Docker Strategy

### Current Approach
- **Base Images**: Use `latest` stable tags, not `latest` bleeding edge
- **Docker Engine**: Any version 20.0+ (with update suggestions)
- **Compose**: V2 plugin preferred, V1 standalone supported

### Update Process
```bash
# Check Docker versions
docker --version
docker-compose --version  # or docker compose version

# Update Docker Desktop through GUI
# Or on Linux: sudo apt update && sudo apt upgrade docker-ce
```

## 📦 Dependencies Strategy

### Python Packages
- **Core deps**: Specify minimum versions (`>=1.0.0`)
- **Security deps**: Update regularly
- **Pin exact versions**: Only when necessary for stability

### Node.js/Frontend
- **Use latest LTS** for Node.js
- **Update dependencies** quarterly
- **Security patches** immediately

## 🔄 Update Cadence

### Monthly Check
```bash
make system-check  # Check for version warnings
```

### Quarterly Updates
1. Review Python/Docker versions
2. Update base images
3. Test with `make dev-reset`
4. Update documentation

### Immediate Updates
- Security patches
- Critical bug fixes
- Breaking changes that affect consistency

## 🛠️ Version Update Checklist

### Updating Python Version

**In Docker:**
1. Update `backend/Dockerfile` base image
2. Test: `make dev-reset`
3. Update `VERSION_STRATEGY.md`

**For Local Development:**
```bash
# Check what's available
pyenv install --list  # if using pyenv

# Install new version
pyenv install 3.13.0  # example
pyenv global 3.13.0

# Recreate virtual environment
rm -rf .venv
make setup-venv
source .venv/bin/activate
make dev-setup
```

### Updating Docker
1. Update Docker Desktop
2. Test: `make check-docker`
3. Test full stack: `make dev-start`

## 🎯 Consistency Validation

```bash
# Check version alignment
make system-check

# Should show:
# ✅ Docker Python: 3.12
# ✅ Local Python: 3.11 (or whatever you have)
# 📝 Different versions detected - this is normal
```

## 📝 Team Guidelines

### For Developers
- **Don't worry about exact Python versions** - our structure handles differences
- **Use latest stable when starting fresh**
- **Check `make system-check` if things break**

### For DevOps/Maintainers
- **Review versions quarterly**
- **Update Docker base images** when Python releases new stable
- **Test updates in dev environment first**
- **Document any breaking changes**

## 🚀 Future-Proofing

### When Python 3.13+ is stable:
1. Update `backend/Dockerfile` to `python:3.13-slim`
2. Test compatibility
3. Update minimum version recommendations

### When Docker releases major updates:
1. Test new Docker version
2. Update version checks in Makefile
3. Document any new features we can leverage

## 💡 Why This Approach Works

- ✅ **No version lock-in** - easy to upgrade
- ✅ **Consistent behavior** - our package structure ensures imports work everywhere
- ✅ **Latest features** - security and performance improvements
- ✅ **Backwards compatible** - works with older versions too
- ✅ **Easy maintenance** - clear update process 