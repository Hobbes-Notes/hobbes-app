"""
Repository Implementations

This module provides factory functions for repository implementations.
"""

import os
from typing import Optional

from ...repositories.project_repository import ProjectRepository
from ...repositories.note_repository import NoteRepository
from ...repositories.ai_repository import AIRepository
# from ...repositories.action_item_repository import ActionItemRepository

# Removed auto-imports - use lazy loading instead:
# from .project_repository_impl import DynamoDBProjectRepository
# from .note_repository_impl import DynamoDBNoteRepository  
# from .ai_repository_impl import AIRepositoryImpl
# from .user_repository_impl import UserRepositoryImpl

# from .action_item_repository_impl import DynamoDBActionItemRepository
from ...services.ai_service import AIService
# from ...services.action_item_service import ActionItemService
from ..ai_file_repository import AIFileRepository
# from .ai_file_repository_impl import AIFileRepositoryImpl
from ..s3_repository import S3Repository
# from .s3_repository_impl import S3RepositoryImpl

# Singleton instances
_project_repository = None
_note_repository = None
_user_repository = None
_action_item_repository = None
_ai_repository_instance: Optional[AIRepository] = None
_ai_service_instance: Optional[AIService] = None
# _action_item_service_instance: Optional[ActionItemService] = None
_ai_file_repository_instance: Optional[AIFileRepository] = None
_ai_file_s3_repository_instance: Optional[S3Repository] = None

def get_project_repository() -> ProjectRepository:
    """
    Get the project repository implementation.
    
    Returns:
        The project repository implementation.
    """
    global _project_repository
    if _project_repository is None:
        from .project_repository_impl import DynamoDBProjectRepository
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
        from .note_repository_impl import DynamoDBNoteRepository
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
        from .user_repository_impl import UserRepositoryImpl
        _user_repository = UserRepositoryImpl()
    return _user_repository

# def get_action_item_repository() -> ActionItemRepository:
#     """
#     Get the action item repository implementation.
#     
#     Returns:
#         The action item repository implementation.
#     """
#     global _action_item_repository
#     if _action_item_repository is None:
#         _action_item_repository = DynamoDBActionItemRepository()
#     return _action_item_repository

def get_ai_repository() -> AIRepository:
    """
    Get the AI repository instance.
    
    Returns:
        AIRepository instance
    """
    global _ai_repository_instance
    
    if _ai_repository_instance is None:
        from .ai_repository_impl import AIRepositoryImpl
        _ai_repository_instance = AIRepositoryImpl()
        
    return _ai_repository_instance

def get_ai_service() -> AIService:
    """
    Get the AI service instance.
    
    Returns:
        AIService instance
    """
    global _ai_service_instance
    
    if _ai_service_instance is None:
        _ai_service_instance = AIService(get_ai_repository())
        
    return _ai_service_instance

# def get_action_item_service() -> ActionItemService:
#     """
#     Get the action item service instance.
#     
#     Returns:
#         ActionItemService instance
#     """
#     global _action_item_service_instance
#     
#     if _action_item_service_instance is None:
#         _action_item_service_instance = ActionItemService(get_action_item_repository())
#         
#     return _action_item_service_instance

# def get_ai_file_repository() -> AIFileRepository:
#     """
#     Get the AI file repository instance.
#     
#     Returns:
#         AIFileRepository instance
#     """
#     global _ai_file_repository_instance
#     
#     if _ai_file_repository_instance is None:
#         _ai_file_repository_instance = AIFileRepositoryImpl()
#         
#     return _ai_file_repository_instance

# def get_ai_file_s3_repository() -> S3Repository:
#     """
#     Get the AI file S3 repository instance.
#     
#     Returns:
#         S3Repository instance
#     """
#     global _ai_file_s3_repository_instance
#     
#     if _ai_file_s3_repository_instance is None:
#         bucket_name = os.environ.get('AI_FILES_S3_BUCKET', 'ai-files')
#         _ai_file_s3_repository_instance = S3RepositoryImpl(bucket_name)
#         
#     return _ai_file_s3_repository_instance
