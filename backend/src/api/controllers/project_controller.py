from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models.project import Project, ProjectCreate, ProjectUpdate
from ..services.project_service import ProjectService

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

_project_service = None

def get_project_service() -> ProjectService:
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.get_project(project_id)

@router.get("/projects", response_model=List[Project])
async def get_projects(
    user_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.get_projects(user_id)

@router.post("/projects", response_model=Project)
async def create_project(
    project: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.create_project(project)

@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.update_project(project_id, project_update)

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.delete_project(project_id) 