"""
Service for storage management
"""

import io
import uuid
from pathlib import Path
import logging

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException

from src.app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storage management"""

    def __init__(self):
        self.minio_endpoint = settings.minio_endpoint
        self.minio_access_key = settings.minio_access_key
        self.minio_secret_key = settings.minio_secret_key
        self.minio_secure = settings.minio_secure
        self.bucket_name = settings.minio_bucket_name

        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=self.minio_secure
        )

        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create the bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created successfully")
        except S3Error as e:
            logger.error(f"Error creating/verifying bucket: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage error: {str(e)}"
            )

    async def upload_file(self, file: UploadFile, folder: str = "pdfs") -> str:
        """
        Upload file to MinIO/S3
        
        Args:
            file: File to upload
            folder: Folder where to save the file
            
        Returns:
            str: Name of the object in MinIO (path of the file)
        """
        try:
            file_extension = Path(file.filename).suffix if file.filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            object_name = f"{folder}/{unique_filename}"

            file_content = await file.read()
            file_size = len(file_content)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=(
                    file.content_type or "application/octet-stream"
                )
            )
            
            logger.info(f"File uploaded successfully: {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(e)}"
            )
    
    def get_file_url(self, object_name: str, expires_in_hours: int = 1) -> str:
        """
        Generate presigned URL to download file
        
        Args:
            object_name: Name of the object in MinIO
            expires_in_hours: Validity hours of the URL
            
        Returns:
            str: Presigned URL to download file
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(hours=expires_in_hours)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating URL: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating URL to download file: {str(e)}"
            )
    
    def get_file_stream(self, object_name: str):
        """
        Get stream of the file for direct download
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            Stream of the file
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return response
        except S3Error as e:
            logger.error(f"Error getting file: {e}")
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO/S3
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            bool: True if the file was deleted successfully
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"File deleted: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        Verify if a file exists in MinIO/S3
        
        Args:
            object_name: Name of the object to verify
            
        Returns:
            bool: True if the file exists
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False


storage_service = StorageService()
