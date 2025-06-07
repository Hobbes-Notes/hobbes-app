from pydantic import BaseModel
from typing import Optional

class ProjectRef(BaseModel):
    id: str
    name: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: str
    parent_id: Optional[str] = None  # ID of the parent project

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    summary: str = ""
    created_at: str
    user_id: str  # Owner of the project
    parent_id: Optional[str] = None  # ID of the parent project
    level: int = 1  # Level in the hierarchy (1 to 3)

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None 