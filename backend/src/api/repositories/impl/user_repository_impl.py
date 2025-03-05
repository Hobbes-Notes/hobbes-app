"""
User Repository Implementation

This module provides the implementation for user data operations.
"""

import logging
from typing import Optional, Dict

from ..user_repository import UserRepository
from infrastructure.dynamodb_client import get_dynamodb_client

logger = logging.getLogger(__name__)

class UserRepositoryImpl(UserRepository):
    """Implementation of the UserRepository interface."""
    
    def __init__(self):
        """Initialize the repository with a DynamoDB client."""
        self.dynamodb_client = get_dynamodb_client()
    
    async def create_user_table(self) -> None:
        """Create the Users table if it doesn't exist."""
        try:
            if not self.dynamodb_client.table_exists('Users'):
                logger.info("Creating Users table...")
                self.dynamodb_client.create_table(
                    table_name='Users',
                    key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                    provisioned_throughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                
                # Wait for table to be active
                self.dynamodb_client.get_client().get_waiter('table_exists').wait(TableName='Users')
                logger.info("Users table created successfully")
            else:
                logger.info("Users table already exists")
        except Exception as e:
            logger.error(f"Error creating user tables: {str(e)}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User data dictionary if found, None otherwise
        """
        try:
            item = self.dynamodb_client.get_item(table_name='Users', key={'id': user_id})
            return item
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    async def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user.
        
        Args:
            user_data: The user data to save
            
        Returns:
            The created user data
        """
        try:
            self.dynamodb_client.put_item(table_name='Users', item=user_data)
            return user_data
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """
        Update a user.
        
        Args:
            user_id: The user's ID
            user_data: The user data to update
            
        Returns:
            The updated user data
        """
        try:
            # Remove id from update data as it's the key
            update_data = {k: v for k, v in user_data.items() if k != 'id'}
            
            # Build update expression
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_data.keys())
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
            
            # Update item
            self.dynamodb_client.update_item(
                table_name='Users',
                key={'id': user_id},
                update_expression=update_expression,
                expression_attribute_names=expression_attribute_names,
                expression_attribute_values=expression_attribute_values
            )
            
            # Get updated item
            return await self.get_user(user_id)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise 