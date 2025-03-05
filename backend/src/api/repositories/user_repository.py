"""
User Repository Interface

This module defines the interface for user data operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

class UserRepository(ABC):
    """Interface for user data operations."""
    
    @abstractmethod
    async def create_user_table(self) -> None:
        """Create the Users table if it doesn't exist."""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User data dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user.
        
        Args:
            user_data: The user data to save
            
        Returns:
            The created user data
        """
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """
        Update a user.
        
        Args:
            user_id: The user's ID
            user_data: The user data to update
            
        Returns:
            The updated user data
        """
        pass 