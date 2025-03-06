"""
Default AI Configurations

This module provides default configurations for AI operations.
"""

from ..models.ai import AIUseCase

DEFAULT_CONFIGS = {
    AIUseCase.PROJECT_SUMMARY: {
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are an AI assistant that helps summarize project notes.",
        "user_prompt_template": """
        Project name: {project_name}
        Project description: {project_description}
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
        """,
        "max_tokens": 500,
        "temperature": 0.7,
        "description": "Default project summary configuration"
    },
    AIUseCase.RELEVANCE_EXTRACTION: {
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are an AI assistant that helps categorize and extract relevant information from notes.",
        "user_prompt_template": """
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
        """,
        "max_tokens": 800,
        "temperature": 0.7,
        "description": "Default relevance extraction configuration"
    }
} 