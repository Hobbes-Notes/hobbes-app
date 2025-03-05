"""
User Service Layer

This module provides service-level functionality for user management,
including CRUD operations and business logic.
"""

import logging
from datetime import datetime
from typing import Optional

from ..models.user import User, UserCreate, UserUpdate
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
        return await self.user_repository.get_user(user_id)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: The user data to save
            
        Returns:
            The created User object
        """
        # Create a complete user with timestamp
        timestamp = datetime.now().isoformat()
        
        # Create a User object with all required fields
        user = User(
            id=user_data.id,
            email=user_data.email,
            name=user_data.name,
            picture_url=user_data.picture_url,
            created_at=timestamp
        )
        
        # Create the user in the repository
        return await self.user_repository.create_user(UserCreate(**user.dict()))
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """
        Update a user.
        
        Args:
            user_id: The user's ID
            user_data: The user data to update
            
        Returns:
            The updated User object
        """
        return await self.user_repository.update_user(user_id, user_data) 