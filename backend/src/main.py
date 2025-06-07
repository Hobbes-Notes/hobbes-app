import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api.controllers.auth_controller import router as auth_router
from api.controllers.project_controller import router as project_router
from api.controllers.note_controller import router as note_router
from api.controllers.user_controller import router as user_router
from api.controllers.ai_controller import router as ai_router
from api.controllers.ai_file_controller import router as ai_file_router
from api.services.auth_service import AuthService
from api.services.user_service import UserService
from api.services import get_ai_file_service
from api.repositories.impl import (
    get_project_repository, 
    get_note_repository, 
    get_ai_repository,
    get_ai_file_repository,
    get_ai_file_s3_repository
)
from api.middleware import LoggingMiddleware
from consumer.ai_file_consumer import create_consumer
from infrastructure.sqs_client import get_sqs_client
from infrastructure.s3_client import get_s3_client

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
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Create services
auth_service = AuthService()
user_service = UserService()

# AI file consumer instance
ai_file_consumer = None

# Get environment variables
AI_FILES_QUEUE_NAME = os.environ.get('AI_FILES_QUEUE_NAME', 'ai-files')
AI_FILES_S3_BUCKET = os.environ.get('AI_FILES_S3_BUCKET', 'ai-files')

# Create DynamoDB tables if they don't exist
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Initializing application...")
        
        # Initialize repositories and create tables
        project_repository = get_project_repository()
        note_repository = get_note_repository()
        ai_repository = get_ai_repository()
        ai_file_repository = get_ai_file_repository()
        ai_file_s3_repository = get_ai_file_s3_repository()
        
        # Create tables
        await project_repository.create_table()
        await note_repository.create_table()
        await auth_service.initialize_tables()
        await ai_repository.create_table()
        
        # Initialize default AI configurations
        await ai_repository._init_default_configurations()
        
        # Ensure S3 bucket exists
        s3_client = get_s3_client()
        if not s3_client.bucket_exists(AI_FILES_S3_BUCKET):
            logger.info(f"Creating S3 bucket: {AI_FILES_S3_BUCKET}")
            s3_client.create_bucket(AI_FILES_S3_BUCKET)
        
        # Ensure SQS queue exists
        sqs_client = get_sqs_client()
        queue_url = sqs_client.get_queue_url(AI_FILES_QUEUE_NAME)
        if not queue_url:
            logger.info(f"Creating SQS queue: {AI_FILES_QUEUE_NAME}")
            sqs_client.create_queue(AI_FILES_QUEUE_NAME)
        
        # Get AI file service
        ai_file_service = get_ai_file_service()
        
        # Start AI file consumer in a background thread
        global ai_file_consumer
        ai_file_consumer = create_consumer(
            queue_name=AI_FILES_QUEUE_NAME,
            ai_file_service=ai_file_service
        )
        ai_file_consumer.start()
        
        logger.info("Application initialized successfully")
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    
    # Stop AI file consumer
    global ai_file_consumer
    if ai_file_consumer:
        ai_file_consumer.stop()
    
    logger.info("Application shutdown complete")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(project_router, tags=["projects"])
app.include_router(note_router, tags=["notes"])
app.include_router(user_router, tags=["users"])
app.include_router(ai_router, tags=["ai"])
app.include_router(ai_file_router, tags=["ai-files"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API Data"} 

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and debugging"""
    return {"status": "healthy", "service": "backend"} 