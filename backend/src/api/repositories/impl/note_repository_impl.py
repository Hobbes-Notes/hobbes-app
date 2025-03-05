"""
Note Repository Implementation

This module provides a DynamoDB implementation of the note repository interface.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException

from ...repositories.note_repository import NoteRepository
from ...models.note import Note, NoteCreate, NoteUpdate
from ...models.pagination import PaginatedResponse, PaginationParams
from ...models.project import ProjectRef
from infrastructure.dynamodb_client import get_dynamodb_client

# Set up logging
logger = logging.getLogger(__name__)

class DynamoDBNoteRepository(NoteRepository):
    """
    DynamoDB implementation of the note repository interface.
    """
    
    def __init__(self):
        """
        Initialize the DynamoDBNoteRepository with a DynamoDB client.
        """
        self.dynamodb_client = get_dynamodb_client()
        self.table_name = 'Notes'
        self.project_notes_table_name = 'ProjectNotes'
        self.projects_table_name = 'Projects'
        
        # Get table resources for convenience
        self.notes_table = self.dynamodb_client.get_table_resource(self.table_name)
        self.project_notes_table = self.dynamodb_client.get_table_resource(self.project_notes_table_name)
        self.projects_table = self.dynamodb_client.get_table_resource(self.projects_table_name)
    
    async def create_table(self) -> None:
        """
        Create the Notes table if it doesn't exist.
        """
        if not self.dynamodb_client.table_exists(self.table_name):
            logger.info(f"Creating {self.table_name} table...")
            self.dynamodb_client.create_table(
                table_name=self.table_name,
                key_schema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                global_secondary_indexes=[
                    {
                        'IndexName': 'user_id-created_at-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
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

        # Create ProjectNotes mapping table if it doesn't exist
        if not self.dynamodb_client.table_exists(self.project_notes_table_name):
            logger.info(f"Creating {self.project_notes_table_name} mapping table...")
            self.dynamodb_client.create_table(
                table_name=self.project_notes_table_name,
                key_schema=[
                    {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'},
                    {'AttributeName': 'note_id', 'AttributeType': 'S'}
                ],
                global_secondary_indexes=[
                    {
                        'IndexName': 'note_id-index',
                        'KeySchema': [
                            {'AttributeName': 'note_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                provisioned_throughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"{self.project_notes_table_name} mapping table created successfully")
            
            # Wait for the table to be active
            self.dynamodb_client.get_client().get_waiter('table_exists').wait(TableName=self.project_notes_table_name)
            logger.info(f"{self.project_notes_table_name} table is now active")
        else:
            logger.info(f"{self.project_notes_table_name} table already exists")
    
    def _dict_to_note(self, data: Dict) -> Note:
        """
        Convert a dictionary to a Note model.
        
        Args:
            data: Dictionary containing note data
            
        Returns:
            Note model
        """
        return Note(**data)
    
    def _note_to_dict(self, note: Note) -> Dict:
        """
        Convert a Note model to a dictionary.
        
        Args:
            note: Note model
            
        Returns:
            Dictionary representation of the note
        """
        return note.dict()
    
    def _dict_to_project_ref(self, data: Dict) -> ProjectRef:
        """
        Convert a dictionary to a ProjectRef model.
        
        Args:
            data: Dictionary containing project reference data
            
        Returns:
            ProjectRef model
        """
        return ProjectRef(**data)
    
    async def get_by_id(self, id: str) -> Optional[Note]:
        """
        Get a note by its ID.
        
        Args:
            id: The unique identifier of the note
            
        Returns:
            The note if found, None otherwise
        """
        try:
            item = self.dynamodb_client.get_item(table_name=self.table_name, key={'id': id})
            if not item:
                return None
                
            # Add project references
            item['projects'] = await self.get_projects_for_note(id)
            
            return self._dict_to_note(item)
        except Exception as e:
            logger.error(f"Error getting note with ID {id}: {str(e)}")
            return None
    
    async def create(self, data: NoteCreate) -> Note:
        """
        Create a new note.
        
        Args:
            data: The note data to create (NoteCreate object or dict)
            
        Returns:
            The created note
        """
        try:
            # Convert model to dict if it's not already a dict
            if hasattr(data, 'dict'):
                note_dict = data.dict()
            else:
                note_dict = dict(data)
            
            # Generate a unique ID and timestamp if not provided
            note_dict['id'] = note_dict.get('id', str(uuid.uuid4()))
            if 'created_at' not in note_dict:
                note_dict['created_at'] = datetime.utcnow().isoformat()
            
            # Save to DynamoDB
            self.dynamodb_client.put_item(table_name=self.table_name, item=note_dict)
            
            # Initialize projects list if not present
            note_dict['projects'] = note_dict.get('projects', [])
            
            return self._dict_to_note(note_dict)
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update(self, id: str, data: NoteUpdate) -> Optional[Note]:
        """
        Update an existing note.
        
        Args:
            id: The unique identifier of the note
            data: The updated data
            
        Returns:
            The updated note if found, None otherwise
        """
        try:
            # Check if note exists
            note = await self.get_by_id(id)
            if not note:
                return None
            
            # Convert model to dict
            update_dict = data.dict(exclude_unset=True)
            
            # Update the note
            update_expression = "set "
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for key, value in update_dict.items():
                if key != 'id' and key != 'projects':  # Don't update the ID or projects
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
            
            updated_note_dict = response.get('Attributes', {})
            
            # Add project references
            updated_note_dict['projects'] = await self.get_projects_for_note(id)
            
            return self._dict_to_note(updated_note_dict)
        except Exception as e:
            logger.error(f"Error updating note {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """
        Delete a note by its ID.
        
        Args:
            id: The unique identifier of the note
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Check if note exists
            note = await self.get_by_id(id)
            if not note:
                return False
            
            # Delete the note
            self.dynamodb_client.delete_item(table_name=self.table_name, key={'id': id})
            
            # Delete project-note associations
            response = self.dynamodb_client.scan(
                table_name=self.project_notes_table_name,
                filter_expression="note_id = :note_id",
                expression_attribute_values={":note_id": id}
            )
            
            for item in response.get('Items', []):
                self.dynamodb_client.delete_item(
                    table_name=self.project_notes_table_name,
                    key={
                        'project_id': item['project_id'],
                        'created_at': item['created_at']
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error deleting note {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_projects_for_note(self, note_id: str) -> List[ProjectRef]:
        """
        Get all projects associated with a note.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            List of project references
        """
        try:
            # Query the ProjectNotes table for associations
            response = self.dynamodb_client.scan(
                table_name=self.project_notes_table_name,
                filter_expression="note_id = :note_id",
                expression_attribute_values={":note_id": note_id}
            )
            
            project_refs = []
            for item in response.get('Items', []):
                # Get the project details
                project = self.dynamodb_client.get_item(
                    table_name=self.projects_table_name, 
                    key={'id': item['project_id']}
                )
                if project:
                    project_ref_dict = {
                        'id': project['id'],
                        'name': project['name']
                    }
                    project_refs.append(self._dict_to_project_ref(project_ref_dict))
            
            return project_refs
        except Exception as e:
            logger.error(f"Error getting projects for note {note_id}: {str(e)}")
            return []
    
    async def associate_note_with_project(self, note_id: str, project_id: str, timestamp: str) -> None:
        """
        Associate a note with a project.
        
        Args:
            note_id: The unique identifier of the note
            project_id: The unique identifier of the project
            timestamp: The timestamp of the association
        """
        try:
            # Create project-note association
            self.dynamodb_client.put_item(
                table_name=self.project_notes_table_name,
                item={
                    'project_id': project_id,
                    'note_id': note_id,
                    'created_at': timestamp
                }
            )
        except Exception as e:
            logger.error(f"Error associating note {note_id} with project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_notes_by_project(self, project_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        """
        Get paginated notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            pagination: Pagination parameters
            
        Returns:
            Paginated response containing Note objects and pagination metadata
        """
        try:
            page = pagination.page
            page_size = pagination.page_size
            exclusive_start_key = pagination.exclusive_start_key
            
            # Query the ProjectNotes table for the project
            if exclusive_start_key:
                response = self.dynamodb_client.query(
                    table_name=self.project_notes_table_name,
                    key_condition_expression="project_id = :project_id",
                    expression_attribute_values={":project_id": project_id},
                    scan_index_forward=False,  # Sort by created_at in descending order
                    limit=page_size,
                    exclusive_start_key=exclusive_start_key
                )
            else:
                response = self.dynamodb_client.query(
                    table_name=self.project_notes_table_name,
                    key_condition_expression="project_id = :project_id",
                    expression_attribute_values={":project_id": project_id},
                    scan_index_forward=False,  # Sort by created_at in descending order
                    limit=page_size
                )
            
            # Get the notes for each project-note association
            notes = []
            for item in response.get('Items', []):
                note_dict = self.dynamodb_client.get_item(
                    table_name=self.table_name, 
                    key={'id': item['note_id']}
                )
                if note_dict:
                    # Add project references
                    note_dict['projects'] = await self.get_projects_for_note(note_dict['id'])
                    notes.append(self._dict_to_note(note_dict))
            
            # Prepare the response
            return PaginatedResponse[Note](
                items=notes,
                page=page,
                page_size=page_size,
                has_more='LastEvaluatedKey' in response,
                last_evaluated_key=response.get('LastEvaluatedKey')
            )
        except Exception as e:
            logger.error(f"Error getting notes for project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_notes_by_user(self, user_id: str, pagination: PaginationParams) -> PaginatedResponse[Note]:
        """
        Get paginated notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            pagination: Pagination parameters
            
        Returns:
            Paginated response containing Note objects and pagination metadata
        """
        try:
            page = pagination.page
            page_size = pagination.page_size
            exclusive_start_key = pagination.exclusive_start_key
            
            # Query the Notes table for the user
            if exclusive_start_key:
                response = self.dynamodb_client.query(
                    table_name=self.table_name,
                    index_name='user_id-created_at-index',
                    key_condition_expression="user_id = :user_id",
                    expression_attribute_values={":user_id": user_id},
                    scan_index_forward=False,  # Sort by created_at in descending order
                    limit=page_size,
                    exclusive_start_key=exclusive_start_key
                )
            else:
                response = self.dynamodb_client.query(
                    table_name=self.table_name,
                    index_name='user_id-created_at-index',
                    key_condition_expression="user_id = :user_id",
                    expression_attribute_values={":user_id": user_id},
                    scan_index_forward=False,  # Sort by created_at in descending order
                    limit=page_size
                )
            
            # Add project references to each note
            notes = []
            for note_dict in response.get('Items', []):
                note_dict['projects'] = await self.get_projects_for_note(note_dict['id'])
                notes.append(self._dict_to_note(note_dict))
            
            # Prepare the response
            return PaginatedResponse[Note](
                items=notes,
                page=page,
                page_size=page_size,
                has_more='LastEvaluatedKey' in response,
                last_evaluated_key=response.get('LastEvaluatedKey')
            )
        except Exception as e:
            logger.error(f"Error getting notes for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 