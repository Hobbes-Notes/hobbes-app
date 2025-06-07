"""
SQS Client

This module provides a comprehensive wrapper around the AWS SQS library to simplify
interactions with SQS and provide a clean abstraction for the application.

This client implements best practices for working with SQS and handles:
- Connection management
- Error handling and logging
- Common SQS operations with simplified interfaces
- Message batching
"""

import logging
import boto3
import os
import json
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)

# Singleton instance of SQS client
_sqs_client_instance: Optional['SQSClient'] = None

class SQSClient:
    """
    A wrapper client for AWS SQS.
    
    This client provides simplified methods for common SQS operations
    and handles connection management and error handling. It is designed to be
    used as the foundation for all SQS interactions in the application.
    
    Features:
    - Simplified API for common operations
    - Comprehensive error handling
    - Consistent logging
    - Support for local SQS endpoints for development
    - Message batching
    """
    
    def __init__(self, region_name: str = 'us-east-1', endpoint_url: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        """
        Initialize the SQS client.
        
        Args:
            region_name: AWS region name
            endpoint_url: Optional endpoint URL for local development
            aws_access_key_id: Optional AWS access key ID
            aws_secret_access_key: Optional AWS secret access key
        """
        # Use environment variables if not provided
        if aws_access_key_id is None:
            aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        if aws_secret_access_key is None:
            aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if region_name is None:
            region_name = os.environ.get('AWS_REGION', 'us-east-1')
        if endpoint_url is None:
            endpoint_url = os.environ.get('SQS_ENDPOINT')
            
        # Initialize the SQS client
        self._sqs = boto3.client(
            'sqs',
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Initialize the SQS resource for higher-level operations
        self._sqs_resource = boto3.resource(
            'sqs',
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Cache for queue URLs
        self._queue_url_cache: Dict[str, str] = {}
        
        logger.info(f"Initialized SQS client with endpoint: {endpoint_url or 'default AWS'}")
    
    def get_queue_url(self, queue_name: str) -> Optional[str]:
        """
        Get the URL for a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Queue URL if found, None otherwise
        """
        # Check cache first
        if queue_name in self._queue_url_cache:
            return self._queue_url_cache[queue_name]
            
        try:
            response = self._sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            
            # Cache the URL
            self._queue_url_cache[queue_name] = queue_url
            
            return queue_url
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                logger.warning(f"Queue {queue_name} does not exist")
                return None
            else:
                logger.error(f"Error getting URL for queue {queue_name}: {str(e)}")
                raise
    
    def create_queue(self, queue_name: str, attributes: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Create a new SQS queue.
        
        Args:
            queue_name: Name of the queue to create
            attributes: Optional queue attributes
            
        Returns:
            Queue URL if created successfully, None otherwise
        """
        try:
            params = {'QueueName': queue_name}
            if attributes:
                params['Attributes'] = attributes
                
            response = self._sqs.create_queue(**params)
            queue_url = response['QueueUrl']
            
            # Cache the URL
            self._queue_url_cache[queue_name] = queue_url
            
            logger.info(f"Created queue {queue_name}")
            return queue_url
        except ClientError as e:
            logger.error(f"Error creating queue {queue_name}: {str(e)}")
            return None
    
    def delete_queue(self, queue_name: str) -> bool:
        """
        Delete an SQS queue.
        
        Args:
            queue_name: Name of the queue to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot delete queue {queue_name}: queue does not exist")
            return False
            
        try:
            self._sqs.delete_queue(QueueUrl=queue_url)
            
            # Remove from cache
            if queue_name in self._queue_url_cache:
                del self._queue_url_cache[queue_name]
                
            logger.info(f"Deleted queue {queue_name}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting queue {queue_name}: {str(e)}")
            return False
    
    def send_message(self, queue_name: str, message_body: Union[str, Dict, List],
                    delay_seconds: int = 0, message_attributes: Optional[Dict] = None) -> Optional[str]:
        """
        Send a message to an SQS queue.
        
        Args:
            queue_name: Name of the queue to send to
            message_body: Message body (string or JSON-serializable object)
            delay_seconds: Delay in seconds before the message becomes available
            message_attributes: Optional message attributes
            
        Returns:
            Message ID if sent successfully, None otherwise
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot send message to queue {queue_name}: queue does not exist")
            return None
            
        # Convert message body to string if it's a dict or list
        if isinstance(message_body, (dict, list)):
            message_body = json.dumps(message_body)
            
        try:
            params = {
                'QueueUrl': queue_url,
                'MessageBody': message_body
            }
            
            if delay_seconds > 0:
                params['DelaySeconds'] = delay_seconds
                
            if message_attributes:
                params['MessageAttributes'] = message_attributes
                
            response = self._sqs.send_message(**params)
            message_id = response['MessageId']
            
            logger.info(f"Sent message to queue {queue_name} with ID {message_id}")
            return message_id
        except ClientError as e:
            logger.error(f"Error sending message to queue {queue_name}: {str(e)}")
            return None
    
    def send_message_batch(self, queue_name: str, messages: List[Dict]) -> Dict[str, List[str]]:
        """
        Send a batch of messages to an SQS queue.
        
        Args:
            queue_name: Name of the queue to send to
            messages: List of message dictionaries, each with:
                - id: Unique ID for the message
                - body: Message body (string or JSON-serializable object)
                - delay_seconds: (Optional) Delay in seconds
                - message_attributes: (Optional) Message attributes
            
        Returns:
            Dictionary with 'successful' and 'failed' lists of message IDs
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot send batch to queue {queue_name}: queue does not exist")
            return {'successful': [], 'failed': [msg['id'] for msg in messages]}
            
        # Prepare batch entries
        entries = []
        for msg in messages:
            # Convert message body to string if it's a dict or list
            body = msg['body']
            if isinstance(body, (dict, list)):
                body = json.dumps(body)
                
            entry = {
                'Id': msg['id'],
                'MessageBody': body
            }
            
            if 'delay_seconds' in msg and msg['delay_seconds'] > 0:
                entry['DelaySeconds'] = msg['delay_seconds']
                
            if 'message_attributes' in msg:
                entry['MessageAttributes'] = msg['message_attributes']
                
            entries.append(entry)
            
        # Send in batches of 10 (SQS limit)
        successful_ids = []
        failed_ids = []
        
        for i in range(0, len(entries), 10):
            batch = entries[i:i+10]
            
            try:
                response = self._sqs.send_message_batch(
                    QueueUrl=queue_url,
                    Entries=batch
                )
                
                # Track successful and failed messages
                if 'Successful' in response:
                    successful_ids.extend([msg['Id'] for msg in response['Successful']])
                    
                if 'Failed' in response:
                    failed_ids.extend([msg['Id'] for msg in response['Failed']])
                    for failed in response['Failed']:
                        logger.warning(f"Failed to send message {failed['Id']} to queue {queue_name}: {failed.get('Message')}")
                        
            except ClientError as e:
                # If the entire batch fails, mark all as failed
                failed_ids.extend([entry['Id'] for entry in batch])
                logger.error(f"Error sending batch to queue {queue_name}: {str(e)}")
                
        logger.info(f"Sent batch to queue {queue_name}: {len(successful_ids)} successful, {len(failed_ids)} failed")
        return {
            'successful': successful_ids,
            'failed': failed_ids
        }
    
    def receive_messages(self, queue_name: str, max_messages: int = 1, wait_time_seconds: int = 0,
                        visibility_timeout: int = 30, message_attributes: Optional[List[str]] = None) -> List[Dict]:
        """
        Receive messages from an SQS queue.
        
        Args:
            queue_name: Name of the queue to receive from
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Time to wait for messages (0-20)
            visibility_timeout: Visibility timeout in seconds
            message_attributes: Optional list of message attribute names to receive
            
        Returns:
            List of message dictionaries
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot receive messages from queue {queue_name}: queue does not exist")
            return []
            
        try:
            params = {
                'QueueUrl': queue_url,
                'MaxNumberOfMessages': min(max_messages, 10),  # SQS limit is 10
                'VisibilityTimeout': visibility_timeout
            }
            
            if wait_time_seconds > 0:
                params['WaitTimeSeconds'] = min(wait_time_seconds, 20)  # SQS limit is 20
                
            if message_attributes:
                params['MessageAttributeNames'] = message_attributes
                
            response = self._sqs.receive_message(**params)
            
            messages = response.get('Messages', [])
            
            # Parse message bodies that are JSON
            for msg in messages:
                try:
                    body = msg['Body']
                    json_body = json.loads(body)
                    msg['parsed_body'] = json_body
                except (json.JSONDecodeError, TypeError):
                    # Not JSON or couldn't be parsed
                    msg['parsed_body'] = None
            
            logger.info(f"Received {len(messages)} messages from queue {queue_name}")
            return messages
        except ClientError as e:
            logger.error(f"Error receiving messages from queue {queue_name}: {str(e)}")
            return []
    
    def delete_message(self, queue_name: str, receipt_handle: str) -> bool:
        """
        Delete a message from an SQS queue.
        
        Args:
            queue_name: Name of the queue
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot delete message from queue {queue_name}: queue does not exist")
            return False
            
        try:
            self._sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info(f"Deleted message from queue {queue_name}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting message from queue {queue_name}: {str(e)}")
            return False
    
    def delete_message_batch(self, queue_name: str, receipt_handles: List[str]) -> Dict[str, List[str]]:
        """
        Delete a batch of messages from an SQS queue.
        
        Args:
            queue_name: Name of the queue
            receipt_handles: List of receipt handles to delete
            
        Returns:
            Dictionary with 'successful' and 'failed' lists of receipt handles
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot delete batch from queue {queue_name}: queue does not exist")
            return {'successful': [], 'failed': receipt_handles}
            
        # Prepare batch entries
        entries = [
            {
                'Id': f"msg-{i}",
                'ReceiptHandle': handle
            }
            for i, handle in enumerate(receipt_handles)
        ]
        
        # Delete in batches of 10 (SQS limit)
        successful_handles = []
        failed_handles = []
        
        for i in range(0, len(entries), 10):
            batch = entries[i:i+10]
            
            try:
                response = self._sqs.delete_message_batch(
                    QueueUrl=queue_url,
                    Entries=batch
                )
                
                # Map successful IDs back to receipt handles
                if 'Successful' in response:
                    successful_ids = [msg['Id'] for msg in response['Successful']]
                    for entry in batch:
                        if entry['Id'] in successful_ids:
                            successful_handles.append(entry['ReceiptHandle'])
                    
                # Map failed IDs back to receipt handles
                if 'Failed' in response:
                    failed_ids = [msg['Id'] for msg in response['Failed']]
                    for entry in batch:
                        if entry['Id'] in failed_ids:
                            failed_handles.append(entry['ReceiptHandle'])
                            
            except ClientError as e:
                # If the entire batch fails, mark all as failed
                failed_handles.extend([entry['ReceiptHandle'] for entry in batch])
                logger.error(f"Error deleting batch from queue {queue_name}: {str(e)}")
                
        logger.info(f"Deleted batch from queue {queue_name}: {len(successful_handles)} successful, {len(failed_handles)} failed")
        return {
            'successful': successful_handles,
            'failed': failed_handles
        }
    
    def purge_queue(self, queue_name: str) -> bool:
        """
        Purge all messages from an SQS queue.
        
        Args:
            queue_name: Name of the queue to purge
            
        Returns:
            True if purged successfully, False otherwise
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot purge queue {queue_name}: queue does not exist")
            return False
            
        try:
            self._sqs.purge_queue(QueueUrl=queue_url)
            logger.info(f"Purged queue {queue_name}")
            return True
        except ClientError as e:
            logger.error(f"Error purging queue {queue_name}: {str(e)}")
            return False
    
    def process_messages(self, queue_name: str, handler: Callable[[Dict], bool], 
                        max_messages: int = 10, wait_time_seconds: int = 20,
                        visibility_timeout: int = 30, auto_delete: bool = True,
                        max_iterations: Optional[int] = None) -> int:
        """
        Process messages from an SQS queue using a handler function.
        
        Args:
            queue_name: Name of the queue to process
            handler: Function that takes a message dictionary and returns True if processed successfully
            max_messages: Maximum number of messages to receive per batch
            wait_time_seconds: Time to wait for messages
            visibility_timeout: Visibility timeout in seconds
            auto_delete: Whether to automatically delete messages that were processed successfully
            max_iterations: Maximum number of iterations to process (None for unlimited)
            
        Returns:
            Number of messages processed successfully
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot process queue {queue_name}: queue does not exist")
            return 0
            
        processed_count = 0
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            
            # Receive messages
            messages = self.receive_messages(
                queue_name=queue_name,
                max_messages=max_messages,
                wait_time_seconds=wait_time_seconds,
                visibility_timeout=visibility_timeout
            )
            
            if not messages:
                # No messages received, break the loop
                break
                
            # Process messages
            successful_handles = []
            
            for message in messages:
                try:
                    success = handler(message)
                    if success and auto_delete:
                        successful_handles.append(message['ReceiptHandle'])
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing message from queue {queue_name}: {str(e)}")
                    
            # Delete successful messages
            if successful_handles:
                self.delete_message_batch(queue_name, successful_handles)
                
        return processed_count
    
    def get_queue_attributes(self, queue_name: str, attribute_names: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Get attributes of an SQS queue.
        
        Args:
            queue_name: Name of the queue
            attribute_names: List of attribute names to get (None for all)
            
        Returns:
            Dictionary of queue attributes
        """
        queue_url = self.get_queue_url(queue_name)
        if not queue_url:
            logger.warning(f"Cannot get attributes for queue {queue_name}: queue does not exist")
            return {}
            
        try:
            params = {'QueueUrl': queue_url}
            
            if attribute_names:
                params['AttributeNames'] = attribute_names
            else:
                params['AttributeNames'] = ['All']
                
            response = self._sqs.get_queue_attributes(**params)
            return response.get('Attributes', {})
        except ClientError as e:
            logger.error(f"Error getting attributes for queue {queue_name}: {str(e)}")
            return {}
    
    def get_client(self):
        """
        Get the underlying boto3 SQS client.
        
        Returns:
            boto3 SQS client
        """
        return self._sqs
    
    def get_resource(self):
        """
        Get the underlying boto3 SQS resource.
        
        Returns:
            boto3 SQS resource
        """
        return self._sqs_resource


def get_sqs_client() -> SQSClient:
    """
    Get the singleton instance of the SQS client.
    
    Returns:
        SQSClient instance
    """
    global _sqs_client_instance
    
    if _sqs_client_instance is None:
        # Get configuration from environment variables
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        endpoint_url = os.environ.get('SQS_ENDPOINT')
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        _sqs_client_instance = SQSClient(
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
    return _sqs_client_instance 