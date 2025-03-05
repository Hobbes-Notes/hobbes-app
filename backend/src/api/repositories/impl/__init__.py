"""
Repository Implementation Package

This package provides implementations of the repository interfaces.
"""

from .project_repository_impl import DynamoDBProjectRepository
from .note_repository_impl import DynamoDBNoteRepository
from .user_repository_impl import UserRepositoryImpl

# Singleton instances
_project_repository = None
_note_repository = None
_user_repository = None

def get_project_repository():
    """
    Get the project repository instance.
    
    Returns:
        The project repository instance
    """
    global _project_repository
    if _project_repository is None:
        _project_repository = DynamoDBProjectRepository()
    return _project_repository

def get_note_repository():
    """
    Get the note repository instance.
    
    Returns:
        The note repository instance
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
