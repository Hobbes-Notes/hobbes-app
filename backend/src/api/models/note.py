from pydantic import BaseModel
from typing import List, Optional, Dict
from .project import ProjectRef
from .pagination import PaginatedResponse

class NoteCreate(BaseModel):
    content: str
    user_id: str
    project_id: Optional[str] = None

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    project_id: Optional[str] = None

class Note(BaseModel):
    id: str
    content: str
    created_at: str
    user_id: str
    projects: List[ProjectRef] = []  # For response, includes project details

class PaginatedNotes(PaginatedResponse):
    """Paginated response for notes listing."""
    items: List[Note]

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123",
                        "content": "Sample note",
                        "created_at": "2024-03-02T12:00:00Z",
                        "user_id": "user123",
                        "projects": [
                            {
                                "id": "project123",
                                "name": "Project Name"
                            }
                        ]
                    }
                ],
                "page": 1,
                "page_size": 10,
                "has_more": False,
                "LastEvaluatedKey": None
            }
        } 