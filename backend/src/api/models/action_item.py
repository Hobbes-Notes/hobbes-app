from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class ActionItemCreate(BaseModel):
    task: str
    doer: Optional[str] = None
    deadline: Optional[str] = None
    theme: Optional[str] = None
    context: Optional[str] = None
    extracted_entities: Dict[str, List[str]] = {}
    status: str = "open"
    type: str = "task"
    projects: List[str] = []
    user_id: str
    source_note_id: Optional[str] = None

class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    doer: Optional[str] = None
    deadline: Optional[str] = None
    theme: Optional[str] = None
    context: Optional[str] = None
    extracted_entities: Optional[Dict[str, List[str]]] = None
    status: Optional[str] = None
    type: Optional[str] = None
    projects: Optional[List[str]] = None
    source_note_id: Optional[str] = None

class ActionItem(BaseModel):
    id: str
    task: str
    doer: Optional[str] = None
    deadline: Optional[str] = None
    theme: Optional[str] = None
    context: Optional[str] = None
    extracted_entities: Dict[str, List[str]] = {}
    status: str = "open"  # open, completed
    type: str = "task"  # task, reminder, decision_point
    projects: List[str] = []
    created_at: str
    updated_at: str
    user_id: str
    source_note_id: Optional[str] = None 