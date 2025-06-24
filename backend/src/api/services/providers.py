"""
Service Providers

This module provides dependency injection providers with proper caching and separation
of concerns. Providers are responsible for wiring services with their dependencies.

Benefits:
- No circular import dependencies
- Proper singleton caching for stateless services  
- Clear separation between service definitions and DI configuration
- Follows enterprise DI patterns
"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

# Repository imports
from api.repositories.impl import (
    get_note_repository, 
    get_project_repository, 
    get_ai_repository, 
    get_action_item_repository
)
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


# =============================================================================
# STATELESS SINGLETON SERVICES (with @lru_cache)
# =============================================================================

@lru_cache()
def get_monitoring_service() -> MonitoringService:
    """Get monitoring service singleton (stateless)."""
    logger.debug("Creating monitoring service singleton")
    return MonitoringService()


# AI Service - singleton with repository injection
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


# =============================================================================
# STATEFUL/REQUEST-SCOPED SERVICES (new instance per request)
# =============================================================================

def get_action_item_service(
    action_item_repository: Annotated[ActionItemRepository, Depends(get_action_item_repository)]
) -> ActionItemService:
    """Get action item service (new instance per request)."""
    logger.debug("Creating action item service instance")
    # Import here to avoid circular dependencies
    from api.services.project_service import ProjectService
    from api.repositories.impl import get_project_repository
    
    # Create project service for automatic "My Life" linking
    project_service = ProjectService(
        project_repository=get_project_repository(),
        ai_service=None,  # Not needed for get_or_create_my_life_project
        capb_service=None  # Not needed for get_or_create_my_life_project
    )
    
    return ActionItemService(
        action_item_repository=action_item_repository,
        project_service=project_service
    )


def get_ai_file_service() -> AIFileService:
    """Get AI file service (new instance per request)."""
    logger.debug("Creating AI file service instance")
    return AIFileService()


# =============================================================================
# COMPLEX SERVICES WITH DEPENDENCIES  
# =============================================================================

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


def get_user_service(
    project_service: Annotated[ProjectService, Depends(get_project_service)]
) -> UserService:
    """Get user service with injected project service."""
    logger.debug("Creating user service instance with project service")
    return UserService(project_service=project_service)


# AuthService singleton with manual caching (like AI service pattern)
_auth_service_instance = None

def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> AuthService:
    """
    Get auth service singleton (stateless) with injected user service.
    
    Note: AuthService is stateless (no mutable state, pure functions for token validation)
    so it can safely be cached as a singleton for performance.
    """
    global _auth_service_instance
    if _auth_service_instance is None:
        logger.debug("Creating auth service singleton with user service")
        _auth_service_instance = AuthService(user_service=user_service)
    return _auth_service_instance


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


# =============================================================================
# INITIALIZATION
# =============================================================================

def setup_providers():
    """
    Setup function for provider initialization.
    
    Pre-warms only true stateless singletons that don't require DI context.
    Other services are created on-demand through FastAPI's dependency injection.
    """
    logger.info("Setting up service providers")
    
    # Pre-warm only stateless singletons
    get_monitoring_service()
    
    logger.info("Service providers configured successfully") 