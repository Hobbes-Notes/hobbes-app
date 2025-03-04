"""
Note Service Layer

This module provides service-level functionality for note management,
including CRUD operations and note-specific business logic.
"""

import boto3
import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import HTTPException
from litellm import completion

from ..models.note import Note, NoteCreate
from .project_service import ProjectService

# Set up logging
logger = logging.getLogger(__name__)

class NoteService:
    """
    Service for managing notes in the system.
    
    This class handles all business logic related to notes, including
    creation, retrieval, and association with projects.
    """
    
    def __init__(self, dynamodb_resource=None, project_service=None):
        """
        Initialize the NoteService with DynamoDB resources and dependencies.
        
        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource. If not provided,
                               a new resource will be created using environment variables.
            project_service: Optional ProjectService instance. If not provided,
                             a new instance will be created.
        """
        self.dynamodb = dynamodb_resource or boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-2'),
            endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
        )
        self.notes_table = self.dynamodb.Table('Notes')
        self.project_notes_table = self.dynamodb.Table('ProjectNotes')
        self.projects_table = self.dynamodb.Table('Projects')
        self.project_service = project_service or ProjectService(self.dynamodb)
    
    async def get_note(self, note_id: str) -> Dict:
        """
        Get a note by its ID.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            The note data as a dictionary with associated projects
            
        Raises:
            HTTPException: If the note is not found
        """
        try:
            # Get the note
            response = self.notes_table.get_item(Key={'id': note_id})
            
            if 'Item' not in response:
                raise HTTPException(status_code=404, detail="Note not found")
                
            note = response['Item']
            
            # Get associated projects
            projects = await self._get_projects_for_note(note_id)
            note['projects'] = projects
            
            return note
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving note {note_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def _get_projects_for_note(self, note_id: str) -> List[Dict]:
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
    
    async def create_note(self, note_data: NoteCreate) -> Dict:
        """
        Create a new note and associate it with relevant projects.
        
        Args:
            note_data: The note data to create
            
        Returns:
            The created note as a dictionary with associated projects
        """
        try:
            # Generate a unique ID and timestamp
            note_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Create the note item
            note = {
                'id': note_id,
                'content': note_data.content,
                'created_at': timestamp,
                'user_id': note_data.user_id
            }
            
            # Save to DynamoDB
            self.notes_table.put_item(Item=note)
            
            # Get all user's projects to check relevance
            user_projects = await self.project_service.get_projects(note_data.user_id)
            
            # Check relevance for each project
            relevant_projects = []
            for project in user_projects:
                is_relevant = await self._check_project_relevance(note_data.content, project)
                if is_relevant:
                    relevant_projects.append(project)
                    
                    # Create project-note association
                    self.project_notes_table.put_item(Item={
                        'project_id': project['id'],
                        'note_id': note_id,
                        'created_at': timestamp
                    })
                    
                    # Update project summary
                    await self.project_service.update_project_summary(project, note_data.content)
            
            # If no relevant projects found, associate with Miscellaneous
            if not relevant_projects:
                misc_project = await self.project_service.get_or_create_misc_project(note_data.user_id)
                
                # Create project-note association
                self.project_notes_table.put_item(Item={
                    'project_id': misc_project['id'],
                    'note_id': note_id,
                    'created_at': timestamp
                })
                
                relevant_projects.append(misc_project)
            
            # Add project references to the note
            note['projects'] = [{'id': p['id'], 'name': p['name']} for p in relevant_projects]
            
            return note
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def _check_project_relevance(self, content: str, project: dict) -> bool:
        """
        Check if note content is relevant to a project using LLM.
        
        Args:
            content: The note content
            project: The project dictionary
            
        Returns:
            True if the note is relevant to the project, False otherwise
        """
        try:
            logger.info(f"Starting relevance check for project '{project['name']}'")
            
            prompt = f"""
            Determine if this note is relevant to the project. Answer ONLY with the word 'true' or 'false'.

            Project:
            - Name: {project['name']}
            - Description: {project.get('description', 'No description provided')}

            Note:
            {content}

            Rules:
            1. ONLY consider explicit information present in the note and project details
            2. Do NOT make assumptions or creative interpretations
            3. For job search projects, only consider actual job application activities
            4. Answer ONLY with 'true' or 'false', no other text

            Is this note relevant to this project?
            """
            
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = 'true' in response.choices[0].message.content.lower()
            logger.info(f"Relevance check result for project '{project['name']}': {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error in relevance check: {str(e)}")
            return False
    
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
                    note['projects'] = await self._get_projects_for_note(note['id'])
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
                note['projects'] = await self._get_projects_for_note(note['id'])
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
    
    def get_pagination_key(self, page: int, user_id: str) -> Optional[Dict]:
        """
        Get the pagination key for a specific page.
        
        This is a helper method for pagination.
        
        Args:
            page: The page number (1-indexed)
            user_id: The user ID for user-specific pagination
            
        Returns:
            The pagination key or None if it's the first page
        """
        if page <= 1:
            return None
            
        # For simplicity, we're not implementing actual pagination key retrieval
        # In a real implementation, you would store and retrieve pagination keys
        return None 