"""
Project Service Layer

This module provides service-level functionality for project management,
including CRUD operations and project-specific business logic.
"""

import logging
from typing import List, Optional, Dict
from fastapi import HTTPException
from litellm import completion

from ..models.project import Project, ProjectCreate, ProjectUpdate
from ..repositories.project_repository import ProjectRepository
from ..repositories.impl import get_project_repository

# Set up logging
logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service for managing projects in the system.
    
    This class handles all business logic related to projects, including
    creation, retrieval, updating, and deletion of projects.
    """
    
    def __init__(self, project_repository: Optional[ProjectRepository] = None):
        """
        Initialize the ProjectService with a project repository.
        
        Args:
            project_repository: Optional ProjectRepository instance. If not provided,
                                a new instance will be created.
        """
        self.project_repository = project_repository or get_project_repository()
    
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
        # Convert to dictionary
        project_dict = project_data.dict()
        
        # Create the project
        return await self.project_repository.create(project_dict)
    
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
    
    async def generate_project_summary(self, project: Project, new_note_content: str) -> str:
        """
        Generate a project summary based on its current summary and a new note.
        
        Args:
            project: The project to generate summary for
            new_note_content: The content of the new note
            
        Returns:
            The generated summary as a string
        """
        try:
            # Convert project to dict if it's a domain model
            if hasattr(project, 'dict'):
                project_dict = project.dict()
            else:
                project_dict = dict(project)
                
            # Get current summary
            current_summary = project_dict.get('summary', '')
            
            # Generate a prompt for the AI
            prompt = f"""
            You are an AI assistant that helps summarize project notes.
            
            Project name: {project_dict['name']}
            Project description: {project_dict.get('description', '')}
            Current project summary: {current_summary}
            
            New note content:
            {new_note_content}
            
            Based on the new note and the current summary, create an updated summary for this project.
            The summary should include:
            1. Learning Goals - What the user wants to learn or achieve
            2. Next Steps - Concrete actions the user can take
            
            Format the summary with markdown headings (## for main sections).
            Keep it concise (max 250 words) and focused on actionable insights.
            """
            
            # Call the AI to generate a summary
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500
            )
            
            # Extract and return the summary
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}")
            # Return the current summary if there's an error
            return current_summary
    
    # The update_project_summary method has been removed as it's no longer needed.
    # The create_note method now directly calls generate_project_summary and update_project. 