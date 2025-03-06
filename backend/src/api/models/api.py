"""
API Models

This module defines models related to API responses.
"""

from typing import Any, Optional
from pydantic import BaseModel

class APIResponse(BaseModel):
    """
    Standard API response model.
    
    Attributes:
        success: Whether the request was successful
        data: The response data
        message: A message describing the response
    """
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None 