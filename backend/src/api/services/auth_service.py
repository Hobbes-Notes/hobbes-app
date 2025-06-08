"""
Authentication Service Layer

This module provides service-level functionality for user authentication,
including token validation and authentication flows.
"""

import logging
from typing import Optional
import requests as http_requests
from fastapi import HTTPException, status
from datetime import datetime

from api.models.user import User, UserCreate
from .jwt_service import verify_token
from .user_service import UserService

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_service: UserService = None):
        """
        Initialize the service with dependencies.
        
        Args:
            user_service: Service for user operations
        """
        self.user_service = user_service or UserService()
    
    async def initialize_tables(self) -> None:
        """Initialize database tables required for auth operations."""
        await self.user_service.initialize_tables()
    
    async def validate_google_token(self, token: str) -> Optional[User]:
        """
        Validate a Google OAuth token and get or create the user
        
        Args:
            token: The Google OAuth access token
            
        Returns:
            User object if valid, None otherwise
        """
        try:
            # Verify token with Google - use userinfo endpoint for access tokens
            response = http_requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token}'},
                timeout=10  # Add 10 second timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Invalid Google token: Status {response.status_code}, Response: {response.text}")
                return None
                
            userinfo = response.json()
            
            # Get user from database or create if not exists
            user_id = userinfo['sub']
            
            # Check if user exists
            user = await self.user_service.get_user(user_id)
            
            if not user:
                # Create new user
                from datetime import datetime
                user_create = UserCreate(
                    id=user_id,
                    email=userinfo.get('email', ''),
                    name=userinfo.get('name', ''),
                    picture_url=userinfo.get('picture', '')
                )
                
                # Save to database using user service
                user = await self.user_service.create_user(user_create)
                logger.info(f"Created new user: {user.id}")
            
            return user
        except http_requests.exceptions.Timeout as e:
            logger.error(f"Timeout validating Google token: {str(e)}")
            return None
        except http_requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error validating Google token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating Google token: {str(e)}")
            return None
    
    async def validate_token(self, token: str) -> User:
        """
        Validate a JWT token and return the user
        
        Args:
            token: The JWT token
            
        Returns:
            User object if token is valid
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            payload = verify_token(token)
            user = await self.user_service.get_user(payload["sub"])
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