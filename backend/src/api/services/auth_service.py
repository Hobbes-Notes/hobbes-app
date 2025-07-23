"""
Authentication Service Layer

This module provides service-level functionality for authentication,
including JWT token verification and user management.
"""

import logging
from typing import Optional
import requests as http_requests
from fastapi import HTTPException, status
from datetime import datetime
import time

from api.models.user import User, UserCreate, UserUpdate
from api.services.jwt_service import verify_token
from api.services.user_service import UserService

logger = logging.getLogger(__name__)

def log_auth_service_event(event: str, data: dict = None, duration_ms: float = None, correlation_id: str = None):
    """Standardized logging for auth service events."""
    log_data = {
        'event': event,
        'timestamp': time.time(),
        'correlation_id': correlation_id,
        **(data or {})
    }
    if duration_ms is not None:
        log_data['duration_ms'] = round(duration_ms, 2)
    
    logger.info(f"🔐 AUTH_SERVICE [{correlation_id or 'unknown'}] {event}: {log_data}")

def log_auth_service_error(event: str, error: Exception, data: dict = None, duration_ms: float = None, correlation_id: str = None):
    """Standardized error logging for auth service events."""
    log_data = {
        'event': event,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': time.time(),
        'correlation_id': correlation_id,
        **(data or {})
    }
    if duration_ms is not None:
        log_data['duration_ms'] = round(duration_ms, 2)
    
    logger.error(f"❌ AUTH_SERVICE_ERROR [{correlation_id or 'unknown'}] {event}: {log_data}", exc_info=True)

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
    
    async def validate_google_token(self, token: str, token_type: str = "access_token") -> Optional[User]:
        """
        Validate a Google OAuth token and get or create the user
        
        Args:
            token: The Google OAuth token (access_token or id_token)
            token_type: Type of token ("access_token" or "id_token")
            
        Returns:
            User object if valid, None otherwise
        """
        start_time = time.time()
        correlation_id = f"google_validate_{int(time.time() * 1000)}"
        
        log_auth_service_event("validate_google_token_start", {
            "token_type": token_type,
            "token_length": len(token)
        }, correlation_id=correlation_id)
        
        try:
            if token_type == "id_token":
                # For ID tokens, use Google's ID token validation
                log_auth_service_event("validating_id_token", {"endpoint": "google_tokeninfo"}, correlation_id=correlation_id)
                userinfo = await self._validate_id_token(token, correlation_id)
            else:
                # For access tokens, use userinfo endpoint
                log_auth_service_event("validating_access_token", {"endpoint": "google_userinfo"}, correlation_id=correlation_id)
                userinfo = await self._validate_access_token(token, correlation_id)
            
            if not userinfo:
                duration_ms = (time.time() - start_time) * 1000
                log_auth_service_error("google_validation_no_userinfo", 
                                     ValueError("No user info returned"), 
                                     {"token_type": token_type}, 
                                     duration_ms=duration_ms, 
                                     correlation_id=correlation_id)
                return None
            
            # Get user from database or create if not exists
            user_id = userinfo['sub']
            user_email = userinfo.get('email', 'unknown')
            
            log_auth_service_event("google_validation_success", {
                "user_id": user_id,
                "user_email": user_email,
                "token_type": token_type
            }, correlation_id=correlation_id)
            
            # Check if user exists or create new one
            user_lookup_start = time.time()
            log_auth_service_event("user_lookup_start", {"user_id": user_id}, correlation_id=correlation_id)
            
            user = await self.user_service.get_user(user_id)
            user_lookup_duration = (time.time() - user_lookup_start) * 1000
            
            if user:
                log_auth_service_event("existing_user_found", {
                    "user_id": user_id,
                    "user_email": user.email
                }, duration_ms=user_lookup_duration, correlation_id=correlation_id)
            else:
                # Create new user
                user_creation_start = time.time()
                log_auth_service_event("creating_new_user", {
                    "user_id": user_id,
                    "user_email": user_email
                }, correlation_id=correlation_id)
                
                new_user = UserCreate(
                    id=user_id,
                    email=user_email,
                    name=userinfo.get('name', ''),
                    picture=userinfo.get('picture', '')
                )
                
                user = await self.user_service.create_user(new_user)
                user_creation_duration = (time.time() - user_creation_start) * 1000
                
                log_auth_service_event("new_user_created", {
                    "user_id": user.id,
                    "user_email": user.email
                }, duration_ms=user_creation_duration, correlation_id=correlation_id)
            
            total_duration = (time.time() - start_time) * 1000
            log_auth_service_event("validate_google_token_complete", {
                "user_id": user.id,
                "user_email": user.email,
                "total_duration_ms": round(total_duration, 2),
                "user_lookup_ms": round(user_lookup_duration, 2)
            }, correlation_id=correlation_id)
            
            return user
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_auth_service_error("validate_google_token_error", e, {
                "token_type": token_type
            }, duration_ms=duration_ms, correlation_id=correlation_id)
            return None
    
    async def _validate_id_token(self, id_token: str, correlation_id: str = None) -> Optional[dict]:
        """
        Validate a Google ID token using Google's tokeninfo endpoint
        
        Args:
            id_token: The Google ID token
            correlation_id: Correlation ID for logging
            
        Returns:
            User info dict if valid, None otherwise
        """
        start_time = time.time()
        
        try:
            # Use Google's tokeninfo endpoint for ID token validation
            url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
            log_auth_service_event("google_tokeninfo_request_start", {
                "url": url[:100] + "..." if len(url) > 100 else url,  # Truncate for security
                "method": "GET"
            }, correlation_id=correlation_id)
            
            response = http_requests.get(url, timeout=10)
            duration_ms = (time.time() - start_time) * 1000
            
            log_auth_service_event("google_tokeninfo_response", {
                "status_code": response.status_code,
                "response_time_ms": round(duration_ms, 2)
            }, correlation_id=correlation_id)
            
            if response.status_code != 200:
                log_auth_service_error("google_tokeninfo_failed", 
                                     ValueError(f"HTTP {response.status_code}"), {
                                         "status_code": response.status_code,
                                         "response_text": response.text[:200]  # Truncate for logs
                                     }, duration_ms=duration_ms, correlation_id=correlation_id)
                return None
            
            userinfo = response.json()
            
            log_auth_service_event("google_tokeninfo_success", {
                "user_email": userinfo.get('email', 'unknown'),
                "user_id": userinfo.get('sub', 'unknown'),
                "userinfo_keys": list(userinfo.keys())
            }, duration_ms=duration_ms, correlation_id=correlation_id)
            
            return userinfo
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_auth_service_error("google_tokeninfo_error", e, {}, 
                                 duration_ms=duration_ms, correlation_id=correlation_id)
            return None
    
    async def _validate_access_token(self, access_token: str, correlation_id: str = None) -> Optional[dict]:
        """
        Validate a Google access token using the userinfo endpoint
        
        Args:
            access_token: The Google access token
            correlation_id: Correlation ID for logging
            
        Returns:
            User info dict if valid, None otherwise
        """
        start_time = time.time()
        
        try:
            # Verify token with Google - use userinfo endpoint for access tokens
            url = 'https://www.googleapis.com/oauth2/v3/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            
            log_auth_service_event("google_userinfo_request_start", {
                "url": url,
                "method": "GET",
                "has_auth_header": True
            }, correlation_id=correlation_id)
            
            response = http_requests.get(url, headers=headers, timeout=10)
            duration_ms = (time.time() - start_time) * 1000
            
            log_auth_service_event("google_userinfo_response", {
                "status_code": response.status_code,
                "response_time_ms": round(duration_ms, 2)
            }, correlation_id=correlation_id)
            
            if response.status_code != 200:
                log_auth_service_error("google_userinfo_failed", 
                                     ValueError(f"HTTP {response.status_code}"), {
                                         "status_code": response.status_code,
                                         "response_text": response.text[:200]  # Truncate for logs
                                     }, duration_ms=duration_ms, correlation_id=correlation_id)
                return None
                
            userinfo = response.json()
            
            log_auth_service_event("google_userinfo_success", {
                "user_email": userinfo.get('email', 'unknown'),
                "user_id": userinfo.get('sub', 'unknown'),
                "userinfo_keys": list(userinfo.keys())
            }, duration_ms=duration_ms, correlation_id=correlation_id)
            
            return userinfo
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_auth_service_error("google_userinfo_error", e, {}, 
                                 duration_ms=duration_ms, correlation_id=correlation_id)
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
        start_time = time.time()
        correlation_id = f"jwt_validate_{int(time.time() * 1000)}"
        
        log_auth_service_event("validate_jwt_start", {
            "token_length": len(token)
        }, correlation_id=correlation_id)
        
        try:
            payload = verify_token(token)
            jwt_verification_duration = (time.time() - start_time) * 1000
            
            log_auth_service_event("jwt_verified", {
                "user_id": payload.get("sub"),
                "user_email": payload.get("email")
            }, duration_ms=jwt_verification_duration, correlation_id=correlation_id)
            
            user_lookup_start = time.time()
            user = await self.user_service.get_user(payload["sub"])
            user_lookup_duration = (time.time() - user_lookup_start) * 1000
            
            if user is None:
                total_duration = (time.time() - start_time) * 1000
                log_auth_service_error("jwt_user_not_found", 
                                     ValueError("User not found"), {
                                         "user_id": payload.get("sub")
                                     }, duration_ms=total_duration, correlation_id=correlation_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            total_duration = (time.time() - start_time) * 1000
            log_auth_service_event("validate_jwt_success", {
                "user_id": user.id,
                "user_email": user.email,
                "total_duration_ms": round(total_duration, 2),
                "jwt_verification_ms": round(jwt_verification_duration, 2),
                "user_lookup_ms": round(user_lookup_duration, 2)
            }, correlation_id=correlation_id)
            
            return user
        except HTTPException:
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_auth_service_error("validate_jwt_error", e, {}, 
                                 duration_ms=duration_ms, correlation_id=correlation_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get the current user from a JWT token
        
        Args:
            token: The JWT token
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            return await self.validate_token(token)
        except HTTPException:
            return None
        except Exception:
            return None 