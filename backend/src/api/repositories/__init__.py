"""
Repository Interfaces

This module defines the interfaces for repository classes that handle
data access operations for the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Base repository interface that defines common methods for data access.
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict) -> T:
        """
        Create a new entity.
        
        Args:
            data: The data for the new entity
            
        Returns:
            The created entity
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            id: The unique identifier of the entity
            data: The updated data
            
        Returns:
            The updated entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            True if deleted, False otherwise
        """
        pass

