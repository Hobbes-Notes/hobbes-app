"""
Repository Interfaces

This module defines the interfaces for repository classes that handle
data access operations for the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type

T = TypeVar('T')  # Entity type
C = TypeVar('C')  # Create type
U = TypeVar('U')  # Update type

class BaseRepository(ABC, Generic[T, C, U]):
    """
    Base repository interface that defines common methods for data access.
    
    Type Parameters:
        T: The entity type returned by the repository
        C: The create model type used for creating entities
        U: The update model type used for updating entities
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
    async def create(self, data: C) -> T:
        """
        Create a new entity.
        
        Args:
            data: The create model for the new entity
            
        Returns:
            The created entity
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: U) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            id: The unique identifier of the entity
            data: The update model with updated fields
            
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

