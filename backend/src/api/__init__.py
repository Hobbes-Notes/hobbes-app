"""
API Package

This package contains the API layer of the application including
controllers, services, and repositories.

Public API:
- Controllers: HTTP request handlers
- Services: Business logic layer
- Models: Request/response data models
"""

from api.controllers import (
    project_controller,
    note_controller,
    action_item_controller,
    ai_controller,
    user_controller,
    auth_controller
)

from api.services import (
    get_ai_service,
    get_monitoring_service,
    get_auth_service,
    get_action_item_service,
    get_user_service,
    get_ai_file_service,
    get_capb_service,
    get_project_service,
    get_note_service,
    setup_dependencies
)

__all__ = [
    # Controllers
    'project_controller',
    'note_controller', 
    'action_item_controller',
    'ai_controller',
    'user_controller',
    'auth_controller',
    
    # Service factories
    'get_ai_service',
    'get_monitoring_service',
    'get_auth_service',
    'get_action_item_service',
    'get_user_service',
    'get_ai_file_service',
    'get_capb_service',
    'get_project_service',
    'get_note_service',
    'setup_dependencies'
] 