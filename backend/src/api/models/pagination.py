from pydantic import BaseModel, EmailStr
from typing import List, Optional, Set, Dict
from datetime import datetime

class PaginatedResponse(BaseModel):
    """Base class for paginated responses"""
    page: int
    page_size: int
    has_more: bool
    LastEvaluatedKey: Optional[Dict] = None 