import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api.controllers.auth_controller import router as auth_router
from api.controllers.project_controller import router as project_router
from api.controllers.note_controller import router as note_router
# from api.controllers.user_controller import router as user_router
# from api.controllers.ai_controller import router as ai_router
# from api.controllers.ai_file_controller import router as ai_file_router
from api.controllers.action_item_controller import router as action_item_router
from api.services.auth_service import AuthService
from api.services.user_service import UserService
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

app = FastAPI(
    title="Project Notes API",
    description="API for managing projects and notes with AI-powered summaries",
    version="1.0.0",
    debug=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Be more specific about allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to the client
)

# Add logging middleware
# app.add_middleware(LoggingMiddleware)

# Create services
auth_service = AuthService()
user_service = UserService()

# Create DynamoDB tables if they don't exist
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Initializing application...")
        
        # Initialize auth tables only
        await auth_service.initialize_tables()
        
        # Initialize project tables
        project_repository = get_project_repository()
        await project_repository.create_table()
        
        # Initialize note tables
        note_repository = get_note_repository()
        await note_repository.create_table()
        
        # Initialize action items tables
        action_item_repository = get_action_item_repository()
        await action_item_repository.create_table()
        
        logger.info("Application initialized successfully")
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    logger.info("Application shutdown complete")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(project_router, tags=["projects"])
app.include_router(note_router, tags=["notes"])
# app.include_router(user_router, tags=["users"])
# app.include_router(ai_router, tags=["ai"])
# app.include_router(ai_file_router, tags=["ai-files"])
app.include_router(action_item_router, tags=["action-items"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API Data"} 

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and debugging"""
    return {"status": "healthy", "service": "backend"} 