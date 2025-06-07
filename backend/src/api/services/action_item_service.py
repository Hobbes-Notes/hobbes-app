"""
Action Item Service Layer

This module provides service-level functionality for action item operations.
"""

import logging
from typing import List, Optional

from ..models.action_item import ActionItem, ActionItemCreate, ActionItemUpdate
from ..repositories.action_item_repository import ActionItemRepository

logger = logging.getLogger(__name__)

class ActionItemService:
    """Service for action item operations."""
    
    def __init__(self, action_item_repository: ActionItemRepository):
        """
        Initialize the service.
        
        Args:
            action_item_repository: The action item repository to use
        """
        self.action_item_repository = action_item_repository
    
    async def create_action_item(self, action_item_data: ActionItemCreate) -> ActionItem:
        """
        Create a new action item.
        
        Args:
            action_item_data: The action item data
            
        Returns:
            The created action item
        """
        try:
            logger.info(f"Creating action item: {action_item_data.task[:50]}...")
            action_item = await self.action_item_repository.create_action_item(action_item_data)
            logger.info(f"Successfully created action item: {action_item.id}")
            return action_item
        except Exception as e:
            logger.error(f"Error creating action item: {str(e)}")
            raise
    
    async def get_action_item(self, action_item_id: str) -> Optional[ActionItem]:
        """
        Get an action item by ID.
        
        Args:
            action_item_id: The action item ID
            
        Returns:
            The action item if found, None otherwise
        """
        try:
            return await self.action_item_repository.get_action_item(action_item_id)
        except Exception as e:
            logger.error(f"Error getting action item {action_item_id}: {str(e)}")
            raise
    
    async def update_action_item(self, action_item_id: str, update_data: ActionItemUpdate) -> Optional[ActionItem]:
        """
        Update an action item.
        
        Args:
            action_item_id: The action item ID
            update_data: The update data
            
        Returns:
            The updated action item if found, None otherwise
        """
        try:
            logger.info(f"Updating action item: {action_item_id}")
            return await self.action_item_repository.update_action_item(action_item_id, update_data)
        except Exception as e:
            logger.error(f"Error updating action item {action_item_id}: {str(e)}")
            raise
    
    async def get_action_items_by_user(self, user_id: str) -> List[ActionItem]:
        """
        Get all action items for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of action items
        """
        try:
            return await self.action_item_repository.get_action_items_by_user(user_id)
        except Exception as e:
            logger.error(f"Error getting action items for user {user_id}: {str(e)}")
            raise
    
    async def get_action_items_by_project(self, project_id: str, user_id: str) -> List[ActionItem]:
        """
        Get action items for a specific project.
        
        Args:
            project_id: The project ID
            user_id: The user ID
            
        Returns:
            List of action items for the project
        """
        try:
            return await self.action_item_repository.get_action_items_by_project(project_id, user_id)
        except Exception as e:
            logger.error(f"Error getting action items for project {project_id}: {str(e)}")
            raise
    
    async def delete_action_item(self, action_item_id: str) -> bool:
        """
        Delete an action item.
        
        Args:
            action_item_id: The action item ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            logger.info(f"Deleting action item: {action_item_id}")
            return await self.action_item_repository.delete_action_item(action_item_id)
        except Exception as e:
            logger.error(f"Error deleting action item {action_item_id}: {str(e)}")
            raise 