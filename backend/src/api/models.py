from pydantic import BaseModel, EmailStr
from typing import List, Optional, Set, Dict
from datetime import datetime

class User(BaseModel):
    id: str  # Google user ID
    email: EmailStr
    name: str
    picture_url: Optional[str] = None
    created_at: str

class ActivityUser(BaseModel):
    id: str
    name: str

class ActivityDetails(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    note_id: Optional[str] = None
    note_content: Optional[str] = None

class UserActivity(BaseModel):
    timestamp: str
    user: ActivityUser
    activity: str
    details: Dict = {}

class ActivityResponse(BaseModel):
    status: str = "success"
    data: List[UserActivity]

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

class NoteCreate(BaseModel):
    content: str
    user_id: str

class Note(BaseModel):
    id: str
    content: str
    created_at: str
    user_id: str  # Owner of the note
    linked_projects: List[str] = []  # List of project IDs this note is linked to

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None

class ChatMessage(BaseModel):
    content: str
    model: Optional[str] = "gpt-3.5-turbo" 