"""
Services Package

This package contains service layer implementations.
"""

from typing import Optional

# Removed automatic import: from .ai_file_service import AIFileService
# from ..repositories.impl import get_ai_file_repository, get_ai_file_s3_repository, get_ai_service

# Singleton instances
_ai_file_service_instance: Optional['AIFileService'] = None

def get_ai_file_service():
    """
    Get the AI file service instance.
    
    Returns:
        AIFileService instance
    """
    global _ai_file_service_instance
    if _ai_file_service_instance is None:
        # Lazy import - only load when actually needed
        from .ai_file_service import AIFileService
        _ai_file_service_instance = AIFileService()
    return _ai_file_service_instance

__all__ = ['get_ai_file_service'] 