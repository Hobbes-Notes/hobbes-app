"""
AI Service Layer

This module provides service-level functionality for AI operations,
including generating summaries and checking relevance.
"""

import logging
from typing import Optional, Dict
from litellm import completion

from ..models.project import Project

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
    
    async def generate_project_summary(self, project: Project, new_note_content: str) -> str:
        """
        Generate a project summary based on its current summary and a new note.
        
        Args:
            project: The project to generate summary for
            new_note_content: The content of the new note
            
        Returns:
            The generated summary as a string
        """
        try:
            # Convert project to dict if it's a domain model
            if hasattr(project, 'dict'):
                project_dict = project.dict()
            else:
                project_dict = dict(project)
                
            # Get current summary
            current_summary = project_dict.get('summary', '')
            
            # Generate a prompt for the AI
            prompt = f"""
            You are an AI assistant that helps summarize project notes.
            
            Project name: {project_dict['name']}
            Project description: {project_dict.get('description', '')}
            Current project summary: {current_summary}
            
            New note content:
            {new_note_content}
            
            Based on the new note and the current summary, create an updated summary for this project.
            The summary should include:
            1. Learning Goals - What the user wants to learn or achieve
            2. Next Steps - Concrete actions the user can take
            
            Format the summary with markdown headings (## for main sections).
            Keep it concise (max 250 words) and focused on actionable insights.
            """
            
            # Call the AI to generate a summary
            response = completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500
            )
            
            # Extract and return the summary
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}")
            # Return the current summary if there's an error
            return current_summary
    
    async def check_project_relevance(self, content: str, project: Project) -> bool:
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
            if hasattr(project, 'name') and project.name == 'Miscellaneous':
                return False
                
            # Get project attributes
            project_name = project.name if hasattr(project, 'name') else "Unknown Project"
            project_description = project.description if hasattr(project, 'description') else ""
            project_summary = project.summary if hasattr(project, 'summary') else ""
                
            prompt = f"""
            You are an AI assistant that helps categorize notes into relevant projects.
            
            Project name: {project_name}
            Project description: {project_description}
            Project summary: {project_summary}
            
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
            
            logger.info(f"Relevance check result for project '{project_name}': {is_relevant}")
            
            return is_relevant
        except Exception as e:
            logger.error(f"Error checking project relevance: {str(e)}")
            return False 