from fastapi import APIRouter, HTTPException
import boto3
from litellm import completion
import os
from datetime import datetime
import uuid
from .models import *
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-2'),
    endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
)

# Create tables if they don't exist
def create_tables():
    try:
        # Get list of existing tables
        existing_tables = [table.name for table in dynamodb.tables.all()]
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create Projects table if it doesn't exist
        if 'Projects' not in existing_tables:
            logger.info("Creating Projects table...")
            dynamodb.create_table(
                TableName='Projects',
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Projects table created successfully")
        else:
            logger.info("Projects table already exists")

        # Create Notes table if it doesn't exist
        if 'Notes' not in existing_tables:
            logger.info("Creating Notes table...")
            dynamodb.create_table(
                TableName='Notes',
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Notes table created successfully")
        else:
            logger.info("Notes table already exists")

        # Wait for tables to be active if they were just created
        if 'Projects' not in existing_tables or 'Notes' not in existing_tables:
            logger.info("Waiting for tables to be active...")
            dynamodb.Table('Projects').wait_until_exists()
            dynamodb.Table('Notes').wait_until_exists()
            logger.info("All tables are active")
            
    except Exception as e:
        error_msg = f"Error managing tables: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

async def check_project_relevance(content: str, project: dict) -> bool:
    """Check if note content is relevant to a project using LLM."""
    try:
        logger.info(f"Starting relevance check for project '{project['name']}'")
        logger.info(f"Project description: {project.get('description', 'No description')}")
        logger.info(f"Note content: {content}")
        
        prompt = f"""
        Determine if this note is relevant to the project. Answer ONLY with the word 'true' or 'false'.

        Project:
        - Name: {project['name']}
        - Description: {project.get('description', 'No description provided')}

        Note:
        {content}

        Rules:
        1. ONLY consider explicit information present in the note and project details
        2. Do NOT make assumptions or creative interpretations
        3. For job search projects, only consider actual job application activities
        4. Answer ONLY with 'true' or 'false', no other text

        Is this note relevant to this project?
        """
        
        logger.info("Sending relevance check prompt to LLM")
        
        response = completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        result = 'true' in response.choices[0].message.content.lower()
        logger.info(f"Relevance check response: {response.choices[0].message.content}")
        logger.info(f"Final relevance result: {result}")
        
        return result
    except Exception as e:
        logger.error(f"Error in relevance check: {str(e)}")
        logger.error(f"Project: {project['name']}, Note content: {content[:100]}...")
        return False

async def update_project_summary(project: dict, new_note_content: str):
    """
    Generate a new summary by combining existing summary with new note content.
    Organizes information under appropriate headings for better structure.
    """
    try:
        logger.info(f"Starting summary update for project '{project['name']}'")
        logger.info(f"Current project summary: {project['summary']}")
        logger.info(f"New note content (first 100 chars): {new_note_content[:100]}...")
        
        prompt = f"""
        Create a concise, well-structured summary combining the existing summary and new note.

        Current Summary:
        {project['summary']}

        New Note:
        {new_note_content}

        Strict Content Rules:
        1. Extract and summarize key points only - do not copy text verbatim
        2. Focus on concrete actions, decisions, and outcomes
        3. Use clear, concise language
        4. Combine similar points instead of listing them separately
        5. Keep only the most current/relevant information

        Required Markdown Structure:
        1. Each heading MUST start with '## ' (double hashtag + space)
        2. Add ONE blank line after each heading
        3. Each bullet point MUST start with '- ' (hyphen + space)
        4. Add ONE blank line between bullet points
        5. Add TWO blank lines between sections
        6. No paragraphs - use only headings and bullet points

        Example of Required Format:
        ## Target Companies

        - Actively pursuing roles at Company X and Company Y

        - Focused on AI/ML positions in both organizations


        ## Application Status

        - Submitted application to Company X on [Date]

        - Scheduled technical interview with Company Y


        ## Next Steps

        - Follow up with Company X recruiter

        - Prepare technical presentation for Company Y

        Remember:
        - NEVER include speculative or assumed information
        - Keep summaries brief but informative
        - Maintain exact markdown formatting as shown
        - Focus on key facts and actions
        - Use active voice and present tense
        """

        logger.info("Sending summary generation prompt to LLM")
        
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.1
        )
        
        new_summary = response.choices[0].message.content
        logger.info(f"Generated new summary for project '{project['name']}' (first 100 chars): {new_summary[:100]}...")
        
        return new_summary
    except Exception as e:
        logger.error(f"Error updating summary for project '{project['name']}': {str(e)}")
        raise

# Project endpoints
@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    projects_table = dynamodb.Table('Projects')
    try:
        logger.info(f"Fetching project with ID: {project_id}")
        response = projects_table.get_item(Key={'id': project_id})
        
        if 'Item' not in response:
            logger.warning(f"Project not found with ID: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
            
        logger.info(f"Successfully fetched project: {project_id}")
        return response['Item']
    except Exception as e:
        error_msg = f"Error fetching project {project_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/projects", response_model=List[Project])
async def list_projects():
    projects_table = dynamodb.Table('Projects')
    try:
        response = projects_table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    projects_table = dynamodb.Table('Projects')
    project_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'id': project_id,
        'name': project.name,
        'description': project.description,
        'summary': '',
        'created_at': timestamp
    }
    
    try:
        projects_table.put_item(Item=item)
        return item
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Note endpoints with new structure
@router.post("/notes", response_model=Note)
async def create_note(note: NoteCreate):
    """Create a new note and automatically map it to relevant projects."""
    notes_table = dynamodb.Table('Notes')
    projects_table = dynamodb.Table('Projects')
    
    try:
        logger.info("Starting note creation process")
        logger.info(f"Note content (first 100 chars): {note.content[:100]}...")
        
        # Create note
        note_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Find relevant projects
        logger.info("Fetching all projects")
        projects = projects_table.scan().get('Items', [])
        logger.info(f"Found {len(projects)} projects to check for relevance")
        
        relevant_projects = []
        
        for project in projects:
            logger.info(f"Checking relevance for project: {project['name']}")
            is_relevant = await check_project_relevance(note.content, project)
            
            if is_relevant:
                logger.info(f"Note is relevant to project '{project['name']}'. Updating summary...")
                # Generate new summary incorporating the new note
                new_summary = await update_project_summary(project, note.content)
                
                logger.info(f"Updating project '{project['name']}' with new summary")
                # Update project with new summary
                projects_table.update_item(
                    Key={'id': project['id']},
                    UpdateExpression='SET summary = :summary',
                    ExpressionAttributeValues={':summary': new_summary}
                )
                
                relevant_projects.append(project['id'])
                logger.info(f"Project '{project['name']}' updated successfully")
            else:
                logger.info(f"Note is not relevant to project '{project['name']}'")
        
        logger.info(f"Note is relevant to {len(relevant_projects)} projects")
        
        # Create note item
        note_item = {
            'id': note_id,
            'created_at': timestamp,
            'content': note.content,
            'linked_projects': relevant_projects
        }
        
        # Save note
        logger.info("Saving note to database")
        notes_table.put_item(Item=note_item)
        logger.info("Note saved successfully")
        
        return note_item
    except Exception as e:
        logger.error(f"Error in note creation process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes", response_model=List[Note])
async def list_notes(project_id: Optional[str] = None):
    """Get all notes, optionally filtered by project."""
    notes_table = dynamodb.Table('Notes')
    try:
        if project_id:
            response = notes_table.scan(
                FilterExpression='contains(linked_projects, :pid)',
                ExpressionAttributeValues={':pid': project_id}
            )
        else:
            response = notes_table.scan()
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: str):
    notes_table = dynamodb.Table('Notes')
    try:
        response = notes_table.get_item(Key={'id': note_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Note not found")
        return response['Item']
    except Exception as e:
        logger.error(f"Error fetching note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Recreate tables on startup
@router.on_event("startup")
async def startup_event():
    logger.info("Starting table initialization process")
    create_tables()
    logger.info("Table initialization complete") 