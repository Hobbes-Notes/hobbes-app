"""
AI Controller

Handles HTTP requests for AI configuration management operations.
Follows the three-things rule: parse input, call service, return response.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends
from typing import List, Dict, Any
from datetime import datetime
import json

from api.models.ai import AIConfiguration, AIUseCase
from api.services import get_ai_service
from api.services.ai_service import AIService
from api.models.api import APIResponse

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

# All endpoints use the centralized service factory via Depends(get_ai_service)

@router.get("/configurations/{use_case}", response_model=APIResponse)
async def get_configurations(
    request: Request,
    use_case: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get all configurations for a use case.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
            
        configurations = await ai_service.get_all_configurations(use_case_enum)
        
        return APIResponse(
            success=True,
            data=configurations,
            message=f"Retrieved {len(configurations)} configurations for use case: {use_case}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configurations: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting configurations: {str(e)}"
        )

@router.get("/configurations/{use_case}/active", response_model=APIResponse)
async def get_active_configuration(
    request: Request,
    use_case: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get the active configuration for a use case.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
        
        # Get active configuration
        logger.info(f"Getting active configuration for use case: {use_case}")
        configuration = await ai_service.get_active_configuration(use_case_enum)
        
        if not configuration:
            logger.warning(f"No active configuration found for use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active configuration found for use case: {use_case}"
            )
        
        return APIResponse(
            success=True,
            data=configuration,
            message=f"Retrieved active configuration for use case: {use_case}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active configuration: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting active configuration: {str(e)}"
        )

@router.get("/configurations/{use_case}/parameters", response_model=APIResponse)
async def get_available_parameters(
    request: Request,
    use_case: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get available parameters for a use case.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
        
        # Get parameter descriptions from the use case
        logger.info(f"Getting parameter descriptions for use case: {use_case}")
        param_descriptions = use_case_enum.param_descriptions
        logger.debug(f"Parameter descriptions: {json.dumps(param_descriptions, default=str)}")
        
        # Create a list of parameter objects with name and description
        parameters = [
            {"name": param, "description": description}
            for param, description in param_descriptions.items()
        ]
        logger.info(f"Found {len(parameters)} parameters for use case: {use_case}")
        
        return APIResponse(
            success=True,
            data=parameters,
            message=f"Retrieved available parameters for use case: {use_case}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available parameters: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available parameters: {str(e)}"
        )

@router.get("/configurations/{use_case}/response_format", response_model=APIResponse)
async def get_response_format(
    request: Request,
    use_case: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get the expected response format for a use case.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
        
        # Get response format from the use case
        logger.info(f"Getting response format for use case: {use_case}")
        response_format = use_case_enum.response_format
        logger.debug(f"Response format: {response_format}")
        
        return APIResponse(
            success=True,
            data=response_format,
            message=f"Retrieved response format for use case: {use_case}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting response format: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting response format: {str(e)}"
        )

@router.get("/configurations/{use_case}/{version}", response_model=APIResponse)
async def get_configuration(
    request: Request,
    use_case: str,
    version: int,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get a specific configuration by use case and version.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
            
        configuration = await ai_service.get_configuration(use_case_enum, version)
        
        if not configuration:
            logger.warning(f"Configuration not found for use case: {use_case}, version: {version}")
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
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting configuration: {str(e)}"
        )

@router.post("/configurations", response_model=APIResponse)
async def create_configuration(
    request: Request,
    configuration: AIConfiguration,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Create a new configuration. The version will be automatically generated regardless of the version provided in the input.
    """
    try:
        # Set created_at if not provided
        if not configuration.created_at:
            configuration.created_at = datetime.now().isoformat()
            logger.debug(f"Set created_at to {configuration.created_at}")
        
        logger.info(f"Creating configuration for use case: {configuration.use_case}")
        logger.debug(f"Configuration details: model={configuration.model}, max_tokens={configuration.max_tokens}, temperature={configuration.temperature}")
        
        # Create the configuration
        created_config = await ai_service.create_configuration(configuration)
        logger.info(f"Created configuration for use case: {created_config.use_case}, version: {created_config.version}")
        
        return APIResponse(
            success=True,
            data=created_config,
            message=f"Created configuration for use case: {configuration.use_case}, version: {created_config.version}"
        )
    except ValueError as e:
        # Handle validation errors specifically
        logger.warning(f"Validation error creating configuration: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating configuration: {str(e)}"
        )

@router.put("/configurations/{use_case}/{version}/activate", response_model=APIResponse)
async def set_active_configuration(
    request: Request,
    use_case: str,
    version: int,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Set a configuration as active.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
            
        # Set the configuration as active
        logger.info(f"Setting configuration as active for use case: {use_case}, version: {version}")
        updated_config = await ai_service.set_active_configuration(use_case_enum, version)
        logger.info(f"Configuration set as active for use case: {use_case}, version: {version}")
        
        return APIResponse(
            success=True,
            data=updated_config,
            message=f"Set configuration as active for use case: {use_case}, version: {version}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active configuration: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting active configuration: {str(e)}"
        )

@router.delete("/configurations/{use_case}/{version}", response_model=APIResponse)
async def delete_configuration(
    request: Request,
    use_case: str,
    version: int,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Delete a configuration.
    """
    try:
        # Convert string to AIUseCase enum
        try:
            use_case_enum = AIUseCase(use_case)
        except ValueError:
            logger.warning(f"Invalid use case: {use_case}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use case: {use_case}"
            )
            
        # Delete the configuration
        logger.info(f"Deleting configuration for use case: {use_case}, version: {version}")
        success = await ai_service.delete_configuration(use_case_enum, version)
        
        if not success:
            logger.warning(f"Could not delete configuration for use case: {use_case}, version: {version}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not delete configuration. It may be active or not exist."
            )
        
        logger.info(f"Deleted configuration for use case: {use_case}, version: {version}")
        
        return APIResponse(
            success=True,
            data=None,
            message=f"Deleted configuration for use case: {use_case}, version: {version}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration: {str(e)}")
        logger.exception("Detailed exception information:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting configuration: {str(e)}"
        ) 