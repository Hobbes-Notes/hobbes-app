import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api.controllers.auth_controller import router as auth_router
from api.controllers.project_controller import router as project_router
from api.controllers.note_controller import router as note_router
from api.services.auth_service import create_user_tables
from api.services.database_service import DatabaseService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    allow_origins=[os.getenv('CORS_ORIGIN', 'http://localhost:3000')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database service
database_service = DatabaseService()

# Create DynamoDB tables if they don't exist
@app.on_event("startup")
async def startup_event():
    await database_service.create_tables()
    create_user_tables()

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(project_router, tags=["projects"])
app.include_router(note_router, tags=["notes"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API Data"} 