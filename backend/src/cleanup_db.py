import boto3
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def cleanup_tables():
    # Initialize DynamoDB client
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-west-2')
    )

    # Clean up Projects table
    try:
        projects_table = dynamodb.Table('Projects')
        # Scan all items
        response = projects_table.scan()
        items = response.get('Items', [])
        
        # Delete each item
        with projects_table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'id': item['id']})
        
        logger.info(f"Successfully deleted {len(items)} projects")
    except Exception as e:
        logger.error(f"Error cleaning up Projects table: {str(e)}")

    # Clean up Notes table with new structure
    try:
        notes_table = dynamodb.Table('Notes')
        # Scan all items
        response = notes_table.scan()
        items = response.get('Items', [])
        
        # Delete each item using new key schema
        with notes_table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'id': item['id'],
                        'created_at': item['created_at']
                    }
                )
        
        logger.info(f"Successfully deleted {len(items)} notes")
    except Exception as e:
        logger.error(f"Error cleaning up Notes table: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting database cleanup...")
    cleanup_tables()
    logger.info("Database cleanup completed") 