"""
Database Service Layer

This module provides service-level functionality for database management,
including table creation and initialization.
"""

import boto3
import os
import logging
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for managing database resources in the system.
    
    This class handles database initialization, table creation,
    and other database-level operations.
    """
    
    def __init__(self, dynamodb_resource=None):
        """
        Initialize the DatabaseService with DynamoDB resources.
        
        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource. If not provided,
                               a new resource will be created using environment variables.
        """
        self.dynamodb = dynamodb_resource or boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-2'),
            endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
        )
    
    async def create_tables(self) -> None:
        """
        Create all required tables if they don't exist.
        
        This method initializes the DynamoDB table structure for the application.
        """
        try:
            # Get list of existing tables
            existing_tables = [table.name for table in self.dynamodb.tables.all()]
            logger.info(f"Existing tables: {existing_tables}")
            
            # Create Projects table if it doesn't exist
            if 'Projects' not in existing_tables:
                logger.info("Creating Projects table...")
                self.dynamodb.create_table(
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
                self.dynamodb.create_table(
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
                self.dynamodb.create_table(
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
                self.dynamodb.Table('Projects').wait_until_exists()
                self.dynamodb.Table('Notes').wait_until_exists()
                self.dynamodb.Table('ProjectNotes').wait_until_exists()
                logger.info("All tables are active")
                
        except Exception as e:
            error_msg = f"Error managing tables: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def get_dynamodb_resource(self) -> boto3.resource:
        """
        Get the DynamoDB resource.
        
        Returns:
            The boto3 DynamoDB resource
        """
        return self.dynamodb 