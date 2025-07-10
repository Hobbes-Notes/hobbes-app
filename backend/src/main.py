import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from api.controllers.auth_controller import router as auth_router
from api.controllers.project_controller import router as project_router
from api.controllers.note_controller import router as note_router
# from api.controllers.user_controller import router as user_router
# from api.controllers.ai_controller import router as ai_router
# from api.controllers.ai_file_controller import router as ai_file_router
from api.controllers.action_item_controller import router as action_item_router
# Phase 3: Use FastAPI dependencies instead of direct service imports
from api.services import setup_dependencies, get_auth_service, get_user_service
# from api.services import get_ai_file_service
from api.repositories.impl import (
    get_project_repository, 
    get_note_repository, 
    get_ai_repository,
    # get_ai_file_repository,
    # get_ai_file_s3_repository,
    get_action_item_repository
)
# from api.middleware import LoggingMiddleware
# from consumer.ai_file_consumer import create_consumer
# from infrastructure.sqs_client import get_sqs_client
# from infrastructure.s3_client import get_s3_client

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set boto loggers to WARNING to reduce noise
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Detect if we're running on Railway
IS_RAILWAY = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME'))
IS_PRODUCTION = os.getenv('ENVIRONMENT') == 'production' or IS_RAILWAY

logger.info(f"Running in {'Railway' if IS_RAILWAY else 'local'} environment")

app = FastAPI(
    title="Hobbes App API",
    description="API for managing projects and notes with AI-powered summaries",
    version="1.0.0",
    debug=not IS_PRODUCTION
)

# Configure CORS based on environment
if IS_RAILWAY:
    # In production/Railway, allow the actual domain
    railway_domain = os.getenv('RAILWAY_STATIC_URL', '*')
    allowed_origins = [
        railway_domain,
        "https://*.up.railway.app",
        "http://localhost:3000"  # For development
    ]
else:
    # Local development
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Serve static files in Railway environment
if IS_RAILWAY:
    static_dir = Path("/app/frontend/build")
    if static_dir.exists():
        # Serve static files
        app.mount("/static", StaticFiles(directory=str(static_dir / "static")), name="static")
        
        # Serve React app for all non-API routes
        @app.get("/{path:path}")
        async def serve_react_app(path: str):
            """
            Serve the React app for all routes except API routes
            """
            # If it's an API route, let FastAPI handle it
            if path.startswith(('auth/', 'projects/', 'notes/', 'action-items/', 'health', 'api/')):
                # This won't actually be called for API routes, but just in case
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Not found")
            
            # Serve index.html for all other routes (React Router will handle them)
            from fastapi.responses import FileResponse
            return FileResponse(str(static_dir / "index.html"))

# Add logging middleware
# app.add_middleware(LoggingMiddleware)

# Phase 3: Initialize FastAPI dependencies
setup_dependencies()

# Create database tables based on environment
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Initializing application...")
        
        if IS_RAILWAY:
            # Railway: Use PostgreSQL
            logger.info("Initializing PostgreSQL database on Railway...")
            try:
                from database.init_tables import create_tables
                await create_tables()
                logger.info("✅ PostgreSQL tables created successfully")
            except Exception as e:
                logger.error(f"❌ PostgreSQL initialization failed: {e}")
                # Don't raise - let the app start anyway, might be a connection issue
        else:
            # Local: Use DynamoDB
            logger.info("Initializing DynamoDB tables for local development...")
            
            # Initialize auth tables through user service (which has the dependency chain)
            from api.repositories.impl.user_repository_impl import UserRepositoryImpl
            user_repository = UserRepositoryImpl()
            await user_repository.create_user_table()
            
            # Initialize project tables
            project_repository = get_project_repository()
            await project_repository.create_table()
            
            # Initialize note tables
            note_repository = get_note_repository()
            await note_repository.create_table()
            
            # Initialize action items tables
            action_item_repository = get_action_item_repository()
            await action_item_repository.create_table()
            
            logger.info("✅ DynamoDB tables created successfully")
        
        logger.info("Application initialized successfully")
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}", exc_info=True)
        # In production, we might want to continue despite database errors
        if not IS_PRODUCTION:
            raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    
    # Close database connections
    if IS_RAILWAY:
        try:
            from infrastructure.postgresql_client import postgresql_client
            await postgresql_client.close()
            logger.info("PostgreSQL connections closed")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connections: {e}")
    
    logger.info("Application shutdown complete")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(project_router, tags=["projects"])
app.include_router(note_router, tags=["notes"])
# app.include_router(user_router, tags=["users"])
# app.include_router(ai_router, tags=["ai"])
# app.include_router(ai_file_router, tags=["ai-files"])
app.include_router(action_item_router, tags=["action-items"])

@app.get("/api")
async def read_root():
    return {"message": "Welcome to Hobbes API", "environment": "Railway" if IS_RAILWAY else "Local"} 

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and debugging"""
    db_status = "postgresql" if IS_RAILWAY else "dynamodb"
    return {
        "status": "healthy", 
        "service": "hobbes-backend",
        "environment": "railway" if IS_RAILWAY else "local",
        "database": db_status
    } 