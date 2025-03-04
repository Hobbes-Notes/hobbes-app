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
    
    async def get_project(self, project_id: str) -> Dict:
        """
        Get a project by its ID.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            The project data as a dictionary
            
        Raises:
            HTTPException: If the project is not found
        """
        project = await self.project_repository.get_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return project
    
    async def get_projects(self, user_id: str) -> List[Dict]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of project dictionaries
        """
        return await self.project_repository.get_projects_by_user(user_id)
    
    async def create_project(self, project_data: ProjectCreate) -> Dict:
        """
        Create a new project.
        
        Args:
            project_data: The project data to create
            
        Returns:
            The created project as a dictionary
        """
        # Convert to dictionary
        project_dict = project_data.dict()
        
        # Create the project
        return await self.project_repository.create(project_dict)
    
    async def update_project(self, project_id: str, project_update: ProjectUpdate) -> Dict:
        """
        Update an existing project.
        
        Args:
            project_id: The unique identifier of the project
            project_update: The project data to update
            
        Returns:
            The updated project as a dictionary
            
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
    
    async def delete_project(self, project_id: str) -> Dict:
        """
        Delete a project and all its child projects.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            A message indicating the result of the operation
        """
        return await self.project_repository.delete_project_with_descendants(project_id)
    
    async def get_or_create_misc_project(self, user_id: str) -> Dict:
        """
        Get or create a 'Miscellaneous' project for a user.
        
        This project is used for notes that don't match any specific project.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project as a dictionary
        """
        return await self.project_repository.get_or_create_misc_project(user_id)
    
    async def update_project_summary(self, project: Dict, new_note_content: str) -> Dict:
        """
        Update a project's summary based on new note content.
        
        Args:
            project: The project to update
            new_note_content: The content of the new note
            
        Returns:
            The updated project as a dictionary
        """
        try:
            # Get the current summary or initialize it
            current_summary = project.get('summary', '')
            
            # Use AI to generate a new summary
            prompt = f"""
            You are an AI assistant that helps organize and summarize project notes.
            
            Project name: {project['name']}
            Current project summary:
            {current_summary}
            
            New note content:
            {new_note_content}
            
            Based on the new note content and the current summary, please create an updated summary for this project.
            The summary should be in Markdown format with sections for:
            1. Learning Goals (if applicable)
            2. Next Steps
            
            Keep the summary concise but comprehensive, focusing on actionable items and key insights.
            """
            
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500
            )
            
            new_summary = response.choices[0].message.content.strip()
            
            # Update the project with the new summary
            project['summary'] = new_summary
            
            # Save the updated project
            updated_project = await self.project_repository.update(project['id'], {'summary': new_summary})
            
            return updated_project
        except Exception as e:
            logger.error(f"Error updating project summary: {str(e)}")
            # Return the original project if there's an error
            return project 