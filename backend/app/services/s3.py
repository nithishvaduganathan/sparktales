"""
AWS S3 service for file storage
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from fastapi import HTTPException, UploadFile
import uuid
from datetime import datetime
from app.config import get_settings

settings = get_settings()


class S3Service:
    """Service for AWS S3 file operations"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            region_name=settings.s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.s3_region
    
    def _generate_key(self, filename: str, folder: str = "uploads") -> str:
        """Generate a unique S3 key for a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        # Clean filename
        clean_name = "".join(c for c in filename if c.isalnum() or c in ".-_")
        return f"{folder}/{timestamp}_{unique_id}_{clean_name}"
    
    def get_file_url(self, key: str) -> str:
        """Get the public URL for a file in S3"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
    
    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "uploads",
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to S3
        
        Args:
            file: The file to upload
            folder: S3 folder/prefix
            content_type: Optional content type override
            
        Returns:
            Dict with file URL and key
        """
        try:
            key = self._generate_key(file.filename, folder)
            
            # Read file content
            content = await file.read()
            
            # Determine content type
            file_content_type = content_type or file.content_type or "application/octet-stream"
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=file_content_type,
            )
            
            return {
                "key": key,
                "url": self.get_file_url(key),
                "filename": file.filename,
                "content_type": file_content_type,
                "size": len(content),
            }
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        expires_in: int = 3600
    ) -> dict:
        """
        Generate a presigned URL for direct upload from frontend
        
        Args:
            filename: Name of the file
            content_type: MIME type of the file
            folder: S3 folder/prefix
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with upload URL and file URL
        """
        try:
            key = self._generate_key(filename, folder)
            
            presigned_url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type,
                },
                ExpiresIn=expires_in,
            )
            
            return {
                "upload_url": presigned_url,
                "file_url": self.get_file_url(key),
                "key": key,
                "expires_in": expires_in,
            }
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate upload URL: {str(e)}"
            )
    
    def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for downloading a file
        
        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned download URL
        """
        try:
            presigned_url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                },
                ExpiresIn=expires_in,
            )
            return presigned_url
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            key: S3 object key
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> list:
        """
        List files in S3 bucket with prefix
        
        Args:
            prefix: S3 key prefix to filter by
            max_keys: Maximum number of files to return
            
        Returns:
            List of file info dicts
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            
            files = []
            for obj in response.get("Contents", []):
                files.append({
                    "key": obj["Key"],
                    "url": self.get_file_url(obj["Key"]),
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
            
            return files
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files: {str(e)}"
            )


# Singleton instance
s3_service = S3Service()
