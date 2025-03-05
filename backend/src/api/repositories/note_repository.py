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
        """
        Get a note by its ID.
        
        Args:
            id: The unique identifier of the note
            
        Returns:
            The note if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, data: NoteCreate) -> Note:
        """
        Create a new note.
        
        Args:
            data: The create model for the new note
            
        Returns:
            The created note
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: NoteUpdate) -> Optional[Note]:
        """
        Update an existing note.
        
        Args:
            id: The unique identifier of the note
            data: The update model with updated fields
            
        Returns:
            The updated note if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a note by its ID.
        
        Args:
            id: The unique identifier of the note
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_notes_by_project(self, project_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        """
        Get paginated notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            pagination: Pagination parameters including page, page_size, and exclusive_start_key
            
        Returns:
            Paginated response containing Note objects and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_notes_by_user(self, user_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        """
        Get paginated notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            pagination: Pagination parameters including page, page_size, and exclusive_start_key
            
        Returns:
            Paginated response containing Note objects and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_projects_for_note(self, note_id: str) -> List[ProjectRef]:
        """
        Get all projects associated with a note.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            List of project references (id and name)
        """
        pass
    
    @abstractmethod
    async def associate_note_with_project(self, note_id: str, project_id: str, timestamp: str) -> None:
        """
        Associate a note with a project.
        
        Args:
            note_id: The unique identifier of the note
            project_id: The unique identifier of the project
            timestamp: The timestamp of the association
        """
        pass 