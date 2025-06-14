"""
Request-Scoped Resource Management

This module provides per-request providers for resources like DB sessions
and external API clients to prevent concurrency bugs.

Future enhancements:
- Database session management
- HTTP client connection pooling
- Request-scoped caching
- Distributed tracing context
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variables for request-scoped resources
_request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class RequestContext:
    """
    Manages request-scoped resources and their lifecycle.
    
    Provides async context managers for resources that need to be
    created per-request and cleaned up after the request completes.
    """
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._cleanup_callbacks: Dict[str, callable] = {}
    
    def set_resource(self, key: str, resource: Any, cleanup_callback: Optional[callable] = None):
        """Set a request-scoped resource with optional cleanup callback."""
        self._resources[key] = resource
        if cleanup_callback:
            self._cleanup_callbacks[key] = cleanup_callback
    
    def get_resource(self, key: str) -> Optional[Any]:
        """Get a request-scoped resource."""
        return self._resources.get(key)
    
    async def cleanup(self):
        """Clean up all request-scoped resources."""
        for key, callback in self._cleanup_callbacks.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._resources.get(key))
                else:
                    callback(self._resources.get(key))
            except Exception as e:
                logger.error(f"Error cleaning up resource {key}: {e}")
        
        self._resources.clear()
        self._cleanup_callbacks.clear()


@asynccontextmanager
async def request_scope() -> AsyncGenerator[RequestContext, None]:
    """
    Async context manager for request-scoped resources.
    
    Usage:
        async with request_scope() as ctx:
            # Set up request-scoped resources
            ctx.set_resource('db_session', create_db_session(), cleanup_db_session)
            
            # Use resources throughout request
            db_session = ctx.get_resource('db_session')
            
            # Resources automatically cleaned up on exit
    """
    context = RequestContext()
    _request_context.set({'context': context})
    
    try:
        logger.debug("Request scope started")
        yield context
    finally:
        await context.cleanup()
        logger.debug("Request scope cleaned up")


def get_current_request_context() -> Optional[RequestContext]:
    """Get the current request context if available."""
    ctx_data = _request_context.get({})
    return ctx_data.get('context')


# Future: Database session provider
async def get_db_session():
    """
    Get or create a request-scoped database session.
    
    This is a placeholder for future database integration.
    When implemented, it will:
    1. Check if a session exists in the current request context
    2. Create a new session if none exists
    3. Register cleanup callback to close session
    4. Return the session
    """
    context = get_current_request_context()
    if not context:
        raise RuntimeError("No request context available for database session")
    
    session = context.get_resource('db_session')
    if session is None:
        # Future: Create actual database session
        # session = create_database_session()
        # context.set_resource('db_session', session, close_database_session)
        logger.warning("Database session provider not yet implemented")
        return None
    
    return session


# Future: HTTP client provider
async def get_http_client():
    """
    Get or create a request-scoped HTTP client.
    
    This is a placeholder for future HTTP client integration.
    When implemented, it will:
    1. Check if a client exists in the current request context
    2. Create a new client with connection pooling if none exists
    3. Register cleanup callback to close connections
    4. Return the client
    """
    context = get_current_request_context()
    if not context:
        raise RuntimeError("No request context available for HTTP client")
    
    client = context.get_resource('http_client')
    if client is None:
        # Future: Create actual HTTP client with connection pooling
        # client = create_http_client()
        # context.set_resource('http_client', client, close_http_client)
        logger.warning("HTTP client provider not yet implemented")
        return None
    
    return client 