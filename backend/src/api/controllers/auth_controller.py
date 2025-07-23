"""
Auth Controller

Handles HTTP requests for authentication operations.
Follows the three-things rule: parse input, call service, return response.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import time
import logging

from api.models.user import User
from api.services import get_auth_service
from api.services.auth_service import AuthService
from api.services.jwt_service import create_tokens, verify_token

# Configure enhanced logging for authentication
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

def get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers or generate a new one."""
    correlation_id = request.headers.get('X-Correlation-ID', f"backend_{int(time.time() * 1000)}")
    return correlation_id

def log_auth_event(correlation_id: str, event: str, data: dict = None, duration_ms: float = None):
    """Standardized logging for authentication events."""
    log_data = {
        'correlation_id': correlation_id,
        'event': event,
        'timestamp': time.time(),
        **(data or {})
    }
    if duration_ms is not None:
        log_data['duration_ms'] = round(duration_ms, 2)
    
    logger.info(f"🔐 AUTH_BACKEND [{correlation_id}] {event}: {log_data}")

def log_auth_error(correlation_id: str, event: str, error: Exception, data: dict = None, duration_ms: float = None):
    """Standardized error logging for authentication events."""
    log_data = {
        'correlation_id': correlation_id,
        'event': event,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': time.time(),
        **(data or {})
    }
    if duration_ms is not None:
        log_data['duration_ms'] = round(duration_ms, 2)
    
    logger.error(f"❌ AUTH_BACKEND_ERROR [{correlation_id}] {event}: {log_data}", exc_info=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get the current authenticated user from JWT token."""
    start_time = time.time()
    correlation_id = f"auth_validate_{int(time.time() * 1000)}"
    
    log_auth_event(correlation_id, "token_validation_start", {
        "token_length": len(credentials.credentials) if credentials.credentials else 0
    })
    
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        duration_ms = (time.time() - start_time) * 1000
        
        if not user:
            log_auth_error(correlation_id, "token_validation_failed", 
                         ValueError("Invalid credentials"), duration_ms=duration_ms)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        log_auth_event(correlation_id, "token_validation_success", {
            "user_id": user.id,
            "user_email": user.email
        }, duration_ms=duration_ms)
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_auth_error(correlation_id, "token_validation_error", e, duration_ms=duration_ms)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/google", response_model=Dict)
async def google_auth(
    request: Request,
    response: Response,
    token: Dict[str, str] = Body(...), 
    auth_service: AuthService = Depends(get_auth_service)
):
    overall_start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    log_auth_event(correlation_id, "google_auth_start", {
        "token_keys": list(token.keys()),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")[:100]  # Truncate long user agents
    })
    
    # Determine which token to use
    google_token = None
    token_type = "access_token"
    token_selection_start = time.time()
    
    if 'id_token' in token and token['id_token']:
        google_token = token['id_token']
        token_type = "id_token"
        log_auth_event(correlation_id, "token_type_selected", {
            "token_type": "id_token",
            "token_length": len(google_token)
        })
    elif 'token' in token and token['token']:
        google_token = token['token']
        token_type = "access_token"
        log_auth_event(correlation_id, "token_type_selected", {
            "token_type": "access_token", 
            "token_length": len(google_token)
        })
    else:
        duration_ms = (time.time() - overall_start_time) * 1000
        log_auth_error(correlation_id, "no_valid_token", 
                      ValueError("No valid token found"), {
                          "available_keys": list(token.keys())
                      }, duration_ms=duration_ms)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token or ID token is required"
        )
        
    token_selection_duration = (time.time() - token_selection_start) * 1000
    log_auth_event(correlation_id, "token_selection_completed", duration_ms=token_selection_duration)
    
    # Validate Google token
    google_validation_start = time.time()
    log_auth_event(correlation_id, "google_validation_start", {
        "token_type": token_type,
        "service": "google_oauth"
    })
    
    try:
        user = await auth_service.validate_google_token(google_token, token_type)
        google_validation_duration = (time.time() - google_validation_start) * 1000
        
        if not user:
            log_auth_error(correlation_id, "google_validation_failed", 
                          ValueError("Google token validation returned no user"), {
                              "token_type": token_type
                          }, duration_ms=google_validation_duration)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        log_auth_event(correlation_id, "google_validation_success", {
            "user_id": user.id,
            "user_email": user.email,
            "token_type": token_type
        }, duration_ms=google_validation_duration)
        
    except HTTPException:
        raise
    except Exception as e:
        google_validation_duration = (time.time() - google_validation_start) * 1000
        log_auth_error(correlation_id, "google_validation_error", e, {
            "token_type": token_type
        }, duration_ms=google_validation_duration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Create JWT tokens
    jwt_creation_start = time.time()
    log_auth_event(correlation_id, "jwt_creation_start", {
        "user_id": user.id
    })
    
    try:
        tokens = create_tokens({
            "sub": user.id,
            "email": user.email,
            "name": user.name
        })
        
        jwt_creation_duration = (time.time() - jwt_creation_start) * 1000
        log_auth_event(correlation_id, "jwt_creation_success", {
            "access_token_length": len(tokens["access_token"]),
            "refresh_token_length": len(tokens["refresh_token"])
        }, duration_ms=jwt_creation_duration)
        
    except Exception as e:
        jwt_creation_duration = (time.time() - jwt_creation_start) * 1000
        log_auth_error(correlation_id, "jwt_creation_error", e, duration_ms=jwt_creation_duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create authentication tokens"
        )
    
    # Set refresh token cookie
    cookie_setting_start = time.time()
    log_auth_event(correlation_id, "cookie_setting_start")
    
    try:
        # Configure cookie for same-origin usage
        # Remove domain restriction for Fly.dev due to public suffix list
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            secure=True,  # Required for HTTPS in production
            samesite="none",  # Allow cross-domain usage
            # domain omitted - cookies will work on the backend domain only
        )
        
        cookie_setting_duration = (time.time() - cookie_setting_start) * 1000
        log_auth_event(correlation_id, "cookie_setting_success", {
            "domain": "backend-only",
            "samesite": "none"
        }, duration_ms=cookie_setting_duration)
        
    except Exception as e:
        cookie_setting_duration = (time.time() - cookie_setting_start) * 1000
        log_auth_error(correlation_id, "cookie_setting_error", e, duration_ms=cookie_setting_duration)
        # Don't fail the whole login for cookie issues
    
    # Final success
    overall_duration = (time.time() - overall_start_time) * 1000
    log_auth_event(correlation_id, "google_auth_complete_success", {
        "user_id": user.id,
        "user_email": user.email,
        "total_duration_ms": round(overall_duration, 2),
        "google_validation_ms": round(google_validation_duration, 2),
        "jwt_creation_ms": round(jwt_creation_duration, 2)
    })
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer",
        "user": user,
        "_debug": {
            "correlation_id": correlation_id,
            "total_duration_ms": round(overall_duration, 2)
        }
    }

@router.post("/refresh")
async def refresh_token(
    request: Request, 
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    log_auth_event(correlation_id, "refresh_token_start", {
        "cookies_received": list(request.cookies.keys()),
        "client_ip": request.client.host if request.client else "unknown"
    })
    
    refresh_token_value = request.cookies.get("refresh_token")
    
    if not refresh_token_value:
        duration_ms = (time.time() - start_time) * 1000
        log_auth_error(correlation_id, "refresh_token_missing", 
                      ValueError("No refresh token cookie"), duration_ms=duration_ms)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    log_auth_event(correlation_id, "refresh_token_found", {
        "token_length": len(refresh_token_value)
    })
    
    try:
        # Verify refresh token
        token_verification_start = time.time()
        payload = verify_token(refresh_token_value)
        token_verification_duration = (time.time() - token_verification_start) * 1000
        
        log_auth_event(correlation_id, "refresh_token_verified", {
            "user_id": payload.get("sub"),
            "user_email": payload.get("email")
        }, duration_ms=token_verification_duration)
        
        # Create new tokens
        token_creation_start = time.time()
        tokens = create_tokens({
            "sub": payload["sub"],
            "email": payload["email"],
            "name": payload["name"]
        })
        token_creation_duration = (time.time() - token_creation_start) * 1000
        
        log_auth_event(correlation_id, "new_tokens_created", duration_ms=token_creation_duration)
        
        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            secure=True,
            samesite="none",  # Allow cross-domain usage
            # domain omitted - cookies will work on the backend domain only
        )
        
        overall_duration = (time.time() - start_time) * 1000
        log_auth_event(correlation_id, "refresh_token_success", {
            "user_id": payload.get("sub"),
            "total_duration_ms": round(overall_duration, 2)
        })
        
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer",
            "_debug": {
                "correlation_id": correlation_id,
                "total_duration_ms": round(overall_duration, 2)
            }
        }
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_auth_error(correlation_id, "refresh_token_error", e, duration_ms=duration_ms)
        
        # Delete refresh token cookie with same attributes used when setting it
        response.delete_cookie(
            key="refresh_token",
            secure=True,
            samesite="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response, 
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    log_auth_event(correlation_id, "logout_start", {
        "user_id": current_user.id,
        "user_email": current_user.email
    })
    
    try:
        # Delete refresh token cookie with same attributes used when setting it
        response.delete_cookie(
            key="refresh_token",
            secure=True,
            samesite="none"
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_auth_event(correlation_id, "logout_success", {
            "user_id": current_user.id
        }, duration_ms=duration_ms)
        
        return {
            "message": "Successfully logged out",
            "_debug": {
                "correlation_id": correlation_id
            }
        }
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_auth_error(correlation_id, "logout_error", e, duration_ms=duration_ms)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user", response_model=User)
async def get_current_user_data(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    correlation_id = get_correlation_id(request)
    
    log_auth_event(correlation_id, "get_user_data", {
        "user_id": current_user.id,
        "user_email": current_user.email
    })
    
    return current_user