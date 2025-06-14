"""
Note Controller

Handles HTTP requests for note management operations.
Follows the three-things rule: parse input, call service, return response.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import json
import logging

from api.models.note import Note, NoteCreate, PaginatedNotes
from api.services import get_note_service
from api.services.note_service import NoteService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/notes", response_model=Note)
async def create_note(
    note: NoteCreate,
    note_service: NoteService = Depends(get_note_service)
):
    """Create a new note."""
    return await note_service.create_note(note)

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    note_service: NoteService = Depends(get_note_service)
):
    """Get a note by ID."""
    return await note_service.get_note(note_id)

@router.get("/notes/count", response_model=Dict[str, int])
async def get_notes_count(
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    note_service: NoteService = Depends(get_note_service)
):
    """Get total count of notes. Requires either project_id or user_id."""
    if project_id:
        count = await note_service.get_notes_count_by_project(project_id)
        return {"count": count}
    elif user_id:
        count = await note_service.get_notes_count_by_user(user_id)
        return {"count": count}
    else:
        raise HTTPException(status_code=400, detail="Either project_id or user_id must be provided")

@router.get("/notes", response_model=PaginatedNotes)
async def list_notes(
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, gt=0),
    page_size: int = Query(10, gt=0, le=50),
    exclusive_start_key: Optional[str] = None,
    note_service: NoteService = Depends(get_note_service)
):
    """List notes with pagination. Requires either project_id or user_id."""
    parsed_key = None
    if exclusive_start_key:
        try:
            parsed_key = json.loads(exclusive_start_key)
        except:
            raise HTTPException(status_code=400, detail="Invalid pagination key format")
    
    if project_id:
        return await note_service.get_notes_by_project(project_id, page, page_size, parsed_key)
    elif user_id:
        return await note_service.get_notes_by_user(user_id, page, page_size, parsed_key)
    else:
        raise HTTPException(status_code=400, detail="Either project_id or user_id must be provided")