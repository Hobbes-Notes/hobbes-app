"""
S3 Repository Interface

This module defines the interface for S3 repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, BinaryIO, Union

class S3Repository(ABC):
    """
    Repository interface for S3 operations.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def download_file(self, object_key: str) -> Optional[bytes]:
        """
        Download a file from S3.
        
        Args:
            object_key: S3 object key (path) for the file
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_key: S3 object key (path) for the file
            
        Returns:
            True if the file was deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_files(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in the S3 bucket with an optional prefix.
        
        Args:
            prefix: Optional prefix to filter files by
            
        Returns:
            List of file information dictionaries
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_object_metadata(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an S3 object.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            Dictionary of metadata if successful, None otherwise
        """
        pass 