"""
Database Repository Interface

This module defines the interface for database repository operations.
"""

from abc import ABC, abstractmethod
import boto3
from typing import Any

class DatabaseRepository(ABC):
    """
    Repository interface for database operations.
    """
    
    @abstractmethod
    async def create_tables(self) -> None:
        """
        Create all required tables if they don't exist.
        
        This method initializes the database table structure for the application.
        """
        pass
    
    @abstractmethod
    def get_dynamodb_resource(self) -> boto3.resource:
        """
        Get the DynamoDB resource.
        
        Returns:
            The boto3 DynamoDB resource
        """
        pass
    
    @abstractmethod
    def get_table(self, table_name: str) -> Any:
        """
        Get a table resource by name.
        
        Args:
            table_name: The name of the table
            
        Returns:
            The table resource
        """
        pass 