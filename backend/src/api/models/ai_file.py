"""
AI File Models

This module defines models related to AI file operations in the system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class AIFileState(str, Enum):
    """
    Enum representing different states of an AI file in the system.
    """
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

class AIFileInput(BaseModel):
    """
    Model representing the input section of an AI file.
    
    Attributes:
        use_case: The use case this file is for
        version: The version of the AI configuration to use
        parameters: The parameters to use for the AI operation
        expected_response: The expected response format (will be copied to output)
    """
    use_case: str
    version: int
    parameters: Dict[str, Any]
    expected_response: Optional[Dict[str, Any]] = None

class AIFileOutput(BaseModel):
    """
    Model representing the output section of an AI file.
    
    Attributes:
        response: The response from the AI operation
        expected_response: The expected response format (copied from input)
    """
    response: Optional[Dict[str, Any]] = None
    expected_response: Optional[Dict[str, Any]] = None

class AIFile(BaseModel):
    """
    Model representing an AI file in the system.
    
    Attributes:
        file_id: Unique identifier for the file
        input: The input section of the file
        output: The output section of the file
    """
    file_id: str
    input: AIFileInput
    output: Optional[AIFileOutput] = None

class AIFileRecord(BaseModel):
    """
    Model representing a record of an AI file in the system.
    
    Attributes:
        file_id: Unique identifier for the file
        user_id: ID of the user who uploaded the file
        state: Current state of the file
        created_at: When the file was created
        updated_at: When the file was last updated
        input_s3_key: S3 key for the input file
        output_s3_key: S3 key for the output file
        error_message: Error message if the file failed to process
        metadata: Additional metadata for the file (e.g., use_case, version)
        total_records: Total number of records in the input file
        processed_records: Number of records processed so far
    """
    file_id: str
    user_id: str
    state: AIFileState
    created_at: str
    updated_at: str
    input_s3_key: str
    output_s3_key: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    total_records: Optional[int] = None
    processed_records: Optional[int] = None

class AIFileUploadRequest(BaseModel):
    """
    Model representing a request to upload an AI file.
    
    Attributes:
        file_content: The content of the file as a JSON object
    """
    file_content: AIFile

class AIFileUploadResponse(BaseModel):
    """
    Model representing a response to an AI file upload request.
    
    Attributes:
        file_id: Unique identifier for the uploaded file
        state: Current state of the file
    """
    file_id: str
    state: AIFileState

class AIFileListResponse(BaseModel):
    """
    Model representing a response to an AI file list request.
    
    Attributes:
        files: List of AI file records
    """
    files: List[AIFileRecord]

class AIFileGetResponse(BaseModel):
    """
    Model representing a response to an AI file get request.
    
    Attributes:
        file: The AI file record
        input_download_url: Presigned URL to download the input file
        output_download_url: Presigned URL to download the output file (if available)
    """
    file: AIFileRecord
    input_download_url: Optional[str] = None
    output_download_url: Optional[str] = None 