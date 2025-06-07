"""
JWT Service Layer

This module provides service-level functionality for JWT token management,
including token creation, verification, and refresh operations.
"""

from datetime import datetime, timedelta
from typing import Dict
from jose import JWTError, jwt
import os
from fastapi import HTTPException, status

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: Dict) -> str:
    """
    Create a new access token
    
    Args:
        data: The payload data to encode in the token
        
    Returns:
        Encoded JWT access token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict) -> str:
    """
    Create a new refresh token
    
    Args:
        data: The payload data to encode in the token
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict:
    """
    Verify a token and return its payload
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_tokens(user_data: Dict) -> Dict:
    """
    Create both access and refresh tokens
    
    Args:
        user_data: The user data to encode in the tokens
        
    Returns:
        Dictionary containing access_token, refresh_token, and token_type
    """
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    } 