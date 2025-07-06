PREREQUISITES
------------
- Docker
- Docker Compose
- Make

PROJECT SETUP GUIDE
------------------

INSTALL ON MAC
-------------
1. Install Homebrew (if not installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. Install Docker Desktop:
   brew install --cask docker

3. Install Make (if not installed):
   brew install make

4. Start Docker Desktop:
   - Open Docker Desktop application
   - Wait for Docker engine to start (whale icon in menu bar should stop animating)

VERIFY INSTALLATION
------------------
Run these commands to verify installation:
docker --version
docker-compose --version
make --version

PROJECT SETUP
------------
1. CREATE ENVIRONMENT FILES
   
   Create .env in root folder:
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=ap-southeast-1
   OPENAI_API_KEY=your_openai_api_key

   Create frontend/.env:
   REACT_APP_API_URL=http://localhost:8888

2. INITIALIZE AND START APPLICATION
   ```bash
   make init
   ```
   This command will:
   - Install dependencies
   - Set up environment files
   - Build and start all services

3. MANAGE DATA
   To clear all data (e.g., when you want to start fresh):
   ```bash
   make clean-data  # This will stop the application and clear all data
   make init        # You can then start the application again
   ```

4. INGEST SAMPLE DATA
   After the application is running, you can load sample data:
   ```bash
   make ingest-data
   ```

5. ACCESS THE APP
   - Website: http://localhost:3000
   - API: http://localhost:8888

DAILY USAGE
-----------
**🚀 Self-Healing Development (Recommended)**
- Full stack: `make dev-start` (starts frontend + backend + db)
- Backend only: `make dev-start-backend` (for pure API work)
- Cursor setup: `make dev-setup` (for local Python development)
- Reset everything: `make dev-reset` (nuclear option when things break)

**🎨 Frontend Development**
- Frontend only: `make frontend-start` (React development focus)
- Frontend logs: `make frontend-logs` (debug React issues)
- Frontend shell: `make frontend-shell` (access container)
- Rebuild frontend: `make frontend-rebuild` (after package changes)
- Install deps: `make frontend-install` (add new packages)
- Clean install: `make frontend-clean-install` (fix corrupted deps)
- Run tests: `make frontend-test` (React test suite)
- Production build: `make frontend-build` (test build process)

**🔧 Standard Commands**
- Start all: `make start` (production-like with all services)
- Stop: `make stop`
- Restart: `make restart`
- View logs: `make logs`
- Clean: `make clean`
- Deploy: `make deploy` (production-ready with health checks)

**🔍 Debugging & Validation**
- **Health check: `make health-check`** (verify all services are working) ⭐
- Full debug: `make debug-all` (comprehensive system + frontend + backend)
- Frontend debug: `make frontend-debug` (React-specific troubleshooting)
- System check: `make system-check` (comprehensive validation)
- Environment check: `make validate-env` (Python, venv, .env files)
- Docker check: `make check-docker` (Docker installation & status)
- Setup venv: `make setup-venv` (create virtual environment)
- Status check: `make status` (running containers)

**💡 For Non-Coders with Cursor**
1. Run `make system-check` (validates everything)
2. Run `make dev-setup` once
3. Use `make dev-start` daily
4. Check health: `make health-check` (verify everything works)
5. If anything breaks: `make dev-reset`

**🔄 Version Philosophy**
- **Latest stable versions** for security and performance
- **Consistency across environments** (Docker, local, Cursor)
- **No hard version locks** - works with Python 3.9+ to latest
- **Easy updates** - see `VERSION_STRATEGY.md` for details

## Development Test Users (Email/Password Authentication)

For testing purposes, you can set up email/password authentication alongside Google OAuth. This feature is only available in development mode.

### Setting Up Test Users

1. **Create test users** by setting the `TEST_USERS` environment variable in your backend:

```bash
# In your backend/.env file or environment
export TEST_USERS='[
  {
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "id": "test_user_1"
  },
  {
    "email": "admin@mycompany.com", 
    "password": "admin123",
    "name": "Admin User",
    "id": "admin_user_1"
  },
  {
    "email": "designer@example.com",
    "password": "design123", 
    "name": "Design User"
  }
]'
```

2. **Restart your backend** after setting the environment variable:

```bash
make dev-start
```

3. **Access the login page** and you'll see:
   - Google OAuth login (production-ready)
   - "Use Email/Password (Development)" button (development only)
   - Quick-fill buttons for configured test users

### Test User Configuration

- **email**: Any valid email format (doesn't need to be a real email)
- **password**: Any string (stored as plain text - development only!)
- **name**: Display name for the user
- **id**: Optional. If not provided, auto-generated from email hash

### Features

- ✅ **Environment-aware**: Only works when `NODE_ENV=development`
- ✅ **Non-Gmail addresses**: Test with any email format
- ✅ **Quick user switching**: Button to fill credentials instantly
- ✅ **Auto-user creation**: Users are created in database on first login
- ✅ **Coexists with Google OAuth**: Both authentication methods work simultaneously

### Security Notes

⚠️ **Development Only**: This feature is automatically disabled in production environments.

⚠️ **Plain Text Passwords**: Test user passwords are stored as plain text in environment variables. Never use this for real users.