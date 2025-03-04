"""
Authentication Controller Layer

This module provides controller-level functionality for authentication routes,
handling HTTP requests and responses for auth operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional

from ..models.user import User
from ..services.auth_service import validate_google_token, get_user_from_db
from ..services.jwt_service import create_tokens, verify_token

# Security setup
security = HTTPBearer()
router = APIRouter()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Get current user from JWT token
    
    Args:
        credentials: The HTTP Authorization credentials
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = verify_token(credentials.credentials)
        user = get_user_from_db(payload["sub"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/google", response_model=Dict)
async def google_auth(token: Dict[str, str] = Body(...), response: Response = None):
    """
    Handle Google OAuth authentication
    
    Args:
        token: Dictionary containing the Google OAuth token
        response: FastAPI Response object for setting cookies
        
    Returns:
        Dictionary with access token and user data
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not token or 'token' not in token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
        
    user = await validate_google_token(token['token'])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Create JWT tokens
    tokens = create_tokens({
        "sub": user.id,
        "email": user.email,
        "name": user.name
    })
    
    # Set cookies
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days
        secure=False,  # Set to True in production
        samesite="lax"
    )
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """
    Refresh access token using refresh token from cookie
    
    Args:
        request: FastAPI Request object for accessing cookies
        response: FastAPI Response object for setting cookies
        
    Returns:
        Dictionary with new access token
        
    Raises:
        HTTPException: If refresh token is invalid or missing
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    try:
        payload = verify_token(refresh_token)
        tokens = create_tokens({
            "sub": payload["sub"],
            "email": payload["email"],
            "name": payload["name"]
        })
        
        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            secure=False,  # Set to True in production
            samesite="lax"
        )
        
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer"
        }
    except:
        # Delete the invalid refresh token cookie
        response.delete_cookie(key="refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """
    Handle user logout
    
    Args:
        response: FastAPI Response object for clearing cookies
        current_user: The authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If an error occurs during logout
    """
    try:
        # Clear refresh token cookie
        response.delete_cookie(key="refresh_token")
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user", response_model=User)
async def get_current_user_data(current_user: User = Depends(get_current_user)):
    """
    Get current user data
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User object
    """
    return current_user 