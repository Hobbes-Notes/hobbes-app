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
import json
import time

from api.models.note import Note, NoteCreate, NoteUpdate, PaginatedNotes
from api.repositories.note_repository import NoteRepository
from api.repositories.project_repository import ProjectRepository
from api.models.pagination import PaginationParams
from api.services.project_service import ProjectService
from api.models.project import Project, ProjectRef, ProjectUpdate
from api.services.ai_service import AIService
from api.models.ai import RelevanceExtraction
from api.services.action_item_service import ActionItemService
from api.models.action_item import ActionItemCreate, ActionItemUpdate
from api.services.capb_service import CapBService

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
        ai_service: Optional[AIService] = None,
        action_item_service: Optional[ActionItemService] = None,
        capb_service: Optional['CapBService'] = None
    ):
        """
        Initialize the NoteService with repositories and services.
        
        Args:
            note_repository: Repository for note operations
            project_repository: Repository for project operations
            project_service: Service for project operations
            ai_service: Service for AI operations (optional)
            action_item_service: Service for action item operations (optional)
            capb_service: Service for CapB project tagging operations (optional)
        """
        self.note_repository = note_repository
        self.project_repository = project_repository
        self.project_service = project_service
        self.ai_service = ai_service or AIService()
        self.action_item_service = action_item_service
        self.capb_service = capb_service
    
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
            overall_start_time = time.time()
            logger.info(f"🚀 TIMING: Starting note creation process for user {note_data.user_id}")
            logger.debug(f"Note content (first 100 chars): '{note_data.content[:100]}...'")
            
            # Set created_at and updated_at if not provided
            if not note_data.created_at:
                note_data.created_at = datetime.now().isoformat()
                logger.debug(f"Setting created_at to {note_data.created_at}")
            if not note_data.updated_at:
                note_data.updated_at = note_data.created_at
                logger.debug(f"Setting updated_at to {note_data.updated_at}")
            
            # Create the note
            note_creation_start = time.time()
            logger.debug(f"Calling note repository to create note")
            created_note = await self.note_repository.create(note_data)
            note_creation_time = time.time() - note_creation_start
            logger.info(f"⏱️ TIMING: Note repository creation took {note_creation_time:.2f}s - Created note ID: {created_note.id}")
            
            # CapA: Manage Action Items based on note content (enabled)
            if self.ai_service and self.action_item_service:
                capa_start_time = time.time()
                logger.info(f"🤖 TIMING: Starting CapA (Action Item Management) for note {created_note.id}")
                try:
                    # Get existing action items for the user
                    fetch_items_start = time.time()
                    existing_action_items = await self.action_item_service.get_action_items_by_user(note_data.user_id)
                    fetch_items_time = time.time() - fetch_items_start
                    logger.info(f"⏱️ TIMING: Fetching existing action items took {fetch_items_time:.2f}s - Found {len(existing_action_items)} items")
                    
                    # Prepare data for AI service (no user_projects needed for CapA)
                    data_prep_start = time.time()
                    existing_action_items_json = json.dumps([
                        {
                            "id": item.id,
                            "task": item.task,
                            "doer": item.doer,
                            "deadline": item.deadline,
                            "theme": item.theme,
                            "context": item.context,
                            "extracted_entities": item.extracted_entities,
                            "status": item.status,
                            "type": item.type,
                            "projects": item.projects
                        } for item in existing_action_items
                    ])
                    data_prep_time = time.time() - data_prep_start
                    logger.info(f"⏱️ TIMING: CapA data preparation took {data_prep_time:.2f}s")
                    
                    # Call CapA (focused only on action management)
                    ai_call_start = time.time()
                    action_operations = await self.ai_service.manage_action_items({
                        "note_content": created_note.content,
                        "existing_action_items": existing_action_items_json,
                        "user_id": note_data.user_id
                    })
                    ai_call_time = time.time() - ai_call_start
                    logger.info(f"⏱️ TIMING: CapA AI service call took {ai_call_time:.2f}s - Suggested {len(action_operations)} operations")
                    
                    # Process action operations
                    processing_start = time.time()
                    for operation in action_operations:
                        action_type = operation.get("action", "new")
                        
                        if action_type == "new":
                            # Create new action item
                            action_create = ActionItemCreate(
                                task=operation.get("task", ""),
                                doer=operation.get("doer"),
                                deadline=operation.get("deadline"),
                                theme=operation.get("theme"),
                                context=operation.get("context"),
                                extracted_entities=operation.get("extracted_entities", {}),
                                status=operation.get("status", "open"),
                                type=operation.get("type", "task"),
                                projects=[],  # CapA doesn't handle project tagging - will be done by CapB
                                user_id=note_data.user_id,
                                source_note_id=created_note.id
                            )
                            logger.info(f"CapA: Creating action item with source_note_id={created_note.id}")
                            new_item = await self.action_item_service.create_action_item(action_create)
                            logger.info(f"✅ CapA: Created action item {new_item.id} with source_note_id={new_item.source_note_id} - {new_item.task[:50]}...")
                            
                        elif action_type in ["update", "complete"]:
                            # Update existing action item
                            item_id = operation.get("id")
                            if item_id:
                                update_data = ActionItemUpdate()
                                
                                if action_type == "complete":
                                    update_data.status = "completed"
                                else:
                                    # Update other fields
                                    if operation.get("task"):
                                        update_data.task = operation.get("task")
                                    if operation.get("doer"):
                                        update_data.doer = operation.get("doer")
                                    if operation.get("deadline"):
                                        update_data.deadline = operation.get("deadline")
                                    if operation.get("theme"):
                                        update_data.theme = operation.get("theme")
                                    if operation.get("context"):
                                        update_data.context = operation.get("context")
                                    if operation.get("extracted_entities"):
                                        update_data.extracted_entities = operation.get("extracted_entities")
                                    if operation.get("type"):
                                        update_data.type = operation.get("type")
                                    # Note: Not updating projects field - CapB will handle project tagging
                                
                                updated_item = await self.action_item_service.update_action_item(item_id, update_data)
                                if updated_item:
                                    logger.info(f"{action_type.capitalize()}d action item: {item_id} - {updated_item.task[:50]}...")
                                else:
                                    logger.warning(f"Could not find action item to {action_type}: {item_id}")
                    
                    processing_time = time.time() - processing_start
                    capa_total_time = time.time() - capa_start_time
                    logger.info(f"⏱️ TIMING: CapA operation processing took {processing_time:.2f}s")
                    logger.info(f"🏁 TIMING: CapA total time: {capa_total_time:.2f}s")
                    
                except Exception as e:
                    capa_total_time = time.time() - capa_start_time
                    logger.error(f"❌ TIMING: CapA failed after {capa_total_time:.2f}s - Error: {str(e)}")
                    logger.exception("Detailed exception information for CapA:")
            else:
                logger.info(f"AI service or action item service not available, skipping CapA")
            
            # CapB: Tag Action Items with Projects (runs after CapA)
            if self.capb_service:
                capb_start_time = time.time()
                logger.info(f"🏷️ TIMING: Starting CapB (Project Tagging) for action items after note {created_note.id}")
                try:
                    capb_result = await self.capb_service.run_for_user(note_data.user_id)
                    capb_total_time = time.time() - capb_start_time
                    
                    if capb_result["success"]:
                        logger.info(f"✅ TIMING: CapB completed successfully in {capb_total_time:.2f}s: {capb_result['message']}")
                        logger.debug(f"CapB results: {capb_result['tagged_action_items']}/{capb_result['total_action_items']} action items tagged")
                    else:
                        logger.warning(f"⚠️ TIMING: CapB failed after {capb_total_time:.2f}s but note creation continues: {capb_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    capb_total_time = time.time() - capb_start_time
                    logger.error(f"❌ TIMING: CapB error after {capb_total_time:.2f}s for note {created_note.id}: {str(e)}")
                    logger.exception("Detailed exception information for CapB:")
                    # CapB failure doesn't affect note creation success
                    logger.info("Note creation continues despite CapB failure")
            else:
                logger.info(f"CapB service not available, skipping project tagging")
            
            # Final steps
            final_steps_start = time.time()
            logger.info(f"Note creation process completed successfully for note {created_note.id}")
            
            # Fetch the projects for the note before returning it (currently empty since we commented out C1)
            logger.debug(f"Fetching projects for note {created_note.id} before returning")
            projects_refs = await self.note_repository.get_projects_for_note(created_note.id)
            created_note.projects = projects_refs
            logger.debug(f"Found {len(projects_refs)} projects for note {created_note.id}")
            final_steps_time = time.time() - final_steps_start
            
            overall_time = time.time() - overall_start_time
            logger.info(f"⏱️ TIMING: Final steps took {final_steps_time:.2f}s")
            logger.info(f"🏁 TIMING: TOTAL note creation process took {overall_time:.2f}s")
            
            return created_note
        except Exception as e:
            overall_time = time.time() - overall_start_time if 'overall_start_time' in locals() else 0
            logger.error(f"❌ TIMING: Note creation failed after {overall_time:.2f}s - Error: {str(e)}")
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
    
    def _get_simplified_project_hierarchy(self, projects: List[Project], current_project_id: str) -> str:
        """
        Create a simplified JSON representation of the project hierarchy, including only
        the name and description of child projects.
        
        Args:
            projects: List of all projects
            current_project_id: ID of the current project
            
        Returns:
            JSON string representing the project hierarchy
        """
        # Create a mapping of parent_id to child projects
        parent_to_children = {}
        for project in projects:
            parent_id = getattr(project, 'parent_id', None)
            if parent_id:
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                # Only include name and description
                parent_to_children[parent_id].append({
                    "name": project.name,
                    "description": project.description or ""
                })
        
        # Function to recursively build the hierarchy
        def build_hierarchy(project_id):
            children = parent_to_children.get(project_id, [])
            return children
        
        # Build the hierarchy for the current project
        hierarchy = build_hierarchy(current_project_id)
        
        # Convert to JSON string
        try:
            return json.dumps(hierarchy)
        except Exception as e:
            logger.error(f"Error converting project hierarchy to JSON: {str(e)}")
            return "[]"
    
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
                # Get simplified project hierarchy
                project_hierarchy = self._get_simplified_project_hierarchy(projects, project.id)
                
                # Prepare parameters for extraction
                params = {
                    "note_content": note.content,
                    "project_name": project.name,
                    "project_description": project.description or "",
                    "project_hierarchy": project_hierarchy,
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
            
            # Get the extraction result for this project
            extraction = extractions.get(project_id)
            
            # Prepare parameters for the AI service
            params = {
                "project_id": project_id,
                "project_name": project.name,
                "project_description": project.description or "",
                "current_summary": project.summary or "",
                "note_content": extraction.extracted_content
            }
            
            # Generate the new summary using the extracted content
            new_summary = await self.ai_service.generate_project_summary(params)
            
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
    
    async def get_notes_count_by_user(self, user_id: str) -> int:
        """
        Get total count of notes for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            Total number of notes for the user
        """
        try:
            return await self.note_repository.get_notes_count_by_user(user_id)
        except Exception as e:
            logger.error(f"Error getting notes count for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes count: {str(e)}")
    
    async def get_notes_count_by_project(self, project_id: str) -> int:
        """
        Get total count of notes for a specific project.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            Total number of notes for the project
        """
        try:
            return await self.note_repository.get_notes_count_by_project(project_id)
        except Exception as e:
            logger.error(f"Error getting notes count for project {project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting notes count: {str(e)}") 