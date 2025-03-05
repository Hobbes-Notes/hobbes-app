"""
Note Repository Interface

This module defines the interface for note repository operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..models.note import Note, NoteCreate, NoteUpdate
from ..models.pagination import PaginatedResponse, PaginationParams
from ..models.project import ProjectRef

class NoteRepository(ABC):
    """
    Repository interface for note data access operations.
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Note]:
        pass
    
    @abstractmethod
    async def create(self, data: NoteCreate) -> Note:
        pass
    
    @abstractmethod
    async def update(self, id: str, data: NoteUpdate) -> Optional[Note]:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_notes_by_project(self, project_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        pass
    
    @abstractmethod
    async def get_notes_by_user(self, user_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        pass
    
    @abstractmethod
    async def get_projects_for_note(self, note_id: str) -> List[ProjectRef]:
        pass
    
    @abstractmethod
    async def associate_note_with_project(self, note_id: str, project_id: str, timestamp: str) -> None:
        pass 