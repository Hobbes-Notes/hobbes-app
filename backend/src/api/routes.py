from fastapi import APIRouter, HTTPException
import boto3
from litellm import completion
import os
from datetime import datetime
import uuid
from .models import *
import logging
import time

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-2')
)

# Create tables if they don't exist
def create_tables():
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
        if 'Table already exists' not in str(e):
            logger.error(f"Error creating Projects table: {str(e)}")
            raise e

    # Notes table
    try:
        dynamodb.create_table(
            TableName='Notes',
            KeySchema=[
                {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'project_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        logger.info("Notes table created")
    except Exception as e:
        if 'Table already exists' not in str(e):
            logger.error(f"Error creating Notes table: {str(e)}")
            raise e

# Recreate tables on startup
@router.on_event("startup")
async def startup_event():
    logger.info("Starting table recreation process")  # Wait for AWS to complete deletion
    create_tables()
    logger.info("Table recreation complete")

# Project endpoints
@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    projects_table = dynamodb.Table('Projects')
    try:
        logger.info(f"Fetching project with ID: {project_id}")
        response = projects_table.get_item(Key={'id': project_id})
        logger.info(f"DynamoDB response: {response}")
        
        if 'Item' not in response:
            # List all projects to debug
            all_projects = projects_table.scan()
            logger.info(f"All projects in table: {all_projects.get('Items', [])}")
            raise HTTPException(status_code=404, detail="Project not found")
            
        return response['Item']
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[Project])
async def list_projects():
    projects_table = dynamodb.Table('Projects')
    try:
        logger.info("Scanning projects table")
        response = projects_table.scan()
        projects = response.get('Items', [])
        logger.info(f"Found {len(projects)} projects")
        return projects
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
        logger.info(f"Creating project: {item}")
        projects_table.put_item(Item=item)
        return item
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Note endpoints
@router.post("/projects/{project_id}/notes", response_model=Note)
async def create_note(project_id: str, note: NoteCreate):
    projects_table = dynamodb.Table('Projects')
    try:
        project_response = projects_table.get_item(Key={'id': project_id})
        logger.info(f"Project response: {project_response}")
        if 'Item' not in project_response:
            logger.error(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        notes_table = dynamodb.Table('Notes')
        timestamp = datetime.utcnow().isoformat()
        
        note_item = {
            'project_id': project_id,
            'created_at': timestamp,
            'content': note.content,
            'id': str(uuid.uuid4())
        }
        
        logger.info(f"Creating note: {note_item}")
        notes_table.put_item(Item=note_item)
        
        # Get all notes for summary
        notes_response = notes_table.query(
            KeyConditionExpression='project_id = :pid',
            ExpressionAttributeValues={
                ':pid': project_id
            }
        )
        
        all_notes = notes_response.get('Items', [])
        notes_text = "\n".join([n['content'] for n in all_notes])
        
        if notes_text:  # Only generate summary if there are notes
            try:
                summary_response = completion(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"Please provide a concise summary of these notes:\n{notes_text}"
                    }],
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                summary = summary_response.choices[0].message.content
                
                projects_table.update_item(
                    Key={'id': project_id},
                    UpdateExpression='SET summary = :summary',
                    ExpressionAttributeValues={':summary': summary}
                )
            except Exception as e:
                logger.error(f"Error generating summary: {str(e)}")
        
        return note_item
    except Exception as e:
        logger.error(f"Error in create_note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/notes", response_model=List[Note])
async def list_notes(project_id: str):
    notes_table = dynamodb.Table('Notes')
    try:
        logger.info(f"Fetching notes for project: {project_id}")
        response = notes_table.query(
            KeyConditionExpression='project_id = :pid',
            ExpressionAttributeValues={
                ':pid': project_id
            },
            ScanIndexForward=False  # Get newest notes first
        )
        notes = response.get('Items', [])
        logger.info(f"Found {len(notes)} notes")
        return notes
    except Exception as e:
        logger.error(f"Error listing notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ... rest of your existing endpoints ... 