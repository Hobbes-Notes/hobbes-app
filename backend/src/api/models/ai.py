"""
AI Models

This module defines models related to AI operations in the system.
"""

from pydantic import BaseModel
from typing import Optional, Dict, List

class RelevanceExtraction(BaseModel):
    """
    Model representing the result of extracting relevant content from a note for a project.
    
    Attributes:
        is_relevant: Whether the note is relevant to the project
        extracted_content: The extracted relevant content from the note
    """
    is_relevant: bool
    extracted_content: str
    
    def __bool__(self):
        """
        Allow using the model in boolean context to check relevance.
        
        Returns:
            True if the note is relevant to the project, False otherwise
        """
        return self.is_relevant 