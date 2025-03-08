"""
AI File Repository Interface

This module defines the interface for AI file repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models.ai_file import AIFileRecord, AIFileState

class AIFileRepository(ABC):
    """
    Repository interface for AI file records.
    """
    
    @abstractmethod
    async def get_file_record(self, file_id: str) -> Optional[AIFileRecord]:
        """
        Get a file record by ID.
        
        Args:
            file_id: The ID of the file record to get
            
        Returns:
            The file record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_file_records_by_user(self, user_id: str) -> List[AIFileRecord]:
        """
        Get all file records for a user.
        
        Args:
            user_id: The ID of the user to get file records for
            
        Returns:
            List of file records for the user
        """
        pass
    
    @abstractmethod
    async def create_file_record(self, file_record: AIFileRecord) -> AIFileRecord:
        """
        Create a new file record.
        
        Args:
            file_record: The file record to create
            
        Returns:
            The created file record
        """
        pass
    
    @abstractmethod
    async def update_file_record(self, file_id: str, updates: Dict[str, Any]) -> Optional[AIFileRecord]:
        """
        Update a file record.
        
        Args:
            file_id: The ID of the file record to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated file record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_file_state(self, file_id: str, state: AIFileState, 
                              error_message: Optional[str] = None) -> Optional[AIFileRecord]:
        """
        Update the state of a file record.
        
        Args:
            file_id: The ID of the file record to update
            state: The new state of the file
            error_message: Optional error message if the state is FAILED
            
        Returns:
            The updated file record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_file_record(self, file_id: str) -> bool:
        """
        Delete a file record.
        
        Args:
            file_id: The ID of the file record to delete
            
        Returns:
            True if the file record was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_files_by_state(self, state: AIFileState) -> List[AIFileRecord]:
        """
        Get all file records with a specific state.
        
        Args:
            state: The state to filter by
            
        Returns:
            List of file records with the specified state
        """
        pass 