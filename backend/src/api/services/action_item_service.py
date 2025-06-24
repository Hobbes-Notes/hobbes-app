"""
Action Item Service Layer

This module provides service-level functionality for action item operations.
"""

import logging
from typing import List, Optional

from api.models.action_item import ActionItem, ActionItemCreate, ActionItemUpdate
from api.repositories.action_item_repository import ActionItemRepository

logger = logging.getLogger(__name__)

class ActionItemService:
    """Service for action item operations."""
    
    def __init__(self, action_item_repository: ActionItemRepository, project_service=None):
        """
        Initialize the service.
        
        Args:
            action_item_repository: The action item repository to use
            project_service: The project service to use for getting My Life project
        """
        self.action_item_repository = action_item_repository
        self.project_service = project_service
    
    async def create_action_item(self, action_item_data: ActionItemCreate) -> ActionItem:
        """
        Create a new action item.
        
        Automatically links the action item to the user's "My Life" project if no
        projects are specified.
        
        Args:
            action_item_data: The action item data
            
        Returns:
            The created action item
        """
        try:
            logger.info(f"Creating action item: {action_item_data.task[:50]}...")
            
            # Automatically link to "My Life" project if no projects specified
            if not action_item_data.projects and self.project_service:
                try:
                    my_life_project = await self.project_service.get_or_create_my_life_project(action_item_data.user_id)
                    if my_life_project:
                        action_item_data.projects = [my_life_project.id]
                        logger.info(f"Auto-linked action item to My Life project: {my_life_project.id}")
                    else:
                        logger.warning(f"Could not find or create My Life project for user {action_item_data.user_id}")
                except Exception as e:
                    logger.error(f"Error linking to My Life project: {str(e)}")
                    # Continue without linking - don't fail action item creation
            
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
        import time
        start_time = time.time()
        
        try:
            logger.info(f"🔧 SERVICE: Starting update for action item {action_item_id}")
            logger.debug(f"🔧 SERVICE: Update data - projects: {update_data.projects}")
            logger.debug(f"🔧 SERVICE: Update data - task: {getattr(update_data, 'task', 'NOT_SET')}")
            logger.debug(f"🔧 SERVICE: Update data - status: {getattr(update_data, 'status', 'NOT_SET')}")
            
            # Call repository
            repo_start = time.time()
            logger.debug(f"🔧 SERVICE: Calling repository.update_action_item for {action_item_id}")
            
            result = await self.action_item_repository.update_action_item(action_item_id, update_data)
            
            repo_time = time.time() - repo_start
            total_time = time.time() - start_time
            
            if result:
                logger.info(f"✅ SERVICE: Successfully updated action item {action_item_id} in {total_time:.3f}s (repo: {repo_time:.3f}s)")
                logger.debug(f"✅ SERVICE: Updated item projects: {result.projects}")
            else:
                logger.warning(f"⚠️ SERVICE: Repository returned None for action item {action_item_id} after {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"❌ SERVICE: Failed to update action item {action_item_id} after {total_time:.3f}s")
            logger.error(f"❌ SERVICE: Error type: {error_type}")
            logger.error(f"❌ SERVICE: Error message: {str(e)}")
            logger.error(f"❌ SERVICE: Update data was: {update_data}")
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