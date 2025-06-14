"""
AI File Controller Module

This controller provides endpoints for managing AI file operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Response
from typing import List, Dict, Any
from datetime import datetime
import json
import uuid
import os
import csv
import io

from api.models.ai_file import (
    AIFileRecord, AIFileState, AIFileListResponse, AIFileGetResponse
)
from api.models.api import APIResponse
from api.services import get_ai_file_service
from api.services.ai_file_service import AIFileService

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ai/files",
    tags=["ai-files"],
    responses={404: {"description": "Not found"}},
)

# Use FastAPI dependency injection from services layer

@router.post("", response_model=APIResponse)
async def upload_csv_file(
    request: Request,
    file: UploadFile = File(...),
    use_case: str = Form(...),
    version: int = Form(...),
    ai_file_service: AIFileService = Depends(get_ai_file_service)
):
    """
    Upload a CSV file for AI processing.
    
    The CSV file should have at least an 'input' column, and optionally an 'expected_output' column.
    The input column should contain JSON data that will be processed by the AI service.
    """
    try:
        # Get user ID from request
        user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
        
        # Generate a file ID
        file_id = str(uuid.uuid4())
        
        # Read the CSV file
        contents = await file.read()
        
        # Upload the CSV file and create a record
        file_record = await ai_file_service.upload_csv_file(
            file_id=file_id,
            file_data=contents,
            use_case=use_case,
            version=version,
            user_id=user_id,
            filename=file.filename
        )
        
        # Return response
        return APIResponse(
            success=True,
            message="CSV file uploaded successfully",
            data={
                "file_id": file_record.file_id,
                "state": file_record.state
            }
        )
    except Exception as e:
        logger.error(f"Error uploading CSV file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading CSV file: {str(e)}"
        )

@router.get("", response_model=APIResponse)
async def list_files(
    request: Request,
    ai_file_service: AIFileService = Depends(get_ai_file_service)
):
    """
    List all AI files for the current user.
    """
    try:
        # Get user ID from request
        user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
        
        # Get file records
        file_records = await ai_file_service.get_file_records_by_user(user_id)
        
        # Return response
        return APIResponse(
            success=True,
            message=f"Found {len(file_records)} files",
            data=AIFileListResponse(
                files=file_records
            )
        )
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing files: {str(e)}"
        )

@router.get("/{file_id}", response_model=APIResponse)
async def get_file(
    file_id: str,
    request: Request,
    ai_file_service: AIFileService = Depends(get_ai_file_service)
):
    """
    Get an AI file by ID.
    """
    try:
        # Get user ID from request
        user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
        
        # Get file record
        file_record = await ai_file_service.get_file_record(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
            
        # Check if the file belongs to the user
        if file_record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this file"
            )
        
        # Get download URLs for the input and output files
        input_download_url = await ai_file_service.get_file_download_url(file_id, is_output=False)
        output_download_url = None
        if file_record.state == AIFileState.COMPLETED and file_record.output_s3_key:
            output_download_url = await ai_file_service.get_file_download_url(file_id, is_output=True)
            
        # Return response
        return APIResponse(
            success=True,
            message="File found",
            data=AIFileGetResponse(
                file=file_record,
                input_download_url=input_download_url,
                output_download_url=output_download_url
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting file: {str(e)}"
        )

@router.post("/{file_id}/interrupt", response_model=APIResponse)
async def interrupt_file_processing(
    file_id: str,
    request: Request,
    ai_file_service: AIFileService = Depends(get_ai_file_service)
):
    """
    Interrupt the processing of an AI file.
    """
    try:
        # Get user ID from request
        user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
        
        # Get file record
        file_record = await ai_file_service.get_file_record(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
            
        # Check if the file belongs to the user
        if file_record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to interrupt this file's processing"
            )
            
        # Check if the file is in a state that can be interrupted
        if file_record.state != AIFileState.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file_id} is not currently being processed (state: {file_record.state})"
            )
            
        # Interrupt the file processing
        success = await ai_file_service.interrupt_file_processing(file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to interrupt processing of file {file_id}"
            )
            
        # Return response
        return APIResponse(
            success=True,
            message=f"Processing of file {file_id} has been interrupted"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interrupting file processing {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interrupting file processing: {str(e)}"
        ) 