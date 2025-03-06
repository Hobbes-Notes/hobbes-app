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

from ..models.project import Project
from ..models.ai import RelevanceExtraction, AIUseCase, AIConfiguration
from ..repositories.ai_repository import AIRepository
from ..models.note import Note

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
    
    async def generate_project_summary(self, project: Project, extracted_note_content: str) -> str:
        """
        Generate a summary for a project based on extracted note content.
        
        Args:
            project: The project to generate a summary for
            extracted_note_content: The extracted content from relevant notes
            
        Returns:
            The generated summary
        """
        logger.info(f"Starting project summary generation for project {project.id} - '{project.name}'")
        
        if not self._client:
            logger.error("OpenAI client not initialized. Cannot generate project summary.")
            return "Unable to generate summary: AI service not configured."
        
        try:
            # Log input parameters
            logger.info(f"Generating summary for project: {project.id} - {project.name}")
            logger.debug(f"Project data: {json.dumps({k: str(v) for k, v in project.__dict__.items() if not k.startswith('_')}, default=str)}")
            logger.debug(f"Extracted note content length: {len(extracted_note_content)} chars")
            logger.debug(f"Extracted content preview: '{extracted_note_content[:100]}...'")
            
            # Get current summary
            current_summary = project.summary or ""
            logger.debug(f"Current summary length: {len(current_summary)} chars")
            if current_summary:
                logger.debug(f"Current summary preview: '{current_summary[:100]}...'")
            else:
                logger.debug("No existing summary found for this project")
            
            # Get the active configuration for project summary
            logger.debug(f"Fetching AI configuration for PROJECT_SUMMARY use case")
            config = await self._get_configuration(AIUseCase.PROJECT_SUMMARY)
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Prepare variables for the template
            project_name = project.name
            project_description = project.description or ""
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    project_name=project_name,
                    project_description=project_description,
                    current_summary=current_summary,
                    extracted_note_content=extracted_note_content
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"User prompt length: {len(user_prompt)} chars")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: project_name, project_description, current_summary, extracted_note_content")
                # Fallback to a basic prompt if template formatting fails
                user_prompt = f"""
                Project: {project_name}
                Description: {project_description}
                Current summary: {current_summary}
                
                Relevant note content:
                {extracted_note_content}
                
                Generate an updated summary for this project based on the note content.
                Return JSON with "summary" containing the generated summary with markdown formatting.
                """
                logger.warning(f"Using fallback prompt due to template formatting error")
            
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
    
    async def extract_relevant_note_for_project(self, params: Dict[str, Any]) -> RelevanceExtraction:
        """
        Extract relevant content from a note for a specific project.
        
        Args:
            params: Dictionary containing:
                - content: The note content
                - project: The project to check relevance for
                - user_id: The user ID
                
        Returns:
            RelevanceExtraction object with is_relevant and extracted_content
        """
        logger.info("Starting relevance extraction process")
        
        if not self._client:
            logger.error("OpenAI client not initialized. Cannot extract relevant content.")
            return RelevanceExtraction(is_relevant=False, extracted_content="")
        
        try:
            # Extract parameters
            content = params.get("content", "")
            project = params.get("project", {})
            user_id = params.get("user_id", "")
            
            # Log input parameters
            logger.info(f"Extracting relevance for user: {user_id}, project: {project.get('id', 'unknown')} - '{project.get('name', 'unknown')}'")
            logger.debug(f"Content length: {len(content)} chars")
            logger.debug(f"Content preview: '{content[:100]}...'")
            logger.debug(f"Project data: {json.dumps(project, default=str)}")
            
            # Get the active configuration for relevance extraction
            logger.debug("Fetching AI configuration for RELEVANCE_EXTRACTION use case")
            config = await self._get_configuration(AIUseCase.RELEVANCE_EXTRACTION)
            logger.debug(f"Using model: {config.model}, max_tokens: {config.max_tokens}, temperature: {config.temperature}")
            
            # Log the template before replacement
            logger.debug(f"Prompt template before replacement:\n{config.user_prompt_template}")
            
            # Prepare variables for the template
            project_name = project.get("name", "")
            project_description = project.get("description", "")
            project_summary = project.get("summary", "")
            
            # Safely format the template
            try:
                user_prompt = config.user_prompt_template.format(
                    project_name=project_name,
                    project_description=project_description,
                    project_summary=project_summary,
                    content=content
                )
                logger.debug(f"Prompt after replacement (first 500 chars):\n{user_prompt[:500]}...")
                logger.debug(f"Prepared user prompt with length: {len(user_prompt)}")
            except KeyError as e:
                logger.error(f"Error formatting prompt template: {str(e)}")
                logger.error(f"Template: {config.user_prompt_template}")
                logger.error(f"Available variables: project_name, project_description, project_summary, content")
                # Fallback to a basic prompt if template formatting fails
                user_prompt = f"""
                Project: {project_name}
                Description: {project_description}
                Summary: {project_summary}
                
                Note content:
                {content}
                
                Determine if this note is relevant to the project and extract relevant content.
                Return JSON with "is_relevant" (boolean) and "extracted_content" (string).
                """
                logger.warning(f"Using fallback prompt due to template formatting error")
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for relevance extraction for project {project.get('id', 'unknown')}")
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
                is_relevant = response_json.get("is_relevant", False)
                extracted_content = response_json.get("extracted_content", "")
                
                logger.info(f"Relevance determination: {'Relevant' if is_relevant else 'Not relevant'}")
                if is_relevant:
                    logger.debug(f"Extracted content length: {len(extracted_content)} chars")
                    logger.debug(f"Extracted content preview: '{extracted_content[:100]}...'")
                
                return RelevanceExtraction(
                    is_relevant=is_relevant,
                    extracted_content=extracted_content
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                return RelevanceExtraction(is_relevant=False, extracted_content="")
                
        except Exception as e:
            logger.exception(f"Error extracting relevance: {str(e)}")
            return RelevanceExtraction(is_relevant=False, extracted_content="")
    
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
        """
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