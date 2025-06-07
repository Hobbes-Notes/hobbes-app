"""
Action Item Repository Implementation

This module provides the DynamoDB implementation of the action item repository.
"""

from ..action_item_repository import ActionItemRepository
from ...infrastructure.dynamodb_client import DynamoDBClient

class DynamoDBActionItemRepository(ActionItemRepository):
    """DynamoDB implementation of ActionItemRepository."""
    
    def __init__(self):
        """Initialize the repository with DynamoDB client."""
        self.dynamodb_client = DynamoDBClient()
        super().__init__(self.dynamodb_client) 