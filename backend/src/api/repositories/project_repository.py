"""
Project Repository Interface

This module defines the interface for project repository operations.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from . import BaseRepository

class ProjectRepository(BaseRepository[Dict]):
    """
    Repository interface for project data access operations.
    """
    
    @abstractmethod
    async def get_projects_by_user(self, user_id: str) -> List[Dict]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of project dictionaries
        """
        pass
    
    @abstractmethod
    async def get_or_create_misc_project(self, user_id: str) -> Dict:
        """
        Get or create a 'Miscellaneous' project for a user.
        
        This project is used for notes that don't match any specific project.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project as a dictionary
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