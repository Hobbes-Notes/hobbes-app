"""
User Service Layer

This module provides service-level functionality for user management,
including CRUD operations and business logic.
"""

import logging
from datetime import datetime
from typing import Optional

from api.models.user import User, UserCreate, UserUpdate
from api.repositories.user_repository import UserRepository
from api.repositories.impl.user_repository_impl import UserRepositoryImpl

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations."""
    
    def __init__(self, user_repository: UserRepository = None, project_service: Optional['ProjectService'] = None):
        """
        Initialize the service with dependencies.
        
        Args:
            user_repository: Repository for user data operations
            project_service: Service for project operations (for user initialization)
        """
        self.user_repository = user_repository or UserRepositoryImpl()
        self.project_service = project_service
    
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
        Create a new user with complete initialization.
        
        This includes creating the user record and setting up their default workspace
        with a "My Life" root project.
        
        Args:
            user_data: The user data to save
            
        Returns:
            The created User object
        """
        logger.info(f"Creating new user: {user_data.id} ({user_data.email})")
        
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
        created_user = await self.user_repository.create_user(UserCreate(**user.dict()))
        logger.info(f"✅ User {created_user.id} created successfully")
        
        # Initialize user's default workspace with "My Life" project
        await self._initialize_user_workspace(created_user.id)
        
        return created_user
    
    async def _initialize_user_workspace(self, user_id: str) -> None:
        """
        Initialize a new user's workspace with default projects.
        
        Creates the "My Life" root project that serves as the top-level container
        for all the user's projects.
        
        Args:
            user_id: The unique identifier of the user
        """
        try:
            if self.project_service:
                logger.info(f"Initializing workspace for user {user_id}")
                await self.project_service.create_my_life_project(user_id)
                logger.info(f"✅ Workspace initialized successfully for user {user_id}")
            else:
                logger.warning(f"⚠️ ProjectService not available - user {user_id} created without default workspace")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize workspace for user {user_id}: {str(e)}")
            # Don't fail user creation if workspace initialization fails
            logger.warning(f"User {user_id} created successfully but without default workspace")
    
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