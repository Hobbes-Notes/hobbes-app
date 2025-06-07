"""
S3 Repository Implementation

This module provides an implementation of the S3 repository interface.
"""

import logging
import json
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO, Union
import asyncio
import io

from api.repositories.s3_repository import S3Repository
from infrastructure.s3_client import get_s3_client

# Set up logging
logger = logging.getLogger(__name__)

class S3RepositoryImpl(S3Repository):
    """
    Implementation of the S3 repository.
    """
    
    def __init__(self, bucket_name: str):
        """
        Initialize the repository.
        
        Args:
            bucket_name: Name of the S3 bucket to use
        """
        self._bucket_name = bucket_name
        self._s3_client = get_s3_client()
        
        # Ensure the bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """
        Ensure the S3 bucket exists, creating it if necessary.
        """
        if not self._s3_client.bucket_exists(self._bucket_name):
            logger.info(f"Creating S3 bucket: {self._bucket_name}")
            
            # Create the bucket
            self._s3_client.create_bucket(self._bucket_name)
            
            logger.info(f"Created S3 bucket: {self._bucket_name}")
    
    async def upload_file(self, file_data: Union[bytes, BinaryIO, str], object_key: str, 
                        content_type: Optional[str] = None,
                        metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload a file to S3.
        
        Args:
            file_data: File data as bytes, file-like object, or local file path
            object_key: S3 object key (path) for the file
            content_type: Optional content type of the file
            metadata: Optional metadata for the file
            
        Returns:
            True if the file was uploaded successfully, False otherwise
        """
        # Run the upload in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.upload_file(
                file_data=file_data,
                bucket_name=self._bucket_name,
                object_key=object_key,
                content_type=content_type,
                metadata=metadata
            )
        )
    
    async def download_file(self, object_key: str) -> Optional[bytes]:
        """
        Download a file from S3.
        
        Args:
            object_key: S3 object key (path) for the file
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        # Run the download in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.download_file(
                bucket_name=self._bucket_name,
                object_key=object_key
            )
        )
    
    async def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_key: S3 object key (path) for the file
            
        Returns:
            True if the file was deleted successfully, False otherwise
        """
        # Run the delete in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.delete_file(
                bucket_name=self._bucket_name,
                object_key=object_key
            )
        )
    
    async def list_files(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in the S3 bucket with an optional prefix.
        
        Args:
            prefix: Optional prefix to filter files by
            
        Returns:
            List of file information dictionaries
        """
        # Run the list in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.list_files(
                bucket_name=self._bucket_name,
                prefix=prefix
            )
        )
    
    async def generate_presigned_url(self, object_key: str, 
                                   expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            object_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        # Run the URL generation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.generate_presigned_url(
                bucket_name=self._bucket_name,
                object_key=object_key,
                expiration=expiration
            )
        )
    
    async def get_object_metadata(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an S3 object.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            Dictionary of metadata if successful, None otherwise
        """
        # Run the metadata retrieval in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._s3_client.get_object_metadata(
                bucket_name=self._bucket_name,
                object_key=object_key
            )
        ) 