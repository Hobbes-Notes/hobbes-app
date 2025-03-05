"""
User Service Layer

This module provides service-level functionality for user management,
including CRUD operations and business logic.
"""

import logging
from datetime import datetime
from typing import Optional, Dict

from ..models.user import User
from ..repositories.user_repository import UserRepository
from ..repositories.impl.user_repository_impl import UserRepositoryImpl

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations."""
    
    def __init__(self, user_repository: UserRepository = None):
        """
        Initialize the service with dependencies.
        
        Args:
            user_repository: Repository for user data operations
        """
        self.user_repository = user_repository or UserRepositoryImpl()
    
    async def initialize_tables(self) -> None:
        """Initialize database tables required for user operations."""
        await self.user_repository.create_user_table()
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User object if found, None otherwise
        """
        user_data = await self.user_repository.get_user(user_id)
        if user_data:
            return User(**user_data)
        return None
    
    async def create_user(self, user_data: Dict) -> User:
        """
        Create a new user.
        
        Args:
            user_data: The user data to save
            
        Returns:
            The created User object
        """
        # Ensure created_at is set
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.now().isoformat()
            
        created_user = await self.user_repository.create_user(user_data)
        return User(**created_user)
    
    async def update_user(self, user_id: str, user_data: Dict) -> User:
        """
        Update a user.
        
        Args:
            user_id: The user's ID
            user_data: The user data to update
            
        Returns:
            The updated User object
        """
        updated_user = await self.user_repository.update_user(user_id, user_data)
        return User(**updated_user) 