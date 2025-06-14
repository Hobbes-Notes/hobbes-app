"""
Action Item Controller

Handles HTTP requests for action item management operations.
Follows the three-things rule: parse input, call service, return response.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional

from api.models.action_item import ActionItem, ActionItemCreate, ActionItemUpdate
from api.services import get_action_item_service
from api.services.action_item_service import ActionItemService
from api.models.api import APIResponse
from api.controllers.auth_controller import get_current_user
from api.models.user import User

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/action-items",
    tags=["action-items"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=APIResponse)
async def get_action_items(
    request: Request,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Get all action items for the current user.
    """
    try:
        action_items = await action_item_service.get_action_items_by_user(current_user.id)
        
        return APIResponse(
            success=True,
            data=action_items,
            message=f"Retrieved {len(action_items)} action items"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting action items: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=APIResponse)
async def get_action_items_by_project(
    request: Request,
    project_id: str,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Get action items for a specific project.
    """
    try:
        action_items = await action_item_service.get_action_items_by_project(project_id, current_user.id)
        
        return APIResponse(
            success=True,
            data=action_items,
            message=f"Retrieved {len(action_items)} action items for project {project_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action items for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting action items: {str(e)}"
        )

@router.post("", response_model=APIResponse)
async def create_action_item(
    request: Request,
    action_item_data: ActionItemCreate,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Create a new action item.
    """
    try:
        # Set user_id from current user
        action_item_data.user_id = current_user.id
        
        action_item = await action_item_service.create_action_item(action_item_data)
        
        return APIResponse(
            success=True,
            data=action_item,
            message="Action item created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating action item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating action item: {str(e)}"
        )

@router.put("/{action_item_id}", response_model=APIResponse)
async def update_action_item(
    request: Request,
    action_item_id: str,
    update_data: ActionItemUpdate,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Update an action item.
    """
    try:
        action_item = await action_item_service.update_action_item(action_item_id, update_data)
        
        if not action_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action item not found"
            )
        
        return APIResponse(
            success=True,
            data=action_item,
            message="Action item updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating action item {action_item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating action item: {str(e)}"
        )

@router.delete("/{action_item_id}", response_model=APIResponse)
async def delete_action_item(
    request: Request,
    action_item_id: str,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Delete an action item.
    """
    try:
        deleted = await action_item_service.delete_action_item(action_item_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action item not found"
            )
        
        return APIResponse(
            success=True,
            data=None,
            message="Action item deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting action item {action_item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting action item: {str(e)}"
        )

@router.post("/retag-projects", response_model=APIResponse)
async def retag_action_items_with_projects(
    request: Request,
    current_user: User = Depends(get_current_user),
    action_item_service: ActionItemService = Depends(get_action_item_service)
):
    """
    Manually trigger CapB to retag all action items with projects.
    This is useful for backfilling project associations on existing action items.
    """
    try:
        # Import CapB service here to avoid circular imports
        from api.services import get_capb_service
        capb_service = get_capb_service()
        
        # Run CapB for the current user
        logger.info(f"Manual CapB trigger requested by user {current_user.id}")
        result = await capb_service.run_for_user(current_user.id)
        
        return APIResponse(
            success=result["success"],
            data=result,
            message=result.get("message", "CapB processing completed")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running CapB for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retagging action items: {str(e)}"
        ) 