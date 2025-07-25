"""
Project Service Layer

This module provides service-level functionality for project management,
including CRUD operations and project-specific business logic.
"""

import logging
from typing import List, Optional, Dict
from fastapi import HTTPException
from litellm import completion

from api.models.project import Project, ProjectCreate, ProjectUpdate
from api.repositories.project_repository import ProjectRepository
from api.repositories.impl import get_project_repository, get_ai_repository
from api.services.ai_service import AIService

# Set up logging
logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service for managing projects in the system.
    
    This class handles all business logic related to projects, including
    creation, retrieval, updating, and deletion of projects.
    """
    
    def __init__(
        self, 
        project_repository: Optional[ProjectRepository] = None, 
        ai_service: Optional[AIService] = None,
        capb_service: Optional['CapBService'] = None
    ):
        """
        Initialize the ProjectService with a project repository.
        
        Args:
            project_repository: Optional ProjectRepository instance. If not provided,
                                a new instance will be created.
            ai_service: Optional AIService instance. If not provided,
                        a new instance will be created.
            capb_service: Optional CapBService instance for project tagging.
        """
        self.project_repository = project_repository or get_project_repository()
        self.ai_service = ai_service or AIService(get_ai_repository())
        self.capb_service = capb_service
    
    async def get_project(self, project_id: str) -> Project:
        """
        Get a project by its ID.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            The project as a Project domain model
            
        Raises:
            HTTPException: If the project is not found
        """
        project = await self.project_repository.get_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return project
    
    async def get_projects(self, user_id: str) -> List[Project]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of Project domain models
        """
        return await self.project_repository.get_projects_by_user(user_id)
    
    async def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create a new project.
        
        Args:
            project_data: The project data to create
            
        Returns:
            The created project as a Project domain model
        """
        logger.info(f"Creating new project: '{project_data.name}' for user {project_data.user_id}")
        
        # Convert to dictionary
        project_dict = project_data.dict()
        
        # Create the project
        created_project = await self.project_repository.create(project_dict)
        logger.info(f"✅ Successfully created project {created_project.id} - '{created_project.name}'")
        
        # CapB: Tag existing action items with the new project
        if self.capb_service:
            logger.info(f"Starting CapB: Tagging existing action items with new project {created_project.id}")
            try:
                capb_result = await self.capb_service.run_for_user(project_data.user_id)
                
                if capb_result["success"]:
                    logger.info(f"✅ CapB completed for new project: {capb_result['message']}")
                    logger.debug(f"CapB tagged {capb_result['tagged_action_items']}/{capb_result['total_action_items']} action items after project creation")
                else:
                    logger.warning(f"⚠️ CapB failed but project creation succeeds: {capb_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ CapB error after creating project {created_project.id}: {str(e)}")
                logger.exception("Detailed exception information for CapB after project creation:")
                # CapB failure doesn't affect project creation success
                logger.info("Project creation succeeded despite CapB failure")
        else:
            logger.info(f"CapB service not available, skipping action item tagging for new project")
        
        return created_project
    
    async def update_project(self, project_id: str, project_update: ProjectUpdate) -> Project:
        """
        Update an existing project.
        
        Args:
            project_id: The unique identifier of the project
            project_update: The project data to update
            
        Returns:
            The updated project as a Project domain model
            
        Raises:
            HTTPException: If the project is not found
        """
        # Convert to dictionary, excluding unset fields
        update_data = project_update.dict(exclude_unset=True)
        
        # Update the project
        updated_project = await self.project_repository.update(project_id, update_data)
        
        if not updated_project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return updated_project
    
    async def delete_project(self, project_id: str) -> Project:
        """
        Delete a project and all its child projects.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            The deleted Project domain model with additional metadata
        """
        return await self.project_repository.delete_project_with_descendants(project_id)
    
    async def get_or_create_misc_project(self, user_id: str) -> Project:
        """
        Get or create a miscellaneous project for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project as a Project domain model
        """
        try:
            # Try to get the Miscellaneous project by name
            misc_project = await self.project_repository.get_by_name("Miscellaneous", user_id)
            
            # If found, return it
            if misc_project:
                return misc_project
            
            # Otherwise, create a new one
            misc_project_data = ProjectCreate(
                name="Miscellaneous",
                description="Default project for uncategorized notes",
                user_id=user_id
            )
            
            return await self.project_repository.create(misc_project_data)
        except Exception as e:
            logger.error(f"Error getting or creating miscellaneous project: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_or_create_my_life_project(self, user_id: str) -> Project:
        """
        Get or create the "My Life" project for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The "My Life" project as a Project domain model
        """
        try:
            # Try to get the "My Life" project by name
            my_life_project = await self.project_repository.get_by_name("My Life", user_id)
            
            # If found, return it
            if my_life_project:
                return my_life_project
            
            # Otherwise, create a new one
            logger.info(f"Creating 'My Life' project for user {user_id}")
            my_life_project_data = ProjectCreate(
                name="My Life",
                description="Your main life project - organize everything under this",
                user_id=user_id,
                parent_id=None  # This is the root project
            )
            
            created_project = await self.project_repository.create(my_life_project_data.dict())
            logger.info(f"✅ Successfully created 'My Life' project {created_project.id} for user {user_id}")
            
            return created_project
        except Exception as e:
            logger.error(f"Error getting or creating 'My Life' project: {str(e)}")
            # Don't raise HTTPException here - this is used by action item service
            logger.warning(f"Failed to get/create 'My Life' project for user {user_id}: {str(e)}")
            return None
    
    async def create_my_life_project(self, user_id: str) -> Project:
        """
        Create the root "My Life" project for a new user.
        
        This method delegates to get_or_create_my_life_project for consistency.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The created "My Life" project as a Project domain model
        """
        return await self.get_or_create_my_life_project(user_id)
    
    # The generate_project_summary method has been moved to AIService.
    # The create_note method now directly calls AIService.generate_project_summary.
    
    # The update_project_summary method has been removed as it's no longer needed.
    # The create_note method now directly calls generate_project_summary and update_project. 