"""
AI File Repository Implementation

This module provides a DynamoDB implementation of the AI file repository interface.
"""

import logging
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from api.repositories.ai_file_repository import AIFileRepository
from api.models.ai_file import AIFileRecord, AIFileState
from infrastructure.dynamodb_client import get_dynamodb_client

# Set up logging
logger = logging.getLogger(__name__)

class AIFileRepositoryImpl(AIFileRepository):
    """
    Implementation of the AI file repository with DynamoDB persistence.
    """
    
    def __init__(self, table_name: str = "ai_file_records"):
        """
        Initialize the repository.
        """
        self._table_name = table_name
        self._dynamodb_client = get_dynamodb_client()
        
        # Ensure the table exists
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """
        Ensure the DynamoDB table exists, creating it if necessary.
        """
        if not self._dynamodb_client.table_exists(self._table_name):
            logger.info(f"Creating DynamoDB table: {self._table_name}")
            
            # Create the table
            self._dynamodb_client.create_table(
                table_name=self._table_name,
                key_schema=[
                    {
                        'AttributeName': 'file_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                attribute_definitions=[
                    {
                        'AttributeName': 'file_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'state',
                        'AttributeType': 'S'
                    }
                ],
                global_secondary_indexes=[
                    {
                        'IndexName': 'user_id-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'state-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'state',
                                'KeyType': 'HASH'
                            }
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
                provisioned_throughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            logger.info(f"Created DynamoDB table: {self._table_name}")
    
    def _record_to_item(self, record: AIFileRecord) -> Dict[str, Any]:
        """
        Convert a file record to a DynamoDB item.
        
        Args:
            record: The file record to convert
            
        Returns:
            DynamoDB item dictionary
        """
        item = {
            'file_id': record.file_id,
            'user_id': record.user_id,
            'state': record.state.value,
            'created_at': record.created_at,
            'updated_at': record.updated_at,
            'input_s3_key': record.input_s3_key,
            'output_s3_key': record.output_s3_key if record.output_s3_key else None,
            'error_message': record.error_message if record.error_message else None,
            'metadata': record.metadata if record.metadata else {},
        }
        
        if record.total_records is not None:
            item['total_records'] = record.total_records
            
        if record.processed_records is not None:
            item['processed_records'] = record.processed_records
            
        return item
    
    def _item_to_record(self, item: Dict[str, Any]) -> AIFileRecord:
        """
        Convert a DynamoDB item to a file record.
        
        Args:
            item: The DynamoDB item to convert
            
        Returns:
            File record
        """
        return AIFileRecord(
            file_id=item['file_id'],
            user_id=item['user_id'],
            state=AIFileState(item['state']),
            created_at=item['created_at'],
            updated_at=item['updated_at'],
            input_s3_key=item['input_s3_key'],
            output_s3_key=item.get('output_s3_key'),
            error_message=item.get('error_message'),
            metadata=item.get('metadata', {}),
            total_records=item.get('total_records'),
            processed_records=item.get('processed_records')
        )
    
    async def get_file_record(self, file_id: str) -> Optional[AIFileRecord]:
        """
        Get a file record by ID.
        
        Args:
            file_id: The ID of the file record to get
            
        Returns:
            The file record if found, None otherwise
        """
        try:
            item = self._dynamodb_client.get_item(
                table_name=self._table_name,
                key={'file_id': file_id}
            )
            
            if not item:
                return None
                
            return self._item_to_record(item)
        except Exception as e:
            logger.error(f"Error getting file record {file_id}: {str(e)}")
            raise
    
    async def get_file_records_by_user(self, user_id: str) -> List[AIFileRecord]:
        """
        Get all file records for a user.
        
        Args:
            user_id: The ID of the user to get file records for
            
        Returns:
            List of file records for the user, sorted by created_at in descending order (latest first)
        """
        try:
            response = self._dynamodb_client.query(
                table_name=self._table_name,
                index_name='user_id-index',
                key_condition_expression=Key('user_id').eq(user_id)
            )
            
            items = response.get('Items', [])
            records = [self._item_to_record(item) for item in items]
            
            # Sort records by created_at in descending order (latest first)
            records.sort(key=lambda x: x.created_at, reverse=True)
            
            return records
        except Exception as e:
            logger.error(f"Error getting file records for user {user_id}: {str(e)}")
            raise
    
    async def create_file_record(self, file_record: AIFileRecord) -> AIFileRecord:
        """
        Create a new file record.
        
        Args:
            file_record: The file record to create
            
        Returns:
            The created file record
        """
        try:
            # Convert to DynamoDB item
            item = self._record_to_item(file_record)
            
            # Put item in DynamoDB
            self._dynamodb_client.put_item(
                table_name=self._table_name,
                item=item
            )
            
            logger.info(f"Created file record {file_record.file_id}")
            return file_record
        except Exception as e:
            logger.error(f"Error creating file record: {str(e)}")
            raise
    
    async def update_file_record(self, file_id: str, updates: Dict[str, Any]) -> Optional[AIFileRecord]:
        """
        Update a file record.
        
        Args:
            file_id: The ID of the file record to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated file record if found, None otherwise
        """
        try:
            # Get the current record
            record = await self.get_file_record(file_id)
            if not record:
                return None
                
            # Prepare update expression and attribute values
            update_expression_parts = []
            expression_attribute_values = {}
            
            for key, value in updates.items():
                if key in ['file_id', 'user_id', 'created_at']:
                    # Skip immutable fields
                    continue
                    
                update_expression_parts.append(f"#{key} = :{key}")
                expression_attribute_values[f":{key}"] = value
                
            # Always update the updated_at timestamp
            update_expression_parts.append("#updated_at = :updated_at")
            expression_attribute_values[":updated_at"] = datetime.now().isoformat()
            
            # Build the update expression
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            # Build expression attribute names
            expression_attribute_names = {f"#{key}": key for key in updates.keys() if key not in ['file_id', 'user_id', 'created_at']}
            expression_attribute_names["#updated_at"] = "updated_at"
            
            # Update the item
            result = self._dynamodb_client.update_item(
                table_name=self._table_name,
                key={'file_id': file_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
                expression_attribute_names=expression_attribute_names,
                return_values="ALL_NEW"
            )
            
            if 'Attributes' not in result:
                return None
                
            logger.info(f"Updated file record {file_id}")
            return self._item_to_record(result['Attributes'])
        except Exception as e:
            logger.error(f"Error updating file record {file_id}: {str(e)}")
            raise
    
    async def update_file_state(self, file_id: str, state: AIFileState, 
                              error_message: Optional[str] = None) -> Optional[AIFileRecord]:
        """
        Update the state of a file record.
        
        Args:
            file_id: The ID of the file record to update
            state: The new state of the file
            error_message: Optional error message if the state is FAILED
            
        Returns:
            The updated file record if found, None otherwise
        """
        updates = {'state': state.value}
        
        if error_message and state == AIFileState.FAILED:
            updates['error_message'] = error_message
            
        return await self.update_file_record(file_id, updates)
    
    async def delete_file_record(self, file_id: str) -> bool:
        """
        Delete a file record.
        
        Args:
            file_id: The ID of the file record to delete
            
        Returns:
            True if the file record was deleted, False otherwise
        """
        try:
            # Check if the record exists
            record = await self.get_file_record(file_id)
            if not record:
                return False
                
            # Delete the item
            self._dynamodb_client.delete_item(
                table_name=self._table_name,
                key={'file_id': file_id}
            )
            
            logger.info(f"Deleted file record {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file record {file_id}: {str(e)}")
            raise
    
    async def get_files_by_state(self, state: AIFileState) -> List[AIFileRecord]:
        """
        Get all file records with a specific state.
        
        Args:
            state: The state to filter by
            
        Returns:
            List of file records with the specified state
        """
        try:
            response = self._dynamodb_client.query(
                table_name=self._table_name,
                index_name='state-index',
                key_condition_expression=Key('state').eq(state.value)
            )
            
            items = response.get('Items', [])
            return [self._item_to_record(item) for item in items]
        except Exception as e:
            logger.error(f"Error getting file records with state {state.value}: {str(e)}")
            raise 