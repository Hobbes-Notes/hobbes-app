"""
User Repository Interface

This module defines the interface for user data operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..models.user import User, UserCreate, UserUpdate

class UserRepository(ABC):
    """Interface for user data operations."""
    
    @abstractmethod
    async def create_user_table(self) -> None:
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create_user(self, user_data: UserCreate) -> User:
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        pass 