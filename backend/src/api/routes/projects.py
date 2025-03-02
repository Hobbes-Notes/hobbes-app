from fastapi import APIRouter, HTTPException, Query
import boto3
from litellm import completion
import os
from datetime import datetime
import uuid
from typing import List, Optional, Dict
from api.models import Project, ProjectCreate, Note, NoteCreate, ProjectUpdate, PaginatedNotes
import logging
import time
from dotenv import load_dotenv
from fastapi import Depends
from boto3.dynamodb.conditions import Key
import json

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
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user_id-created_at-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Notes table created successfully")
        else:
            logger.info("Notes table already exists")

        # Create ProjectNotes mapping table if it doesn't exist
        if 'ProjectNotes' not in existing_tables:
            logger.info("Creating ProjectNotes mapping table...")
            dynamodb.create_table(
                TableName='ProjectNotes',
                KeySchema=[
                    {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'},
                    {'AttributeName': 'note_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'note_id-index',
                        'KeySchema': [
                            {'AttributeName': 'note_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("ProjectNotes mapping table created successfully")
        else:
            logger.info("ProjectNotes mapping table already exists")

        # Wait for tables to be active if they were just created
        if 'Projects' not in existing_tables or 'Notes' not in existing_tables or 'ProjectNotes' not in existing_tables:
            logger.info("Waiting for tables to be active...")
            dynamodb.Table('Projects').wait_until_exists()
            dynamodb.Table('Notes').wait_until_exists()
            dynamodb.Table('ProjectNotes').wait_until_exists()
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

async def get_or_create_misc_project(user_id: str) -> dict:
    """Get or create the Miscellaneous project for a user."""
    projects_table = dynamodb.Table('Projects')
    try:
        # Try to find existing Miscellaneous project
        response = projects_table.scan(
            FilterExpression='user_id = :uid AND #name = :name',
            ExpressionAttributeNames={'#name': 'name'},
            ExpressionAttributeValues={':uid': user_id, ':name': 'Miscellaneous'}
        )
        
        if response.get('Items'):
            return response['Items'][0]
            
        # Create new Miscellaneous project if not found
        project_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'id': project_id,
            'name': 'Miscellaneous',
            'description': 'Default project for uncategorized notes',
            'summary': '',
            'created_at': timestamp,
            'user_id': user_id
        }
        
        projects_table.put_item(Item=item)
        return item
    except Exception as e:
        logger.error(f"Error managing Miscellaneous project: {str(e)}")
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
async def get_projects(user_id: str):
    projects_table = dynamodb.Table('Projects')
    try:
        # Get all projects for the user
        response = projects_table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )

        # Convert DynamoDB items to Project models
        projects = [Project(**item) for item in response.get('Items', [])]

        # Sort projects by level and name to ensure consistent ordering
        projects.sort(key=lambda x: (x.level or 1, x.name))

        return projects

    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get projects")

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    projects_table = dynamodb.Table('Projects')
    project_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    try:
        logger.info(f"Creating project: {project.name} for user: {project.user_id}")
        logger.info(f"Project details - ID: {project_id}, Description: {project.description}, Parent ID: {project.parent_id}")
        
        # Validate project name length
        if len(project.name.strip()) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Project name must be at least 3 characters long (current length: {})".format(
                    len(project.name.strip())
                )
            )
            
        # Validate description length if provided
        if project.description and len(project.description.strip()) < 5:
            raise HTTPException(
                status_code=400, 
                detail="Project description must be at least 5 characters long (current length: {})".format(
                    len(project.description.strip())
                )
            )

        # Get all existing projects for the user
        existing_projects = projects_table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': project.user_id}
        ).get('Items', [])

        # Filter projects with same parent
        same_level_projects = [p for p in existing_projects 
                             if p.get('parent_id') == project.parent_id]
        
        # Check for duplicate names at the same level
        if any(p['name'].lower() == project.name.strip().lower() 
               for p in same_level_projects):
            raise HTTPException(
                status_code=400, 
                detail="A project with the name '{}' already exists at this level".format(project.name)
            )

        # Determine project level
        level = 1
        if project.parent_id:
            # Find parent project
            parent = next((p for p in existing_projects if p['id'] == project.parent_id), None)
            if not parent:
                raise HTTPException(
                    status_code=400,
                    detail="Parent project not found"
                )
            level = parent.get('level', 1) + 1
            if level > 3:
                raise HTTPException(
                    status_code=400,
                    detail="Maximum nesting level (3) exceeded"
                )
        
        item = {
            'id': project_id,
            'name': project.name.strip(),
            'description': project.description.strip() if project.description else '',
            'summary': '',
            'created_at': timestamp,
            'user_id': project.user_id,
            'parent_id': project.parent_id,
            'level': level
        }
        
        logger.info(f"Project data to be stored: {item}")
        projects_table.put_item(Item=item)
        logger.info(f"Successfully created project: {project_id}")
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error creating project: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"Failed project data: {project_id=}, {project.name=}, {project.user_id=}")
        raise HTTPException(status_code=500, detail=error_msg)

# Note endpoints with new structure
@router.post("/notes", response_model=Note)
async def create_note(note: NoteCreate):
    """Create a new note and automatically map it to relevant projects."""
    notes_table = dynamodb.Table('Notes')
    projects_table = dynamodb.Table('Projects')
    project_notes_table = dynamodb.Table('ProjectNotes')
    
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
        project_names = []
        
        for project in projects:
            if project['name'] != 'Miscellaneous':
                logger.info(f"Checking relevance for project: {project['name']}")
                is_relevant = await check_project_relevance(note.content, project)
                
                if is_relevant:
                    relevant_projects.append(project)
                    project_names.append(project['name'])
                    
                    # Update project summary
                    try:
                        logger.info(f"Updating summary for project: {project['name']}")
                        new_summary = await update_project_summary(project, note.content)
                        projects_table.update_item(
                            Key={'id': project['id']},
                            UpdateExpression='SET summary = :summary',
                            ExpressionAttributeValues={':summary': new_summary}
                        )
                        logger.info(f"Summary updated for project: {project['name']}")
                    except Exception as e:
                        logger.error(f"Error updating summary for project {project['name']}: {str(e)}")
        
        # If no relevant projects found, add to Miscellaneous project
        if not relevant_projects:
            logger.info("No relevant projects found, adding to Miscellaneous")
            misc_project = await get_or_create_misc_project(note.user_id)
            relevant_projects.append(misc_project)
            project_names.append('Miscellaneous')
            
            # Update Miscellaneous project summary
            try:
                logger.info("Updating Miscellaneous project summary")
                new_summary = await update_project_summary(misc_project, note.content)
                projects_table.update_item(
                    Key={'id': misc_project['id']},
                    UpdateExpression='SET summary = :summary',
                    ExpressionAttributeValues={':summary': new_summary}
                )
                logger.info("Miscellaneous project summary updated")
            except Exception as e:
                logger.error(f"Error updating Miscellaneous project summary: {str(e)}")
        
        # Create note item
        note_item = {
            'id': note_id,
            'created_at': timestamp,
            'content': note.content,
            'user_id': note.user_id,
            'projects': []  # Initialize empty projects list
        }
        
        # Save note
        logger.info("Saving note to database")
        notes_table.put_item(Item=note_item)
        
        # Create project-note mappings and build projects list for response
        project_refs = []
        for project in relevant_projects:
            project_notes_table.put_item(
                Item={
                    'project_id': project['id'],
                    'created_at': timestamp,
                    'note_id': note_id
                }
            )
            project_refs.append({
                'id': project['id'],
                'name': project['name']
            })
        
        # Add project details to response
        note_item['projects'] = project_refs
        
        logger.info("Note and project mappings saved successfully")
        return note_item
    except Exception as e:
        logger.error(f"Error in note creation process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_pagination_key(page: int, user_id: str) -> Optional[dict]:
    """Helper function to get the pagination key for GSI queries."""
    if page <= 1:
        return None
        
    notes_table = dynamodb.Table('Notes')
    try:
        # Calculate how many items to skip
        items_to_skip = (page - 1) * 10
        
        # Query the GSI to get the last evaluated key for the previous page
        response = notes_table.query(
            IndexName='user_id-created_at-index',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,
            Limit=items_to_skip
        )
        
        # If we have a LastEvaluatedKey and we've fetched enough items,
        # return it for the next query
        if response.get('LastEvaluatedKey') and len(response.get('Items', [])) >= items_to_skip:
            return response['LastEvaluatedKey']
        return None
    except Exception as e:
        logger.error(f"Error getting pagination key: {str(e)}")
        return None

def get_notes_by_project(table, project_notes_table, projects_table, project_id: str, page_size: int, exclusive_start_key: Optional[dict] = None) -> dict:
    """
    Query notes by project_id using the ProjectNotes mapping table.
    Returns notes sorted by created_at in descending order with project details.
    """
    # First, query the ProjectNotes table to get note IDs for the project
    query_params = {
        'TableName': 'ProjectNotes',
        'KeyConditionExpression': 'project_id = :pid',
        'ExpressionAttributeValues': {':pid': project_id},
        'ScanIndexForward': False,  # Sort in descending order
        'Limit': page_size
    }
    
    if exclusive_start_key:
        query_params['ExclusiveStartKey'] = exclusive_start_key
        
    project_notes_response = project_notes_table.query(**query_params)
    
    # Get the note IDs from the mapping table results
    note_ids = [item['note_id'] for item in project_notes_response.get('Items', [])]
    
    # If no notes found, return empty result
    if not note_ids:
        return {
            'Items': [],
            'LastEvaluatedKey': project_notes_response.get('LastEvaluatedKey')
        }
    
    # Batch get the actual notes
    notes = []
    for i in range(0, len(note_ids), 25):  # Process in batches of 25 (DynamoDB limit)
        batch = note_ids[i:i + 25]
        response = dynamodb.batch_get_item(
            RequestItems={
                'Notes': {
                    'Keys': [{'id': note_id} for note_id in batch]
                }
            }
        )
        notes.extend(response['Responses']['Notes'])
    
    # Sort notes by created_at in descending order
    notes.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Get project details for each note
    for note in notes:
        # Query ProjectNotes table for all projects linked to this note
        project_mappings = project_notes_table.query(
            IndexName='note_id-index',
            KeyConditionExpression='note_id = :nid',
            ExpressionAttributeValues={':nid': note['id']}
        ).get('Items', [])
        
        # Get project details
        project_ids = [mapping['project_id'] for mapping in project_mappings]
        projects = []
        for pid in project_ids:
            project = projects_table.get_item(Key={'id': pid}).get('Item')
            if project:
                projects.append({
                    'id': project['id'],
                    'name': project['name']
                })
        note['projects'] = projects
    
    return {
        'Items': notes,
        'LastEvaluatedKey': project_notes_response.get('LastEvaluatedKey')
    }

def get_notes_by_user(table, project_notes_table, projects_table, user_id: str, page_size: int, exclusive_start_key: Optional[dict] = None) -> dict:
    """
    Query notes by user_id using the user_id-created_at-index GSI.
    Returns notes sorted by created_at in descending order with project details.
    """
    query_params = {
        'IndexName': 'user_id-created_at-index',
        'KeyConditionExpression': 'user_id = :uid',
        'ExpressionAttributeValues': {':uid': user_id},
        'ScanIndexForward': False,  # Sort in descending order
        'Limit': page_size
    }
    
    if exclusive_start_key:
        query_params['ExclusiveStartKey'] = exclusive_start_key
        
    response = table.query(**query_params)
    notes = response.get('Items', [])
    
    # Get project details for each note
    for note in notes:
        # Query ProjectNotes table for all projects linked to this note
        project_mappings = project_notes_table.query(
            IndexName='note_id-index',
            KeyConditionExpression='note_id = :nid',
            ExpressionAttributeValues={':nid': note['id']}
        ).get('Items', [])
        
        # Get project details
        project_ids = [mapping['project_id'] for mapping in project_mappings]
        projects = []
        for pid in project_ids:
            project = projects_table.get_item(Key={'id': pid}).get('Item')
            if project:
                projects.append({
                    'id': project['id'],
                    'name': project['name']
                })
        note['projects'] = projects
    
    return {
        'Items': notes,
        'LastEvaluatedKey': response.get('LastEvaluatedKey')
    }

@router.get("/notes", response_model=PaginatedNotes)
async def list_notes(
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, gt=0),
    page_size: int = Query(10, gt=0, le=50),
    exclusive_start_key: Optional[str] = None
):
    """
    Get paginated notes, filtered by project or user, sorted by created_at desc.
    Uses GSIs for efficient querying and pagination.
    Either project_id or user_id must be provided.
    """
    if not project_id and not user_id:
        raise HTTPException(
            status_code=400,
            detail="Either project_id or user_id must be provided"
        )

    notes_table = dynamodb.Table('Notes')
    project_notes_table = dynamodb.Table('ProjectNotes')
    projects_table = dynamodb.Table('Projects')
    
    try:
        # Convert exclusive_start_key from string to dict if provided
        start_key = None
        if exclusive_start_key:
            try:
                start_key = json.loads(exclusive_start_key)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid exclusive_start_key format")

        # Fetch one extra item to determine if there are more pages
        actual_limit = page_size + 1
        
        if project_id:
            response = get_notes_by_project(notes_table, project_notes_table, projects_table, project_id, actual_limit, start_key)
        else:  # user_id is present since we checked above
            response = get_notes_by_user(notes_table, project_notes_table, projects_table, user_id, actual_limit, start_key)

        # Get items and check if we have more
        items = response.get('Items', [])
        has_more = len(items) > page_size
        
        # Remove the extra item if we fetched one
        if has_more:
            items = items[:page_size]

        # Convert DynamoDB items to Note models and ensure projects field exists
        for item in items:
            if 'projects' not in item:
                item['projects'] = []
            if 'linked_projects' in item:
                del item['linked_projects']

        return PaginatedNotes(
            items=items,
            page=page,
            page_size=page_size,
            has_more=has_more,
            LastEvaluatedKey=response.get('LastEvaluatedKey')
        )
            
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

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its child projects recursively"""
    projects_table = dynamodb.Table('Projects')
    project_notes_table = dynamodb.Table('ProjectNotes')
    
    try:
        # Check if project exists
        response = projects_table.get_item(Key={'id': project_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Project not found")
            
        project = response['Item']
        
        # Get all projects to find children
        all_projects = projects_table.scan().get('Items', [])
        
        # Function to get all descendant project IDs recursively
        def get_descendant_ids(parent_id):
            children = [p for p in all_projects if p.get('parent_id') == parent_id]
            descendant_ids = [parent_id]
            for child in children:
                descendant_ids.extend(get_descendant_ids(child['id']))
            return descendant_ids
        
        # Get all projects to be deleted (including descendants)
        projects_to_delete = get_descendant_ids(project_id)
        
        logger.info(f"Deleting project {project_id} and {len(projects_to_delete) - 1} child projects")
        
        # Delete all projects and their note mappings
        for pid in projects_to_delete:
            # Delete all project-note mappings for this project
            while True:
                # Query for project-note mappings
                mappings = project_notes_table.query(
                    KeyConditionExpression='project_id = :pid',
                    ExpressionAttributeValues={':pid': pid}
                )
                
                if not mappings.get('Items'):
                    break
                    
                # Delete mappings in batches
                with project_notes_table.batch_writer() as batch:
                    for mapping in mappings['Items']:
                        batch.delete_item(
                            Key={
                                'project_id': mapping['project_id'],
                                'created_at': mapping['created_at']
                            }
                        )
            
            # Delete the project
            projects_table.delete_item(Key={'id': pid})
        
        return {"message": f"Project and {len(projects_to_delete) - 1} child projects deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate):
    """Update a project's details"""
    projects_table = dynamodb.Table('Projects')
    try:
        # Check if project exists
        response = projects_table.get_item(Key={'id': project_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build update expression and attribute values
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        if project_update.name is not None:
            update_expr += "#name = :name, "
            expr_attr_values[':name'] = project_update.name
            expr_attr_names['#name'] = 'name'
            
        if project_update.description is not None:
            update_expr += "description = :description, "
            expr_attr_values[':description'] = project_update.description
            
        if project_update.summary is not None:
            update_expr += "summary = :summary, "
            expr_attr_values[':summary'] = project_update.summary

        # Remove trailing comma and space
        update_expr = update_expr.rstrip(", ")

        # Only update if there are changes
        if expr_attr_values:
            update_params = {
                'Key': {'id': project_id},
                'UpdateExpression': update_expr,
                'ExpressionAttributeValues': expr_attr_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if expr_attr_names:
                update_params['ExpressionAttributeNames'] = expr_attr_names

            response = projects_table.update_item(**update_params)
            return response['Attributes']
        
        # If no changes, return existing project
        return response['Item']
    except Exception as e:
        error_msg = f"Error updating project {project_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# Recreate tables on startup
@router.on_event("startup")
async def startup_event():
    logger.info("Starting table initialization process")
    create_tables()
    logger.info("Table initialization complete") 