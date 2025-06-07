from pydantic import BaseModel, EmailStr
from typing import List, Optional, Set, Dict, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Parameters for pagination"""
    page: int = 1
    page_size: int = 10
    exclusive_start_key: Optional[Dict] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Base class for paginated responses"""
    items: List[T]
    page: int
    page_size: int
    has_more: bool
    last_evaluated_key: Optional[Dict] = None 