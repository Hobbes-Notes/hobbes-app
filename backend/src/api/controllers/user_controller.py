from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..models.user import User, UserUpdate
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
    return current_user

@router.patch("/users/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        updated_user = await user_service.update_user(current_user.id, user_data)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        ) 