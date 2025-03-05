from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import json
import logging

from ..models.note import Note, NoteCreate, PaginatedNotes
from ..services.note_service import NoteService
from ..services.project_service import ProjectService
from ..repositories.impl import get_note_repository, get_project_repository

logger = logging.getLogger(__name__)

router = APIRouter()

project_service = ProjectService()
note_repository = get_note_repository()
project_repository = get_project_repository()
note_service = NoteService(
    note_repository=note_repository,
    project_repository=project_repository,
    project_service=project_service
)

def get_note_service() -> NoteService:
    return note_service

@router.post("/notes", response_model=Note)
async def create_note(
    note: NoteCreate,
    note_service: NoteService = Depends(get_note_service)
):
    return await note_service.create_note(note)

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    note_service: NoteService = Depends(get_note_service)
):
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