"""
Project Service Layer

This module provides service-level functionality for project management,
including CRUD operations and project-specific business logic.
"""

import boto3
import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import HTTPException
from litellm import completion

from ..models.project import Project, ProjectCreate, ProjectUpdate

# Set up logging
logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service for managing projects in the system.
    
    This class handles all business logic related to projects, including
    creation, retrieval, updating, and deletion of projects.
    """
    
    def __init__(self, dynamodb_resource=None):
        """
        Initialize the ProjectService with DynamoDB resources.
        
        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource. If not provided,
                               a new resource will be created using environment variables.
        """
        self.dynamodb = dynamodb_resource or boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-2'),
            endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
        )
        self.projects_table = self.dynamodb.Table('Projects')
        self.project_notes_table = self.dynamodb.Table('ProjectNotes')
    
    async def get_project(self, project_id: str) -> Dict:
        """
        Get a project by its ID.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            The project data as a dictionary
            
        Raises:
            HTTPException: If the project is not found
        """
        try:
            response = self.projects_table.get_item(Key={'id': project_id})
            
            if 'Item' not in response:
                raise HTTPException(status_code=404, detail="Project not found")
                
            return response['Item']
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_projects(self, user_id: str) -> List[Dict]:
        """
        Get all projects for a user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of project dictionaries
        """
        try:
            # Scan for projects with the given user_id
            response = self.projects_table.scan(
                FilterExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id}
            )
            
            projects = response.get('Items', [])
            
            # Sort projects by creation date (newest first)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return projects
        except Exception as e:
            logger.error(f"Error retrieving projects for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def create_project(self, project_data: ProjectCreate) -> Dict:
        """
        Create a new project.
        
        Args:
            project_data: The project data to create
            
        Returns:
            The created project as a dictionary
        """
        try:
            # Generate a unique ID and timestamp
            project_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Validate parent project if specified
            if project_data.parent_id:
                try:
                    parent_project = await self.get_project(project_data.parent_id)
                    
                    # Calculate level based on parent
                    level = parent_project.get('level', 1) + 1
                    if level > 3:
                        raise HTTPException(
                            status_code=400, 
                            detail="Cannot create a project at level > 3. Maximum nesting depth reached."
                        )
                except HTTPException as e:
                    if e.status_code == 404:
                        raise HTTPException(status_code=400, detail="Parent project not found")
                    raise
            else:
                level = 1
            
            # Create the project item
            project = {
                'id': project_id,
                'name': project_data.name,
                'description': project_data.description or "",
                'summary': "",
                'created_at': timestamp,
                'user_id': project_data.user_id,
                'parent_id': project_data.parent_id,
                'level': level
            }
            
            # Save to DynamoDB
            self.projects_table.put_item(Item=project)
            
            return project
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update_project(self, project_id: str, project_update: ProjectUpdate) -> Dict:
        """
        Update a project.
        
        Args:
            project_id: The unique identifier of the project to update
            project_update: The project data to update
            
        Returns:
            The updated project as a dictionary
        """
        try:
            # Get the current project
            project = await self.get_project(project_id)
            
            # Build update expression
            update_expression = "SET "
            expression_attribute_values = {}
            
            # Add fields to update expression if they are provided
            if project_update.name is not None:
                update_expression += "name = :name, "
                expression_attribute_values[":name"] = project_update.name
                
            if project_update.description is not None:
                update_expression += "description = :description, "
                expression_attribute_values[":description"] = project_update.description
                
            if project_update.summary is not None:
                update_expression += "summary = :summary, "
                expression_attribute_values[":summary"] = project_update.summary
            
            # Remove trailing comma and space
            update_expression = update_expression.rstrip(", ")
            
            # Only update if there are changes
            if expression_attribute_values:
                self.projects_table.update_item(
                    Key={'id': project_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
            
            # Get the updated project
            updated_project = await self.get_project(project_id)
            return updated_project
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def delete_project(self, project_id: str) -> Dict:
        """
        Delete a project and all its child projects.
        
        Args:
            project_id: The unique identifier of the project to delete
            
        Returns:
            A dictionary with the result of the operation
        """
        try:
            # Get the project to delete
            project = await self.get_project(project_id)
            
            # Function to recursively get all descendant project IDs
            def get_descendant_ids(parent_id):
                # Scan for child projects
                response = self.projects_table.scan(
                    FilterExpression="parent_id = :parent_id",
                    ExpressionAttributeValues={":parent_id": parent_id}
                )
                
                # Get direct children
                children = response.get('Items', [])
                descendant_ids = [child['id'] for child in children]
                
                # Recursively get descendants of each child
                for child_id in list(descendant_ids):  # Create a copy to avoid modifying during iteration
                    descendant_ids.extend(get_descendant_ids(child_id))
                    
                return descendant_ids
            
            # Get all descendant project IDs
            descendant_ids = get_descendant_ids(project_id)
            all_project_ids = [project_id] + descendant_ids
            
            # Delete all projects
            for pid in all_project_ids:
                # Delete project
                self.projects_table.delete_item(Key={'id': pid})
                
                # Delete project-note associations
                # Note: This is a scan operation which is not efficient for large datasets
                # In a production environment, you might want to use a more efficient approach
                response = self.project_notes_table.scan(
                    FilterExpression="project_id = :project_id",
                    ExpressionAttributeValues={":project_id": pid}
                )
                
                for item in response.get('Items', []):
                    self.project_notes_table.delete_item(
                        Key={
                            'project_id': item['project_id'],
                            'created_at': item['created_at']
                        }
                    )
            
            return {"message": f"Project {project_id} and {len(descendant_ids)} child projects deleted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_or_create_misc_project(self, user_id: str) -> Dict:
        """
        Get or create a 'Miscellaneous' project for a user.
        
        This project is used for notes that don't match any specific project.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            The miscellaneous project as a dictionary
        """
        try:
            # Try to find an existing Miscellaneous project
            response = self.projects_table.scan(
                FilterExpression="user_id = :user_id AND #n = :name",
                ExpressionAttributeNames={
                    "#n": "name"
                },
                ExpressionAttributeValues={
                    ":user_id": user_id,
                    ":name": "Miscellaneous"
                }
            )
            
            items = response.get('Items', [])
            
            if items:
                return items[0]
            
            # Create a new Miscellaneous project
            project_data = ProjectCreate(
                name="Miscellaneous",
                description="Automatically created for notes that don't match any specific project",
                user_id=user_id
            )
            
            return await self.create_project(project_data)
        except Exception as e:
            logger.error(f"Error getting/creating misc project for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update_project_summary(self, project: Dict, new_note_content: str) -> Dict:
        """
        Update a project's summary with new note content.
        
        Args:
            project: The project dictionary to update
            new_note_content: The content of the new note
            
        Returns:
            The updated project dictionary
        """
        try:
            logger.info(f"Starting summary update for project '{project['name']}'")
            
            prompt = f"""
            Create a concise, well-structured summary combining the existing summary and new note.

            Current Summary:
            {project['summary']}

            New Note:
            {new_note_content}

            Strict Content Rules:
            1. Extract and summarize key points only - do not copy text verbatim
            2. Focus on concrete actions, decisions, and outcomes
            3. Use clear, concise language
            4. Combine similar points instead of listing them separately
            5. Keep only the most current/relevant information

            Required Markdown Structure:
            1. Each heading MUST start with '## ' (double hashtag + space)
            2. Add ONE blank line after each heading
            3. Each bullet point MUST start with '- ' (hyphen + space)
            4. Add ONE blank line between bullet points
            5. Add TWO blank lines between sections
            6. No paragraphs - use only headings and bullet points

            Remember:
            - NEVER include speculative or assumed information
            """
            
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            new_summary = response.choices[0].message.content.strip()
            logger.info(f"Generated new summary for project '{project['name']}'")
            
            # Update the project with the new summary
            update_expression = "SET summary = :summary"
            expression_attribute_values = {":summary": new_summary}
            
            self.projects_table.update_item(
                Key={'id': project['id']},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            # Get the updated project
            updated_project = await self.get_project(project['id'])
            return updated_project
        except Exception as e:
            logger.error(f"Error updating project summary: {str(e)}")
            # Return the original project if there's an error
            return project 