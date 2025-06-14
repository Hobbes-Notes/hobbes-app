"""
Repository Implementation Module

This module provides implementations of various repositories
used throughout the application.
"""

import logging
from typing import Optional

from api.repositories.note_repository import NoteRepository
from api.repositories.project_repository import ProjectRepository
from api.repositories.ai_repository import AIRepository
from api.repositories.action_item_repository import ActionItemRepository
from api.repositories.impl.note_repository_impl import DynamoDBNoteRepository
from api.repositories.impl.project_repository_impl import DynamoDBProjectRepository
from api.repositories.impl.ai_repository_impl import AIRepositoryImpl
from api.repositories.impl.action_item_repository_impl import DynamoDBActionItemRepository

# Set up logging
logger = logging.getLogger(__name__)

# Singleton instances for repositories only
_note_repository_instance = None
_project_repository_instance = None
_ai_repository_instance = None
_action_item_repository_instance = None

def get_note_repository() -> NoteRepository:
    """
    Get the note repository instance.
    
    Returns:
        NoteRepository instance
    """
    global _note_repository_instance
    
    if _note_repository_instance is None:
        _note_repository_instance = DynamoDBNoteRepository()
        
    return _note_repository_instance

def get_project_repository() -> ProjectRepository:
    """
    Get the project repository instance.
    
    Returns:
        ProjectRepository instance
    """
    global _project_repository_instance
    
    if _project_repository_instance is None:
        _project_repository_instance = DynamoDBProjectRepository()
        
    return _project_repository_instance

def get_ai_repository() -> AIRepository:
    """
    Get the AI repository instance.
    
    Returns:
        AIRepository instance
    """
    global _ai_repository_instance
    
    if _ai_repository_instance is None:
        _ai_repository_instance = AIRepositoryImpl()
        
    return _ai_repository_instance

def get_action_item_repository() -> ActionItemRepository:
    """
    Get the action item repository instance.
    
    Returns:
        ActionItemRepository instance
    """
    global _action_item_repository_instance
    
    if _action_item_repository_instance is None:
        _action_item_repository_instance = DynamoDBActionItemRepository()
        
    return _action_item_repository_instance
