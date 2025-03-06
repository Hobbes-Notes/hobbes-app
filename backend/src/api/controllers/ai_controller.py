"""
AI Controller Module

This controller provides endpoints for managing AI configurations.
These endpoints do not require authentication as they are used for system configuration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from ..models.ai import AIConfiguration, AIUseCase
from ..services.ai_service import AIService
from ..repositories.impl import get_ai_service
from ..models.api import APIResponse

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get AI service
def get_ai_service_dependency() -> AIService:
    """
    Get the AI service instance.
    """
    return get_ai_service()

@router.get("/configurations/{use_case}", response_model=APIResponse)
async def get_configurations(
    use_case: AIUseCase,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Get all configurations for a use case.
    """
    try:
        configurations = await ai_service.get_all_configurations(use_case)
        return APIResponse(
            success=True,
            data=configurations,
            message=f"Retrieved {len(configurations)} configurations for use case: {use_case}"
        )
    except Exception as e:
        logger.error(f"Error getting configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting configurations: {str(e)}"
        )

@router.get("/configurations/{use_case}/active", response_model=APIResponse)
async def get_active_configuration(
    use_case: AIUseCase,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Get the active configuration for a use case.
    """
    try:
        configuration = await ai_service.get_active_configuration(use_case)
        return APIResponse(
            success=True,
            data=configuration,
            message=f"Retrieved active configuration for use case: {use_case}"
        )
    except Exception as e:
        logger.error(f"Error getting active configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting active configuration: {str(e)}"
        )

@router.get("/configurations/{use_case}/{version}", response_model=APIResponse)
async def get_configuration(
    use_case: AIUseCase,
    version: int,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Get a specific configuration by use case and version.
    """
    try:
        configuration = await ai_service.get_configuration(use_case, version)
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found for use case: {use_case}, version: {version}"
            )
        
        return APIResponse(
            success=True,
            data=configuration,
            message=f"Retrieved configuration for use case: {use_case}, version: {version}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting configuration: {str(e)}"
        )

@router.post("/configurations", response_model=APIResponse)
async def create_configuration(
    configuration: AIConfiguration,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Create a new configuration. The version will be automatically generated regardless of the version provided in the input.
    """
    try:
        # Set created_at if not provided
        if not configuration.created_at:
            configuration.created_at = datetime.now().isoformat()
        
        # Create the configuration
        created_config = await ai_service.create_configuration(configuration)
        
        return APIResponse(
            success=True,
            data=created_config,
            message=f"Created configuration for use case: {configuration.use_case}, version: {configuration.version}"
        )
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating configuration: {str(e)}"
        )

@router.put("/configurations/{use_case}/{version}/activate", response_model=APIResponse)
async def set_active_configuration(
    use_case: AIUseCase,
    version: int,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Set a configuration as active.
    """
    try:
        # Set the configuration as active
        updated_config = await ai_service.set_active_configuration(use_case, version)
        
        return APIResponse(
            success=True,
            data=updated_config,
            message=f"Set configuration as active for use case: {use_case}, version: {version}"
        )
    except Exception as e:
        logger.error(f"Error setting active configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting active configuration: {str(e)}"
        )

@router.delete("/configurations/{use_case}/{version}", response_model=APIResponse)
async def delete_configuration(
    use_case: AIUseCase,
    version: int,
    ai_service: AIService = Depends(get_ai_service_dependency)
):
    """
    Delete a configuration.
    """
    try:
        # Delete the configuration
        success = await ai_service.delete_configuration(use_case, version)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not delete configuration. It may be active or not exist."
            )
        
        return APIResponse(
            success=True,
            data=None,
            message=f"Deleted configuration for use case: {use_case}, version: {version}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting configuration: {str(e)}"
        ) 