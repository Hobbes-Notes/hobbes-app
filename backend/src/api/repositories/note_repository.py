"""
Note Repository Interface

This module defines the interface for note repository operations.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from . import BaseRepository

class NoteRepository(BaseRepository[Dict]):
    """
    Repository interface for note data access operations.
    """
    
    @abstractmethod
    async def get_notes_by_project(self, project_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> Dict:
        """
        Get paginated notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            Dictionary with paginated notes and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_notes_by_user(self, user_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> Dict:
        """
        Get paginated notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            Dictionary with paginated notes and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_projects_for_note(self, note_id: str) -> List[Dict]:
        """
        Get all projects associated with a note.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            List of project reference dictionaries (id and name)
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