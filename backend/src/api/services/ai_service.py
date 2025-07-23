"""
AI Service Layer

This module provides service-level functionality for AI operations,
including generating summaries and checking relevance.
"""

import logging
import json
import openai
import os
from typing import Optional, Dict, Tuple, List, Any
from litellm import completion
from datetime import datetime
import time

from api.models.project import Project
from api.models.ai import RelevanceExtraction, AIUseCase, AIConfiguration
from api.repositories.ai_repository import AIRepository
from api.models.note import Note

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    """
    Service for AI operations in the system.
    
    This class handles all business logic related to AI operations, including
    generating summaries and checking relevance.
    """
    
    def __init__(self, ai_repository: AIRepository):
        """
        Initialize the AIService.
        
        Args:
            ai_repository: The AI repository to use
        """
        self._ai_repository = ai_repository
        self._openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        if self._openai_api_key:
            self._client = openai.OpenAI(api_key=self._openai_api_key)
        else:
            logger.warning("OpenAI API key not found. AI features will not work.")
            self._client = None
    
    async def _get_configuration(self, use_case: AIUseCase) -> AIConfiguration:
        """
        Get the active configuration for a use case.
        
        Args:
            use_case: The use case to get the configuration for
            
        Returns:
            The active configuration for the use case
        """
        # Get the active configuration for the use case
        # The repository ensures a valid configuration is always returned
        return await self._ai_repository.get_active_configuration(use_case)
    
    async def generate_project_summary(self, params: Dict[str, Any], version: Optional[int] = None) -> str:
        """
        Generate a summary for a project based on extracted note content.
        
        Args:
            params: Dictionary containing:
                - project_name: The name of the project
                - project_description: The description of the project
                - current_summary: The current summary of the project
                - note_content: The extracted content from relevant notes
                - project_id: The ID of the project (for logging purposes)
            version: Optional specific version to use. If not provided, the active configuration will be used.
            
        Returns:
            The generated summary
        """
        project_id = params.get("project_id", "unknown")
        project_name = params.get("project_name", "")
        logger.info(f"Starting project summary generation for project {project_id} - '{project_name}'")
        
        if not self._client:
            logger.error("OpenAI client not initialized. Cannot generate project summary.")
            return "Unable to generate summary: AI service not configured."
        
        try:
            # Extract parameters
            project_description = params.get("project_description", "")
            current_summary = params.get("current_summary", "")
            note_content = params.get("note_content", "")
            
            # Log input parameters
            logger.info(f"Generating summary for project: {project_id} - {project_name}")
            logger.debug(f"Project description: {project_description}")
            logger.debug(f"Note content length: {len(note_content)} chars")
            logger.debug(f"Note content preview: '{note_content[:100]}...'")
            
            # Log current summary
            logger.debug(f"Current summary length: {len(current_summary)} chars")
            if current_summary:
                logger.debug(f"Current summary preview: '{current_summary[:100]}...'")
            else:
                logger.debug("No existing summary found for this project")
            
            # Get the configuration for project summary
            logger.debug(f"Fetching AI configuration for PROJECT_SUMMARY use case" + (f" version {version}" if version else " (active version)"))
            
            if version is not None:
                config = await self.get_configuration(AIUseCase.PROJECT_SUMMARY, version)
                if not config:
                    logger.error(f"Configuration for PROJECT_SUMMARY version {version} not found, falling back to active configuration")
                    config = await self._get_configuration(AIUseCase.PROJECT_SUMMARY)
            else:
                config = await self._get_configuration(AIUseCase.PROJECT_SUMMARY)
                
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    project_name=project_name,
                    project_description=project_description,
                    current_summary=current_summary,
                    note_content=note_content
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"User prompt length: {len(user_prompt)} chars")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: project_name, project_description, current_summary, note_content")
                raise ValueError(f"Error formatting prompt template: {str(e)}")

            # Append the response format
            user_prompt += AIUseCase.PROJECT_SUMMARY.response_format
            
            logger.info(f"Sending prompt to OpenAI API for project summary generation using model: {config.model}")
            
            # Call the OpenAI API
            start_time = time.time()
            response = self._client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                response_format={"type": "json_object"}
            )
            end_time = time.time()
            
            # Parse the response
            response_content = response.choices[0].message.content
            logger.debug(f"Raw API response: {response_content}")
            logger.info(f"API call completed in {end_time - start_time:.2f} seconds")
            
            try:
                # Parse the JSON response
                logger.debug("Attempting to parse JSON response")
                response_json = json.loads(response_content)
                
                # Extract the summary
                if "summary" in response_json:
                    summary = response_json["summary"]
                    logger.info(f"Successfully generated summary of length {len(summary)} chars")
                    logger.debug(f"Generated summary preview: '{summary[:100]}...'")
                    return summary
                else:
                    logger.warning(f"Response JSON does not contain 'summary' key. Keys found: {list(response_json.keys())}")
                    return "Unable to generate summary: Invalid response format."
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                return "Unable to generate summary: Invalid response format."
            
        except Exception as e:
            logger.exception(f"Error generating project summary: {str(e)}")
            return "Unable to generate summary: An error occurred."
    
    async def extract_relevant_note_for_project(self, params: Dict[str, Any], version: Optional[int] = None) -> RelevanceExtraction:
        """
        Extract relevant content from a note for a specific project.
        
        Args:
            params: Dictionary containing:
                - note_content: The note content
                - project_name: The name of the project
                - project_description: The description of the project
                - project_hierarchy: The hierarchical structure of the project with all child projects in nested JSON format
                - user_id: The user ID
            version: Optional specific version to use. If not provided, the active configuration will be used.
                
        Returns:
            RelevanceExtraction object with is_relevant and extracted_content
        """
        logger.info("Starting relevance extraction process")
        
        if not self._client:
            logger.error("OpenAI client not initialized. Cannot extract relevant content.")
            return RelevanceExtraction(is_relevant=False, extracted_content="")
        
        try:
            # Extract parameters
            note_content = params.get("note_content", "")
            project_name = params.get("project_name", "")
            project_description = params.get("project_description", "")
            project_hierarchy = params.get("project_hierarchy", "{}")
            user_id = params.get("user_id", "")
            
            # Log input parameters
            logger.info(f"Extracting relevance for user: {user_id}, project: '{project_name}'")
            logger.debug(f"Content length: {len(note_content)} chars")
            logger.debug(f"Content preview: '{note_content[:100]}...'")
            logger.debug(f"Project name: {project_name}")
            logger.debug(f"Project description: {project_description}")
            logger.debug(f"Project hierarchy provided: {bool(project_hierarchy)}")
            
            # Get the configuration for relevance extraction
            logger.debug(f"Fetching AI configuration for RELEVANCE_EXTRACTION use case" + (f" version {version}" if version else " (active version)"))
            
            if version is not None:
                config = await self.get_configuration(AIUseCase.RELEVANCE_EXTRACTION, version)
                if not config:
                    logger.error(f"Configuration for RELEVANCE_EXTRACTION version {version} not found, falling back to active configuration")
                    config = await self._get_configuration(AIUseCase.RELEVANCE_EXTRACTION)
            else:
                config = await self._get_configuration(AIUseCase.RELEVANCE_EXTRACTION)
                
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    project_name=project_name,
                    project_description=project_description,
                    note_content=note_content,
                    project_hierarchy=project_hierarchy
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"Prepared user prompt with length: {len(user_prompt)}")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: project_name, project_description, note_content, project_hierarchy")
                raise ValueError(f"Error formatting prompt template: {str(e)}")
            

            # Append the response format
            user_prompt += AIUseCase.RELEVANCE_EXTRACTION.response_format
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for relevance extraction for project '{project_name}'")
            start_time = time.time()
            response = self._client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                response_format={"type": "json_object"}
            )
            end_time = time.time()
            
            # Parse the response
            response_content = response.choices[0].message.content
            logger.debug(f"Raw API response: {response_content}")
            logger.info(f"API call completed in {end_time - start_time:.2f} seconds")
            
            try:
                # Parse the JSON response
                logger.debug("Attempting to parse JSON response")
                response_json = json.loads(response_content)
                
                # Extract the relevance and content
                if "is_relevant" not in response_json or "extracted_content" not in response_json:
                    logger.error(f"Response JSON missing required keys. Keys found: {list(response_json.keys())}")
                    raise ValueError(f"Invalid response format: missing required keys. Keys found: {list(response_json.keys())}")
                
                is_relevant = response_json["is_relevant"]
                extracted_content = response_json["extracted_content"]
                annotation = response_json.get("annotation", "")
                
                logger.info(f"Relevance determination: {'Relevant' if is_relevant else 'Not relevant'}")
                if is_relevant:
                    logger.debug(f"Extracted content length: {len(extracted_content)} chars")
                    logger.debug(f"Extracted content preview: '{extracted_content[:100]}...'")
                
                return RelevanceExtraction(
                    is_relevant=is_relevant,
                    extracted_content=extracted_content,
                    annotation=annotation
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logger.exception(f"Error extracting relevance: {str(e)}")
            raise
    
    async def manage_action_items(self, params: Dict[str, Any], version: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        CapA: Manage action items based on note content and existing action items.
        
        Args:
            params: Dictionary containing:
                - note_content: The content of the new note
                - existing_action_items: JSON string of existing action items
                - user_id: The user ID
            version: Optional specific version to use. If not provided, the active configuration will be used.
                
        Returns:
            List of action item operations (new, update, complete)
        """
        logger.info("🤖 CapA AI SERVICE: Starting action item management process")
        logger.info(f"🔍 CapA AI SERVICE DEBUG: OpenAI client initialized: {self._client is not None}")
        logger.info(f"🔍 CapA AI SERVICE DEBUG: OpenAI API key available: {self._openai_api_key is not None}")
        
        if not self._client:
            logger.error("❌ CapA AI SERVICE: OpenAI client not initialized. Cannot manage action items.")
            logger.error(f"❌ CapA AI SERVICE: OpenAI API key is: {self._openai_api_key}")
            return []
        
        try:
            # Extract parameters
            note_content = params.get("note_content", "")
            existing_action_items = params.get("existing_action_items", "[]")
            user_id = params.get("user_id", "")
            
            # Log input parameters
            logger.info(f"Managing action items for user: {user_id}")
            logger.debug(f"Note content length: {len(note_content)} chars")
            logger.debug(f"Note content preview: '{note_content[:100]}...'")
            logger.debug(f"Existing action items: {existing_action_items[:500]}...")
            
            # Get the configuration for action management
            logger.debug(f"Fetching AI configuration for ACTION_MANAGEMENT use case" + (f" version {version}" if version else " (active version)"))
            
            if version is not None:
                config = await self.get_configuration(AIUseCase.ACTION_MANAGEMENT, version)
                if not config:
                    logger.error(f"Configuration for ACTION_MANAGEMENT version {version} not found, falling back to active configuration")
                    config = await self._get_configuration(AIUseCase.ACTION_MANAGEMENT)
            else:
                config = await self._get_configuration(AIUseCase.ACTION_MANAGEMENT)
                
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    note_content=note_content,
                    existing_action_items=existing_action_items,
                    user_id=user_id
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"Prepared user prompt with length: {len(user_prompt)}")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: note_content, existing_action_items, user_id")
                raise ValueError(f"Error formatting prompt template: {str(e)}")
            
            # Append the response format
            user_prompt += AIUseCase.ACTION_MANAGEMENT.response_format
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for action item management")
            start_time = time.time()
            response = self._client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                response_format={
                    "type": "json_object"
                }
            )
            end_time = time.time()
            
            # Parse the response
            response_content = response.choices[0].message.content
            logger.debug(f"Raw API response: {response_content}")
            logger.info(f"API call completed in {end_time - start_time:.2f} seconds")
            
            try:
                # Parse the JSON response
                logger.debug("Attempting to parse JSON response")
                response_json = json.loads(response_content)
                
                # Extract the action items
                if "action_items" not in response_json:
                    logger.error(f"Response JSON missing required 'action_items' key. Keys found: {list(response_json.keys())}")
                    raise ValueError(f"Invalid response format: missing 'action_items' key. Keys found: {list(response_json.keys())}")
                
                action_items = response_json["action_items"]
                
                logger.info(f"AI suggested {len(action_items)} action item operations")
                for i, item in enumerate(action_items):
                    action_type = item.get("action", "unknown")
                    task = item.get("task", "")[:50]
                    logger.debug(f"Action {i+1}: {action_type} - {task}...")
                
                return action_items
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logger.exception(f"Error managing action items: {str(e)}")
            raise
    
    async def tag_action_items_with_projects(self, params: Dict[str, Any], version: Optional[int] = None) -> Dict[str, List[str]]:
        """
        CapB: Tag action items with relevant projects based on semantic similarity.
        
        Args:
            params: Dictionary containing:
                - action_items: JSON string/list of action items to tag
                - user_projects: JSON string/list of user's projects
            version: Optional specific version to use. If not provided, the active configuration will be used.
                
        Returns:
            Dictionary mapping action_item_id -> list of project_ids
        """
        logger.info("Starting project tagging process for action items")
        
        if not self._client:
            logger.error("OpenAI client not initialized. Cannot tag action items with projects.")
            return {}
        
        try:
            # Extract and validate parameters
            action_items = params.get("action_items", [])
            user_projects = params.get("user_projects", [])
            
            # Convert to JSON strings if they're lists
            if isinstance(action_items, list):
                action_items_json = json.dumps(action_items)
            else:
                action_items_json = action_items
                
            if isinstance(user_projects, list):
                user_projects_json = json.dumps(user_projects)
            else:
                user_projects_json = user_projects
            
            # Log input parameters
            logger.info(f"Tagging {len(action_items) if isinstance(action_items, list) else 'unknown count'} action items with projects")
            logger.debug(f"Action items: {action_items_json[:500]}...")
            logger.debug(f"User projects: {user_projects_json[:500]}...")
            
            # Skip processing if no action items or projects
            if not action_items or not user_projects:
                logger.info("No action items or projects provided, returning empty mapping")
                return {}
            
            # Get the configuration for project tagging
            logger.debug(f"Fetching AI configuration for PROJECT_TAGGING use case" + (f" version {version}" if version else " (active version)"))
            
            if version is not None:
                config = await self.get_configuration(AIUseCase.PROJECT_TAGGING, version)
                if not config:
                    logger.error(f"Configuration for PROJECT_TAGGING version {version} not found, falling back to active configuration")
                    config = await self._get_configuration(AIUseCase.PROJECT_TAGGING)
            else:
                config = await self._get_configuration(AIUseCase.PROJECT_TAGGING)
                
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    action_items=action_items_json,
                    user_projects=user_projects_json
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"Prepared user prompt with length: {len(user_prompt)}")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: action_items, user_projects")
                raise ValueError(f"Error formatting prompt template: {str(e)}")
            
            # Append the response format
            user_prompt += AIUseCase.PROJECT_TAGGING.response_format
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for project tagging")
            start_time = time.time()
            response = self._client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                response_format={
                    "type": "json_object"
                }
            )
            end_time = time.time()
            
            # Parse the response
            response_content = response.choices[0].message.content
            logger.debug(f"Raw API response: {response_content}")
            logger.info(f"API call completed in {end_time - start_time:.2f} seconds")
            
            try:
                # Parse the JSON response
                logger.debug("Attempting to parse JSON response")
                response_json = json.loads(response_content)
                
                # Extract the project mappings
                if "project_mappings" not in response_json:
                    logger.error(f"Response JSON missing required 'project_mappings' key. Keys found: {list(response_json.keys())}")
                    raise ValueError(f"Invalid response format: missing 'project_mappings' key. Keys found: {list(response_json.keys())}")
                
                project_mappings = response_json["project_mappings"]
                
                # Convert to the expected format: action_item_id -> list of project_ids
                result = {}
                for mapping in project_mappings:
                    action_item_id = mapping.get("action_item_id")
                    project_ids = mapping.get("project_ids", [])
                    
                    if action_item_id:
                        result[action_item_id] = project_ids
                
                logger.info(f"AI tagged {len(result)} action items with projects")
                for action_id, project_ids in result.items():
                    if project_ids:
                        logger.debug(f"Action {action_id} tagged with projects: {project_ids}")
                    else:
                        logger.debug(f"Action {action_id} not tagged with any projects")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logger.exception(f"Error tagging action items with projects: {str(e)}")
            raise
    
    async def get_configuration(self, use_case: AIUseCase, version: int) -> Optional[AIConfiguration]:
        """
        Get a specific configuration.
        
        Args:
            use_case: The use case to get the configuration for
            version: The version of the configuration
            
        Returns:
            The configuration if found, None otherwise
        """
        return await self._ai_repository.get_configuration(use_case, version)
    
    async def get_active_configuration(self, use_case: AIUseCase) -> AIConfiguration:
        """
        Get the active configuration for a use case.
        
        Args:
            use_case: The use case to get the configuration for
            
        Returns:
            The active configuration
        """
        return await self._ai_repository.get_active_configuration(use_case)
    
    async def get_all_configurations(self, use_case: AIUseCase) -> List[AIConfiguration]:
        """
        Get all configurations for a use case.
        
        Args:
            use_case: The use case to get configurations for
            
        Returns:
            List of configurations for the use case
        """
        return await self._ai_repository.get_all_configurations(use_case)
    
    async def create_configuration(self, configuration: AIConfiguration) -> AIConfiguration:
        """
        Create a new configuration.
        
        Args:
            configuration: The configuration to create
            
        Returns:
            The created configuration
            
        Raises:
            ValueError: If the template contains invalid parameters
        """
        # Validate that the template only uses valid parameters
        invalid_params = configuration.use_case.get_invalid_params(configuration.user_prompt_template)
        if invalid_params:
            raise ValueError(
                f"Template for {configuration.use_case} contains invalid parameters: {invalid_params}. "
                f"Valid parameters are: {configuration.use_case.expected_params}"
            )
            
        # Log missing parameters as a warning, but don't block creation
        missing_params = configuration.use_case.get_missing_params(configuration.user_prompt_template)
        if missing_params:
            logger.warning(
                f"Template for {configuration.use_case} is missing some available parameters: {missing_params}. "
                f"This is not an error, but you may want to consider using these parameters."
            )
            
        return await self._ai_repository.create_configuration(configuration)
    
    async def set_active_configuration(self, use_case: AIUseCase, version: int) -> AIConfiguration:
        """
        Set the active configuration for a use case.
        
        Args:
            use_case: The use case to set the active configuration for
            version: The version to set as active
            
        Returns:
            The updated configuration
        """
        return await self._ai_repository.set_active_configuration(use_case, version)
    
    async def delete_configuration(self, use_case: AIUseCase, version: int) -> bool:
        """
        Delete a configuration.
        
        Args:
            use_case: The use case of the configuration
            version: The version of the configuration
            
        Returns:
            True if the configuration was deleted, False otherwise
        """
        return await self._ai_repository.delete_configuration(use_case, version)