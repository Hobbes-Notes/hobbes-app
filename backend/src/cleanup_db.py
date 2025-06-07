import os
from dotenv import load_dotenv
import logging
from infrastructure.dynamodb_client import get_dynamodb_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def cleanup_tables():
    # Initialize DynamoDB client
    dynamodb_client = get_dynamodb_client()

    # Clean up Projects table
    try:
        # Scan all items
        response = dynamodb_client.scan(table_name='Projects')
        items = response.get('Items', [])
        
        # Delete each item
        for item in items:
            dynamodb_client.delete_item(
                table_name='Projects',
                key={'id': item['id']}
            )
        
        logger.info(f"Successfully deleted {len(items)} projects")
    except Exception as e:
        logger.error(f"Error cleaning up Projects table: {str(e)}")

    # Clean up Notes table
    try:
        # Scan all items
        response = dynamodb_client.scan(table_name='Notes')
        items = response.get('Items', [])
        
        # Delete each item
        for item in items:
            dynamodb_client.delete_item(
                table_name='Notes',
                key={'id': item['id']}
            )
        
        logger.info(f"Successfully deleted {len(items)} notes")
    except Exception as e:
        logger.error(f"Error cleaning up Notes table: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting database cleanup...")
    cleanup_tables()
    logger.info("Database cleanup completed") 