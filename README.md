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

2. FIRST TIME BUILD & START
   Run: make init

3. ACCESS THE APP
   - Website: http://localhost:3000
   - API: http://localhost:8888

DAILY USAGE
-----------
- Start: make start
- Stop: make stop
- Restart: make restart
- View logs: make logs
- Clean (when dependencies change): make clean