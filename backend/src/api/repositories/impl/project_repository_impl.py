"""
Project Repository Implementation

This module provides a DynamoDB implementation of the project repository interface.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException

from ...repositories.project_repository import ProjectRepository
from ...models.project import Project, ProjectCreate
from ...models.pagination import PaginatedResponse, PaginationParams
from infrastructure.dynamodb_client import get_dynamodb_client

# Set up logging
logger = logging.getLogger(__name__)

class DynamoDBProjectRepository(ProjectRepository):
    """
    DynamoDB implementation of the project repository interface.
    """
    
    def __init__(self):
        """
        Initialize the DynamoDBProjectRepository with a DynamoDB client.
        """
        self.dynamodb_client = get_dynamodb_client()
        self.table_name = 'Projects'
        
        # Get table resource for convenience
        self.projects_table = self.dynamodb_client.get_table_resource(self.table_name)
    
    async def create_table(self) -> None:
        """
        Create the Projects table if it doesn't exist.
        """
        if not self.dynamodb_client.table_exists(self.table_name):
            logger.info(f"Creating {self.table_name} table...")
            self.dynamodb_client.create_table(
                table_name=self.table_name,
                key_schema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                provisioned_throughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"{self.table_name} table created successfully")
            
            # Wait for the table to be active
            self.dynamodb_client.get_client().get_waiter('table_exists').wait(TableName=self.table_name)
            logger.info(f"{self.table_name} table is now active")
        else:
            logger.info(f"{self.table_name} table already exists")
    
    def _dict_to_project(self, data: Dict) -> Optional[Project]:
        """
        Convert a dictionary to a Project domain model.
        
        Args:
            data: Dictionary containing project data
            
        Returns:
            Project domain model or None if data is None
        """
        if not data:
            return None
        
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Expected dictionary but got {type(data)}: {data}")
            return None
            
        return Project(**data)
    
    async def get_by_id(self, id: str) -> Optional[Project]:
        """
        Get a project by its ID.
        
        Args:
            id: The unique identifier of the project
            
        Returns:
            The project as a Project domain model if found, None otherwise
        """
        try:
            item = self.dynamodb_client.get_item(table_name=self.table_name, key={'id': id})
            return self._dict_to_project(item)
        except Exception as e:
            logger.error(f"Error getting project with ID {id}: {str(e)}")
            return None
    
    async def create(self, data: ProjectCreate) -> Project:
        """
        Create a new project.
        
        Args:
            data: The project data to create
            
        Returns:
            The created project as a Project domain model
        """
        try:
            # Convert to dictionary if it's a Pydantic model
            if hasattr(data, 'dict'):
                data_dict = data.dict()
            else:
                data_dict = dict(data)
                
            # Generate a unique ID and timestamp if not provided
            if 'id' not in data_dict:
                data_dict['id'] = str(uuid.uuid4())
            if 'created_at' not in data_dict:
                data_dict['created_at'] = datetime.utcnow().isoformat()
            
            # Save to DynamoDB
            self.dynamodb_client.put_item(table_name=self.table_name, item=data_dict)
            
            return self._dict_to_project(data_dict)
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update(self, id: str, data: Dict) -> Optional[Project]:
        """
        Update an existing project.
        
        Args:
            id: The unique identifier of the project
            data: The updated data
            
        Returns:
            The updated project as a Project domain model if found, None otherwise
        """
        try:
            # Check if project exists
            project = await self.get_by_id(id)
            if not project:
                return None
            
            # Update the project
            update_expression = "set "
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for key, value in data.items():
                if key != 'id':  # Don't update the ID
                    update_expression += f"#{key} = :{key}, "
                    expression_attribute_values[f":{key}"] = value
                    expression_attribute_names[f"#{key}"] = key
            
            # Remove trailing comma and space
            update_expression = update_expression[:-2]
            
            # Update the item
            response = self.dynamodb_client.update_item(
                table_name=self.table_name,
                key={'id': id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
                expression_attribute_names=expression_attribute_names,
                return_values="ALL_NEW"
            )
            
            return self._dict_to_project(response.get('Attributes'))
        except Exception as e:
            logger.error(f"Error updating project {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """
        Delete a project by its ID.
        
        Args:
            id: The unique identifier of the project
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Check if project exists
            project = await self.get_by_id(id)
            if not project:
                return False
            
            # Delete the project
            self.dynamodb_client.delete_item(table_name=self.table_name, key={'id': id})
            
            return True
        except Exception as e:
            logger.error(f"Error deleting project {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_projects_by_user(self, user_id: str) -> List[Project]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of Project domain models
        """
        try:
            # Scan for projects with the given user_id
            response = self.dynamodb_client.scan(
                table_name=self.table_name,
                filter_expression="user_id = :user_id",
                expression_attribute_values={":user_id": user_id}
            )
            
            # Ensure we have items in the response
            if not isinstance(response, dict) or 'Items' not in response:
                logger.error(f"Unexpected response format: {response}")
                return []
            
            # Convert to Project domain models
            projects = []
            for item in response['Items']:
                project = self._dict_to_project(item)
                if project:
                    projects.append(project)
            
            return projects
        except Exception as e:
            logger.error(f"Error getting projects for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_or_create_misc_project(self, user_id: str) -> Project:
        """
        Get or create a miscellaneous project for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project as a Project domain model
        """
        try:
            # Scan for Miscellaneous project
            items = self.dynamodb_client.scan(
                table_name=self.table_name,
                filter_expression="user_id = :user_id AND #name = :name",
                expression_attribute_names={"#name": "name"},
                expression_attribute_values={":user_id": user_id, ":name": "Miscellaneous"}
            )
            
            # If found, return the first one
            if items:
                return self._dict_to_project(items[0])
            
            # Otherwise, create a new one
            misc_project = {
                "id": str(uuid.uuid4()),
                "name": "Miscellaneous",
                "description": "Default project for uncategorized notes",
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save to DynamoDB
            self.dynamodb_client.put_item(table_name=self.table_name, item=misc_project)
            
            return self._dict_to_project(misc_project)
        except Exception as e:
            logger.error(f"Error getting or creating miscellaneous project: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def delete_project_with_descendants(self, project_id: str) -> Dict:
        """
        Delete a project and all its descendants.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            A message indicating the result of the operation
        """
        try:
            # Get the project to delete
            project = await self.get_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Get all descendant project IDs
            descendant_ids = []
            
            def get_descendant_ids(parent_id):
                # Scan for child projects
                response = self.dynamodb_client.scan(
                    table_name=self.table_name,
                    filter_expression="parent_id = :parent_id",
                    expression_attribute_values={":parent_id": parent_id}
                )
                
                for child in response.get('Items', []):
                    child_id = child['id']
                    descendant_ids.append(child_id)
                    # Recursively get descendants
                    get_descendant_ids(child_id)
            
            # Start the recursive search
            get_descendant_ids(project_id)
            
            # Delete all descendant projects
            for descendant_id in descendant_ids:
                self.dynamodb_client.delete_item(table_name=self.table_name, key={'id': descendant_id})
                logger.info(f"Deleted descendant project {descendant_id}")
            
            # Delete the project itself
            self.dynamodb_client.delete_item(table_name=self.table_name, key={'id': project_id})
            logger.info(f"Deleted project {project_id}")
            
            # Return a success message
            return {
                "message": f"Project {project_id} and {len(descendant_ids)} descendant projects deleted successfully"
            }
        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise e
        except Exception as e:
            logger.error(f"Error deleting project {project_id} with descendants: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 