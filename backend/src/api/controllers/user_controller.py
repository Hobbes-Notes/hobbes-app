"""
User Controller

Handles HTTP requests for user management operations.
Follows the three-things rule: parse input, call service, return response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.models.user import User, UserUpdate
from api.services import get_user_service
from api.services.user_service import UserService
from api.controllers.auth_controller import get_current_user

# Create router
router = APIRouter()

@router.get("/users/me", response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get the current user's profile."""
    return await user_service.get_user(current_user.id)

@router.patch("/users/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update the current user's profile."""
    try:
        updated_user = await user_service.update_user(current_user.id, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        ) 