"""
Project Controller

Handles HTTP requests for project management operations.
Follows the three-things rule: parse input, call service, return response.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from api.models.project import Project, ProjectCreate, ProjectUpdate
from api.services import get_project_service
from api.services.project_service import ProjectService

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get a project by ID."""
    return await project_service.get_project(project_id)

@router.get("/projects", response_model=List[Project])
async def get_projects(
    user_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get all projects for a user."""
    return await project_service.get_projects(user_id)

@router.post("/projects", response_model=Project)
async def create_project(
    project: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service)
):
    """Create a new project."""
    return await project_service.create_project(project)

@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update an existing project."""
    return await project_service.update_project(project_id, project_update)

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Delete a project and all its descendants."""
    return await project_service.delete_project(project_id) 