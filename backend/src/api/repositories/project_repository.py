"""
Project Repository Interface

This module defines the interface for project repository operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from api.models.project import Project, ProjectCreate, ProjectUpdate

class ProjectRepository(ABC):
    """
    Repository interface for project data access operations.
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Project]:
        pass
    
    @abstractmethod
    async def create(self, data: ProjectCreate) -> Project:
        pass
    
    @abstractmethod
    async def update(self, id: str, data: ProjectUpdate) -> Optional[Project]:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_projects_by_user(self, user_id: str) -> List[Project]:
        pass
    
    @abstractmethod
    async def delete_project_with_descendants(self, project_id: str) -> Project:
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str, user_id: str) -> Optional[Project]:
        pass 