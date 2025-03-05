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
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict) -> Dict:
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user_data: Dict) -> Dict:
        pass 