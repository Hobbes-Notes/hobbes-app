"""
Services Package

This package provides service implementations for the application.
"""

from typing import Optional

from .ai_file_service import AIFileService
from ..repositories.impl import get_ai_file_repository, get_ai_file_s3_repository, get_ai_service

# Singleton instances
_ai_file_service_instance: Optional[AIFileService] = None

def get_ai_file_service() -> AIFileService:
    """
    Get the AI file service instance.
    
    Returns:
        AIFileService instance
    """
    global _ai_file_service_instance
    
    if _ai_file_service_instance is None:
        _ai_file_service_instance = AIFileService(
            ai_file_repository=get_ai_file_repository(),
            s3_repository=get_ai_file_s3_repository(),
            ai_service=get_ai_service()
        )
        
    return _ai_file_service_instance 