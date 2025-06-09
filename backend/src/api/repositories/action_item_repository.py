"""
Action Item Repository

This module provides data access layer for action items.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.models.action_item import ActionItem, ActionItemCreate, ActionItemUpdate
from infrastructure.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)

class ActionItemRepository:
    """Repository for action item data operations."""
    
    def __init__(self, dynamodb_client: DynamoDBClient):
        """
        Initialize the repository.
        
        Args:
            dynamodb_client: The DynamoDB client to use
        """
        self.dynamodb_client = dynamodb_client
        self.table_name = "action_items"
    
    async def create_action_item(self, action_item_data: ActionItemCreate) -> ActionItem:
        """
        Create a new action item.
        
        Args:
            action_item_data: The action item data
            
        Returns:
            The created action item
        """
        try:
            # Generate unique ID
            action_item_id = str(uuid.uuid4())
            current_time = datetime.utcnow().isoformat()
            
            # Create the action item record
            action_item_record = {
                "id": action_item_id,
                "task": action_item_data.task,
                "doer": action_item_data.doer,
                "deadline": action_item_data.deadline,
                "theme": action_item_data.theme,
                "context": action_item_data.context,
                "extracted_entities": action_item_data.extracted_entities,
                "status": action_item_data.status,
                "type": action_item_data.type,
                "projects": action_item_data.projects,
                "created_at": current_time,
                "updated_at": current_time,
                "user_id": action_item_data.user_id,
                "source_note_id": action_item_data.source_note_id
            }
            
            # Save to DynamoDB
            await self.dynamodb_client.put_item(self.table_name, action_item_record)
            
            logger.info(f"✅ Repository: Created action item {action_item_id} with source_note_id={action_item_record.get('source_note_id')}")
            return ActionItem(**action_item_record)
            
        except Exception as e:
            logger.error(f"Error creating action item: {str(e)}")
            raise
    
    async def get_action_item(self, action_item_id: str) -> Optional[ActionItem]:
        """
        Get an action item by ID.
        
        Args:
            action_item_id: The action item ID
            
        Returns:
            The action item if found, None otherwise
        """
        try:
            result = await self.dynamodb_client.get_item(
                self.table_name, 
                {"id": action_item_id}
            )
            
            if result:
                return ActionItem(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting action item {action_item_id}: {str(e)}")
            raise
    
    async def update_action_item(self, action_item_id: str, update_data: ActionItemUpdate) -> Optional[ActionItem]:
        """
        Update an action item.
        
        Args:
            action_item_id: The action item ID
            update_data: The update data
            
        Returns:
            The updated action item if found, None otherwise
        """
        try:
            # Get existing item first
            existing_item = await self.get_action_item(action_item_id)
            if not existing_item:
                return None
            
            # Prepare update expression and values
            update_expression_parts = []
            expression_attribute_values = {}
            
            # Build update expression for non-None fields
            if update_data.task is not None:
                update_expression_parts.append("task = :task")
                expression_attribute_values[":task"] = update_data.task
            
            if update_data.doer is not None:
                update_expression_parts.append("doer = :doer")
                expression_attribute_values[":doer"] = update_data.doer
            
            if update_data.deadline is not None:
                update_expression_parts.append("deadline = :deadline")
                expression_attribute_values[":deadline"] = update_data.deadline
            
            if update_data.theme is not None:
                update_expression_parts.append("theme = :theme")
                expression_attribute_values[":theme"] = update_data.theme
            
            if update_data.context is not None:
                update_expression_parts.append("context = :context")
                expression_attribute_values[":context"] = update_data.context
            
            if update_data.extracted_entities is not None:
                update_expression_parts.append("extracted_entities = :extracted_entities")
                expression_attribute_values[":extracted_entities"] = update_data.extracted_entities
            
            if update_data.status is not None:
                update_expression_parts.append("#status = :status")
                expression_attribute_values[":status"] = update_data.status
                
            if update_data.type is not None:
                update_expression_parts.append("#type = :type")
                expression_attribute_values[":type"] = update_data.type
            
            if update_data.projects is not None:
                update_expression_parts.append("projects = :projects")
                expression_attribute_values[":projects"] = update_data.projects
            
            if update_data.source_note_id is not None:
                update_expression_parts.append("source_note_id = :source_note_id")
                expression_attribute_values[":source_note_id"] = update_data.source_note_id
            
            # Always update the updated_at timestamp
            update_expression_parts.append("updated_at = :updated_at")
            expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
            
            if not update_expression_parts:
                return existing_item
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            # Use expression attribute names for reserved keywords
            expression_attribute_names = {
                "#status": "status",
                "#type": "type"
            }
            
            await self.dynamodb_client.update_item(
                self.table_name,
                {"id": action_item_id},
                update_expression,
                expression_attribute_values,
                expression_attribute_names
            )
            
            # Return updated item
            return await self.get_action_item(action_item_id)
            
        except Exception as e:
            logger.error(f"Error updating action item {action_item_id}: {str(e)}")
            raise
    
    async def get_action_items_by_user(self, user_id: str) -> List[ActionItem]:
        """
        Get all action items for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of action items
        """
        try:
            # Query by user_id (assuming we have a GSI on user_id)
            result = self.dynamodb_client.query(
                self.table_name,
                index_name="user_id-index",
                key_condition_expression="user_id = :user_id",
                expression_attribute_values={":user_id": user_id}
            )
            
            action_items = []
            for item in result.get("Items", []):
                action_items.append(ActionItem(**item))
            
            return action_items
            
        except Exception as e:
            logger.error(f"Error getting action items for user {user_id}: {str(e)}")
            raise
    
    async def get_action_items_by_project(self, project_id: str, user_id: str) -> List[ActionItem]:
        """
        Get action items for a specific project.
        
        Args:
            project_id: The project ID
            user_id: The user ID
            
        Returns:
            List of action items for the project
        """
        try:
            # Get all user's action items and filter by project
            all_action_items = await self.get_action_items_by_user(user_id)
            
            # Filter by project ID
            project_action_items = [
                item for item in all_action_items 
                if project_id in item.projects
            ]
            
            return project_action_items
            
        except Exception as e:
            logger.error(f"Error getting action items for project {project_id}: {str(e)}")
            raise
    
    async def delete_action_item(self, action_item_id: str) -> bool:
        """
        Delete an action item.
        
        Args:
            action_item_id: The action item ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if item exists first
            existing_item = await self.get_action_item(action_item_id)
            if not existing_item:
                return False
            
            await self.dynamodb_client.delete_item(
                self.table_name,
                {"id": action_item_id}
            )
            
            logger.info(f"Deleted action item: {action_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting action item {action_item_id}: {str(e)}")
            raise
    
    async def create_table(self) -> None:
        """
        Create the action items table if it doesn't exist.
        """
        try:
            # Check if table already exists
            if self.dynamodb_client.table_exists(self.table_name):
                logger.info(f"Action items table '{self.table_name}' already exists")
                return
            
            # Define table schema parameters
            key_schema = [
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ]
            
            attribute_definitions = [
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                }
            ]
            
            global_secondary_indexes = [
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ]
            
            # Create table using existing client method
            self.dynamodb_client.create_table(
                table_name=self.table_name,
                key_schema=key_schema,
                attribute_definitions=attribute_definitions,
                global_secondary_indexes=global_secondary_indexes,
                provisioned_throughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be active
            self.dynamodb_client.get_client().get_waiter('table_exists').wait(TableName=self.table_name)
            logger.info(f"Action items table '{self.table_name}' created successfully")
            
        except Exception as e:
            logger.error(f"Error creating action items table: {str(e)}")
            raise 