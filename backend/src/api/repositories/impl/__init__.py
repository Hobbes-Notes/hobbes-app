"""
Repository Implementation Package

This package provides implementations of the repository interfaces.
"""

from .project_repository_impl import DynamoDBProjectRepository
from .note_repository_impl import DynamoDBNoteRepository

# Singleton instances
_project_repository = None
_note_repository = None

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
