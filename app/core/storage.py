"""
Storage Utilities for InsureCove Document Service

This module provides storage abstractions and utilities for handling
file storage operations with support for local and AWS S3 backends.

Author: InsureCove Team
Date: July 8, 2025
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, IO, Union
from datetime import datetime, timedelta
from pathlib import Path
import mimetypes
import uuid
import aiofiles
import asyncio
from urllib.parse import urlparse

# TODO: Import exceptions
# from app.core.exceptions import StorageError

# TODO: Import AWS SDK
# import boto3
# from botocore.exceptions import ClientError, NoCredentialsError

# TODO: Import configuration
# from app.core.config import settings
# from app.core.exceptions import StorageError, StorageQuotaExceededError


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def store_file(
        self,
        file_content: Union[bytes, IO],
        storage_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store file content to storage backend"""
        pass
    
    @abstractmethod
    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file content from storage"""
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
        download: bool = False
    ) -> str:
        """Generate URL for file access"""
        pass
    
    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage"""
        pass
    
    @abstractmethod
    async def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        pass
    
    @abstractmethod
    async def list_files(
        self,
        prefix: str = "",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files with optional prefix filter"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "uploads").mkdir(exist_ok=True)
        (self.base_path / "processed").mkdir(exist_ok=True)
        (self.base_path / "cache").mkdir(exist_ok=True)
    
    def _get_file_path(self, storage_path: str) -> Path:
        """Get absolute file path from storage path"""
        # Remove leading slash if present
        clean_path = storage_path.lstrip("/")
        return self.base_path / clean_path
    
    async def store_file(
        self,
        file_content: Union[bytes, IO],
        storage_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store file to local filesystem"""
        
        file_path = self._get_file_path(storage_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Handle different file content types
            content_to_write: bytes
            
            if isinstance(file_content, bytes):
                content_to_write = file_content
            elif isinstance(file_content, str):
                content_to_write = file_content.encode('utf-8')
            elif isinstance(file_content, (bytearray, memoryview)):
                content_to_write = bytes(file_content)
            elif hasattr(file_content, 'read') and callable(getattr(file_content, 'read', None)):
                # Handle file-like object with read method
                try:
                    content = await file_content.read() if asyncio.iscoroutinefunction(file_content.read) else file_content.read()
                    if hasattr(file_content, 'seek') and callable(getattr(file_content, 'seek', None)):
                        try:
                            file_content.seek(0)  # Reset file pointer
                        except (AttributeError, OSError):
                            pass  # Ignore if seek fails
                    
                    if isinstance(content, bytes):
                        content_to_write = content
                    elif isinstance(content, str):
                        content_to_write = content.encode('utf-8')
                    else:
                        content_to_write = bytes(content)
                except Exception as e:
                    # TODO: Use proper StorageError when imported
                    raise ValueError(f"Failed to read file content: {e}")
            else:
                # Fallback: try to convert to bytes
                try:
                    content_to_write = bytes(file_content)
                except (TypeError, ValueError) as e:
                    # TODO: Use proper StorageError when imported
                    raise ValueError(f"Unsupported file content type: {type(file_content)}, error: {e}")
            
            # Write content to file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content_to_write)
            
            # Store metadata in sidecar file
            if metadata:
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                async with aiofiles.open(metadata_path, 'w') as f:
                    import json
                    await f.write(json.dumps(metadata, default=str))
            
            # Get file stats
            stat = file_path.stat()
            
            return {
                "storage_path": storage_path,
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "content_type": content_type or mimetypes.guess_type(str(file_path))[0],
                "etag": f'"{stat.st_mtime}-{stat.st_size}"'
            }
            
        except Exception as e:
            # TODO: Convert to StorageError
            raise Exception(f"Failed to store file: {str(e)}")
    
    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file content from local storage"""
        file_path = self._get_file_path(storage_path)
        
        if not file_path.exists():
            # TODO: Raise NotFoundError
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            # TODO: Convert to StorageError
            raise Exception(f"Failed to read file: {str(e)}")
    
    async def get_file_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
        download: bool = False
    ) -> str:
        """Generate URL for local file (placeholder implementation)"""
        # TODO: Implement proper URL generation with expiry
        # TODO: Add download disposition support
        
        # For local development, return a simple path
        return f"/files/{storage_path}"
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from local storage"""
        file_path = self._get_file_path(storage_path)
        
        try:
            if file_path.exists():
                file_path.unlink()
                
                # Delete metadata file if exists
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                return True
            return False
        except Exception as e:
            # TODO: Convert to StorageError
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in local storage"""
        file_path = self._get_file_path(storage_path)
        return file_path.exists()
    
    async def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata from local storage"""
        file_path = self._get_file_path(storage_path)
        
        if not file_path.exists():
            # TODO: Raise NotFoundError
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        stat = file_path.stat()
        metadata = {
            "storage_path": storage_path,
            "size": stat.st_size,
            "last_modified": datetime.fromtimestamp(stat.st_mtime),
            "content_type": mimetypes.guess_type(str(file_path))[0],
            "etag": f'"{stat.st_mtime}-{stat.st_size}"'
        }
        
        # Load custom metadata if exists
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, 'r') as f:
                    import json
                    custom_metadata = json.loads(await f.read())
                    metadata.update(custom_metadata)
            except Exception:
                pass  # Ignore metadata errors
        
        return metadata
    
    async def list_files(
        self,
        prefix: str = "",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files in local storage"""
        search_path = self.base_path / prefix if prefix else self.base_path
        files = []
        
        try:
            for file_path in search_path.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith('.meta'):
                    relative_path = file_path.relative_to(self.base_path)
                    stat = file_path.stat()
                    
                    files.append({
                        "storage_path": str(relative_path),
                        "size": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime),
                        "content_type": mimetypes.guess_type(str(file_path))[0]
                    })
                    
                    if len(files) >= limit:
                        break
            
            return files
        except Exception as e:
            # TODO: Convert to StorageError
            raise Exception(f"Failed to list files: {str(e)}")


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend"""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        prefix: str = "",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix.rstrip("/") + "/" if prefix else ""
        
        # TODO: Initialize boto3 client
        # self.s3_client = boto3.client(
        #     's3',
        #     region_name=region,
        #     aws_access_key_id=aws_access_key_id,
        #     aws_secret_access_key=aws_secret_access_key
        # )
        
        # Placeholder for now
        self.s3_client = None
    
    def _get_s3_key(self, storage_path: str) -> str:
        """Get S3 key from storage path"""
        clean_path = storage_path.lstrip("/")
        return f"{self.prefix}{clean_path}"
    
    async def store_file(
        self,
        file_content: Union[bytes, IO],
        storage_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store file to S3"""
        # TODO: Implement S3 upload
        # TODO: Add multipart upload for large files
        # TODO: Add server-side encryption
        # TODO: Add lifecycle policies
        
        s3_key = self._get_s3_key(storage_path)
        
        # Placeholder implementation
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file content from S3"""
        # TODO: Implement S3 download
        # TODO: Add streaming for large files
        # TODO: Add retry logic
        
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def get_file_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
        download: bool = False
    ) -> str:
        """Generate presigned URL for S3 file"""
        # TODO: Implement presigned URL generation
        # TODO: Add response content disposition for downloads
        # TODO: Add content type override
        
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from S3"""
        # TODO: Implement S3 delete
        # TODO: Add batch delete for multiple files
        
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in S3"""
        # TODO: Implement S3 head object
        
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata from S3"""
        # TODO: Implement S3 head object with metadata
        
        raise NotImplementedError("S3 storage backend not yet implemented")
    
    async def list_files(
        self,
        prefix: str = "",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files in S3 bucket"""
        # TODO: Implement S3 list objects
        # TODO: Add pagination support
        
        raise NotImplementedError("S3 storage backend not yet implemented")


class StorageManager:
    """Storage manager with multiple backend support"""
    
    def __init__(self, backend: StorageBackend):
        self.backend = backend
        self._usage_stats = {
            "total_uploads": 0,
            "total_downloads": 0,
            "total_storage_bytes": 0,
            "last_reset": datetime.utcnow()
        }
    
    async def upload_file(
        self,
        file_content: Union[bytes, IO],
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload file with automatic path generation"""
        
        # Generate storage path
        storage_path = self._generate_storage_path(filename, user_id)
        
        # Add user metadata
        full_metadata = {
            "user_id": user_id,
            "original_filename": filename,
            "upload_timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        # Store file
        result = await self.backend.store_file(
            file_content,
            storage_path,
            content_type,
            full_metadata
        )
        
        # Update usage stats
        self._usage_stats["total_uploads"] += 1
        self._usage_stats["total_storage_bytes"] += result.get("size", 0)
        
        return {
            **result,
            "storage_path": storage_path,
            "user_id": user_id,
            "original_filename": filename
        }
    
    async def download_file(self, storage_path: str, user_id: str) -> bytes:
        """Download file with access control"""
        
        # TODO: Verify user access to file
        # TODO: Log download event
        
        content = await self.backend.get_file(storage_path)
        
        # Update usage stats
        self._usage_stats["total_downloads"] += 1
        
        return content
    
    async def get_download_url(
        self,
        storage_path: str,
        user_id: str,
        expires_in: int = 3600,
        download: bool = False
    ) -> str:
        """Get download URL with access control"""
        
        # TODO: Verify user access to file
        # TODO: Log URL generation event
        
        return await self.backend.get_file_url(storage_path, expires_in, download)
    
    async def delete_file(self, storage_path: str, user_id: str) -> bool:
        """Delete file with access control"""
        
        # TODO: Verify user access to file
        # TODO: Log deletion event
        # TODO: Update usage stats
        
        return await self.backend.delete_file(storage_path)
    
    def _generate_storage_path(self, filename: str, user_id: str) -> str:
        """Generate storage path for file"""
        
        # Extract file extension
        file_ext = Path(filename).suffix
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())
        
        # Create path: user_id/year/month/day/uuid.ext
        return f"{user_id}/{timestamp}/{unique_id}{file_ext}"
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        return self._usage_stats.copy()
    
    async def cleanup_expired_files(self, max_age_days: int = 30) -> int:
        """Cleanup files older than specified days"""
        # TODO: Implement file cleanup based on age
        # TODO: Add configurable retention policies
        # TODO: Add soft delete support
        
        return 0  # Placeholder


# ============= UTILITY FUNCTIONS =============

def get_storage_backend(storage_type: str = "local", **kwargs) -> StorageBackend:
    """Factory function to create storage backend"""
    
    if storage_type.lower() == "local":
        return LocalStorageBackend(kwargs.get("base_path", "./storage"))
    elif storage_type.lower() == "s3":
        return S3StorageBackend(
            bucket_name=kwargs.get("bucket_name", "default-bucket"),
            region=kwargs.get("region", "us-east-1"),
            prefix=kwargs.get("prefix", ""),
            aws_access_key_id=kwargs.get("aws_access_key_id"),
            aws_secret_access_key=kwargs.get("aws_secret_access_key")
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


def create_storage_manager(config: Dict[str, Any]) -> StorageManager:
    """Create storage manager from configuration"""
    
    storage_type = config.get("type", "local")
    backend = get_storage_backend(storage_type, **config)
    
    return StorageManager(backend)


# TODO: Add file integrity verification
# TODO: Add file compression support
# TODO: Add image thumbnail generation
# TODO: Add file virus scanning integration
# TODO: Add storage analytics and monitoring
# TODO: Add backup and replication support
