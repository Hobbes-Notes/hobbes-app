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
from ...repositories.database_repository import DatabaseRepository

# Set up logging
logger = logging.getLogger(__name__)

class DynamoDBNoteRepository(NoteRepository):
    """
    DynamoDB implementation of the note repository interface.
    """
    
    def __init__(self, database_repository: DatabaseRepository):
        """
        Initialize the DynamoDBNoteRepository with a database repository.
        
        Args:
            database_repository: The database repository to use for data access
        """
        self.database_repository = database_repository
        self.notes_table = database_repository.get_table('Notes')
        self.project_notes_table = database_repository.get_table('ProjectNotes')
        self.projects_table = database_repository.get_table('Projects')
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """
        Get a note by its ID.
        
        Args:
            id: The unique identifier of the note
            
        Returns:
            The note data as a dictionary if found, None otherwise
        """
        try:
            response = self.notes_table.get_item(Key={'id': id})
            
            if 'Item' not in response:
                return None
            
            note = response['Item']
            
            # Add project references
            note['projects'] = await self.get_projects_for_note(note['id'])
            
            return note
        except Exception as e:
            logger.error(f"Error retrieving note {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def create(self, data: Dict) -> Dict:
        """
        Create a new note.
        
        Args:
            data: The note data to create
            
        Returns:
            The created note as a dictionary
        """
        try:
            # Generate a unique ID and timestamp if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            
            # Save to DynamoDB
            self.notes_table.put_item(Item=data)
            
            # Initialize projects list if not present
            if 'projects' not in data:
                data['projects'] = []
            
            return data
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update(self, id: str, data: Dict) -> Optional[Dict]:
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
            
            # Update the note
            update_expression = "set "
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for key, value in data.items():
                if key != 'id' and key != 'projects':  # Don't update the ID or projects
                    update_expression += f"#{key} = :{key}, "
                    expression_attribute_values[f":{key}"] = value
                    expression_attribute_names[f"#{key}"] = key
            
            # Remove trailing comma and space
            update_expression = update_expression[:-2]
            
            # Update the item
            response = self.notes_table.update_item(
                Key={'id': id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names,
                ReturnValues="ALL_NEW"
            )
            
            updated_note = response.get('Attributes', {})
            
            # Add project references
            updated_note['projects'] = await self.get_projects_for_note(id)
            
            return updated_note
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
            self.notes_table.delete_item(Key={'id': id})
            
            # Delete project-note associations
            response = self.project_notes_table.scan(
                FilterExpression="note_id = :note_id",
                ExpressionAttributeValues={":note_id": id}
            )
            
            for item in response.get('Items', []):
                self.project_notes_table.delete_item(
                    Key={
                        'project_id': item['project_id'],
                        'created_at': item['created_at']
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error deleting note {id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_projects_for_note(self, note_id: str) -> List[Dict]:
        """
        Get all projects associated with a note.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            List of project reference dictionaries (id and name)
        """
        try:
            # Query the ProjectNotes table for associations
            response = self.project_notes_table.scan(
                FilterExpression="note_id = :note_id",
                ExpressionAttributeValues={":note_id": note_id}
            )
            
            project_refs = []
            for item in response.get('Items', []):
                # Get the project details
                project_response = self.projects_table.get_item(Key={'id': item['project_id']})
                if 'Item' in project_response:
                    project = project_response['Item']
                    project_refs.append({
                        'id': project['id'],
                        'name': project['name']
                    })
            
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
            self.project_notes_table.put_item(Item={
                'project_id': project_id,
                'note_id': note_id,
                'created_at': timestamp
            })
        except Exception as e:
            logger.error(f"Error associating note {note_id} with project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_notes_by_project(self, project_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> Dict:
        """
        Get paginated notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            Dictionary with paginated notes and pagination metadata
        """
        try:
            # Query the ProjectNotes table for the project
            if exclusive_start_key:
                response = self.project_notes_table.query(
                    KeyConditionExpression="project_id = :project_id",
                    ExpressionAttributeValues={":project_id": project_id},
                    ScanIndexForward=False,  # Sort by created_at in descending order
                    Limit=page_size,
                    ExclusiveStartKey=exclusive_start_key
                )
            else:
                response = self.project_notes_table.query(
                    KeyConditionExpression="project_id = :project_id",
                    ExpressionAttributeValues={":project_id": project_id},
                    ScanIndexForward=False,  # Sort by created_at in descending order
                    Limit=page_size
                )
            
            # Get the notes for each project-note association
            notes = []
            for item in response.get('Items', []):
                note_response = self.notes_table.get_item(Key={'id': item['note_id']})
                if 'Item' in note_response:
                    note = note_response['Item']
                    # Add project references
                    note['projects'] = await self.get_projects_for_note(note['id'])
                    notes.append(note)
            
            # Prepare the response
            result = {
                'items': notes,
                'page': page,
                'page_size': page_size,
                'has_more': 'LastEvaluatedKey' in response,
                'LastEvaluatedKey': response.get('LastEvaluatedKey')
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting notes for project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_notes_by_user(self, user_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> Dict:
        """
        Get paginated notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            Dictionary with paginated notes and pagination metadata
        """
        try:
            # Query the Notes table for the user
            if exclusive_start_key:
                response = self.notes_table.query(
                    IndexName='user_id-created_at-index',
                    KeyConditionExpression="user_id = :user_id",
                    ExpressionAttributeValues={":user_id": user_id},
                    ScanIndexForward=False,  # Sort by created_at in descending order
                    Limit=page_size,
                    ExclusiveStartKey=exclusive_start_key
                )
            else:
                response = self.notes_table.query(
                    IndexName='user_id-created_at-index',
                    KeyConditionExpression="user_id = :user_id",
                    ExpressionAttributeValues={":user_id": user_id},
                    ScanIndexForward=False,  # Sort by created_at in descending order
                    Limit=page_size
                )
            
            # Add project references to each note
            notes = []
            for note in response.get('Items', []):
                note['projects'] = await self.get_projects_for_note(note['id'])
                notes.append(note)
            
            # Prepare the response
            result = {
                'items': notes,
                'page': page,
                'page_size': page_size,
                'has_more': 'LastEvaluatedKey' in response,
                'LastEvaluatedKey': response.get('LastEvaluatedKey')
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting notes for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 