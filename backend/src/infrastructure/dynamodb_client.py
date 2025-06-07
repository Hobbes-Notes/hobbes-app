"""
DynamoDB Client

This module provides a comprehensive wrapper around the AWS DynamoDB library to simplify
interactions with DynamoDB and provide a clean abstraction for the application.

This client implements best practices for working with DynamoDB and handles:
- Connection management
- Error handling and logging
- Common DynamoDB operations with simplified interfaces
- Batch operations and pagination
- Transaction support
"""

import logging
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional, Union, Iterable, Generator

logger = logging.getLogger(__name__)

# Singleton instance of DynamoDB client
_dynamodb_client_instance: Optional['DynamoDBClient'] = None

class DynamoDBClient:
    """
    A wrapper client for AWS DynamoDB.
    
    This client provides simplified methods for common DynamoDB operations
    and handles connection management and error handling. It is designed to be
    used as the foundation for all DynamoDB interactions in the application.
    
    Features:
    - Simplified API for common operations
    - Comprehensive error handling
    - Consistent logging
    - Support for local DynamoDB endpoints for development
    - Pagination handling for large result sets
    - Transaction support
    """
    
    def __init__(self, region_name: str = 'us-east-1', endpoint_url: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        """
        Initialize the DynamoDB client.
        
        Args:
            region_name: AWS region name
            endpoint_url: Optional endpoint URL for local development or testing
            aws_access_key_id: Optional AWS access key ID
            aws_secret_access_key: Optional AWS secret access key
        """
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        
        # Configuration kwargs for boto3
        config_kwargs = {
            'region_name': region_name,
        }
        
        if endpoint_url:
            config_kwargs['endpoint_url'] = endpoint_url
            
        if aws_access_key_id and aws_secret_access_key:
            config_kwargs['aws_access_key_id'] = aws_access_key_id
            config_kwargs['aws_secret_access_key'] = aws_secret_access_key
        
        # Configure the client
        self.client = boto3.client('dynamodb', **config_kwargs)
        
        # Create a resource for higher-level operations
        self.resource = boto3.resource('dynamodb', **config_kwargs)
        
        logger.info(f"DynamoDB client initialized. Region: {region_name}, Endpoint: {endpoint_url or 'AWS Default'}")

    # Table operations
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the DynamoDB instance.
        
        Returns:
            List of table names
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            tables = []
            response = self.client.list_tables()
            tables.extend(response.get('TableNames', []))
            
            # Handle pagination for large numbers of tables
            while 'LastEvaluatedTableName' in response:
                response = self.client.list_tables(
                    ExclusiveStartTableName=response['LastEvaluatedTableName']
                )
                tables.extend(response.get('TableNames', []))
                
            return tables
        except ClientError as e:
            logger.error(f"Failed to list tables: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if the table exists, False otherwise
        """
        try:
            tables = self.list_tables()
            return table_name in tables
        except ClientError:
            logger.exception(f"Error checking if table {table_name} exists")
            return False
    
    def create_table(self, table_name: str, key_schema: List[Dict], 
                    attribute_definitions: List[Dict],
                    provisioned_throughput: Optional[Dict] = None,
                    global_secondary_indexes: Optional[List[Dict]] = None,
                    local_secondary_indexes: Optional[List[Dict]] = None,
                    billing_mode: str = 'PROVISIONED') -> Dict:
        """
        Create a new DynamoDB table.
        
        Args:
            table_name: Name of the table to create
            key_schema: Key schema for the table
            attribute_definitions: Attribute definitions for the table
            provisioned_throughput: Provisioned throughput for the table. Required if billing_mode is PROVISIONED.
            global_secondary_indexes: Optional global secondary indexes for the table
            local_secondary_indexes: Optional local secondary indexes for the table
            billing_mode: Billing mode for the table (PROVISIONED or PAY_PER_REQUEST)
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ValueError: If the table already exists or if provisioned_throughput is not provided for PROVISIONED billing mode
            ClientError: If there's an error communicating with DynamoDB
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            raise ValueError(f"Table {table_name} already exists")
        
        create_kwargs = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': billing_mode
        }
        
        if billing_mode == 'PROVISIONED':
            if not provisioned_throughput:
                provisioned_throughput = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            create_kwargs['ProvisionedThroughput'] = provisioned_throughput
        
        if global_secondary_indexes:
            create_kwargs['GlobalSecondaryIndexes'] = global_secondary_indexes
        
        if local_secondary_indexes:
            create_kwargs['LocalSecondaryIndexes'] = local_secondary_indexes
        
        try:
            response = self.client.create_table(**create_kwargs)
            logger.info(f"Created table {table_name}")
            
            # Wait for the table to be created
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            logger.info(f"Table {table_name} is now active")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise
    
    def delete_table(self, table_name: str) -> Dict:
        """
        Delete a DynamoDB table.
        
        Args:
            table_name: Name of the table to delete
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ValueError: If the table doesn't exist
            ClientError: If there's an error communicating with DynamoDB
        """
        if not self.table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist")
            raise ValueError(f"Table {table_name} does not exist")
        
        try:
            response = self.client.delete_table(TableName=table_name)
            logger.info(f"Deleted table {table_name}")
            
            # Wait for the table to be deleted
            waiter = self.client.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
            logger.info(f"Table {table_name} is now deleted")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to delete table {table_name}: {str(e)}")
            raise
    
    def describe_table(self, table_name: str) -> Dict:
        """
        Get detailed information about a table.
        
        Args:
            table_name: Name of the table to describe
            
        Returns:
            Table description
            
        Raises:
            ValueError: If the table doesn't exist
            ClientError: If there's an error communicating with DynamoDB
        """
        if not self.table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist")
            raise ValueError(f"Table {table_name} does not exist")
        
        try:
            response = self.client.describe_table(TableName=table_name)
            return response.get('Table', {})
        except ClientError as e:
            logger.error(f"Failed to describe table {table_name}: {str(e)}")
            raise
    
    # Item operations
    
    def put_item(self, table_name: str, item: Dict, 
                condition_expression: Optional[str] = None,
                expression_attribute_names: Optional[Dict] = None,
                expression_attribute_values: Optional[Dict] = None) -> Dict:
        """
        Put an item in a DynamoDB table.
        
        Args:
            table_name: Name of the table
            item: Item to put
            condition_expression: Optional condition expression
            expression_attribute_names: Optional expression attribute names
            expression_attribute_values: Optional expression attribute values
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            put_kwargs = {'Item': item}
            
            if condition_expression:
                put_kwargs['ConditionExpression'] = condition_expression
            
            if expression_attribute_names:
                put_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if expression_attribute_values:
                put_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            response = table.put_item(**put_kwargs)
            logger.debug(f"Put item in table {table_name}")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to put item in table {table_name}: {str(e)}")
            raise
    
    def get_item(self, table_name: str, key: Dict, 
                consistent_read: bool = False,
                projection_expression: Optional[str] = None,
                expression_attribute_names: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get an item from a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key: Key of the item to get
            consistent_read: Whether to use consistent read
            projection_expression: Optional projection expression to limit returned attributes
            expression_attribute_names: Optional expression attribute names
            
        Returns:
            The item if found, None otherwise
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            get_kwargs = {
                'Key': key,
                'ConsistentRead': consistent_read
            }
            
            if projection_expression:
                get_kwargs['ProjectionExpression'] = projection_expression
            
            if expression_attribute_names:
                get_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            response = table.get_item(**get_kwargs)
            item = response.get('Item')
            
            if item:
                logger.debug(f"Got item from table {table_name}")
            else:
                logger.debug(f"Item not found in table {table_name}")
            
            return item
        except ClientError as e:
            logger.error(f"Failed to get item from table {table_name}: {str(e)}")
            raise
    
    def update_item(self, table_name: str, key: Dict, 
                   update_expression: str, 
                   expression_attribute_values: Optional[Dict] = None,
                   condition_expression: Optional[str] = None,
                   expression_attribute_names: Optional[Dict] = None,
                   return_values: str = "UPDATED_NEW") -> Dict:
        """
        Update an item in a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key: Key of the item to update
            update_expression: Update expression
            expression_attribute_values: Optional expression attribute values
            condition_expression: Optional condition expression
            expression_attribute_names: Optional expression attribute names
            return_values: What values to return
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            update_kwargs = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ReturnValues': return_values
            }
            
            if expression_attribute_values:
                update_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if condition_expression:
                update_kwargs['ConditionExpression'] = condition_expression
            
            if expression_attribute_names:
                update_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            response = table.update_item(**update_kwargs)
            logger.debug(f"Updated item in table {table_name}")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to update item in table {table_name}: {str(e)}")
            raise
    
    def delete_item(self, table_name: str, key: Dict, 
                   condition_expression: Optional[str] = None,
                   expression_attribute_values: Optional[Dict] = None,
                   expression_attribute_names: Optional[Dict] = None,
                   return_values: str = "NONE") -> Dict:
        """
        Delete an item from a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key: Key of the item to delete
            condition_expression: Optional condition expression
            expression_attribute_values: Optional expression attribute values
            expression_attribute_names: Optional expression attribute names
            return_values: What values to return
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            delete_kwargs = {
                'Key': key,
                'ReturnValues': return_values
            }
            
            if condition_expression:
                delete_kwargs['ConditionExpression'] = condition_expression
            
            if expression_attribute_values:
                delete_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if expression_attribute_names:
                delete_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            response = table.delete_item(**delete_kwargs)
            logger.debug(f"Deleted item from table {table_name}")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to delete item from table {table_name}: {str(e)}")
            raise
    
    # Query and scan operations
    
    def query(self, table_name: str, 
             key_condition_expression,
             filter_expression=None,
             expression_attribute_values=None,
             expression_attribute_names=None,
             index_name=None,
             select=None,
             projection_expression=None,
             limit=None,
             consistent_read=False,
             scan_index_forward=True,
             exclusive_start_key=None,
             return_consumed_capacity=None) -> Dict:
        """
        Query items in a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key_condition_expression: Key condition expression
            filter_expression: Optional filter expression
            expression_attribute_values: Optional expression attribute values
            expression_attribute_names: Optional expression attribute names
            index_name: Optional index name
            select: Optional select type
            projection_expression: Optional projection expression
            limit: Optional limit
            consistent_read: Whether to use consistent read
            scan_index_forward: Whether to scan forward
            exclusive_start_key: Optional exclusive start key for pagination
            return_consumed_capacity: Optional return consumed capacity
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            query_kwargs = {
                'KeyConditionExpression': key_condition_expression,
                'ConsistentRead': consistent_read,
                'ScanIndexForward': scan_index_forward
            }
            
            if filter_expression:
                query_kwargs['FilterExpression'] = filter_expression
            
            if expression_attribute_values:
                query_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if expression_attribute_names:
                query_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if index_name:
                query_kwargs['IndexName'] = index_name
            
            if select:
                query_kwargs['Select'] = select
            
            if projection_expression:
                query_kwargs['ProjectionExpression'] = projection_expression
            
            if limit:
                query_kwargs['Limit'] = limit
            
            if exclusive_start_key:
                query_kwargs['ExclusiveStartKey'] = exclusive_start_key
            
            if return_consumed_capacity:
                query_kwargs['ReturnConsumedCapacity'] = return_consumed_capacity
            
            response = table.query(**query_kwargs)
            
            logger.debug(f"Queried table {table_name}, found {len(response.get('Items', []))} items")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to query table {table_name}: {str(e)}")
            raise
    
    def query_all(self, table_name: str, 
                 key_condition_expression,
                 filter_expression=None,
                 expression_attribute_values=None,
                 expression_attribute_names=None,
                 index_name=None,
                 projection_expression=None,
                 consistent_read=False,
                 scan_index_forward=True) -> List[Dict]:
        """
        Query all matching items in a DynamoDB table, handling pagination.
        
        Args:
            table_name: Name of the table
            key_condition_expression: Key condition expression
            filter_expression: Optional filter expression
            expression_attribute_values: Optional expression attribute values
            expression_attribute_names: Optional expression attribute names
            index_name: Optional index name
            projection_expression: Optional projection expression
            consistent_read: Whether to use consistent read
            scan_index_forward: Whether to scan forward
            
        Returns:
            List of items from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            all_items = []
            last_evaluated_key = None
            
            while True:
                response = self.query(
                    table_name=table_name,
                    key_condition_expression=key_condition_expression,
                    filter_expression=filter_expression,
                    expression_attribute_values=expression_attribute_values,
                    expression_attribute_names=expression_attribute_names,
                    index_name=index_name,
                    projection_expression=projection_expression,
                    consistent_read=consistent_read,
                    scan_index_forward=scan_index_forward,
                    exclusive_start_key=last_evaluated_key
                )
                
                items = response.get('Items', [])
                all_items.extend(items)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            logger.debug(f"Query all from table {table_name} found {len(all_items)} items")
            
            return all_items
        except ClientError as e:
            logger.error(f"Failed to query all from table {table_name}: {str(e)}")
            raise
    
    def scan(self, table_name: str, 
            filter_expression=None,
            expression_attribute_values=None,
            expression_attribute_names=None,
            index_name=None,
            select=None,
            projection_expression=None,
            limit=None,
            consistent_read=False,
            exclusive_start_key=None,
            segment=None,
            total_segments=None,
            return_consumed_capacity=None) -> Dict:
        """
        Scan items in a DynamoDB table.
        
        Args:
            table_name: Name of the table
            filter_expression: Optional filter expression
            expression_attribute_values: Optional expression attribute values
            expression_attribute_names: Optional expression attribute names
            index_name: Optional index name
            select: Optional select type
            projection_expression: Optional projection expression
            limit: Optional limit
            consistent_read: Whether to use consistent read
            exclusive_start_key: Optional exclusive start key for pagination
            segment: Optional segment for parallel scan
            total_segments: Optional total segments for parallel scan
            return_consumed_capacity: Optional return consumed capacity
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            table = self.resource.Table(table_name)
            
            scan_kwargs = {
                'ConsistentRead': consistent_read
            }
            
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
            
            if expression_attribute_values:
                scan_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if expression_attribute_names:
                scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if index_name:
                scan_kwargs['IndexName'] = index_name
            
            if select:
                scan_kwargs['Select'] = select
            
            if projection_expression:
                scan_kwargs['ProjectionExpression'] = projection_expression
            
            if limit:
                scan_kwargs['Limit'] = limit
            
            if exclusive_start_key:
                scan_kwargs['ExclusiveStartKey'] = exclusive_start_key
            
            if segment is not None and total_segments is not None:
                scan_kwargs['Segment'] = segment
                scan_kwargs['TotalSegments'] = total_segments
            
            if return_consumed_capacity:
                scan_kwargs['ReturnConsumedCapacity'] = return_consumed_capacity
            
            response = table.scan(**scan_kwargs)
            
            logger.debug(f"Scanned table {table_name}, found {len(response.get('Items', []))} items")
            
            return response
        except ClientError as e:
            logger.error(f"Failed to scan table {table_name}: {str(e)}")
            raise
    
    def scan_all(self, table_name: str, 
                filter_expression=None,
                expression_attribute_values=None,
                expression_attribute_names=None,
                index_name=None,
                projection_expression=None,
                consistent_read=False) -> List[Dict]:
        """
        Scan all items in a DynamoDB table, handling pagination.
        
        Args:
            table_name: Name of the table
            filter_expression: Optional filter expression
            expression_attribute_values: Optional expression attribute values
            expression_attribute_names: Optional expression attribute names
            index_name: Optional index name
            projection_expression: Optional projection expression
            consistent_read: Whether to use consistent read
            
        Returns:
            List of items from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            all_items = []
            last_evaluated_key = None
            
            while True:
                response = self.scan(
                    table_name=table_name,
                    filter_expression=filter_expression,
                    expression_attribute_values=expression_attribute_values,
                    expression_attribute_names=expression_attribute_names,
                    index_name=index_name,
                    projection_expression=projection_expression,
                    consistent_read=consistent_read,
                    exclusive_start_key=last_evaluated_key
                )
                
                items = response.get('Items', [])
                all_items.extend(items)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            logger.debug(f"Scan all from table {table_name} found {len(all_items)} items")
            
            return all_items
        except ClientError as e:
            logger.error(f"Failed to scan all from table {table_name}: {str(e)}")
            raise
    
    # Batch operations
    
    def batch_write(self, table_name: str, items: List[Dict] = None, delete_keys: List[Dict] = None) -> Dict:
        """
        Batch write items to a DynamoDB table.
        
        Args:
            table_name: Name of the table
            items: List of items to put
            delete_keys: List of keys to delete
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ValueError: If neither items nor delete_keys are provided
            ClientError: If there's an error communicating with DynamoDB
        """
        if not items and not delete_keys:
            raise ValueError("Either items or delete_keys must be provided")
        
        try:
            table = self.resource.Table(table_name)
            with table.batch_writer() as batch:
                # Write items
                if items:
                    for item in items:
                        batch.put_item(Item=item)
                        
                # Delete items
                if delete_keys:
                    for key in delete_keys:
                        batch.delete_item(Key=key)
            
            logger.debug(f"Batch write to {table_name} completed. "
                         f"Put: {len(items) if items else 0}, "
                         f"Delete: {len(delete_keys) if delete_keys else 0}")
            
            return {'Status': 'Success'}
        except ClientError as e:
            logger.error(f"Failed batch write to table {table_name}: {str(e)}")
            raise
    
    def batch_get(self, table_name: str, keys: List[Dict]) -> List[Dict]:
        """
        Batch get items from a DynamoDB table.
        
        Args:
            table_name: Name of the table
            keys: List of keys to get
            
        Returns:
            List of items retrieved
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        if not keys:
            return []
            
        try:
            # DynamoDB limits batch gets to 100 items at a time
            all_items = []
            for i in range(0, len(keys), 100):
                chunk = keys[i:i+100]
                response = self.resource.batch_get_item(
                    RequestItems={
                        table_name: {
                            'Keys': chunk
                        }
                    }
                )
                
                items = response.get('Responses', {}).get(table_name, [])
                all_items.extend(items)
                
                # Handle unprocessed keys
                unprocessed_keys = response.get('UnprocessedKeys', {})
                while unprocessed_keys:
                    response = self.resource.batch_get_item(
                        RequestItems=unprocessed_keys
                    )
                    items = response.get('Responses', {}).get(table_name, [])
                    all_items.extend(items)
                    unprocessed_keys = response.get('UnprocessedKeys', {})
            
            logger.debug(f"Batch get from {table_name} returned {len(all_items)} items")
            
            return all_items
        except ClientError as e:
            logger.error(f"Failed batch get from table {table_name}: {str(e)}")
            raise
    
    # Transaction operations
    
    def transact_write_items(self, transact_items: List[Dict]) -> Dict:
        """
        Execute a transaction to write multiple items.
        
        Args:
            transact_items: List of transact write items
            
        Returns:
            Response from DynamoDB
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            response = self.client.transact_write_items(
                TransactItems=transact_items
            )
            logger.debug(f"Executed transact_write_items with {len(transact_items)} items")
            return response
        except ClientError as e:
            logger.error(f"Failed to execute transact_write_items: {str(e)}")
            raise
    
    def transact_get_items(self, transact_items: List[Dict]) -> List[Dict]:
        """
        Execute a transaction to get multiple items.
        
        Args:
            transact_items: List of transact get items
            
        Returns:
            List of items retrieved
            
        Raises:
            ClientError: If there's an error communicating with DynamoDB
        """
        try:
            response = self.client.transact_get_items(
                TransactItems=transact_items
            )
            logger.debug(f"Executed transact_get_items with {len(transact_items)} items")
            
            # Process the response to extract the items
            items = []
            for item_response in response.get('Responses', []):
                if 'Item' in item_response:
                    items.append(self.resource.meta.client._get_response_metadata(item_response['Item']))
            
            return items
        except ClientError as e:
            logger.error(f"Failed to execute transact_get_items: {str(e)}")
            raise
    
    # Helper methods
    
    def get_table_resource(self, table_name: str):
        """
        Get a boto3 Table resource for the specified table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            boto3 Table resource
        """
        return self.resource.Table(table_name)
    
    def get_resource(self):
        """
        Get the boto3 DynamoDB resource.
        
        Returns:
            The boto3 DynamoDB resource
        """
        return self.resource
    
    def get_client(self):
        """
        Get the boto3 DynamoDB client.
        
        Returns:
            The boto3 DynamoDB client
        """
        return self.client 

def get_dynamodb_client() -> DynamoDBClient:
    """
    Get a DynamoDB client instance.
    
    This function implements the Singleton pattern to ensure only one DynamoDB
    client is created for the application. It retrieves configuration from
    environment variables.
    
    Returns:
        DynamoDB client instance
        
    Example:
        ```
        from infrastructure.dynamodb_client import get_dynamodb_client
        
        # Get the DynamoDB client
        dynamodb = get_dynamodb_client()
        
        # Use the client
        tables = dynamodb.list_tables()
        ```
    """
    global _dynamodb_client_instance
    
    if _dynamodb_client_instance is None:
        # Create a new client if one doesn't exist
        region_name = os.getenv('AWS_REGION', 'us-east-1')
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
        access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        _dynamodb_client_instance = DynamoDBClient(
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
    
    return _dynamodb_client_instance 