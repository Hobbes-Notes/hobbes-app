"""
CapB Service Layer

This module provides CapB (Capability B) functionality for automatically tagging
action items with relevant projects based on semantic similarity.
"""

import logging
import json
import time
import traceback
from typing import Dict, List, Optional, TYPE_CHECKING
from tenacity import retry, stop_after_attempt, wait_exponential

from api.services.ai_service import AIService
from api.services.action_item_service import ActionItemService
from api.services.monitoring_service import MonitoringService
from api.models.action_item import ActionItemUpdate

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from api.services.project_service import ProjectService

# Set up logging
logger = logging.getLogger(__name__)

class CapBService:
    """
    Service for CapB - Automatic Project Tagging of Action Items.
    
    This service analyzes action items and projects to determine semantic
    relationships and automatically tags action items with relevant projects.
    """
    
    def __init__(
        self, 
        ai_service: AIService,
        action_item_service: ActionItemService,
        project_service: Optional['ProjectService'] = None,
        monitoring_service: Optional[MonitoringService] = None
    ):
        """
        Initialize the CapBService.
        
        Args:
            ai_service: Service for AI operations
            action_item_service: Service for action item operations
            project_service: Service for project operations (optional, set later for circular dependency)
            monitoring_service: Service for monitoring metrics (optional)
        """
        self.ai_service = ai_service
        self.action_item_service = action_item_service
        self.project_service = project_service
        self.monitoring_service = monitoring_service or MonitoringService()
        
        # Initialize in-memory metrics
        self._metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_action_items_processed": 0,
            "total_action_items_tagged": 0,
            "average_processing_time": 0,
            "error_counts": {}
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _update_action_item_with_retry(self, action_item_id: str, update_data: ActionItemUpdate) -> bool:
        """
        Update an action item with retry mechanism.
        
        Args:
            action_item_id: The action item ID to update
            update_data: The update data
            
        Returns:
            bool: True if successful, False otherwise
        """
        update_start = time.time()
        logger.debug(f"🔄 CapB RETRY: Starting attempt for action item {action_item_id}")
        logger.debug(f"🔄 CapB RETRY: Update data type: {type(update_data)}")
        logger.debug(f"🔄 CapB RETRY: Update data - projects: {update_data.projects}")
        logger.debug(f"🔄 CapB RETRY: Update data - task: {update_data.task}")
        logger.debug(f"🔄 CapB RETRY: Update data - status: {update_data.status}")
        
        try:
            # Log before calling action_item_service
            logger.debug(f"🔄 CapB RETRY: Calling action_item_service.update_action_item for {action_item_id}")
            service_call_start = time.time()
            
            result = await self.action_item_service.update_action_item(action_item_id, update_data)
            
            service_call_time = time.time() - service_call_start
            logger.debug(f"🔄 CapB RETRY: Service call completed in {service_call_time:.3f}s")
            logger.debug(f"🔄 CapB RETRY: Result type: {type(result)}")
            logger.debug(f"🔄 CapB RETRY: Result is None: {result is None}")
            
            if result:
                logger.debug(f"🔄 CapB RETRY: Result has projects attribute: {hasattr(result, 'projects')}")
                if hasattr(result, 'projects'):
                    logger.debug(f"🔄 CapB RETRY: Result projects: {result.projects}")
                else:
                    logger.error(f"❌ CapB RETRY: Result object missing 'projects' attribute!")
                    logger.error(f"❌ CapB RETRY: Result object attributes: {dir(result)}")
                
                update_time = time.time() - update_start
                logger.debug(f"✅ CapB RETRY: Successfully updated {action_item_id} in {update_time:.3f}s (service: {service_call_time:.3f}s)")
                return True
            else:
                update_time = time.time() - update_start
                logger.error(f"❌ CapB RETRY: Update returned None for {action_item_id} after {update_time:.3f}s")
                return False
            
        except Exception as e:
            update_time = time.time() - update_start
            error_type = type(e).__name__
            logger.error(f"❌ CapB RETRY: Exception in {action_item_id} after {update_time:.3f}s")
            logger.error(f"❌ CapB RETRY: Error type: {error_type}")
            logger.error(f"❌ CapB RETRY: Error message: {str(e)}")
            logger.error(f"❌ CapB RETRY: Error traceback: {traceback.format_exc()}")
            logger.error(f"❌ CapB RETRY: Update data was: {update_data}")
            raise  # Let retry handle it
    
    async def run_for_user(self, user_id: str) -> Dict[str, any]:
        """
        Run CapB for all action items of a user.
        
        This method gets all the user's action items and projects,
        uses AI to determine project associations, and updates the action items.
        
        Args:
            user_id: The user ID to run CapB for
            
        Returns:
            Dictionary with results:
            {
                "success": bool,
                "tagged_action_items": int,
                "total_action_items": int,
                "total_projects": int,
                "error": str (if any),
                "metrics": Dict[str, any]
            }
        """
        start_time = time.time()
        run_id = f"capb_{int(start_time)}_{user_id}"
        logger.info(f"🚀 CapB TIMING: Starting CapB run {run_id} for user {user_id}")
        
        # Safety check: ensure project_service is available
        if not self.project_service:
            logger.error("CapB TIMING: project_service not available (circular dependency not resolved)")
            return {
                "success": False,
                "tagged_action_items": 0, 
                "total_action_items": 0,
                "total_projects": 0,
                "error": "project_service not available",
                "metrics": self._metrics
            }
        
        self._metrics["total_runs"] += 1
        
        try:
            # Step 1: Get user's action items
            fetch_actions_start = time.time()
            logger.debug(f"CapB TIMING: Fetching action items for user {user_id}")
            action_items = await self.action_item_service.get_action_items_by_user(user_id)
            fetch_actions_time = time.time() - fetch_actions_start
            logger.info(f"⏱️ CapB TIMING: Fetching action items took {fetch_actions_time:.2f}s - Found {len(action_items)} items")
            
            # Step 2: Get user's projects
            fetch_projects_start = time.time()
            logger.debug(f"CapB TIMING: Fetching projects for user {user_id}")
            projects = await self.project_service.get_projects(user_id)
            fetch_projects_time = time.time() - fetch_projects_start
            logger.info(f"⏱️ CapB TIMING: Fetching projects took {fetch_projects_time:.2f}s - Found {len(projects)} projects")
            
            # Step 3: Early exit if no action items or projects
            if not action_items:
                total_time = time.time() - start_time
                logger.info(f"🏁 CapB TIMING: No action items found, completed in {total_time:.2f}s")
                result = {
                    "success": True,
                    "tagged_action_items": 0,
                    "total_action_items": 0,
                    "total_projects": len(projects),
                    "message": "No action items to tag",
                    "metrics": self._metrics
                }
                self.monitoring_service.update_capb_metrics(result)
                return result
            
            if not projects:
                total_time = time.time() - start_time
                logger.info(f"🏁 CapB TIMING: No projects found, completed in {total_time:.2f}s")
                result = {
                    "success": True,
                    "tagged_action_items": 0,
                    "total_action_items": len(action_items),
                    "total_projects": 0,
                    "message": "No projects available for tagging",
                    "metrics": self._metrics
                }
                self.monitoring_service.update_capb_metrics(result)
                return result
            
            # Step 4: Prepare data for AI service
            data_prep_start = time.time()
            logger.debug(f"CapB TIMING: Preparing data for AI analysis")
            action_items_data = [
                {
                    "id": item.id,
                    "task": item.task,
                    "doer": item.doer,
                    "theme": item.theme,
                    "context": item.context,
                    "extracted_entities": item.extracted_entities,
                    "type": item.type,
                    "current_projects": item.projects
                }
                for item in action_items
            ]
            
            projects_data = [
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "parent_id": project.parent_id
                }
                for project in projects
            ]
            data_prep_time = time.time() - data_prep_start
            logger.info(f"⏱️ CapB TIMING: Data preparation took {data_prep_time:.2f}s")
            
            # Step 5: Call AI service for project tagging
            ai_call_start = time.time()
            logger.info(f"🤖 CapB TIMING: Calling AI service to tag {len(action_items)} action items with {len(projects)} projects")
            project_mappings = await self.ai_service.tag_action_items_with_projects({
                "action_items": action_items_data,
                "user_projects": projects_data
            })
            ai_call_time = time.time() - ai_call_start
            logger.info(f"⏱️ CapB TIMING: AI service call took {ai_call_time:.2f}s - Returned mappings for {len(project_mappings)} action items")
            
            # Step 6: Update action items with project associations
            update_start = time.time()
            tagged_count = 0
            failed_updates = []
            
            logger.info(f"🔄 CapB UPDATE LOOP: Starting to process {len(project_mappings)} action item updates")
            
            for i, (action_item_id, project_ids) in enumerate(project_mappings.items(), 1):
                item_start = time.time()
                logger.info(f"🔄 CapB UPDATE LOOP: Processing item {i}/{len(project_mappings)}: {action_item_id}")
                
                try:
                    if project_ids:  # Only update if there are project associations
                        logger.info(f"🔄 CapB UPDATE LOOP: Item {action_item_id} needs tagging with projects: {project_ids}")
                        
                        # Update the action item with new project associations
                        update_data = ActionItemUpdate(projects=project_ids)
                        logger.debug(f"🔄 CapB UPDATE LOOP: Created ActionItemUpdate object for {action_item_id}")
                        
                        success = await self._update_action_item_with_retry(action_item_id, update_data)
                        
                        if success:
                            tagged_count += 1
                            item_time = time.time() - item_start
                            logger.info(f"✅ CapB UPDATE LOOP: Successfully tagged item {i}/{len(project_mappings)} ({action_item_id}) with {len(project_ids)} projects in {item_time:.3f}s")
                        else:
                            item_time = time.time() - item_start
                            logger.error(f"❌ CapB UPDATE LOOP: Failed to tag item {i}/{len(project_mappings)} ({action_item_id}) after {item_time:.3f}s")
                            failed_updates.append(action_item_id)
                    else:
                        item_time = time.time() - item_start
                        logger.info(f"⏭️ CapB UPDATE LOOP: Item {i}/{len(project_mappings)} ({action_item_id}) has no projects to tag - skipped in {item_time:.3f}s")
                        
                except Exception as e:
                    item_time = time.time() - item_start
                    error_type = type(e).__name__
                    self._metrics["error_counts"][error_type] = self._metrics["error_counts"].get(error_type, 0) + 1
                    logger.error(f"❌ CapB UPDATE LOOP: Exception in item {i}/{len(project_mappings)} ({action_item_id}) after {item_time:.3f}s")
                    logger.error(f"❌ CapB UPDATE LOOP: Error type: {error_type}, message: {str(e)}")
                    failed_updates.append(action_item_id)
                    continue
            
            update_time = time.time() - update_start
            logger.info(f"⏱️ CapB TIMING: Updating action items took {update_time:.2f}s - Tagged {tagged_count} items")
            
            # Update metrics
            self._metrics["total_action_items_processed"] += len(action_items)
            self._metrics["total_action_items_tagged"] += tagged_count
            processing_time = time.time() - start_time
            self._metrics["average_processing_time"] = (
                (self._metrics["average_processing_time"] * (self._metrics["total_runs"] - 1) + processing_time)
                / self._metrics["total_runs"]
            )
            
            # Step 7: Return success results
            success = len(failed_updates) == 0
            if success:
                self._metrics["successful_runs"] += 1
            else:
                self._metrics["failed_runs"] += 1
            
            total_time = time.time() - start_time
            logger.info(f"🏁 CapB TIMING: CapB completed in {total_time:.2f}s for user {user_id}: {tagged_count}/{len(action_items)} action items tagged")
            if failed_updates:
                logger.warning(f"⚠️ CapB TIMING: Had {len(failed_updates)} failed updates: {failed_updates}")
            
            result = {
                "success": success,
                "tagged_action_items": tagged_count,
                "total_action_items": len(action_items),
                "total_projects": len(projects),
                "failed_updates": failed_updates,
                "message": f"Successfully tagged {tagged_count} out of {len(action_items)} action items",
                "metrics": self._metrics
            }
            
            # Update monitoring service
            self.monitoring_service.update_capb_metrics(result)
            
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            self._metrics["error_counts"][error_type] = self._metrics["error_counts"].get(error_type, 0) + 1
            self._metrics["failed_runs"] += 1
            
            total_time = time.time() - start_time
            logger.error(f"❌ CapB TIMING: CapB failed after {total_time:.2f}s for user {user_id}: {str(e)}")
            logger.exception("CapB detailed error information:")
            
            result = {
                "success": False,
                "tagged_action_items": 0,
                "total_action_items": len(action_items) if 'action_items' in locals() else 0,
                "total_projects": len(projects) if 'projects' in locals() else 0,
                "error": str(e),
                "error_type": error_type,
                "metrics": self._metrics
            }
            
            # Update monitoring service with error
            self.monitoring_service.update_capb_metrics(result)
            
            return result
    
    def get_metrics(self, time_range: str = "all") -> Dict[str, any]:
        """
        Get CapB metrics for the specified time range.
        
        Args:
            time_range: Time range to get metrics for ("hour", "day", "week", "all")
            
        Returns:
            Dictionary containing CapB metrics
        """
        return self.monitoring_service.get_capb_metrics(time_range)
    
    def get_error_rates(self, time_range: str = "day") -> Dict[str, float]:
        """
        Get CapB error rates for the specified time range.
        
        Args:
            time_range: Time range to get error rates for ("hour", "day", "week")
            
        Returns:
            Dictionary containing error rates by type
        """
        return self.monitoring_service.get_capb_error_rates(time_range)
    
    def get_success_rate(self, time_range: str = "day") -> float:
        """
        Get CapB success rate for the specified time range.
        
        Args:
            time_range: Time range to get success rate for ("hour", "day", "week")
            
        Returns:
            Success rate as a float between 0 and 1
        """
        return self.monitoring_service.get_capb_success_rate(time_range) 