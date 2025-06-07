#!/usr/bin/env python3
"""
Script to clear all AI configurations from the database.
"""

import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_ai_configurations():
    """Clear all AI configurations from the database."""
    try:
        # Connect to DynamoDB
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://dynamodb-local:7777',
            region_name='ap-southeast-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        # Get the table
        table = dynamodb.Table('ai_configurations')
        
        # Scan for all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Delete each item
        for item in items:
            table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            logger.info(f"Deleted configuration: {item['PK']} - {item['SK']}")
        
        logger.info(f"Successfully deleted {len(items)} AI configurations")
        return len(items)
    
    except Exception as e:
        logger.error(f"Error clearing AI configurations: {str(e)}")
        raise

if __name__ == "__main__":
    count = clear_ai_configurations()
    print(f"Deleted {count} AI configurations") 