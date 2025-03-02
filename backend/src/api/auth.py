from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import boto3
from datetime import datetime
from typing import Optional, List
from .models import User, UserActivity
import requests as http_requests
import logging
from .jwt import verify_token

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-2'),
    endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

def create_user_tables():
    """Create Users and UserActivity tables if they don't exist"""
    try:
        existing_tables = [table.name for table in dynamodb.tables.all()]
        
        if 'Users' not in existing_tables:
            dynamodb.create_table(
                TableName='Users',
                KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
        
        if 'UserActivity' not in existing_tables:
            dynamodb.create_table(
                TableName='UserActivity',
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            logger.info("UserActivity table created successfully")
        else:
            logger.info("UserActivity table already exists")
            
        # Wait for tables to be active
        dynamodb.Table('Users').wait_until_exists()
        dynamodb.Table('UserActivity').wait_until_exists()
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        raise

def get_user_from_db(user_id: str) -> Optional[User]:
    """Get user from database"""
    try:
        users_table = dynamodb.Table('Users')
        response = users_table.get_item(Key={'id': user_id})
        if 'Item' in response:
            return User(**response['Item'])
        return None
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        user = get_user_from_db(payload["sub"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def validate_google_token(token: str) -> Optional[User]:
    """Validate Google token and return or create user"""
    try:
        # Get user info from Google
        response = http_requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code != 200:
            raise ValueError("Invalid token")
            
        userinfo = response.json()
        
        # Get user from database or create if not exists
        users_table = dynamodb.Table('Users')
        user_id = userinfo['sub']
        
        try:
            response = users_table.get_item(Key={'id': user_id})
            
            if 'Item' not in response:
                # Create new user
                user = {
                    'id': user_id,
                    'email': userinfo['email'],
                    'name': userinfo['name'],
                    'picture_url': userinfo.get('picture'),
                    'created_at': datetime.utcnow().isoformat()
                }
                users_table.put_item(Item=user)
            else:
                user = response['Item']
            
            # Log activity
            log_user_activity(user_id, "session_validated")
            
            return User(**user)
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

def log_user_activity(user_id: str, activity_type: str, details: dict = None):
    """Log user activity with additional details"""
    try:
        logger.info(f"Attempting to log activity - Type: {activity_type}, User: {user_id}")
        logger.info(f"Activity details: {details}")
        
        activity_table = dynamodb.Table('UserActivity')
        activity = {
            'user_id': user_id,
            'activity_type': activity_type,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        logger.info(f"Activity data to be stored: {activity}")
        
        activity_table.put_item(Item=activity)
        logger.info("Activity logged successfully")
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        logger.error(f"Failed activity data: {activity_type=}, {user_id=}, {details=}")
        # Don't raise the error as this is a non-critical operation

async def get_user_activities(user_id: str, limit: int = 10) -> List[UserActivity]:
    """Get user's recent activities"""
    try:
        activity_table = dynamodb.Table('UserActivity')
        response = activity_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=limit,
            ScanIndexForward=False  # Sort in descending order (most recent first)
        )
        return [UserActivity(**item) for item in response.get('Items', [])]
    except Exception as e:
        print(f"Error fetching activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user activities"
        ) 