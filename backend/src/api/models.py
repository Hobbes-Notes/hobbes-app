from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None

class NoteCreate(BaseModel):
    content: str

class Note(BaseModel):
    project_id: str
    created_at: str
    content: str
    id: str

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    summary: Optional[str]
    created_at: str

class ChatMessage(BaseModel):
    content: str
    model: Optional[str] = "gpt-3.5-turbo" 