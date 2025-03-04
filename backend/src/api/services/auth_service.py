"""
Authentication Service Layer

This module provides service-level functionality for user authentication,
including database operations and token validation.
"""

import os
import boto3
import logging
from datetime import datetime
from typing import Optional
import requests as http_requests
from fastapi import HTTPException, status

from ..models.user import User
from .jwt_service import verify_token

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-2'),
    endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
)

logger = logging.getLogger(__name__)

def create_user_tables():
    """
    Create Users table if it doesn't exist
    
    This function initializes the DynamoDB table structure for user data.
    """
    try:
        existing_tables = [table.name for table in dynamodb.tables.all()]
        
        if 'Users' not in existing_tables:
            dynamodb.create_table(
                TableName='Users',
                KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
        # Wait for table to be active
        dynamodb.Table('Users').wait_until_exists()
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise

def get_user_from_db(user_id: str) -> Optional[User]:
    """
    Get user from database
    
    Args:
        user_id: The unique identifier for the user
        
    Returns:
        User object if found, None otherwise
        
    Raises:
        HTTPException: If a database error occurs
    """
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

async def validate_google_token(token: str) -> Optional[User]:
    """
    Validate Google token and return or create user
    
    Args:
        token: The Google OAuth token to validate
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or a database error occurs
    """
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