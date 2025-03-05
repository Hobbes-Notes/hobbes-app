"""
Authentication Service Layer

This module provides service-level functionality for user authentication,
including database operations and token validation.
"""

import os
import logging
from datetime import datetime
from typing import Optional
import requests as http_requests
from fastapi import HTTPException, status

from ..models.user import User
from .jwt_service import verify_token
from infrastructure.dynamodb_client import get_dynamodb_client

# Get DynamoDB client
dynamodb_client = get_dynamodb_client()

logger = logging.getLogger(__name__)

async def create_user_tables():
    """
    Create Users table if it doesn't exist
    
    This function initializes the DynamoDB table structure for user data.
    """
    try:
        if not dynamodb_client.table_exists('Users'):
            logger.info("Creating Users table...")
            dynamodb_client.create_table(
                table_name='Users',
                key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            # Wait for table to be active
            dynamodb_client.get_client().get_waiter('table_exists').wait(TableName='Users')
            logger.info("Users table created successfully")
        else:
            logger.info("Users table already exists")
    except Exception as e:
        logger.error(f"Error creating user tables: {str(e)}")
        raise

def get_user_from_db(user_id: str) -> Optional[User]:
    """
    Get a user from the database by ID
    
    Args:
        user_id: The user's ID
        
    Returns:
        User object if found, None otherwise
    """
    try:
        item = dynamodb_client.get_item(table_name='Users', key={'id': user_id})
        if item:
            return User(**item)
        return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None

async def validate_google_token(token: str) -> Optional[User]:
    """
    Validate a Google ID token and get or create the user
    
    Args:
        token: The Google ID token
        
    Returns:
        User object if valid, None otherwise
    """
    try:
        # Verify token with Google
        response = http_requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        )
        
        if response.status_code != 200:
            logger.error(f"Invalid Google token: {response.text}")
            return None
            
        userinfo = response.json()
        
        # Get user from database or create if not exists
        user_id = userinfo['sub']
        
        # Check if user exists
        user = get_user_from_db(user_id)
        
        if not user:
            # Create new user
            user_data = {
                'id': user_id,
                'email': userinfo.get('email', ''),
                'name': userinfo.get('name', ''),
                'picture': userinfo.get('picture', ''),
                'created_at': datetime.now().isoformat()
            }
            
            # Save to database
            dynamodb_client.put_item(table_name='Users', item=user_data)
            
            user = User(**user_data)
            logger.info(f"Created new user: {user.id}")
        
        return user
    except Exception as e:
        logger.error(f"Error validating Google token: {str(e)}")
        return None 