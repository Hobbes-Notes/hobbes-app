"""
FastAPI Dependencies

DEPRECATED: This module is being phased out in favor of providers.py
for better separation of concerns and cleaner dependency management.

This module now serves as a compatibility layer that imports from providers.py
"""

import logging
from typing import Annotated

from fastapi import Depends

# Import all providers from the new providers module
from api.services.providers import (
    get_ai_service,
    get_monitoring_service,
    get_auth_service,
    get_action_item_service,
    get_user_service,
    get_ai_file_service,
    get_capb_service,
    get_project_service,
    get_note_service,
    setup_providers
)

# Service type imports for type aliases
from api.services.ai_service import AIService
from api.services.monitoring_service import MonitoringService
from api.services.auth_service import AuthService
from api.services.action_item_service import ActionItemService
from api.services.user_service import UserService
from api.services.ai_file_service import AIFileService
from api.services.capb_service import CapBService
from api.services.project_service import ProjectService
from api.services.note_service import NoteService

logger = logging.getLogger(__name__)


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
    
    This is now a compatibility wrapper around setup_providers().
    """
    logger.info("Setting up FastAPI dependencies (via providers)")
    setup_providers()
    logger.info("FastAPI dependencies configured successfully") 