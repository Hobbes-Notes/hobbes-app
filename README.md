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