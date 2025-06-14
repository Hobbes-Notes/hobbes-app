"""
Controllers Package

This package contains HTTP request handlers that follow the three-things rule:
1. Parse input
2. Call service
3. Return response

Controllers should not contain business logic - that belongs in services.
"""

# Import all controller modules
from . import (
    project_controller,
    note_controller,
    action_item_controller,
    ai_controller,
    user_controller,
    auth_controller
)

__all__ = [
    'project_controller',
    'note_controller',
    'action_item_controller', 
    'ai_controller',
    'user_controller',
    'auth_controller'
] 