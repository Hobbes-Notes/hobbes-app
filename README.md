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
   cd scripts
   python ingest_notes.py
   ```

5. ACCESS THE APP
   - Website: http://localhost:3000
   - API: http://localhost:8888

DAILY USAGE
-----------
- Start: make start
- Stop: make stop
- Restart: make restart
- View logs: make logs
- Clean (when dependencies change): make clean