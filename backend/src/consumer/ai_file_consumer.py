"""
AI File Consumer

This module provides a consumer for processing AI files from SQS.
"""

import logging
import json
import os
import asyncio
import signal
import sys
from typing import Dict, Any, Optional
import threading

from ..infrastructure.sqs_client import get_sqs_client
from api.services.ai_file_service import AIFileService
from api.models.ai_file import AIFileState

# Set up logging
logger = logging.getLogger(__name__)

class AIFileConsumer:
    """
    Consumer for processing AI files from SQS.
    """
    
    def __init__(self, queue_name: str, ai_file_service: AIFileService):
        """
        Initialize the consumer.
        
        Args:
            queue_name: Name of the SQS queue to consume from
            ai_file_service: Service for AI file operations
        """
        self._queue_name = queue_name
        self._sqs_client = get_sqs_client()
        self._ai_file_service = ai_file_service
        self._running = False
        self._task = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, sig, frame):
        """
        Handle termination signals.
        """
        logger.info(f"Received signal {sig}, shutting down...")
        self._running = False
    
    async def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a message from the queue.
        
        Args:
            message: The message to process
            
        Returns:
            True if the message was processed successfully, False otherwise
        """
        try:
            # Parse the message body
            if 'parsed_body' in message and message['parsed_body']:
                body = message['parsed_body']
            else:
                body = json.loads(message['Body'])
                
            logger.debug(f"Processing message: {body}")
                
            # Get the file ID from the message
            file_id = body.get('file_id')
            if not file_id:
                logger.error("Message does not contain a file_id")
                return False
                
            logger.info(f"Processing file {file_id}")
            
            # Get additional information from the message
            metadata = body.get('metadata', {})
            user_id = body.get('user_id', 'unknown')
            input_s3_key = body.get('input_s3_key', '')
            
            logger.info(f"File {file_id} details - User: {user_id}, S3 Key: {input_s3_key}, Metadata: {metadata}")
            
            # Process the file
            success = await self._ai_file_service.process_file(file_id)
            
            if success:
                logger.info(f"Successfully processed file {file_id}")
            else:
                logger.error(f"Failed to process file {file_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return False
    
    async def run(self, max_messages: int = 10, wait_time_seconds: int = 20,
                visibility_timeout: int = 300, polling_interval: int = 0):
        """
        Run the consumer.
        
        Args:
            max_messages: Maximum number of messages to receive per batch
            wait_time_seconds: Time to wait for messages
            visibility_timeout: Visibility timeout in seconds
            polling_interval: Interval between polling in seconds (0 for continuous)
        """
        self._running = True
        
        logger.info(f"Starting AI file consumer for queue {self._queue_name}")
        logger.info(f"Consumer settings: max_messages={max_messages}, wait_time_seconds={wait_time_seconds}, visibility_timeout={visibility_timeout}, polling_interval={polling_interval}")
        
        poll_count = 0
        
        while self._running:
            try:
                poll_count += 1
                logger.debug(f"Polling queue {self._queue_name} (poll #{poll_count})")
                
                # Receive messages
                messages = self._sqs_client.receive_messages(
                    queue_name=self._queue_name,
                    max_messages=max_messages,
                    wait_time_seconds=wait_time_seconds,
                    visibility_timeout=visibility_timeout
                )
                
                if not messages:
                    logger.debug(f"No messages received from queue {self._queue_name} (poll #{poll_count})")
                    if polling_interval > 0:
                        logger.debug(f"Sleeping for {polling_interval} seconds before next poll")
                        await asyncio.sleep(polling_interval)
                    continue
                    
                logger.info(f"Received {len(messages)} messages from queue {self._queue_name} (poll #{poll_count})")
                
                # Process messages
                for i, message in enumerate(messages):
                    message_id = message.get('MessageId', 'unknown')
                    logger.info(f"Processing message {i+1}/{len(messages)} with ID {message_id}")
                    
                    success = await self.process_message(message)
                    
                    if success:
                        # Delete the message
                        logger.info(f"Successfully processed message {message_id}, deleting from queue")
                        self._sqs_client.delete_message(
                            queue_name=self._queue_name,
                            receipt_handle=message['ReceiptHandle']
                        )
                        logger.info(f"Deleted message {message_id} from queue {self._queue_name}")
                    else:
                        logger.warning(f"Failed to process message {message_id}, it will return to the queue after visibility timeout")
                
                # Sleep if polling interval is set
                if polling_interval > 0:
                    logger.debug(f"Sleeping for {polling_interval} seconds before next poll")
                    await asyncio.sleep(polling_interval)
            except Exception as e:
                logger.error(f"Error in consumer loop: {str(e)}", exc_info=True)
                if polling_interval > 0:
                    logger.debug(f"Sleeping for {polling_interval} seconds before next poll after error")
                    await asyncio.sleep(polling_interval)
                else:
                    logger.debug("Sleeping for 1 second before next poll after error")
                    await asyncio.sleep(1)  # Avoid tight loop on error
        
        logger.info("AI file consumer stopped")
    
    def start(self):
        """
        Start the consumer in a background thread.
        """
        if self._running:
            logger.warning("Consumer is already running")
            return
            
        def _run_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.run())
            except Exception as e:
                logger.error(f"Error in consumer thread: {str(e)}", exc_info=True)
            finally:
                if loop.is_running():
                    loop.close()
        
        # Start in a daemon thread so it doesn't block application shutdown
        self._thread = threading.Thread(target=_run_in_thread, daemon=True)
        self._thread.start()
        logger.info("AI file consumer started in background")
    
    def stop(self):
        """
        Stop the consumer.
        """
        if not self._running:
            logger.warning("Consumer is not running")
            return
            
        self._running = False
        logger.info("AI file consumer stopping...")

def create_consumer(queue_name: str = None, ai_file_service: AIFileService = None) -> AIFileConsumer:
    """
    Create an AI file consumer.
    
    Args:
        queue_name: Name of the SQS queue to consume from (defaults to environment variable)
        ai_file_service: Service for AI file operations (defaults to getting from service factory)
        
    Returns:
        AIFileConsumer instance
    """
    if queue_name is None:
        queue_name = os.environ.get('AI_FILES_QUEUE_NAME', 'ai-files')
    
    if ai_file_service is None:
        from api.services import get_ai_file_service
        ai_file_service = get_ai_file_service()
        
    return AIFileConsumer(queue_name, ai_file_service) 