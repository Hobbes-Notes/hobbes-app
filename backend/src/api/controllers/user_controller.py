"""
User Controller Layer

This module provides controller-level functionality for user routes,
handling HTTP requests and responses for user operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, List

from ..models.user import User
from ..services.user_service import UserService
from .auth_controller import get_current_user

# Create router
router = APIRouter()

# Create services
user_service = UserService()

# Dependency to get services
def get_user_service() -> UserService:
    return user_service

@router.get("/users/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User object
    """
    return current_user

@router.patch("/users/me", response_model=User)
async def update_current_user(
    user_data: Dict = Body(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile
    
    Args:
        user_data: The user data to update
        current_user: The authenticated user
        user_service: The user service dependency
        
    Returns:
        Updated User object
    """
    try:
        # Prevent updating id
        if 'id' in user_data:
            del user_data['id']
            
        updated_user = await user_service.update_user(current_user.id, user_data)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        ) 