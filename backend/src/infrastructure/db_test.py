"""
DynamoDB Client Test Script

This script demonstrates the usage of the DynamoDB client.
"""

import logging
import os
import sys
import uuid
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.dynamodb_client import get_dynamodb_client

def test_dynamodb_client():
    """Test the DynamoDB client functionality"""
    
    logger.info("Starting DynamoDB client test")
    
    # Get the DynamoDB client
    dynamodb_client = get_dynamodb_client()
    
    # List tables
    tables = dynamodb_client.list_tables()
    logger.info(f"Tables in DynamoDB: {tables}")
    
    # Test table name and data
    test_table_name = "TestTable"
    test_item = {
        "id": str(uuid.uuid4()),
        "name": "Test Item",
        "description": "This is a test item",
        "created_at": "2023-03-10T12:00:00Z"
    }
    
    # Create a test table if it doesn't exist
    if not dynamodb_client.table_exists(test_table_name):
        logger.info(f"Creating test table: {test_table_name}")
        
        key_schema = [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'  # Partition key
            }
        ]
        
        attribute_definitions = [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'  # String
            }
        ]
        
        dynamodb_client.create_table(
            table_name=test_table_name,
            key_schema=key_schema,
            attribute_definitions=attribute_definitions
        )
        
        logger.info(f"Test table created: {test_table_name}")
    
    # Put an item
    dynamodb_client.put_item(test_table_name, test_item)
    logger.info(f"Added item to {test_table_name}: {test_item}")
    
    # Get the item
    retrieved_item = dynamodb_client.get_item(test_table_name, {'id': test_item['id']})
    logger.info(f"Retrieved item from {test_table_name}: {retrieved_item}")
    
    # Update the item
    update_response = dynamodb_client.update_item(
        table_name=test_table_name,
        key={'id': test_item['id']},
        update_expression="SET #desc = :new_desc",
        expression_attribute_values={':new_desc': "This is an updated test item"},
        expression_attribute_names={'#desc': 'description'}
    )
    logger.info(f"Updated item in {test_table_name}: {update_response}")
    
    # Get the updated item
    updated_item = dynamodb_client.get_item(test_table_name, {'id': test_item['id']})
    logger.info(f"Retrieved updated item from {test_table_name}: {updated_item}")
    
    # Scan the table
    scan_response = dynamodb_client.scan(test_table_name)
    logger.info(f"Scan of {test_table_name} found {len(scan_response.get('Items', []))} items")
    
    # Delete the item
    delete_response = dynamodb_client.delete_item(test_table_name, {'id': test_item['id']})
    logger.info(f"Deleted item from {test_table_name}: {delete_response}")
    
    # Clean up - uncomment if you want to delete the test table
    # dynamodb_client.delete_table(test_table_name)
    # logger.info(f"Deleted test table: {test_table_name}")
    
    logger.info("DynamoDB client test completed successfully")

if __name__ == "__main__":
    test_dynamodb_client() 