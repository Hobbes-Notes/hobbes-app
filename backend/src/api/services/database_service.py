"""
Database Service Layer

This module provides service-level functionality for database management,
including table creation and initialization.
"""

import logging
from typing import Any

from ..repositories.database_repository import DatabaseRepository
from ..repositories.impl import get_database_repository

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for managing database resources in the system.
    
    This class handles database initialization, table creation,
    and other database-level operations.
    """
    
    def __init__(self, database_repository: DatabaseRepository = None):
        """
        Initialize the DatabaseService with a database repository.
        
        Args:
            database_repository: Optional DatabaseRepository instance. If not provided,
                                 a new instance will be created.
        """
        self.database_repository = database_repository or get_database_repository()
    
    async def create_tables(self) -> None:
        """
        Create all required tables if they don't exist.
        
        This method initializes the database table structure for the application.
        """
        await self.database_repository.create_tables()
    
    def get_dynamodb_resource(self) -> Any:
        """
        Get the DynamoDB resource.
        
        Returns:
            The boto3 DynamoDB resource
        """
        return self.database_repository.get_dynamodb_resource()
    
    def get_table(self, table_name: str) -> Any:
        """
        Get a table resource by name.
        
        Args:
            table_name: The name of the table
            
        Returns:
            The table resource
        """
        return self.database_repository.get_table(table_name) 