"""
AI Models

This module defines models related to AI operations in the system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum

class AIUseCase(str, Enum):
    """
    Enum representing different AI use cases in the system.
    Each use case has an associated list of expected parameters for its prompt template.
    """
    PROJECT_SUMMARY = "project_summary"
    RELEVANCE_EXTRACTION = "relevance_extraction"
    ACTION_MANAGEMENT = "action_management"
    PROJECT_TAGGING = "project_tagging"
    
    @property
    def expected_params(self) -> List[str]:
        """
        Returns a list of parameter names expected in the prompt template for this use case.
        """
        params_map = {
            self.PROJECT_SUMMARY: ["project_name", "project_description", "current_summary", "note_content"],
            self.RELEVANCE_EXTRACTION: ["project_name", "project_description", "note_content", "project_hierarchy"],
            self.ACTION_MANAGEMENT: ["note_content", "existing_action_items", "user_id"],
            self.PROJECT_TAGGING: ["action_items", "user_projects"]
        }
        return params_map.get(self, [])
    
    @property
    def param_descriptions(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping parameter names to their descriptions.
        """
        descriptions = {
            "project_name": "The name of the project",
            "project_description": "The description of the project",
            "current_summary": "The current summary of the project",
            "note_content": "The content of the note",
            "project_hierarchy": "The hierarchical structure of the project with all child projects in nested JSON format",
            "existing_action_items": "JSON list of existing action items that the user currently has",
            "user_id": "The ID of the user",
            "action_items": "JSON list of action items to tag with projects",
            "user_projects": "JSON list of user's projects for tagging action items"
        }
        return {param: descriptions.get(param, "") for param in self.expected_params}
    
    @property
    def response_format(self) -> str:
        """
        Returns the expected response format for this use case.
        This will be appended to the user prompt.
        """
        formats = {
            self.PROJECT_SUMMARY: """
Return your response as a JSON object with the following structure:
{
    "summary": "The generated summary with markdown formatting"
}

Ensure your response is valid JSON and nothing else.
""",
            self.RELEVANCE_EXTRACTION: """
Return your response as a JSON object with the following structure:
{
    "is_relevant": true/false,
    "extracted_content": "The extracted content if relevant, empty string otherwise",
    "annotation": "Brief explanation of why the note is relevant or not relevant to this project"
}

Ensure your response is valid JSON and nothing else.
""",
            self.ACTION_MANAGEMENT: """
Return your response as a JSON object with the following structure:
{
    "action_items": [
        {
            "action": "new|update|complete",
            "id": "existing_action_item_id_if_updating_or_completing",
            "task": "The action item task description",
            "doer": "Who should do this (default to user if not specified)",
            "deadline": "YYYY-MM-DD format if a deadline is mentioned, null otherwise",
            "theme": "A thematic grouping for this action item",
            "context": "Additional context that helps understand or complete the task",
            "extracted_entities": {
                "people": ["list of people mentioned"],
                "places": ["list of places mentioned"],
                "tools": ["list of tools/technologies mentioned"]
            },
            "type": "task|reminder|decision_point"
        }
    ]
}

Ensure your response is valid JSON and nothing else.
""",
            self.PROJECT_TAGGING: """
Return your response as a JSON object with the following structure:
{
    "project_mappings": [
        {
            "action_item_id": "string_id_of_action_item",
            "project_ids": ["array_of_project_ids_that_match"]
        }
    ]
}

Ensure your response is valid JSON and nothing else.
"""
        }
        return formats.get(self, "")
    
    def _extract_template_params(self, template: str) -> List[str]:
        """
        Extracts parameter names from a template string, ignoring escaped curly braces.
        
        Args:
            template: The template string to extract parameters from
            
        Returns:
            List[str]: List of parameter names found in the template
        """
        import re
        
        # First, temporarily replace escaped braces (double braces) with a placeholder
        # This handles JSON examples in the template
        placeholder = "___JSON_PLACEHOLDER___"
        temp_template = template.replace("{{", placeholder).replace("}}", placeholder)
        
        # Now find all parameters in the format {param_name} in the modified template
        found_params = re.findall(r'\{([^{}]+)\}', temp_template)
        
        return found_params
    
    def validate_template(self, template: str) -> bool:
        """
        Validates that a prompt template only uses valid parameters.
        
        Args:
            template: The prompt template string to validate
            
        Returns:
            bool: True if the template only uses valid parameters, False otherwise
        """
        return len(self.get_invalid_params(template)) == 0
        
    def get_missing_params(self, template: str) -> List[str]:
        """
        Returns a list of expected parameters that are missing from the template.
        This is informational only and not used for validation.
        
        Args:
            template: The prompt template string to check
            
        Returns:
            List[str]: List of parameter names that are missing from the template
        """
        found_params = self._extract_template_params(template)
        return [param for param in self.expected_params if param not in found_params]
        
    def get_invalid_params(self, template: str) -> List[str]:
        """
        Returns a list of parameters in the template that are not valid for this use case.
        
        Args:
            template: The prompt template string to check
            
        Returns:
            List[str]: List of parameter names in the template that are not valid
        """
        found_params = self._extract_template_params(template)
        return [param for param in found_params if param not in self.expected_params]

class AIConfiguration(BaseModel):
    """
    Model representing a configuration for an AI operation.
    
    Attributes:
        use_case: The use case this configuration is for
        version: The version of this configuration (auto-generated, input value is ignored)
        model: The AI model to use
        system_prompt: The system prompt that defines the AI assistant's role and behavior
        user_prompt_template: The template for the user prompt with variables to be filled
        max_tokens: Maximum tokens for the response
        temperature: Temperature for response generation
        description: Optional description of this configuration version
        created_at: When this configuration was created
        is_active: Whether this configuration is active
    """
    use_case: AIUseCase
    version: int = 0  # This value is ignored and auto-generated during creation
    model: str
    system_prompt: str
    user_prompt_template: str
    max_tokens: int = 500
    temperature: float = 0.7
    description: Optional[str] = None
    created_at: Optional[str] = None
    is_active: bool = False
    
    def get_key(self) -> str:
        """
        Get a unique key for this configuration.
        
        Returns:
            String in the format "use_case:version"
        """
        return f"{self.use_case}:{self.version}"

class RelevanceExtraction(BaseModel):
    """
    Model representing the result of extracting relevant content from a note for a project.
    
    Attributes:
        is_relevant: Whether the note is relevant to the project
        extracted_content: The extracted relevant content from the note
        annotation: The reason why the note was found to be relevant or not relevant
    """
    is_relevant: bool
    extracted_content: str
    annotation: Optional[str] = None
    
    def __bool__(self):
        """
        Allow using the model in boolean context to check relevance.
        
        Returns:
            True if the note is relevant to the project, False otherwise
        """
        return self.is_relevant 