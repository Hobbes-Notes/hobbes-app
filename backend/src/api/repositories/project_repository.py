"""
Project Repository Interface

This module defines the interface for project repository operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..models.project import Project, ProjectCreate, ProjectUpdate

class ProjectRepository(ABC):
    """
    Repository interface for project data access operations.
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Project]:
        """
        Get a project by its ID.
        
        Args:
            id: The unique identifier of the project
            
        Returns:
            The project if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, data: ProjectCreate) -> Project:
        """
        Create a new project.
        
        Args:
            data: The create model for the new project
            
        Returns:
            The created project
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: ProjectUpdate) -> Optional[Project]:
        """
        Update an existing project.
        
        Args:
            id: The unique identifier of the project
            data: The update model with updated fields
            
        Returns:
            The updated project if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a project by its ID.
        
        Args:
            id: The unique identifier of the project
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_projects_by_user(self, user_id: str) -> List[Project]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of projects
        """
        pass
    
    @abstractmethod
    async def get_or_create_misc_project(self, user_id: str) -> Project:
        """
        Get or create a 'Miscellaneous' project for a user.
        
        This project is used for notes that don't match any specific project.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project
        """
        pass
    
    @abstractmethod
    async def delete_project_with_descendants(self, project_id: str) -> Dict:
        """
        Delete a project and all its descendants.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            A message indicating the result of the operation
        """
        pass 