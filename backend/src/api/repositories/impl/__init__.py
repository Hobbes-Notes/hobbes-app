"""
Repository Implementation Package

This package provides implementations of the repository interfaces.
"""

from .database_repository_impl import DynamoDBRepository
from .project_repository_impl import DynamoDBProjectRepository
from .note_repository_impl import DynamoDBNoteRepository

# Singleton instances
_database_repository = None
_project_repository = None
_note_repository = None

def get_database_repository():
    """
    Get the database repository instance.
    
    Returns:
        The database repository instance
    """
    global _database_repository
    if _database_repository is None:
        _database_repository = DynamoDBRepository()
    return _database_repository

def get_project_repository():
    """
    Get the project repository instance.
    
    Returns:
        The project repository instance
    """
    global _project_repository
    if _project_repository is None:
        _project_repository = DynamoDBProjectRepository(get_database_repository())
    return _project_repository

def get_note_repository():
    """
    Get the note repository instance.
    
    Returns:
        The note repository instance
    """
    global _note_repository
    if _note_repository is None:
        _note_repository = DynamoDBNoteRepository(get_database_repository())
    return _note_repository
