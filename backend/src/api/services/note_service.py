"""
Note Service Layer

This module provides service-level functionality for note management,
including CRUD operations and note-specific business logic.
"""

import logging
from typing import List, Optional, Dict
from fastapi import HTTPException, Depends
from datetime import datetime
from litellm import completion

from ..models.note import Note, NoteCreate, NoteUpdate
from ..repositories.note_repository import NoteRepository
from ..repositories.project_repository import ProjectRepository
from ..models.pagination import PaginationParams
from ..services.project_service import ProjectService

# Set up logging
logger = logging.getLogger(__name__)

class NoteService:
    """
    Service for managing notes in the system.
    
    This class handles all business logic related to notes, including
    creation, retrieval, and association with projects.
    """
    
    def __init__(
        self, 
        note_repository: Optional[NoteRepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        project_service: Optional[ProjectService] = None,
        ai_service = None
    ):
        """
        Initialize the NoteService with repositories and services.
        
        Args:
            note_repository: Repository for note operations
            project_repository: Repository for project operations
            project_service: Service for project operations
            ai_service: Service for AI operations (optional)
        """
        self.note_repository = note_repository
        self.project_repository = project_repository
        self.project_service = project_service
        self.ai_service = ai_service
    
    async def get_note(self, note_id: str) -> Dict:
        """
        Get a note by its ID.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            The note data as a dictionary
            
        Raises:
            HTTPException: If the note is not found
        """
        note = await self.note_repository.get_by_id(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
            
        return note
    
    async def create_note(self, note_data: NoteCreate) -> Dict:
        """
        Create a new note and associate it with relevant projects.
        
        Args:
            note_data: The note data to create
            
        Returns:
            The created note as a dictionary with associated projects
        """
        try:
            # Generate timestamp
            timestamp = datetime.utcnow().isoformat()
            
            # Create the note item
            note_dict = note_data.dict()
            note_dict['created_at'] = timestamp
            
            # Save to database
            note = await self.note_repository.create(note_dict)
            
            # Convert note to dictionary
            note_dict = dict(note)
            
            # Get all user's projects to check relevance
            user_projects = await self.project_service.get_projects(note_data.user_id)
            
            # Check relevance for each project
            relevant_projects = []
            for project in user_projects:
                is_relevant = await self._check_project_relevance(note_data.content, project)
                if is_relevant:
                    relevant_projects.append(project)
                    
                    # Create project-note association
                    await self.note_repository.associate_note_with_project(note_dict['id'], project['id'], timestamp)
                    
                    # Update project summary
                    await self.project_service.update_project_summary(project, note_data.content)
            
            # If no relevant projects found, associate with Miscellaneous project
            if not relevant_projects and getattr(note_data, 'project_id', None) is None:
                misc_project = await self.project_service.get_or_create_misc_project(note_data.user_id)
                await self.note_repository.associate_note_with_project(note_dict['id'], misc_project['id'], timestamp)
                relevant_projects.append(misc_project)
            # If project_id is provided, associate with that project
            elif getattr(note_data, 'project_id', None) is not None:
                project = await self.project_service.get_project(note_data.project_id)
                if project:
                    await self.note_repository.associate_note_with_project(note_dict['id'], project['id'], timestamp)
                    if project not in relevant_projects:
                        relevant_projects.append(project)
            
            # Add project references to the note
            note_dict['projects'] = [{'id': p['id'], 'name': p['name']} for p in relevant_projects]
            
            return note_dict
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def _check_project_relevance(self, content: str, project: dict) -> bool:
        """
        Check if a note's content is relevant to a project.
        
        Args:
            content: The note content
            project: The project to check relevance against
            
        Returns:
            True if the note is relevant to the project, False otherwise
        """
        try:
            # Skip relevance check for Miscellaneous project
            if project.get('name') == 'Miscellaneous':
                return False
                
            prompt = f"""
            You are an AI assistant that helps categorize notes into relevant projects.
            
            Project name: {project['name']}
            Project description: {project.get('description', '')}
            Project summary: {project.get('summary', '')}
            
            Note content:
            {content}
            
            Is this note relevant to the project? Consider the following:
            1. Does the note mention topics related to the project?
            2. Does the note contain information that would be useful for the project?
            3. Does the note describe actions or tasks related to the project?
            
            Answer with ONLY 'Yes' or 'No'.
            """
            
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            is_relevant = answer.startswith('yes')
            
            logger.info(f"Relevance check result for project '{project['name']}': {is_relevant}")
            
            return is_relevant
        except Exception as e:
            logger.error(f"Error checking project relevance: {str(e)}")
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
            pagination = PaginationParams(
                page=page,
                page_size=page_size,
                exclusive_start_key=exclusive_start_key
            )
            return await self.note_repository.get_notes_by_project(project_id, pagination)
        except Exception as e:
            logger.error(f"Error getting notes for project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes: {str(e)}")
    
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
            pagination = PaginationParams(
                page=page,
                page_size=page_size,
                exclusive_start_key=exclusive_start_key
            )
            return await self.note_repository.get_notes_by_user(user_id, pagination)
        except Exception as e:
            logger.error(f"Error getting notes for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes: {str(e)}") 