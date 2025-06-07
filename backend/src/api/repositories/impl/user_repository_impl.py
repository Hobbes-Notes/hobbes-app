"""
User Repository Implementation

This module provides a DynamoDB implementation of the user repository interface.
"""

import logging
from typing import Optional, Dict

from ..user_repository import UserRepository
from ...models.user import User, UserCreate, UserUpdate
from infrastructure.dynamodb_client import get_dynamodb_client

logger = logging.getLogger(__name__)

class UserRepositoryImpl(UserRepository):
    
    def __init__(self):
        self.dynamodb_client = get_dynamodb_client()
    
    async def create_user_table(self) -> None:
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
    
    def _dict_to_user(self, data: Dict) -> Optional[User]:
        if not data:
            return None
        return User(**data)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        try:
            item = self.dynamodb_client.get_item(table_name='Users', key={'id': user_id})
            return self._dict_to_user(item)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    async def create_user(self, user_data: UserCreate) -> User:
        try:
            from datetime import datetime
            # Convert to dict for DynamoDB
            user_dict = user_data.dict()
            # Add created_at timestamp
            user_dict['created_at'] = datetime.utcnow().isoformat()
            self.dynamodb_client.put_item(table_name='Users', item=user_dict)
            return self._dict_to_user(user_dict)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        try:
            # Convert to dict and remove None values
            update_data = {k: v for k, v in user_data.dict().items() if v is not None}
            
            if not update_data:
                # No fields to update, return current user
                return await self.get_user(user_id)
            
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
                expression_attribute_values=expression_attribute_values,
                return_values='ALL_NEW'
            )
            
            # Get the updated item
            updated_item = self.dynamodb_client.get_item(table_name='Users', key={'id': user_id})
            return self._dict_to_user(updated_item)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise 