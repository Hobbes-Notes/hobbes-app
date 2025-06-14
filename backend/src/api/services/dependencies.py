"""
FastAPI Dependencies

This module provides dependency injection using FastAPI's native Depends system.
Replaces the dependency-injector library with FastAPI's built-in DI.

Benefits:
- Zero compatibility issues
- Native FastAPI integration
- Automatic request scoping
- Built-in async support
- Cleaner syntax
"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

# Repository imports
from api.repositories.impl import get_note_repository, get_project_repository, get_ai_repository, get_action_item_repository
from api.repositories.ai_repository import AIRepository
from api.repositories.action_item_repository import ActionItemRepository

# Service imports
from api.services.ai_service import AIService
from api.services.action_item_service import ActionItemService
from api.services.monitoring_service import MonitoringService
from api.services.auth_service import AuthService
from api.services.user_service import UserService
from api.services.note_service import NoteService
from api.services.project_service import ProjectService
from api.services.capb_service import CapBService
from api.services.ai_file_service import AIFileService

logger = logging.getLogger(__name__)


# Singleton services (manual caching for DI compatibility)
_ai_service_instance = None

def get_ai_service(
    ai_repository: Annotated[AIRepository, Depends(get_ai_repository)]
) -> AIService:
    """Get AI service singleton with injected AI repository."""
    global _ai_service_instance
    if _ai_service_instance is None:
        logger.debug("Creating AI service singleton with AI repository")
        _ai_service_instance = AIService(ai_repository=ai_repository)
    return _ai_service_instance


@lru_cache()
def get_monitoring_service() -> MonitoringService:
    """Get monitoring service singleton."""
    logger.debug("Creating monitoring service singleton")
    return MonitoringService()


@lru_cache()
def get_auth_service() -> AuthService:
    """Get auth service singleton."""
    logger.debug("Creating auth service singleton")
    return AuthService()


# Factory services (new instance per request)
def get_action_item_service(
    action_item_repository: Annotated[ActionItemRepository, Depends(get_action_item_repository)]
) -> ActionItemService:
    """Get action item service (new instance per request)."""
    logger.debug("Creating action item service instance")
    return ActionItemService(action_item_repository=action_item_repository)


def get_user_service() -> UserService:
    """Get user service (new instance per request)."""
    logger.debug("Creating user service instance")
    return UserService()


def get_ai_file_service() -> AIFileService:
    """Get AI file service (new instance per request)."""
    logger.debug("Creating AI file service instance")
    return AIFileService()


# Complex services with dependencies
def get_capb_service(
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    action_item_service: Annotated[ActionItemService, Depends(get_action_item_service)],
    monitoring_service: Annotated[MonitoringService, Depends(get_monitoring_service)]
) -> CapBService:
    """Get CapB service with injected dependencies."""
    logger.debug("Creating CapB service with dependencies")
    # Create CapBService without project_service initially to handle circular dependency
    capb = CapBService(
        ai_service=ai_service,
        action_item_service=action_item_service,
        project_service=None,  # Will be set by get_project_service
        monitoring_service=monitoring_service
    )
    return capb


def get_project_service(
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    capb_service: Annotated[CapBService, Depends(get_capb_service)]
) -> ProjectService:
    """Get project service with injected dependencies."""
    logger.debug("Creating project service with dependencies")
    project_repository = get_project_repository()
    
    project_service = ProjectService(
        project_repository=project_repository,
        ai_service=ai_service,
        capb_service=capb_service
    )
    
    # Handle circular dependency: inject project_service into capb_service
    capb_service.project_service = project_service
    
    return project_service


def get_note_service(
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    action_item_service: Annotated[ActionItemService, Depends(get_action_item_service)],
    capb_service: Annotated[CapBService, Depends(get_capb_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)]
) -> NoteService:
    """Get note service with injected dependencies."""
    logger.debug("Creating note service with dependencies")
    note_repository = get_note_repository()
    project_repository = get_project_repository()
    
    return NoteService(
        note_repository=note_repository,
        project_repository=project_repository,
        project_service=project_service,
        ai_service=ai_service,
        action_item_service=action_item_service,
        capb_service=capb_service
    )


# Type aliases for cleaner controller signatures
AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
MonitoringServiceDep = Annotated[MonitoringService, Depends(get_monitoring_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ActionItemServiceDep = Annotated[ActionItemService, Depends(get_action_item_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AIFileServiceDep = Annotated[AIFileService, Depends(get_ai_file_service)]
CapBServiceDep = Annotated[CapBService, Depends(get_capb_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]


def setup_dependencies():
    """
    Setup function for dependency initialization.
    
    This is called at application startup to ensure all dependencies
    are properly configured. Services are now request-scoped and created
    on-demand through FastAPI's dependency injection.
    """
    logger.info("Setting up FastAPI dependencies")
    
    # Pre-warm only true singletons that don't require DI context
    get_monitoring_service()
    get_auth_service()
    
    # Note: get_ai_service() removed from eager initialization
    # It will be created on-demand with proper dependency injection
    
    logger.info("FastAPI dependencies configured successfully") 