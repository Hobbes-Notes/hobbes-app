"""
AI File Service

This module provides services for AI file operations.
"""

import logging
import json
import uuid
import os
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO, Union

from ..models.ai_file import AIFile, AIFileRecord, AIFileState, AIFileInput, AIFileOutput
from ..repositories.ai_file_repository import AIFileRepository
from ..repositories.s3_repository import S3Repository
from api.services.ai_service import AIService
from api.models.ai import AIUseCase, AIConfiguration
from infrastructure.sqs_client import get_sqs_client

# Set up logging
logger = logging.getLogger(__name__)

class AIFileService:
    """
    Service for AI file operations.
    """
    
    def __init__(self, ai_file_repository: AIFileRepository, s3_repository: S3Repository, ai_service: AIService):
        """
        Initialize the service.
        
        Args:
            ai_file_repository: Repository for AI file records
            s3_repository: Repository for S3 operations
            ai_service: AI service for AI operations
        """
        self._ai_file_repository = ai_file_repository
        self._s3_repository = s3_repository
        self._ai_service = ai_service
        self._sqs_client = get_sqs_client()
        self._queue_name = os.environ.get('AI_FILES_QUEUE_NAME', 'ai-files')
    
    async def upload_file(self, file_content: AIFile, user_id: str) -> AIFileRecord:
        """
        Upload an AI file and queue it for processing.
        
        Args:
            file_content: Content of the file
            user_id: ID of the user uploading the file
            
        Returns:
            The created file record
        """
        # Generate a file ID if not provided
        if not file_content.file_id:
            file_content.file_id = str(uuid.uuid4())
            
        # Create timestamps
        now = datetime.now().isoformat()
        
        # Create S3 keys
        input_s3_key = f"input/{file_content.file_id}.json"
        
        # Create file record
        file_record = AIFileRecord(
            file_id=file_content.file_id,
            user_id=user_id,
            state=AIFileState.ACCEPTED,
            created_at=now,
            updated_at=now,
            input_s3_key=input_s3_key
        )
        
        # Upload file to S3
        input_json = file_content.json()
        await self._s3_repository.upload_file(
            file_data=input_json.encode('utf-8'),
            object_key=input_s3_key,
            content_type='application/json'
        )
        
        # Create file record in DynamoDB
        await self._ai_file_repository.create_file_record(file_record)
        
        # Queue the file for processing
        await self._queue_file_for_processing(file_record.file_id)
        
        logger.info(f"Uploaded AI file {file_content.file_id} for user {user_id}")
        return file_record
    
    async def upload_csv_file(self, file_id: str, file_data: bytes, use_case: str, version: int, user_id: str, filename: str) -> AIFileRecord:
        """
        Upload a CSV file and queue it for processing.
        
        Args:
            file_id: ID for the file
            file_data: Content of the CSV file
            use_case: Use case for AI processing
            version: Version of the AI configuration to use
            user_id: ID of the user uploading the file
            filename: Name of the uploaded file
            
        Returns:
            The created file record
        """
        # Create timestamps
        now = datetime.now().isoformat()
        
        # Create S3 keys
        input_s3_key = f"input/{file_id}.csv"
        
        # Create file record
        file_record = AIFileRecord(
            file_id=file_id,
            user_id=user_id,
            state=AIFileState.ACCEPTED,
            created_at=now,
            updated_at=now,
            input_s3_key=input_s3_key,
            metadata={
                "use_case": use_case,
                "version": version,
                "filename": filename
            }
        )
        
        # Upload file to S3
        await self._s3_repository.upload_file(
            file_data=file_data,
            object_key=input_s3_key,
            content_type='text/csv'
        )
        
        # Create file record in DynamoDB
        await self._ai_file_repository.create_file_record(file_record)
        
        # Queue the file for processing
        await self._queue_file_for_processing(file_record.file_id)
        
        logger.info(f"Uploaded CSV file {file_id} for user {user_id}")
        return file_record
    
    async def _queue_file_for_processing(self, file_id: str) -> bool:
        """
        Queue a file for processing by sending a message to SQS.
        
        Args:
            file_id: ID of the file to process
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        # Get the file record to include more information in the message
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            logger.error(f"Failed to queue file {file_id} for processing: file record not found")
            return False
            
        # Convert metadata to ensure it's JSON serializable
        metadata = {}
        for key, value in file_record.metadata.items():
            # Convert Decimal to int or float
            if hasattr(value, 'as_integer_ratio'):  # Check if it's a Decimal
                if value % 1 == 0:  # Check if it's a whole number
                    metadata[key] = int(value)
                else:
                    metadata[key] = float(value)
            else:
                metadata[key] = value
            
        # Send message to SQS queue for processing with more information
        message = {
            "file_id": file_id,
            "user_id": file_record.user_id,
            "state": file_record.state.value,
            "input_s3_key": file_record.input_s3_key,
            "metadata": metadata
        }
        
        logger.debug(f"Queueing file {file_id} for processing with message: {message}")
        
        # Send the message
        message_id = self._sqs_client.send_message(
            queue_name=self._queue_name,
            message_body=message
        )
        
        if message_id:
            logger.info(f"Sent message to queue {self._queue_name} with ID {message_id} for file {file_id}")
            return True
        else:
            logger.error(f"Failed to send message to queue {self._queue_name} for file {file_id}")
            return False
    
    async def get_file_record(self, file_id: str) -> Optional[AIFileRecord]:
        """
        Get a file record by ID.
        
        Args:
            file_id: The ID of the file record to get
            
        Returns:
            The file record if found, None otherwise
        """
        return await self._ai_file_repository.get_file_record(file_id)
    
    async def get_file_records_by_user(self, user_id: str) -> List[AIFileRecord]:
        """
        Get all file records for a user.
        
        Args:
            user_id: The ID of the user to get file records for
            
        Returns:
            List of file records for the user
        """
        return await self._ai_file_repository.get_file_records_by_user(user_id)
    
    async def get_file_download_url(self, file_id: str, is_output: bool = False) -> Optional[str]:
        """
        Get a presigned URL to download a file.
        
        Args:
            file_id: The ID of the file to download
            is_output: Whether to get the output file (True) or input file (False)
            
        Returns:
            Presigned URL if the file exists, None otherwise
        """
        # Get the file record
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            return None
            
        # Get the S3 key
        if is_output:
            if not file_record.output_s3_key:
                return None
            s3_key = file_record.output_s3_key
        else:
            s3_key = file_record.input_s3_key
            
        # Generate presigned URL
        return await self._s3_repository.generate_presigned_url(s3_key)
    
    async def get_file_as_csv(self, file_id: str, is_output: bool = False) -> Optional[bytes]:
        """
        Get a file as CSV data.
        
        Args:
            file_id: The ID of the file to get
            is_output: Whether to get the output file (True) or input file (False)
            
        Returns:
            CSV data if the file exists, None otherwise
        """
        # Get the file record
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            return None
            
        # Get the S3 key
        if is_output:
            if not file_record.output_s3_key:
                return None
            s3_key = file_record.output_s3_key
        else:
            s3_key = file_record.input_s3_key
            
        # Download the file
        file_data = await self._s3_repository.download_file(s3_key)
        if not file_data:
            return None
            
        return file_data
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_id: The ID of the file to delete
            
        Returns:
            True if the file was deleted, False otherwise
        """
        # Get the file record
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            return False
            
        # Delete the files from S3
        await self._s3_repository.delete_file(file_record.input_s3_key)
        if file_record.output_s3_key:
            await self._s3_repository.delete_file(file_record.output_s3_key)
            
        # Delete the file record
        return await self._ai_file_repository.delete_file_record(file_id)
    
    async def interrupt_file_processing(self, file_id: str) -> bool:
        """
        Interrupt the processing of a file.
        
        Args:
            file_id: The ID of the file to interrupt
            
        Returns:
            True if the file processing was interrupted, False otherwise
        """
        # Get the file record
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            return False
            
        # Update the file state to interrupted
        await self._ai_file_repository.update_file_state(file_id, AIFileState.INTERRUPTED)
        logger.info(f"Interrupted processing of file {file_id}, state updated to {AIFileState.INTERRUPTED}")
        
        return True
    
    async def process_file(self, file_id: str) -> bool:
        """
        Process a CSV file.
        
        Args:
            file_id: The ID of the file to process
            
        Returns:
            True if the file was processed successfully, False otherwise
        """
        logger.info(f"Starting to process file {file_id}")
        
        # Get the file record
        file_record = await self._ai_file_repository.get_file_record(file_id)
        if not file_record:
            logger.error(f"File record {file_id} not found")
            return False
            
        logger.info(f"Retrieved file record {file_id} - Current state: {file_record.state}, Metadata: {file_record.metadata}")
            
        # Update the file state to processing
        await self._ai_file_repository.update_file_state(file_id, AIFileState.PROCESSING)
        logger.info(f"Processing file {file_id}, state updated to {AIFileState.PROCESSING}")
        
        try:
            # Download the input CSV file
            logger.info(f"Downloading file from S3: {file_record.input_s3_key}")
            csv_data = await self._s3_repository.download_file(file_record.input_s3_key)
            if not csv_data:
                error_message = f"Input file {file_record.input_s3_key} not found"
                logger.error(error_message)
                await self._ai_file_repository.update_file_state(file_id, AIFileState.FAILED, error_message)
                return False
            
            logger.info(f"Successfully downloaded file {file_record.input_s3_key}, size: {len(csv_data)} bytes")
            
            # Get metadata from file record
            use_case = file_record.metadata.get("use_case")
            version = file_record.metadata.get("version")
            
            logger.info(f"File {file_id} metadata - Use case: {use_case}, Version: {version}")
            
            if not use_case or not version:
                error_message = "Missing use_case or version in file metadata"
                logger.error(error_message)
                await self._ai_file_repository.update_file_state(file_id, AIFileState.FAILED, error_message)
                return False
            
            # Parse the CSV file
            logger.info(f"Parsing CSV file for {file_id}")
            csv_text = csv_data.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            
            # Check if the CSV has the required columns
            fieldnames = csv_reader.fieldnames
            logger.info(f"CSV columns: {fieldnames}")
            
            if not fieldnames or 'input' not in fieldnames:
                error_message = "CSV file must have an 'input' column"
                logger.error(error_message)
                await self._ai_file_repository.update_file_state(file_id, AIFileState.FAILED, error_message)
                return False
            
            # Process each row in the CSV
            rows = list(csv_reader)
            total_records = len(rows)
            processed_records = 0
            processed_rows = []
            processing_errors = []
            
            logger.info(f"Found {total_records} records to process in file {file_id}")
            
            # Update the file record with total records count
            await self._ai_file_repository.update_file_record(
                file_id=file_id,
                updates={
                    'total_records': total_records,
                    'processed_records': processed_records
                }
            )
            
            logger.info(f"Updated file record with total_records={total_records}")
            
            # Create output CSV with headers
            output_fieldnames = ['input']
            if any('expected_output' in row for row in rows):
                output_fieldnames.append('expected_output')
            output_fieldnames.append('actual_output')
            
            logger.info(f"Created output CSV with columns: {output_fieldnames}")
            
            output_buffer = io.StringIO()
            csv_writer = csv.DictWriter(output_buffer, fieldnames=output_fieldnames)
            csv_writer.writeheader()
            
            # Process each row
            for i, row in enumerate(rows):
                # Check if processing has been interrupted
                current_file_record = await self._ai_file_repository.get_file_record(file_id)
                if current_file_record.state == AIFileState.INTERRUPTED:
                    logger.info(f"Processing of file {file_id} was interrupted after processing {processed_records} of {total_records} records")
                    
                    # Upload the partial output file
                    output_s3_key = f"output/{file_id}.csv"
                    logger.info(f"Uploading partial output file to {output_s3_key}")
                    
                    await self._s3_repository.upload_file(
                        file_data=output_buffer.getvalue().encode('utf-8'),
                        object_key=output_s3_key,
                        content_type='text/csv'
                    )
                    
                    # Update the file record
                    await self._ai_file_repository.update_file_record(
                        file_id=file_id,
                        updates={
                            'output_s3_key': output_s3_key,
                            'processed_records': processed_records
                        }
                    )
                    
                    logger.info(f"Updated file record with output_s3_key and processed_records={processed_records}")
                    return True
                
                try:
                    logger.debug(f"Processing row {i+1}/{total_records} for file {file_id}")
                    
                    # Parse the input JSON
                    input_json = json.loads(row['input'])
                    
                    # Process with AI based on use case
                    logger.debug(f"Calling AI service for row {i+1} with use case {use_case}")
                    
                    if use_case == AIUseCase.PROJECT_SUMMARY.value:
                        result = await self._ai_service.generate_project_summary(input_json, version=int(version))
                        response = {"summary": result}
                    elif use_case == AIUseCase.RELEVANCE_EXTRACTION.value:
                        result = await self._ai_service.extract_relevant_note_for_project(input_json, version=int(version))
                        response = {
                            "is_relevant": result.is_relevant,
                            "extracted_content": result.extracted_content,
                            "annotation": result.annotation if result.annotation else ""
                        }
                    else:
                        error_msg = f"Unsupported use case: {use_case}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    
                    # Create output row
                    output_row = {
                        'input': row['input']
                    }
                    
                    # Add expected_output if it exists
                    if 'expected_output' in row and row['expected_output']:
                        output_row['expected_output'] = row['expected_output']
                    
                    # Add actual_output
                    output_row['actual_output'] = json.dumps(response)
                    
                    # Write the row to the output file
                    csv_writer.writerow(output_row)
                    processed_rows.append(output_row)
                    
                    # Update processed records count
                    processed_records += 1
                    
                    # Update the file record with progress every 10 records
                    if processed_records % 10 == 0 or processed_records == total_records:
                        logger.info(f"Processed {processed_records}/{total_records} records for file {file_id}")
                        await self._ai_file_repository.update_file_record(
                            file_id=file_id,
                            updates={
                                'processed_records': processed_records
                            }
                        )
                except Exception as e:
                    error_msg = f"Error processing row {i+1}: {str(e)}"
                    logger.error(error_msg)
                    processing_errors.append(error_msg)
                    
                    # Add row with error
                    output_row = {
                        'input': row['input']
                    }
                    
                    # Add expected_output if it exists
                    if 'expected_output' in row and row['expected_output']:
                        output_row['expected_output'] = row['expected_output']
                    
                    # Add error as actual_output
                    output_row['actual_output'] = json.dumps({"error": str(e)})
                    
                    # Write the row to the output file
                    csv_writer.writerow(output_row)
                    processed_rows.append(output_row)
                    
                    # Update processed records count
                    processed_records += 1
                    
                    # Update the file record with progress every 10 records
                    if processed_records % 10 == 0 or processed_records == total_records:
                        logger.info(f"Processed {processed_records}/{total_records} records for file {file_id} (with errors)")
                        await self._ai_file_repository.update_file_record(
                            file_id=file_id,
                            updates={
                                'processed_records': processed_records
                            }
                        )
            
            # Upload output CSV to S3
            output_s3_key = f"output/{file_id}.csv"
            logger.info(f"Uploading final output file to {output_s3_key}")
            
            await self._s3_repository.upload_file(
                file_data=output_buffer.getvalue().encode('utf-8'),
                object_key=output_s3_key,
                content_type='text/csv'
            )
            
            # Update the file record
            updates = {
                'output_s3_key': output_s3_key,
                'processed_records': processed_records
            }
            
            # Set state based on whether there were any errors
            if processing_errors:
                updates['state'] = AIFileState.COMPLETED.value
                error_summary = f"Processed with {len(processing_errors)} errors: {'; '.join(processing_errors[:3])}" + (f" and {len(processing_errors) - 3} more" if len(processing_errors) > 3 else "")
                updates['error_message'] = error_summary
                logger.info(f"Completed processing file {file_id} with errors: {error_summary}")
            else:
                updates['state'] = AIFileState.COMPLETED.value
                logger.info(f"Successfully completed processing file {file_id} with no errors")
                
            await self._ai_file_repository.update_file_record(
                file_id=file_id,
                updates=updates
            )
            
            logger.info(f"Processed CSV file {file_id}, state updated to {AIFileState.COMPLETED}")
            return True
        except Exception as e:
            error_message = f"Error processing file: {str(e)}"
            logger.error(error_message, exc_info=True)
            await self._ai_file_repository.update_file_state(file_id, AIFileState.FAILED, error_message)
            logger.info(f"Failed to process file {file_id}, state updated to {AIFileState.FAILED}")
            return False 