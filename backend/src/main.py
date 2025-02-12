from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api.routes import router

app = FastAPI(
    title="Project Notes API",
    description="API for managing projects and notes with AI-powered summaries",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('CORS_ORIGIN', 'http://localhost:3000')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API Data"} 