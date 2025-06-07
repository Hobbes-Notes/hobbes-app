"""
S3 Client

This module provides a comprehensive wrapper around the AWS S3 library to simplify
interactions with S3 and provide a clean abstraction for the application.

This client implements best practices for working with S3 and handles:
- Connection management
- Error handling and logging
- Common S3 operations with simplified interfaces
- Presigned URL generation
"""

import logging
import boto3
import os
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple
import io

logger = logging.getLogger(__name__)

# Singleton instance of S3 client
_s3_client_instance: Optional['S3Client'] = None

class S3Client:
    """
    A wrapper client for AWS S3.
    
    This client provides simplified methods for common S3 operations
    and handles connection management and error handling. It is designed to be
    used as the foundation for all S3 interactions in the application.
    
    Features:
    - Simplified API for common operations
    - Comprehensive error handling
    - Consistent logging
    - Support for local S3 endpoints for development
    """
    
    def __init__(self, region_name: str = 'us-east-1', endpoint_url: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        """
        Initialize the S3 client.
        
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
            endpoint_url = os.environ.get('S3_ENDPOINT')
            
        # Initialize the S3 client
        self._s3 = boto3.client(
            's3',
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Initialize the S3 resource for higher-level operations
        self._s3_resource = boto3.resource(
            's3',
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        logger.info(f"Initialized S3 client with endpoint: {endpoint_url or 'default AWS'}")
    
    def list_buckets(self) -> List[str]:
        """
        List all S3 buckets.
        
        Returns:
            List of bucket names
        """
        try:
            response = self._s3.list_buckets()
            return [bucket['Name'] for bucket in response.get('Buckets', [])]
        except ClientError as e:
            logger.error(f"Error listing buckets: {str(e)}")
            raise
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        Args:
            bucket_name: Name of the bucket to check
            
        Returns:
            True if the bucket exists, False otherwise
        """
        try:
            self._s3.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            elif e.response['Error']['Code'] == '403':
                logger.error(f"Access denied to bucket {bucket_name}")
                return True  # Bucket exists but we don't have access
            else:
                logger.error(f"Error checking if bucket {bucket_name} exists: {str(e)}")
                raise
    
    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """
        Create a new S3 bucket.
        
        Args:
            bucket_name: Name of the bucket to create
            region: AWS region for the bucket
            
        Returns:
            True if the bucket was created, False otherwise
        """
        try:
            if region is None:
                region = os.environ.get('AWS_REGION', 'us-east-1')
                
            if region == 'us-east-1':
                self._s3.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': region}
                self._s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=location
                )
            logger.info(f"Created bucket {bucket_name} in region {region}")
            return True
        except ClientError as e:
            logger.error(f"Error creating bucket {bucket_name}: {str(e)}")
            return False
    
    def upload_file(self, file_data: Union[bytes, BinaryIO, str], bucket_name: str, 
                   object_key: str, content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload a file to S3.
        
        Args:
            file_data: File data as bytes, file-like object, or local file path
            bucket_name: Name of the bucket to upload to
            object_key: S3 object key (path) for the file
            content_type: Optional content type of the file
            metadata: Optional metadata for the file
            
        Returns:
            True if the file was uploaded successfully, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
                
            # Handle different input types
            if isinstance(file_data, str):
                # Assume it's a file path
                self._s3.upload_file(file_data, bucket_name, object_key, ExtraArgs=extra_args)
            elif isinstance(file_data, bytes):
                # It's bytes data
                self._s3.upload_fileobj(io.BytesIO(file_data), bucket_name, object_key, ExtraArgs=extra_args)
            else:
                # Assume it's a file-like object
                self._s3.upload_fileobj(file_data, bucket_name, object_key, ExtraArgs=extra_args)
                
            logger.info(f"Uploaded file to s3://{bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to s3://{bucket_name}/{object_key}: {str(e)}")
            return False
    
    def download_file(self, bucket_name: str, object_key: str) -> Optional[bytes]:
        """
        Download a file from S3.
        
        Args:
            bucket_name: Name of the bucket to download from
            object_key: S3 object key (path) for the file
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        try:
            response = self._s3.get_object(Bucket=bucket_name, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: s3://{bucket_name}/{object_key}")
                return None
            else:
                logger.error(f"Error downloading file from s3://{bucket_name}/{object_key}: {str(e)}")
                raise
    
    def download_file_to_path(self, bucket_name: str, object_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to a local path.
        
        Args:
            bucket_name: Name of the bucket to download from
            object_key: S3 object key (path) for the file
            local_path: Local path to save the file to
            
        Returns:
            True if the file was downloaded successfully, False otherwise
        """
        try:
            self._s3.download_file(bucket_name, object_key, local_path)
            logger.info(f"Downloaded file from s3://{bucket_name}/{object_key} to {local_path}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: s3://{bucket_name}/{object_key}")
                return False
            else:
                logger.error(f"Error downloading file from s3://{bucket_name}/{object_key} to {local_path}: {str(e)}")
                return False
    
    def delete_file(self, bucket_name: str, object_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            bucket_name: Name of the bucket to delete from
            object_key: S3 object key (path) for the file
            
        Returns:
            True if the file was deleted successfully, False otherwise
        """
        try:
            self._s3.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"Deleted file s3://{bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file s3://{bucket_name}/{object_key}: {str(e)}")
            return False
    
    def list_files(self, bucket_name: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a bucket with an optional prefix.
        
        Args:
            bucket_name: Name of the bucket to list files from
            prefix: Optional prefix to filter files by
            
        Returns:
            List of file information dictionaries
        """
        try:
            params = {'Bucket': bucket_name}
            if prefix:
                params['Prefix'] = prefix
                
            response = self._s3.list_objects_v2(**params)
            
            if 'Contents' not in response:
                return []
                
            return [
                {
                    'key': item['Key'],
                    'size': item['Size'],
                    'last_modified': item['LastModified'],
                    'etag': item['ETag'].strip('"')
                }
                for item in response['Contents']
            ]
        except ClientError as e:
            logger.error(f"Error listing files in bucket {bucket_name}: {str(e)}")
            raise
    
    def generate_presigned_url(self, bucket_name: str, object_key: str, 
                              expiration: int = 3600, method: str = 'get_object') -> Optional[str]:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            bucket_name: Name of the bucket
            object_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            method: S3 method to generate URL for (default: get_object)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            url = self._s3.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            
            # Replace internal Docker hostname with localhost for external access
            if 'localstack:4566' in url:
                url = url.replace('localstack:4566', 'localhost:4566')
                logger.info(f"Modified presigned URL to use localhost: {url}")
                
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL for s3://{bucket_name}/{object_key}: {str(e)}")
            return None
    
    def get_object_metadata(self, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an S3 object.
        
        Args:
            bucket_name: Name of the bucket
            object_key: S3 object key (path)
            
        Returns:
            Dictionary of metadata if successful, None otherwise
        """
        try:
            response = self._s3.head_object(Bucket=bucket_name, Key=object_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object not found: s3://{bucket_name}/{object_key}")
                return None
            else:
                logger.error(f"Error getting metadata for s3://{bucket_name}/{object_key}: {str(e)}")
                raise
    
    def get_client(self):
        """
        Get the underlying boto3 S3 client.
        
        Returns:
            boto3 S3 client
        """
        return self._s3
    
    def get_resource(self):
        """
        Get the underlying boto3 S3 resource.
        
        Returns:
            boto3 S3 resource
        """
        return self._s3_resource


def get_s3_client() -> S3Client:
    """
    Get the singleton instance of the S3 client.
    
    Returns:
        S3Client instance
    """
    global _s3_client_instance
    
    if _s3_client_instance is None:
        # Get configuration from environment variables
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        endpoint_url = os.environ.get('S3_ENDPOINT')
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        _s3_client_instance = S3Client(
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
    return _s3_client_instance 