"""
Logging Middleware

This module provides middleware for logging requests and responses.
"""

import logging
import json
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, log it, and pass it to the next middleware or endpoint.
        
        Args:
            request: The FastAPI request object
            call_next: The next middleware or endpoint to call
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Start timer
        start_time = time.time()
        
        # Get request path and method
        path = request.url.path
        method = request.method
        
        # Log all endpoints for debugging
        # Log request
        await self._log_request(request)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Log all endpoints for debugging
            # Log response
            duration_ms = (time.time() - start_time) * 1000
            self._log_response(path, method, response.status_code, duration_ms)
                
            return response
        except Exception as e:
            # Log exception
            logger.exception(f"Exception processing request: {path} {method}")
                
            # Re-raise the exception
            raise
    
    async def _log_request(self, request: Request) -> None:
        """
        Log request details.
        
        Args:
            request: The FastAPI request object
        """
        # Get request path and method
        path = request.url.path
        method = request.method
        
        # Log basic request info
        logger.info(f"Request: {method} {path}")
        logger.debug(f"Request details: client={request.client}, headers={dict(request.headers)}")
        
        # Log request body for POST and PUT requests
        if method in ['POST', 'PUT']:
            try:
                # Clone the request body
                body_bytes = await request.body()
                
                # Restore the request body
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
                
                # Try to parse as JSON
                try:
                    body = json.loads(body_bytes)
                    logger.debug(f"Request body: {json.dumps(body, default=str)}")
                except:
                    # If not JSON, log as string
                    logger.debug(f"Request body: {body_bytes.decode('utf-8', errors='replace')}")
            except Exception as e:
                logger.warning(f"Could not log request body: {str(e)}")
    
    def _log_response(self, path: str, method: str, status_code: int, duration_ms: float) -> None:
        """
        Log response details.
        
        Args:
            path: The request path
            method: The request method
            status_code: The response status code
            duration_ms: The request duration in milliseconds
        """
        logger.info(f"Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)")
        
        # Log more details for error responses
        if status_code >= 400:
            logger.warning(f"Error response: {method} {path} - {status_code}") 