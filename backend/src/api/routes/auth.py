from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request
from ..auth import validate_google_token, get_current_user
from ..models import User
from ..jwt import create_tokens, verify_token
from typing import List, Dict
from datetime import datetime

router = APIRouter()

@router.post("/google", response_model=Dict)
async def google_auth(token: Dict[str, str] = Body(...), response: Response = None):
    """Handle Google OAuth authentication"""
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
    """Refresh access token using refresh token from cookie"""
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
    """Handle user logout"""
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
    """Get current user data"""
    return current_user 