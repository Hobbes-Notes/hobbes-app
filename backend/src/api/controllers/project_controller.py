"""
Project Controller Layer

This module provides controller-level functionality for project routes,
handling HTTP requests and responses for project operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models.project import Project, ProjectCreate, ProjectUpdate
from ..services.project_service import ProjectService

# Set up logging
import logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Create service
project_service = ProjectService()

# Dependency to get service
def get_project_service() -> ProjectService:
    return project_service

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Get a project by its ID.
    
    Args:
        project_id: The unique identifier of the project
        project_service: The project service dependency
        
    Returns:
        The project data
    """
    return await project_service.get_project(project_id)

@router.get("/projects", response_model=List[Project])
async def get_projects(
    user_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Get all projects for a user.
    
    Args:
        user_id: The unique identifier of the user
        project_service: The project service dependency
        
    Returns:
        List of projects
    """
    return await project_service.get_projects(user_id)

@router.post("/projects", response_model=Project)
async def create_project(
    project: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Create a new project.
    
    Args:
        project: The project data to create
        project_service: The project service dependency
        
    Returns:
        The created project
    """
    return await project_service.create_project(project)

@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Update a project.
    
    Args:
        project_id: The unique identifier of the project to update
        project_update: The project data to update
        project_service: The project service dependency
        
    Returns:
        The updated project
    """
    return await project_service.update_project(project_id, project_update)

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Delete a project and all its child projects.
    
    Args:
        project_id: The unique identifier of the project to delete
        project_service: The project service dependency
        
    Returns:
        A message indicating the result of the operation
    """
    return await project_service.delete_project(project_id) 