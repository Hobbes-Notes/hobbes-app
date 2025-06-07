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
        {note_content}
        
        Based on the relevant note content and the current summary, create an updated summary for this project.
        The summary should include:
        1. Learning Goals - What the user wants to learn or achieve
        2. Next Steps - Concrete actions the user can take
        
        Format the summary with markdown headings (## for main sections).
        Keep it concise (max 250 words) and focused on actionable insights.
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
            Project hierarchy (child projects): {project_hierarchy}
            
            Note content:
            {note_content}
            
            Task:
            1. First, determine if this note is relevant to the project. Consider:
            - Does the note mention topics related to the project?
            - Does the note contain information that would be useful for the project?
            - Does the note describe actions or tasks related to the project?
            - Does the note relate to any of the child projects in the hierarchy?
            
            2. If the note is relevant, extract ONLY the parts of the note that are relevant to this specific project.
            - Focus on extracting actionable insights, key learnings, and next steps
            - Discard any information that is not directly relevant to this project
            - Maintain the original wording where possible
            - Keep the extraction concise but complete
            """,
        "max_tokens": 800,
        "temperature": 0.7,
        "description": "Default relevance extraction configuration"
    },
    AIUseCase.ACTION_MANAGEMENT: {
        "model": "gpt-4o-mini",
        "system_prompt": "You are an intelligent action item manager. You help users create, update, and complete action items based on their notes. You excel at understanding task completion, identifying new tasks, and organizing actions effectively.",
        "user_prompt_template": """
        User ID: {user_id}
        
        NEW NOTE CONTENT:
        {note_content}
        
        EXISTING ACTION ITEMS:
        {existing_action_items}
        
        TASK:
        Analyze the new note content and determine what action items should be created, updated, or marked as completed.
        
        INSTRUCTIONS:
        1. **COMPLETE EXISTING ACTIONS**: If the note indicates that any existing action items have been completed, mark them as complete.
        
        2. **UPDATE EXISTING ACTIONS**: If the note provides updates or changes to existing action items, update them accordingly.
        
        3. **CREATE NEW ACTIONS**: Extract new action items from the note content if they represent:
           - Tasks to be done
           - Reminders to set
           - Decisions to be made
           - Follow-ups required
        
        4. **RICH EXTRACTION**: For each action item, extract:
           - **Doer**: Who should do this (default to the user)
           - **Deadline**: If a specific date/time is mentioned
           - **Theme**: A grouping theme (like "vacation planning", "work setup", etc.)
           - **Context**: Additional details that help understand or complete the task
           - **Entities**: People, places, tools mentioned
           - **Type**: task, reminder, or decision_point
        
        EXAMPLES:
        - Note: "Finally deployed the login feature to production" → Mark "Deploy login feature" as completed
        - Note: "Need to call mom tomorrow about vacation plans" → Create reminder with deadline, theme="vacation planning"
        - Note: "The client wants the dashboard blue, not green" → Update existing "Design dashboard" task
        
        NOTE: Do NOT assign projects to action items - that will be handled separately by another process.
        """,
        "max_tokens": 1500,
        "temperature": 0.3,
        "description": "Default action management configuration"
    }
} 