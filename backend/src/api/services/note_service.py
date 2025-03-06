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
        Create a new note.
        
        Args:
            note_data: The note data to create
            
        Returns:
            The created note
        """
        try:
            logger.info(f"Starting note creation process for user {note_data.user_id}")
            logger.debug(f"Note content (first 100 chars): '{note_data.content[:100]}...'")
            
            # Set created_at and updated_at if not provided
            if not note_data.created_at:
                note_data.created_at = datetime.now().isoformat()
                logger.debug(f"Setting created_at to {note_data.created_at}")
            if not note_data.updated_at:
                note_data.updated_at = note_data.created_at
                logger.debug(f"Setting updated_at to {note_data.updated_at}")
            
            # Create the note
            logger.debug(f"Calling note repository to create note")
            created_note = await self.note_repository.create(note_data)
            logger.info(f"Successfully created note with ID: {created_note.id}")
            
            # Find relevant projects
            if self.ai_service:
                logger.info(f"AI service available, finding relevant projects for note {created_note.id}")
                try:
                    logger.debug(f"Calling _find_relevant_projects for note {created_note.id}")
                    relevant_projects = await self._find_relevant_projects(created_note)
                    logger.info(f"Found {len(relevant_projects)} relevant projects for note {created_note.id}")
                    
                    # Associate note with relevant projects
                    for idx, (project, extracted_content) in enumerate(relevant_projects):
                        logger.info(f"Processing association {idx+1}/{len(relevant_projects)}: note {created_note.id} with project {project.id} - '{project.name}'")
                        
                        logger.debug(f"Calling repository to associate note {created_note.id} with project {project.id}")
                        await self.note_repository.associate_note_with_project(
                            created_note.id, 
                            project.id, 
                            extracted_content
                        )
                        logger.info(f"Successfully associated note {created_note.id} with project {project.id}")
                        
                        # Update project summary if AI service is available
                        try:
                            logger.info(f"Starting project summary update for project {project.id} - '{project.name}'")
                            
                            # Use the extracted content from the current note
                            logger.debug(f"Using extracted content from current note for project {project.id}")
                            logger.debug(f"Extracted content length: {len(extracted_content)} chars")
                            
                            # Generate summary
                            logger.info(f"Calling AI service to generate summary for project {project.id}")
                            new_summary = await self.ai_service.generate_project_summary(
                                project, 
                                extracted_content
                            )
                            
                            # Update project
                            logger.info(f"Updating project {project.id} with new summary")
                            await self.project_service.update_project(
                                project.id,
                                ProjectUpdate(summary=new_summary)
                            )
                            logger.info(f"Successfully updated summary for project {project.id}")
                        except Exception as e:
                            logger.error(f"Error updating project summary for project {project.id}: {str(e)}")
                            logger.exception(f"Detailed exception information for project summary update:")
                except Exception as e:
                    logger.error(f"Error finding relevant projects for note {created_note.id}: {str(e)}")
                    logger.exception("Detailed exception information for finding relevant projects:")
            else:
                logger.info(f"AI service not available, skipping project relevance check for note {created_note.id}")
            
            logger.info(f"Note creation process completed successfully for note {created_note.id}")
            
            # Fetch the projects for the note before returning it
            logger.debug(f"Fetching projects for note {created_note.id} before returning")
            projects_refs = await self.note_repository.get_projects_for_note(created_note.id)
            created_note.projects = projects_refs
            logger.debug(f"Found {len(projects_refs)} projects for note {created_note.id}")
            
            return created_note
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            logger.exception("Detailed exception information for note creation:")
            raise
    
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
    
    async def _find_relevant_projects(self, note: Note) -> List[Tuple[Project, str]]:
        """
        Find projects that are relevant to the note and extract relevant content.
        
        Args:
            note: The note to find relevant projects for
            
        Returns:
            List of tuples containing (project, extracted_content)
        """
        logger.info(f"Starting relevance check for note {note.id} from user {note.user_id}")
        
        # Skip if AI service is not available
        if not self.ai_service:
            logger.warning("AI service not available, skipping relevance check")
            return []
        
        # Get all projects
        logger.debug(f"Fetching all projects for user {note.user_id}")
        projects = await self.project_service.get_projects(note.user_id)
        logger.debug(f"Found {len(projects)} projects for user {note.user_id}")
        
        if not projects:
            logger.info(f"No projects found for user {note.user_id}, skipping relevance check")
            return []
        
        # Check relevance for each project
        logger.info(f"Checking relevance of note {note.id} against {len(projects)} projects")
        logger.debug(f"Note content: '{note.content[:100]}...'")
        
        relevant_projects = []
        
        for project in projects:
            # Skip Miscellaneous project
            if project.name == "Miscellaneous":
                logger.debug(f"Skipping relevance check for Miscellaneous project {project.id}")
                continue
                
            try:
                # Prepare parameters for extraction
                params = {
                    "content": note.content,
                    "project": self._convert_to_dict(project),
                    "user_id": note.user_id
                }
                logger.debug(f"Checking relevance for project {project.id} - '{project.name}'")
                logger.debug(f"Extraction parameters: {params}")
                
                # Check if note is relevant to project
                extraction = await self.ai_service.extract_relevant_note_for_project(params)
                logger.debug(f"Relevance extraction result for project {project.id}: is_relevant={extraction.is_relevant}")
                
                if extraction.is_relevant:
                    logger.info(f"Note {note.id} is relevant to project {project.id} - '{project.name}'")
                    logger.debug(f"Extracted content: '{extraction.extracted_content[:100]}...'")
                    relevant_projects.append((project, extraction.extracted_content))
                else:
                    logger.info(f"Note {note.id} is not relevant to project {project.id} - '{project.name}'")
            except Exception as e:
                logger.error(f"Error checking relevance for project {project.id}: {str(e)}")
                logger.exception(f"Detailed exception information for project {project.id}:")
        
        # If no relevant projects found, associate with Miscellaneous project
        if not relevant_projects:
            logger.info(f"No relevant projects found for note {note.id}, associating with Miscellaneous project")
            try:
                # Get or create Miscellaneous project
                misc_project = await self.project_service.get_or_create_misc_project(note.user_id)
                logger.info(f"Using Miscellaneous project {misc_project.id} for note {note.id}")
                
                # Create a RelevanceExtraction with the full note content
                relevant_projects.append((misc_project, note.content))
                logger.info(f"Added Miscellaneous project to relevant projects list")
            except Exception as e:
                logger.error(f"Error getting or creating Miscellaneous project: {str(e)}")
                logger.exception("Detailed exception information for Miscellaneous project:")
        
        # Log results
        project_names = [p.name for p, _ in relevant_projects]
        logger.info(f"Found {len(relevant_projects)} relevant projects for note {note.id}: {', '.join(project_names) if project_names else 'None'}")
        
        return relevant_projects
    
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