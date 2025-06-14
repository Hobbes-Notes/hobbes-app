"""
Services Package

This package contains service layer implementations using FastAPI's native dependency injection.
All service creation goes through FastAPI Depends for proper lifetime management.

Dependency lifetimes:
- Singleton: Stateless services (AI, Monitoring, Auth) - cached with @lru_cache
- Factory: Stateful services that need fresh instances per request
- Type aliases: Clean controller signatures with Annotated types
"""

# Re-export all service factories from FastAPI dependencies
from .dependencies import (
    get_ai_service,
    get_monitoring_service,
    get_auth_service,
    get_action_item_service,
    get_user_service,
    get_ai_file_service,
    get_capb_service,
    get_project_service,
    get_note_service,
    setup_dependencies,
    # Type aliases for controllers
    AIServiceDep,
    MonitoringServiceDep,
    AuthServiceDep,
    ActionItemServiceDep,
    UserServiceDep,
    AIFileServiceDep,
    CapBServiceDep,
    ProjectServiceDep,
    NoteServiceDep
)

__all__ = [
    # Service factory functions
    'get_ai_service',
    'get_monitoring_service', 
    'get_auth_service',
    'get_action_item_service',
    'get_user_service',
    'get_ai_file_service',
    'get_capb_service',
    'get_project_service',
    'get_note_service',
    'setup_dependencies',
    
    # Type aliases for controllers
    'AIServiceDep',
    'MonitoringServiceDep',
    'AuthServiceDep',
    'ActionItemServiceDep',
    'UserServiceDep',
    'AIFileServiceDep',
    'CapBServiceDep',
    'ProjectServiceDep',
    'NoteServiceDep'
] 