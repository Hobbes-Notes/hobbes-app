"""
Note Controller Layer

This module provides controller-level functionality for note routes,
handling HTTP requests and responses for note operations.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import json
import logging

from ..models.note import Note, NoteCreate, PaginatedNotes
from ..services.note_service import NoteService
from ..services.project_service import ProjectService
from ..services.database_service import DatabaseService

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Create services
database_service = DatabaseService()
project_service = ProjectService(database_service.get_dynamodb_resource())
note_service = NoteService(database_service.get_dynamodb_resource(), project_service)

# Dependency to get services
def get_note_service() -> NoteService:
    return note_service

@router.post("/notes", response_model=Note)
async def create_note(
    note: NoteCreate,
    note_service: NoteService = Depends(get_note_service)
):
    """
    Create a new note.
    
    Args:
        note: The note data to create
        note_service: The note service dependency
        
    Returns:
        The created note with associated projects
    """
    return await note_service.create_note(note)

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get a note by ID.
    
    Args:
        note_id: The unique identifier of the note
        note_service: The note service dependency
        
    Returns:
        The note data with associated projects
    """
    return await note_service.get_note(note_id)

@router.get("/notes", response_model=PaginatedNotes)
async def list_notes(
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, gt=0),
    page_size: int = Query(10, gt=0, le=50),
    exclusive_start_key: Optional[str] = None,
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get paginated notes, either by project or by user.
    
    Args:
        project_id: Optional project ID to filter notes by
        user_id: Optional user ID to filter notes by
        page: The page number (1-indexed)
        page_size: The number of items per page
        exclusive_start_key: Optional key for pagination
        note_service: The note service dependency
        
    Returns:
        Paginated notes with metadata
    """
    # Parse the exclusive_start_key if provided
    parsed_key = None
    if exclusive_start_key:
        try:
            parsed_key = json.loads(exclusive_start_key)
        except:
            raise HTTPException(status_code=400, detail="Invalid pagination key format")
    
    # Get notes by project or by user
    if project_id:
        return await note_service.get_notes_by_project(project_id, page, page_size, parsed_key)
    elif user_id:
        return await note_service.get_notes_by_user(user_id, page, page_size, parsed_key)
    else:
        raise HTTPException(status_code=400, detail="Either project_id or user_id must be provided") 