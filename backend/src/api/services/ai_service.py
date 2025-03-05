"""
AI Service Layer

This module provides service-level functionality for AI operations,
including generating summaries and checking relevance.
"""

import logging
import json
from typing import Optional, Dict, Tuple, List
from litellm import completion

from ..models.project import Project
from ..models.ai import RelevanceExtraction

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    """
    Service for AI operations in the system.
    
    This class handles all business logic related to AI operations, including
    generating summaries and checking relevance.
    """
    
    def __init__(self):
        """
        Initialize the AIService.
        """
        pass
    
    async def generate_project_summary(self, project: Dict, extracted_note_content: str) -> str:
        """
        Generate a project summary based on its current summary and extracted relevant note content.
        
        Args:
            project: The project to generate summary for (as a dictionary)
            extracted_note_content: The extracted relevant content from the note
            
        Returns:
            The generated summary as a string
        """
        try:
            # Log input parameters
            logger.info(f"Generating summary for project: {project.get('id', 'unknown')} - {project.get('name', 'unknown')}")
            logger.info(f"Project data: {json.dumps(project, default=str)}")
            logger.info(f"Extracted note content length: {len(extracted_note_content)} chars")
            
            # Get current summary
            current_summary = project.get('summary', '')
            
            # Generate a prompt for the AI
            prompt = f"""
            You are an AI assistant that helps summarize project notes.
            
            Project name: {project['name']}
            Project description: {project.get('description', '')}
            Current project summary: {current_summary}
            
            Relevant note content:
            {extracted_note_content}
            
            Based on the relevant note content and the current summary, create an updated summary for this project.
            The summary should include:
            1. Learning Goals - What the user wants to learn or achieve
            2. Next Steps - Concrete actions the user can take
            
            Format the summary with markdown headings (## for main sections).
            Keep it concise (max 250 words) and focused on actionable insights.
            
            Return your response as a JSON object with the following structure:
            {{
                "summary": "The generated summary with markdown formatting"
            }}
            
            Ensure your response is valid JSON and nothing else.
            """
            
            logger.info(f"Sending prompt to AI for project summary generation")
            
            # Call the AI to generate a summary
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Received AI response: {response_text}")
            
            try:
                response_data = json.loads(response_text)
                
                new_summary = response_data.get('summary', current_summary)
                logger.info(f"Successfully generated summary for project {project.get('id', 'unknown')}")
                logger.info(f"New summary length: {len(new_summary)} chars")
                
                return new_summary
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}, response: {response_text}")
                logger.info(f"Falling back to current summary for project {project.get('id', 'unknown')}")
                return current_summary
                
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}")
            # Return the current summary if there's an error
            return current_summary
    
    async def extract_relevant_note_for_project(self, params: Dict) -> RelevanceExtraction:
        """
        Determine if a note is relevant to a project and extract only the relevant details.
        
        Args:
            params: Dictionary containing all parameters:
                - content: The note content
                - project: The project to check relevance against (as a dictionary)
                - user_id: Optional user ID
                - additional_context: Optional additional context for relevance determination
            
        Returns:
            RelevanceExtraction model with relevance information and extracted content
        """
        try:
            # Log input parameters
            content = params.get('content', '')
            project = params.get('project', {})
            user_id = params.get('user_id', 'unknown')
            
            logger.info(f"Extracting relevant content for project: {project.get('id', 'unknown')} - {project.get('name', 'unknown')}")
            logger.info(f"Project data: {json.dumps(project, default=str)}")
            logger.info(f"Note content length: {len(content)} chars")
            logger.info(f"User ID: {user_id}")
            
            # Skip relevance check for Miscellaneous project
            if project.get('name') == 'Miscellaneous':
                logger.info(f"Skipping relevance check for Miscellaneous project")
                return RelevanceExtraction(
                    is_relevant=False,
                    extracted_content=""
                )
                
            # Get project attributes
            project_name = project.get('name', "Unknown Project")
            project_description = project.get('description', "")
            project_summary = project.get('summary', "")
                
            prompt = f"""
            You are an AI assistant that helps categorize and extract relevant information from notes for specific projects.
            
            Project name: {project_name}
            Project description: {project_description}
            Project summary: {project_summary}
            
            Note content:
            {content}
            
            Task:
            1. First, determine if this note is relevant to the project. Consider:
               - Does the note mention topics related to the project?
               - Does the note contain information that would be useful for the project?
               - Does the note describe actions or tasks related to the project?
            
            2. If the note is relevant, extract ONLY the parts of the note that are relevant to this specific project.
               - Focus on extracting actionable insights, key learnings, and next steps
               - Discard any information that is not directly relevant to this project
               - Maintain the original wording where possible
               - Keep the extraction concise but complete
            
            Return your response as a JSON object with the following structure:
            {{
                "is_relevant": true/false,
                "extracted_content": "The extracted content if relevant, empty string otherwise"
            }}
            
            Ensure your response is valid JSON and nothing else.
            """
            
            logger.info(f"Sending prompt to AI for relevance extraction")
            
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Received AI response: {response_text}")
            
            try:
                response_data = json.loads(response_text)
                
                is_relevant = response_data.get('is_relevant', False)
                extracted_content = response_data.get('extracted_content', '')
                
                logger.info(f"Relevance check result for project '{project_name}': {is_relevant}")
                if is_relevant:
                    logger.info(f"Extracted content length: {len(extracted_content)} chars")
                
                result = RelevanceExtraction(
                    is_relevant=is_relevant,
                    extracted_content=extracted_content
                )
                
                logger.info(f"Returning RelevanceExtraction: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}, response: {response_text}")
                logger.info(f"Returning default non-relevant extraction due to JSON parsing error")
                return RelevanceExtraction(
                    is_relevant=False,
                    extracted_content=""
                )
                
        except Exception as e:
            logger.error(f"Error extracting relevant note content: {str(e)}")
            logger.info(f"Returning default non-relevant extraction due to exception")
            return RelevanceExtraction(
                is_relevant=False,
                extracted_content=""
            ) 