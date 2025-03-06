"""
AI Models

This module defines models related to AI operations in the system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum

class AIUseCase(str, Enum):
    """
    Enum representing different AI use cases in the system.
    """
    PROJECT_SUMMARY = "project_summary"
    RELEVANCE_EXTRACTION = "relevance_extraction"

class AIConfiguration(BaseModel):
    """
    Model representing a configuration for an AI operation.
    
    Attributes:
        use_case: The use case this configuration is for
        version: The version of this configuration (auto-generated, input value is ignored)
        model: The AI model to use
        system_prompt: The system prompt that defines the AI assistant's role and behavior
        user_prompt_template: The template for the user prompt with variables to be filled
        max_tokens: Maximum tokens for the response
        temperature: Temperature for response generation
        description: Optional description of this configuration version
        created_at: When this configuration was created
        is_active: Whether this configuration is active
    """
    use_case: AIUseCase
    version: int = 0  # This value is ignored and auto-generated during creation
    model: str
    system_prompt: str
    user_prompt_template: str
    max_tokens: int = 500
    temperature: float = 0.7
    description: Optional[str] = None
    created_at: Optional[str] = None
    is_active: bool = False
    
    def get_key(self) -> str:
        """
        Get a unique key for this configuration.
        
        Returns:
            String in the format "use_case:version"
        """
        return f"{self.use_case}:{self.version}"

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