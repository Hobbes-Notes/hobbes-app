from pydantic import BaseModel
from typing import List, Optional, Set

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    summary: str = ""
    created_at: str

class NoteCreate(BaseModel):
    content: str

class Note(BaseModel):
    id: str
    content: str
    created_at: str
    linked_projects: List[str] = []  # List of project IDs this note is linked to

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None

class ChatMessage(BaseModel):
    content: str
    model: Optional[str] = "gpt-3.5-turbo" 