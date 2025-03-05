"""
Note Service Layer

This module provides service-level functionality for note management,
including CRUD operations and note-specific business logic.
"""

import logging
from typing import List, Optional, Dict, Tuple
from fastapi import HTTPException, Depends
from datetime import datetime
from litellm import completion

from ..models.note import Note, NoteCreate, NoteUpdate, PaginatedNotes
from ..repositories.note_repository import NoteRepository
from ..repositories.project_repository import ProjectRepository
from ..models.pagination import PaginationParams
from ..services.project_service import ProjectService
from ..models.project import Project, ProjectRef, ProjectUpdate
from ..services.ai_service import AIService
from ..models.ai import RelevanceExtraction

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
        ai_service: Optional[AIService] = None
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
        self.ai_service = ai_service or AIService()
    
    async def get_note(self, note_id: str) -> Note:
        """
        Get a note by its ID.
        
        Args:
            note_id: The unique identifier of the note
            
        Returns:
            The note data as a Note domain model
            
        Raises:
            HTTPException: If the note is not found
        """
        note = await self.note_repository.get_by_id(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
            
        # Ensure we return a Note model
        if not isinstance(note, Note):
            # Convert to Note model if it's a dictionary
            if isinstance(note, dict):
                projects = []
                if 'projects' in note and note['projects']:
                    for p in note['projects']:
                        if isinstance(p, dict) and 'id' in p and 'name' in p:
                            projects.append(ProjectRef(id=p['id'], name=p['name']))
                
                return Note(
                    id=note['id'],
                    content=note['content'],
                    created_at=note['created_at'],
                    user_id=note['user_id'],
                    projects=projects
                )
        
        return note
    
    async def create_note(self, note_data: NoteCreate) -> Note:
        """
        Create a new note and associate it with relevant projects.
        
        Args:
            note_data: The note data to create
            
        Returns:
            The created note as a Note domain model
            
        Raises:
            HTTPException: If there's an error creating the note
        """
        try:
            # Validate input
            self._validate_note_input(note_data)
            
            # Save to database
            note = await self.note_repository.create(note_data)
            
            # Find relevant projects and extract content
            user_projects = await self.project_service.get_projects(note_data.user_id)
            relevant_projects, project_extractions = await self._find_relevant_projects(
                note_data.content, 
                user_projects, 
                note_data.user_id
            )
            
            # Associate note with projects
            await self._associate_note_with_projects(note, relevant_projects)
            
            # Update project summaries
            await self._update_project_summaries(relevant_projects, project_extractions)
            
            # Create and return the note response
            project_refs = self._create_project_references(relevant_projects)
            
            return Note(
                id=note.id,
                content=note.content,
                created_at=note.created_at,
                user_id=note.user_id,
                projects=project_refs
            )
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def _validate_note_input(self, note_data: NoteCreate) -> None:
        """
        Validate the note input data.
        
        Args:
            note_data: The note data to validate
            
        Raises:
            HTTPException: If the input is invalid
        """
        if getattr(note_data, 'project_id', None) is not None:
            raise HTTPException(
                status_code=400, 
                detail="project_id should not be provided in create_note. Project associations are determined automatically."
            )
    
    async def _find_relevant_projects(
        self, 
        content: str, 
        user_projects: List[Project], 
        user_id: str
    ) -> Tuple[List[Project], Dict[str, RelevanceExtraction]]:
        """
        Find projects relevant to the note content and extract relevant content for each.
        
        Args:
            content: The note content
            user_projects: List of user's projects
            user_id: The user ID
            
        Returns:
            Tuple containing:
            - List of relevant projects
            - Dictionary mapping project IDs to RelevanceExtraction objects
        """
        relevant_projects = []
        project_extractions = {}  # Dictionary to store project_id -> RelevanceExtraction
        
        # Check relevance for each project
        for project in user_projects:
            # Convert project to dict if it's a domain model
            project_dict = self._convert_to_dict(project)
            
            # Prepare parameters for extraction
            extraction_params = {
                'content': content,
                'project': project_dict,
                'user_id': user_id
            }
            
            # Extract relevant content
            extraction_result = await self.ai_service.extract_relevant_note_for_project(extraction_params)
            
            if extraction_result.is_relevant:
                relevant_projects.append(project)
                project_id = getattr(project, 'id', None)
                project_extractions[project_id] = extraction_result
        
        # If no relevant projects found, use Miscellaneous project
        if not relevant_projects:
            misc_project = await self.project_service.get_or_create_misc_project(user_id)
            relevant_projects.append(misc_project)
            
            # For Miscellaneous project, create a basic RelevanceExtraction
            project_id = getattr(misc_project, 'id', None)
            project_extractions[project_id] = RelevanceExtraction(
                is_relevant=True,
                extracted_content=content
            )
        
        return relevant_projects, project_extractions
    
    async def _associate_note_with_projects(self, note: Note, projects: List[Project]) -> None:
        """
        Associate a note with multiple projects.
        
        Args:
            note: The note to associate
            projects: The projects to associate with the note
        """
        for project in projects:
            project_id = getattr(project, 'id', None)
            await self.note_repository.associate_note_with_project(note.id, project_id, note.created_at)
    
    async def _update_project_summaries(
        self, 
        projects: List[Project], 
        extractions: Dict[str, RelevanceExtraction]
    ) -> None:
        """
        Update project summaries based on extracted note content.
        
        Args:
            projects: The projects to update
            extractions: Dictionary mapping project IDs to RelevanceExtraction objects
        """
        for project in projects:
            project_id = getattr(project, 'id', None)
            
            # Convert project to dict if it's a domain model
            project_dict = self._convert_to_dict(project)
            
            # Get the extraction result for this project
            extraction = extractions.get(project_id)
            
            # Generate the new summary using the extracted content
            new_summary = await self.ai_service.generate_project_summary(
                project_dict, 
                extraction.extracted_content
            )
            
            # Create a ProjectUpdate object with the new summary
            update_data = ProjectUpdate(summary=new_summary)
            
            # Update the project directly
            await self.project_service.update_project(project.id, update_data)
    
    def _create_project_references(self, projects: List[Project]) -> List[ProjectRef]:
        """
        Create project references for the note response.
        
        Args:
            projects: The projects to create references for
            
        Returns:
            List of ProjectRef objects
        """
        project_refs = []
        for p in projects:
            if hasattr(p, 'id') and hasattr(p, 'name'):
                project_refs.append(ProjectRef(id=p.id, name=p.name))
            elif isinstance(p, dict) and 'id' in p and 'name' in p:
                project_refs.append(ProjectRef(id=p['id'], name=p['name']))
        return project_refs
    
    def _convert_to_dict(self, obj) -> Dict:
        """
        Convert an object to a dictionary.
        
        Args:
            obj: The object to convert
            
        Returns:
            Dictionary representation of the object
        """
        if hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return dict(obj)
    
    async def get_notes_by_project(self, project_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> PaginatedNotes:
        """
        Get paginated notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            PaginatedNotes model with notes and pagination metadata
        """
        try:
            pagination = PaginationParams(
                page=page,
                page_size=page_size,
                exclusive_start_key=exclusive_start_key
            )
            result = await self.note_repository.get_notes_by_project(project_id, pagination)
            
            # If result is already a PaginatedResponse, convert it to PaginatedNotes
            if hasattr(result, 'items') and hasattr(result, 'page'):
                return PaginatedNotes(
                    items=result.items,
                    page=result.page,
                    page_size=result.page_size,
                    has_more=result.has_more,
                    LastEvaluatedKey=result.last_evaluated_key  # Convert from lowercase to camelCase for frontend
                )
            
            # If result is a dictionary, convert it to PaginatedNotes
            if isinstance(result, dict):
                return PaginatedNotes(
                    items=result.get('items', []),
                    page=result.get('page', page),
                    page_size=result.get('page_size', page_size),
                    has_more=result.get('has_more', False),
                    LastEvaluatedKey=result.get('LastEvaluatedKey') or result.get('last_evaluated_key')
                )
            
            # If we can't convert, return an empty result
            return PaginatedNotes(
                items=[],
                page=page,
                page_size=page_size,
                has_more=False,
                LastEvaluatedKey=None
            )
        except Exception as e:
            logger.error(f"Error getting notes for project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes: {str(e)}")
    
    async def get_notes_by_user(self, user_id: str, page: int = 1, page_size: int = 10, exclusive_start_key: Optional[Dict] = None) -> PaginatedNotes:
        """
        Get paginated notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            page: The page number (1-indexed)
            page_size: The number of items per page
            exclusive_start_key: The key to start from for pagination
            
        Returns:
            PaginatedNotes model with notes and pagination metadata
        """
        try:
            pagination = PaginationParams(
                page=page,
                page_size=page_size,
                exclusive_start_key=exclusive_start_key
            )
            result = await self.note_repository.get_notes_by_user(user_id, pagination)
            
            # If result is already a PaginatedResponse, convert it to PaginatedNotes
            if hasattr(result, 'items') and hasattr(result, 'page'):
                return PaginatedNotes(
                    items=result.items,
                    page=result.page,
                    page_size=result.page_size,
                    has_more=result.has_more,
                    LastEvaluatedKey=result.last_evaluated_key  # Convert from lowercase to camelCase for frontend
                )
            
            # If result is a dictionary, convert it to PaginatedNotes
            if isinstance(result, dict):
                return PaginatedNotes(
                    items=result.get('items', []),
                    page=result.get('page', page),
                    page_size=result.get('page_size', page_size),
                    has_more=result.get('has_more', False),
                    LastEvaluatedKey=result.get('LastEvaluatedKey') or result.get('last_evaluated_key')
                )
            
            # If we can't convert, return an empty result
            return PaginatedNotes(
                items=[],
                page=page,
                page_size=page_size,
                has_more=False,
                LastEvaluatedKey=None
            )
        except Exception as e:
            logger.error(f"Error getting notes for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes: {str(e)}") 