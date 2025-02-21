import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api.routes import router
from api.routes.auth import router as auth_router
from api.auth import create_user_tables

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

# Create DynamoDB tables if they don't exist
@app.on_event("startup")
async def startup_event():
    create_user_tables()

# Include routers
app.include_router(router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API Data"} 