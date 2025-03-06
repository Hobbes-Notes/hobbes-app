"""
Repository Implementation Package

This package provides implementations of the repository interfaces.
"""

from ...repositories.project_repository import ProjectRepository
from ...repositories.note_repository import NoteRepository
from ...repositories.ai_repository import AIRepository
from .project_repository_impl import DynamoDBProjectRepository
from .note_repository_impl import DynamoDBNoteRepository
from .ai_repository_impl import AIRepositoryImpl
from .user_repository_impl import UserRepositoryImpl
from ...services.ai_service import AIService

# Singleton instances
_project_repository = None
_note_repository = None
_user_repository = None
_ai_repository = None
_ai_service = None

def get_project_repository() -> ProjectRepository:
    """
    Get the project repository implementation.
    
    Returns:
        The project repository implementation.
    """
    global _project_repository
    if _project_repository is None:
        _project_repository = DynamoDBProjectRepository()
    return _project_repository

def get_note_repository() -> NoteRepository:
    """
    Get the note repository implementation.
    
    Returns:
        The note repository implementation.
    """
    global _note_repository
    if _note_repository is None:
        _note_repository = DynamoDBNoteRepository()
    return _note_repository

def get_user_repository():
    """
    Get the user repository instance.
    
    Returns:
        The user repository instance
    """
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepositoryImpl()
    return _user_repository

def get_ai_repository() -> AIRepository:
    """
    Get the AI repository implementation.
    
    Returns:
        The AI repository implementation.
    """
    global _ai_repository
    if _ai_repository is None:
        _ai_repository = AIRepositoryImpl()
    return _ai_repository

def get_ai_service() -> AIService:
    """
    Get the AI service instance.
    
    Returns:
        The AI service instance
    """
    global _ai_service
    if _ai_service is None:
        # Get AI repository
        ai_repository = get_ai_repository()
        _ai_service = AIService(ai_repository=ai_repository)
    return _ai_service
