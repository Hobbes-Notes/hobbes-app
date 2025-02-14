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

def delete_table_if_exists(table_name: str):
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
        logger.info(f"Deleted existing table: {table_name}")
    except Exception as e:
        if 'ResourceNotFoundException' not in str(e):
            logger.error(f"Error deleting table {table_name}: {str(e)}")

# Create tables if they don't exist
def create_tables():
    # Delete existing tables first
    delete_table_if_exists('Projects')
    delete_table_if_exists('Notes')
    
    time.sleep(5)  # Wait for tables to be fully deleted
    
    # Projects table
    try:
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
        logger.info("Projects table created")
    except Exception as e:
        logger.error(f"Error creating Projects table: {str(e)}")
        raise e

    # Notes table with new structure
    try:
        dynamodb.create_table(
            TableName='Notes',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        logger.info("Notes table created")
    except Exception as e:
        logger.error(f"Error creating Notes table: {str(e)}")
        raise e

async def check_project_relevance(content: str, project: dict) -> bool:
    """Check if note content is relevant to a project using LLM."""
    try:
        prompt = f"""
        Task: Determine if the note content is relevant to the project based on semantic meaning and topic relevance.
        
        Note content:
        ---
        {content}
        ---
        
        Project:
        - Name: {project['name']}
        - Description: {project.get('description', 'No description provided')}
        
        Instructions:
        1. Consider both direct mentions and thematic relevance
        2. Look for topical overlap between the note and project
        3. Answer with ONLY 'true' or 'false'
        
        Is this note relevant to this project?
        """
        
        logger.info(f"Checking relevance for project '{project['name']}' with content: {content[:100]}...")
        
        response = await completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1  # Lower temperature for more consistent true/false responses
        )
        
        result = 'true' in response.choices[0].message.content.lower()
        logger.info(f"Relevance check result for project '{project['name']}': {result}")
        logger.info(f"Full LLM response: {response.choices[0].message.content}")
        
        return result
    except Exception as e:
        logger.error(f"Error checking relevance for project '{project['name']}': {str(e)}")
        return False

async def update_project_summary(project_id: str):
    """Update project summary based on all linked notes."""
    try:
        notes_table = dynamodb.Table('Notes')
        projects_table = dynamodb.Table('Projects')
        
        # Get all notes linked to this project
        response = notes_table.scan(
            FilterExpression='contains(linked_projects, :pid)',
            ExpressionAttributeValues={':pid': project_id}
        )
        notes = response.get('Items', [])
        
        if not notes:
            return
        
        # Combine note contents
        notes_text = "\n".join([note['content'] for note in notes])
        
        # Generate new summary
        summary_response = await completion(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Please provide a concise summary of these notes:\n{notes_text}"
            }],
            api_key=os.getenv("OPENAI_API_KEY")
        )
        summary = summary_response.choices[0].message.content
        
        # Update project
        projects_table.update_item(
            Key={'id': project_id},
            UpdateExpression='SET summary = :summary',
            ExpressionAttributeValues={':summary': summary}
        )
    except Exception as e:
        logger.error(f"Error updating project summary: {str(e)}")
        raise

# Project endpoints
@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    projects_table = dynamodb.Table('Projects')
    try:
        response = projects_table.get_item(Key={'id': project_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Project not found")
        return response['Item']
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        # Create note
        note_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Find relevant projects
        projects = projects_table.scan().get('Items', [])
        relevant_projects = set()
        
        for project in projects:
            is_relevant = await check_project_relevance(note.content, project)
            if is_relevant:
                relevant_projects.add(project['id'])
        
        # Create note item
        note_item = {
            'id': note_id,
            'created_at': timestamp,
            'content': note.content,
            'linked_projects': list(relevant_projects)  # DynamoDB doesn't support sets directly
        }
        
        # Save note
        notes_table.put_item(Item=note_item)
        
        # Update summaries for all relevant projects
        for project_id in relevant_projects:
            await update_project_summary(project_id)
        
        return note_item
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
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
    logger.info("Starting table recreation process")
    create_tables()
    logger.info("Table recreation complete") 