"""
Document Service - Core Business Logic

This module provides the main business logic for document management,
including upload, retrieval, metadata management, and lifecycle operations.

Author: InsureCove Team
Date: July 8, 2025
"""

from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

from app.models import (
    DocumentResponse, DocumentUploadRequest, DocumentUpdateRequest,
    DocumentListResponse, DocumentFilters, DocumentType, DocumentStatus
)
from app.core.config import settings

from app.core.exceptions import (
    DocumentNotFoundError, ValidationError, StorageError,
    DocumentProcessingError, AuthorizationError
)
from app.core.storage import StorageManager
from app.core.logging_config import get_logger

from app.services.storage_service import StorageService
from app.services.validation_service import ValidationService
from app.services.ocr_service import OCRService
from app.services.auth_client_service import AuthClientService
from app.utils.file_utils import FileProcessor
from app.utils.crypto_utils import SecureStorage, TokenGenerator
from app.utils.date_utils import DateTimeHelper
from app.utils.response_utils import ResponseBuilder, APIResponseFormatter


class DocumentService:
    """Core document management service"""
    
    def __init__(
        self,
        storage_service: Optional[StorageService] = None,
        validation_service: Optional[ValidationService] = None,
        ocr_service: Optional[OCRService] = None,
        auth_service: Optional[AuthClientService] = None,
        database_session=None
    ):
        """Initialize document service with dependencies"""
        self.storage = storage_service
        self.validator = validation_service
        self.ocr = ocr_service
        self.auth = auth_service
        self.db = database_session
        self.logger = get_logger(__name__)
        
        # Initialize utility classes
        self.file_processor = FileProcessor()
        self.secure_storage = SecureStorage()
        self.token_generator = TokenGenerator()
        self.datetime_helper = DateTimeHelper()
        self.response_builder = ResponseBuilder()
        
        # Document processing statistics
        self._stats = {
            "total_uploads": 0,
            "total_downloads": 0,
            "total_updates": 0,
            "total_deletes": 0,
            "processing_errors": 0,
            "last_reset": datetime.utcnow()
        }
    
    # ============= DOCUMENT UPLOAD OPERATIONS =============
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        auto_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a document with full validation and processing
        
        Args:
            file_content: Document file content
            filename: Original filename
            user_id: Owner user ID
            content_type: MIME type
            metadata: Additional metadata
            tags: Document tags
            auto_ocr: Trigger OCR automatically
            
        Returns:
            Document response with metadata and URLs
        """
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        try:
            # Validate file content and metadata
            validation_result = await self._validate_upload_file(file_content, filename, content_type)
            if not validation_result.get("is_valid", False):
                raise ValidationError(f"File validation failed: {validation_result.get('errors', [])}")
            
            # Check user quotas and permissions
            if self.auth:
                # Check user upload permissions
                try:
                    has_upload_permission = await self.auth.check_user_permissions(
                        user_id, ["document:upload", "document:create"]
                    )
                    if not has_upload_permission:
                        raise AuthorizationError("User does not have upload permissions")
                    
                    # Get user information for quota checking
                    try:
                        user_info = await self.auth.get_current_user(user_id)
                        storage_quota_mb = user_info.get("storage_quota_mb", 1000)
                    except:
                        storage_quota_mb = 1000
                    
                except Exception as e:
                    self.logger.warning(f"Failed to check user permissions: {str(e)}")
                    # Fallback to basic permissions
                    storage_quota_mb = 1000
            else:
                storage_quota_mb = 1000
                
            # Check storage quota
            current_usage = await self._get_user_storage_usage(user_id)
            file_size = len(file_content)
            quota_limit = storage_quota_mb * 1024 * 1024
            
            if current_usage + file_size > quota_limit:
                raise StorageError("Storage quota exceeded")
            
            # Store file in storage backend
            storage_result = None
            if self.storage:
                storage_result = await self.storage.upload_file(
                    file_content=file_content,
                    filename=filename,
                    content_type=content_type or "application/octet-stream",
                    user_id=user_id,
                    metadata=metadata or {}
                )
            
            # Save document metadata to database
            document_record = await self._save_document_metadata(
                document_id=document_id,
                filename=filename,
                user_id=user_id,
                storage_result=storage_result,
                tags=tags or [],
                content_type=content_type,
                file_size=len(file_content),
                metadata=metadata or {}
            )
            
            # Trigger OCR if requested
            ocr_job_id = None
            if auto_ocr and self.ocr:
                try:
                    ocr_result = await self.ocr.extract_text(file_content, filename)
                    ocr_job_id = ocr_result.get("job_id", str(uuid.uuid4()))
                except Exception as ocr_error:
                    self.logger.warning(f"OCR processing failed for document {document_id}: {str(ocr_error)}")
            
            # Generate response with URLs
            upload_url = None
            download_url = None
            
            if storage_result:
                upload_url = storage_result.get("upload_url")
                download_url = await self._generate_signed_download_url(document_id, user_id)
            
            # Update statistics
            self._stats["total_uploads"] += 1
            
            # Log upload event
            self.logger.info(
                "Document uploaded successfully",
                extra={
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": filename,
                    "file_size": len(file_content),
                    "auto_ocr": auto_ocr,
                    "ocr_job_id": ocr_job_id
                }
            )
            
            return {
                "id": document_id,
                "filename": filename,
                "original_filename": filename,
                "user_id": user_id,
                "status": DocumentStatus.UPLOADED.value,
                "file_size": len(file_content),
                "content_type": content_type or "application/octet-stream",
                "tags": tags or [],
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "auto_ocr": auto_ocr,
                "upload_url": upload_url,
                "download_url": download_url,
                "etag": f'"{hash(file_content)}"',  # Simple hash for etag
                "version": 1,
                "ocr_completed": False,
                "ocr_job_id": ocr_job_id
            }
            
        except (ValidationError, AuthorizationError, StorageError) as e:
            self._stats["processing_errors"] += 1
            self.logger.error(f"Document upload failed: {str(e)}", extra={"document_id": document_id})
            raise
        except Exception as e:
            self._stats["processing_errors"] += 1
            self.logger.error(f"Unexpected error during document upload: {str(e)}", extra={"document_id": document_id})
            raise DocumentProcessingError(f"Document upload failed: {str(e)}")
    
    async def upload_documents_batch(
        self,
        files: List[Dict[str, Any]],
        user_id: str,
        auto_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Upload multiple documents in batch
        
        Args:
            files: List of file data dictionaries
            user_id: Owner user ID
            auto_ocr: Trigger OCR for all documents
            
        Returns:
            List of document responses
        """
        
        # Validate all files before processing
        validation_errors = []
        for i, file_data in enumerate(files):
            try:
                if not file_data.get("content"):
                    validation_errors.append(f"File {i}: Missing content")
                if not file_data.get("filename"):
                    validation_errors.append(f"File {i}: Missing filename")
                if len(file_data.get("content", b"")) > 100 * 1024 * 1024:  # 100MB limit
                    validation_errors.append(f"File {i}: File too large")
            except Exception as e:
                validation_errors.append(f"File {i}: Validation error - {str(e)}")
        
        if validation_errors:
            raise ValidationError(f"Batch validation failed: {'; '.join(validation_errors)}")
        
        # Process uploads in parallel
        upload_tasks = [
            self.upload_document(
                file_data["content"],
                file_data["filename"],
                user_id,
                file_data.get("content_type"),
                file_data.get("metadata"),
                file_data.get("tags"),
                auto_ocr
            )
            for file_data in files
        ]
        
        try:
            # Handle partial failures gracefully
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Return batch results
            processed_results = []
            success_count = 0
            error_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    processed_results.append({
                        "error": str(result),
                        "filename": files[i]["filename"],
                        "success": False,
                        "error_type": type(result).__name__
                    })
                    self.logger.error(f"Batch upload failed for file {files[i]['filename']}: {str(result)}")
                elif isinstance(result, dict):
                    success_count += 1
                    processed_results.append({
                        **result,
                        "success": True
                    })
                else:
                    error_count += 1
                    processed_results.append({
                        "error": f"Unexpected result type: {type(result)}",
                        "filename": files[i]["filename"],
                        "success": False,
                        "error_type": "UnexpectedResultType"
                    })
            
            # Log batch upload summary
            self.logger.info(
                f"Batch upload completed: {success_count} successful, {error_count} failed",
                extra={
                    "user_id": user_id,
                    "total_files": len(files),
                    "success_count": success_count,
                    "error_count": error_count
                }
            )
            
            return {
                "batch_id": str(uuid.uuid4()),
                "total_files": len(files),
                "successful": success_count,
                "failed": error_count,
                "results": processed_results,
                "completed_at": datetime.utcnow()
            }
            
        except Exception as e:
            # Log batch upload error
            self.logger.error(f"Batch upload failed: {str(e)}", extra={"user_id": user_id})
            raise DocumentProcessingError(f"Batch upload failed: {str(e)}")
            raise Exception(f"Batch upload failed: {str(e)}")
    
    # ============= DOCUMENT RETRIEVAL OPERATIONS =============
    
    async def get_document(
        self,
        document_id: str,
        user_id: str,
        include_download_url: bool = True,
        url_expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Retrieve document metadata and generate access URLs
        
        Args:
            document_id: Document unique identifier
            user_id: Requesting user ID
            include_download_url: Generate download URL
            url_expires_in: URL expiry time in seconds
            
        Returns:
            Document metadata with URLs
        """
        
        try:
            # Verify document exists and get metadata from database
            document_record = await self._get_document_record(document_id)
            if not document_record:
                raise DocumentNotFoundError(f"Document {document_id} not found")
            
            # Check user access permissions
            if not await self._check_document_access(document_record, user_id):
                raise AuthorizationError("Access denied to document")
            
            # Generate signed URLs if requested
            download_url = None
            if include_download_url:
                download_url = await self._generate_signed_download_url(
                    document_id, user_id, url_expires_in
                )
            
            # Update access tracking
            await self._log_document_access(document_id, user_id, "view")
            
            # Update last accessed timestamp
            await self._update_last_accessed(document_id)
            
            self._stats["total_downloads"] += 1
            
            # Return document response aligned with DB schema
            return {
                "id": document_record["id"],
                "file_name": document_record["file_name"],
                "original_filename": document_record["original_filename"],
                "uploaded_by": document_record["uploaded_by"],
                "status": document_record["status"],
                "file_size": document_record["file_size"],
                "file_type": document_record["file_type"],
                "mime_type": document_record["mime_type"],
                "document_type": document_record.get("document_type"),
                "tags": document_record.get("tags", []),
                "metadata": document_record.get("metadata", {}),
                "created_at": document_record["created_at"],
                "updated_at": document_record["updated_at"],
                "last_modified": document_record.get("last_modified"),
                "download_url": download_url,
                "etag": document_record.get("etag"),
                "version": document_record.get("version", 1),
                "ocr_completed": document_record.get("ocr_completed", False),
                "ocr_text": document_record.get("ocr_text"),
                "ocr_confidence": document_record.get("ocr_confidence"),
                "security_scan_status": document_record.get("security_scan_status"),
                "virus_scan_status": document_record.get("virus_scan_status"),
                "download_count": document_record.get("download_count", 0),
                "last_accessed": document_record.get("last_accessed")
            }
            
        except (DocumentNotFoundError, AuthorizationError) as e:
            self.logger.error(f"Document retrieval failed: {str(e)}", extra={"document_id": document_id})
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during document retrieval: {str(e)}", extra={"document_id": document_id})
            raise DocumentProcessingError(f"Document retrieval failed: {str(e)}")

    async def _get_document_record(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document record from database"""
        if not self.db:
            return None
            
        try:
            query = """
            SELECT 
                id, file_name, original_filename, uploaded_by, status, file_size,
                file_type, mime_type, file_path, storage_bucket, storage_key,
                file_hash, document_type, version, etag, security_scan_status,
                virus_scan_status, content_validated, ocr_completed, ocr_job_id,
                ocr_text, ocr_confidence, ocr_language, ocr_page_count, ocr_word_count,
                download_count, last_accessed, metadata, tags, upload_date,
                created_at, updated_at, last_modified, deleted_at
            FROM documents 
            WHERE id = %(document_id)s AND deleted_at IS NULL
            """
            result = await self.db.fetchone(query, {"document_id": document_id})
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Database query failed: {str(e)}")
            raise DocumentProcessingError(f"Failed to retrieve document: {str(e)}")

    async def _check_document_access(self, document_record: Dict[str, Any], user_id: str) -> bool:
        """Check if user has access to document"""
        # Basic ownership check
        if document_record.get("uploaded_by") == user_id:
            return True
        
        # Check if document is shared with user (could extend this)
        # For now, only owner has access
        if self.auth:
            # Could implement more complex permission checking here
            user_permissions = await self._get_user_permissions(user_id)
            if user_permissions.get("admin", False):
                return True
        
        return False

    async def _log_document_access(self, document_id: str, user_id: str, access_type: str):
        """Log document access for audit trail"""
        if not self.db:
            return
            
        try:
            access_log = {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "user_id": user_id,
                "access_type": access_type,
                "access_method": "api",
                "success": True,
                "accessed_at": datetime.utcnow()
            }
            
            query = """
            INSERT INTO document_access_log (
                id, document_id, user_id, access_type, access_method, success, accessed_at
            ) VALUES (
                %(id)s, %(document_id)s, %(user_id)s, %(access_type)s, 
                %(access_method)s, %(success)s, %(accessed_at)s
            )
            """
            await self.db.execute(query, access_log)
        except Exception as e:
            self.logger.warning(f"Failed to log document access: {str(e)}")

    async def _update_last_accessed(self, document_id: str):
        """Update document last accessed timestamp"""
        if not self.db:
            return
            
        try:
            query = """
            UPDATE documents 
            SET last_accessed = %(timestamp)s, updated_at = %(timestamp)s
            WHERE id = %(document_id)s
            """
            await self.db.execute(query, {
                "document_id": document_id,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            self.logger.warning(f"Failed to update last accessed: {str(e)}")

    async def _get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user permissions (placeholder for auth service integration)"""
        # This would integrate with the auth service
        return {"admin": False, "can_view": True, "can_download": True}
    
    async def list_documents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        cursor: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List user documents with filtering and pagination
        
        Args:
            user_id: Owner user ID
            page: Page number
            page_size: Items per page
            cursor: Pagination cursor
            filters: Filter criteria
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            Paginated document list
        """
        
        try:
            # Apply user access filters - only show documents user owns or has access to
            base_filters = {"uploaded_by": user_id}
            
            # Apply additional search and filter criteria
            query_filters = await self._build_query_filters(base_filters, filters)
            
            # Implement cursor-based pagination with sorting
            documents, total_count, next_cursor = await self._execute_paginated_query(
                query_filters, page, page_size, cursor, sort_by, sort_order
            )
            
            # Generate download URLs for documents
            for doc in documents:
                doc["download_url"] = await self._generate_signed_download_url(
                    doc["id"], user_id, 3600  # 1 hour expiry
                )
            
            # Calculate pagination metadata
            page_count = (total_count + page_size - 1) // page_size
            has_more = page < page_count
            
            return {
                "items": documents,
                "total_count": total_count,
                "page_count": page_count,
                "current_page": page,
                "page_size": page_size,
                "has_more": has_more,
                "next_cursor": next_cursor,
                "previous_cursor": None  # Implement if needed
            }
            
        except Exception as e:
            self.logger.error(f"Document listing failed: {str(e)}", extra={"user_id": user_id})
            raise DocumentProcessingError(f"Document listing failed: {str(e)}")

    async def _build_query_filters(self, base_filters: Dict[str, Any], additional_filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build SQL query filters from user criteria"""
        filters = base_filters.copy()
        
        if not additional_filters:
            return filters
            
        # Handle common filter types
        if "document_type" in additional_filters:
            filters["document_type"] = additional_filters["document_type"]
            
        if "status" in additional_filters:
            filters["status"] = additional_filters["status"]
            
        if "tags" in additional_filters:
            # PostgreSQL array contains
            filters["tags_contain"] = additional_filters["tags"]
            
        if "file_type" in additional_filters:
            filters["file_type"] = additional_filters["file_type"]
            
        if "created_after" in additional_filters:
            filters["created_after"] = additional_filters["created_after"]
            
        if "created_before" in additional_filters:
            filters["created_before"] = additional_filters["created_before"]
            
        if "search" in additional_filters:
            # Search in filename and OCR text
            filters["search_text"] = additional_filters["search"]
            
        return filters

    async def _execute_paginated_query(
        self,
        filters: Dict[str, Any],
        page: int,
        page_size: int,
        cursor: Optional[str],
        sort_by: str,
        sort_order: str
    ) -> tuple[List[Dict[str, Any]], int, Optional[str]]:
        """Execute paginated query against documents table"""
        
        if not self.db:
            return [], 0, None
            
        try:
            # Build WHERE clause
            where_conditions = ["deleted_at IS NULL"]
            params = {}
            
            # Add filters
            if filters.get("uploaded_by"):
                where_conditions.append("uploaded_by = %(uploaded_by)s")
                params["uploaded_by"] = filters["uploaded_by"]
                
            if filters.get("document_type"):
                where_conditions.append("document_type = %(document_type)s")
                params["document_type"] = filters["document_type"]
                
            if filters.get("status"):
                where_conditions.append("status = %(status)s")
                params["status"] = filters["status"]
                
            if filters.get("file_type"):
                where_conditions.append("file_type = %(file_type)s")
                params["file_type"] = filters["file_type"]
                
            if filters.get("tags_contain"):
                where_conditions.append("tags && %(tags)s")  # PostgreSQL array overlap
                params["tags"] = filters["tags_contain"]
                
            if filters.get("created_after"):
                where_conditions.append("created_at >= %(created_after)s")
                params["created_after"] = filters["created_after"]
                
            if filters.get("created_before"):
                where_conditions.append("created_at <= %(created_before)s")
                params["created_before"] = filters["created_before"]
                
            if filters.get("search_text"):
                where_conditions.append(
                    "(file_name ILIKE %(search)s OR ocr_text ILIKE %(search)s)"
                )
                params["search"] = f"%{filters['search_text']}%"
            
            # Build ORDER BY clause
            valid_sort_fields = {
                "created_at", "updated_at", "file_name", "file_size", 
                "status", "last_accessed", "download_count"
            }
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "desc"
                
            # Calculate offset for pagination
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            # Main query
            where_clause = " AND ".join(where_conditions)
            query = f"""
            SELECT 
                id, file_name, original_filename, uploaded_by, status, file_size,
                file_type, mime_type, document_type, version, etag, 
                ocr_completed, ocr_confidence, security_scan_status, virus_scan_status,
                download_count, last_accessed, metadata, tags,
                created_at, updated_at, last_modified
            FROM documents 
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT %(limit)s OFFSET %(offset)s
            """
            
            # Count query
            count_query = f"""
            SELECT COUNT(*) as total 
            FROM documents 
            WHERE {where_clause}
            """
            
            # Execute queries
            documents_result = await self.db.fetchall(query, params)
            count_result = await self.db.fetchone(count_query, params)
            
            documents = [dict(row) for row in documents_result] if documents_result else []
            total_count = count_result["total"] if count_result else 0
            
            # Generate next cursor (simple implementation)
            next_cursor = str(page + 1) if (page * page_size) < total_count else None
            
            return documents, total_count, next_cursor
            
        except Exception as e:
            self.logger.error(f"Database query failed: {str(e)}")
            raise DocumentProcessingError(f"Failed to query documents: {str(e)}")
    
    # ============= DOCUMENT MANAGEMENT OPERATIONS =============
    
    async def update_document(
        self,
        document_id: str,
        user_id: str,
        updates: Dict[str, Any],
        if_match: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update document metadata with optimistic locking
        
        Args:
            document_id: Document unique identifier
            user_id: Requesting user ID
            updates: Fields to update
            if_match: ETag for optimistic locking
            
        Returns:
            Updated document metadata
        """
        
        try:
            # Verify document exists and user has access
            document = await self._get_document_record(document_id)
            if not document:
                raise DocumentProcessingError("Document not found")
                
            if not await self._check_document_access(document, user_id):
                raise DocumentProcessingError("Access denied to document")
            
            # Check ETag for optimistic locking
            if if_match:
                current_etag = document.get('etag')
                if current_etag != if_match:
                    raise DocumentProcessingError("Document was modified by another request (ETag mismatch)")
            
            # Validate update data
            validated_updates = await self._validate_document_updates(updates)
            
            # Prepare update query with allowed fields only
            allowed_fields = {
                'file_name', 'document_type', 'metadata', 'tags', 'status',
                'last_modified', 'version', 'updated_at'
            }
            
            update_fields = {}
            for field, value in validated_updates.items():
                if field in allowed_fields:
                    update_fields[field] = value
            
            if not update_fields:
                raise DocumentProcessingError("No valid fields to update")
            
            # Add automatic fields
            update_fields['updated_at'] = datetime.utcnow()
            update_fields['last_modified'] = datetime.utcnow()
            update_fields['version'] = document.get('version', 1) + 1
            
            # Build dynamic UPDATE query
            set_clauses = []
            params = {"document_id": document_id}
            
            for field, value in update_fields.items():
                set_clauses.append(f"{field} = %({field})s")
                params[field] = value
            
            query = f"""
                UPDATE documents 
                SET {', '.join(set_clauses)}
                WHERE id = %(document_id)s AND deleted_at IS NULL
            """
            
            # Execute update
            if self.db:
                await self.db.execute(query, params)
            else:
                raise DocumentProcessingError("Database connection not available")
            
            # Get updated document
            updated_document = await self._get_document_record(document_id)
            
            if not updated_document:
                raise DocumentProcessingError("Document update failed")
            
            # Log update event
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="update"
            )
            
            self._stats["total_updates"] += 1
            
            return updated_document
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            # Log error and convert to appropriate exception
            self.logger.error(f"Document update failed for {document_id}: {str(e)}")
            
            # Log failed access
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="update"
            )
            
            raise DocumentProcessingError(f"Document update failed: {str(e)}")
    
    async def delete_document(
        self,
        document_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """
        Delete document with soft/hard delete options
        
        Args:
            document_id: Document unique identifier
            user_id: Requesting user ID
            permanent: Permanently delete (default: soft delete)
            
        Returns:
            True if deletion successful
        """
        
        try:
            # Verify document exists and user has access
            document = await self._get_document_record(document_id)
            if not document:
                raise DocumentProcessingError("Document not found")
                
            if not await self._check_document_access(document, user_id):
                raise DocumentProcessingError("Access denied to document")
            
            if permanent:
                # Hard delete - remove all data
                await self._permanent_delete(document_id)
            else:
                # Soft delete - mark as deleted
                await self._soft_delete(document_id)
            
            self._stats["total_deletes"] += 1
            
            # Log deletion event
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="delete"
            )
            
            return True
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            # Log error and convert to appropriate exception
            self.logger.error(f"Document deletion failed for {document_id}: {str(e)}")
            
            # Log failed access
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="delete"
            )
            
            raise DocumentProcessingError(f"Document deletion failed: {str(e)}")
    
    # ============= DOCUMENT DOWNLOAD OPERATIONS =============
    
    async def download_document(
        self,
        document_id: str,
        user_id: str
    ) -> bytes:
        """
        Download document file content
        
        Args:
            document_id: Document unique identifier
            user_id: Requesting user ID
            
        Returns:
            Document file content
        """
        
        try:
            # Verify document exists and user has access
            document = await self._get_document_record(document_id)
            if not document:
                raise DocumentProcessingError("Document not found")
                
            if not await self._check_document_access(document, user_id):
                raise DocumentProcessingError("Access denied to document")
            
            # Get file content from storage
            if self.storage and document.get("storage_key"):
                try:
                    # Use storage service to download file content
                    download_result = await self.storage.download_file(document_id, user_id)
                    if "content" in download_result:
                        file_content = download_result["content"]
                    else:
                        raise DocumentProcessingError("File content not available in download result")
                except Exception as storage_error:
                    raise DocumentProcessingError(f"File retrieval failed: {str(storage_error)}")
            else:
                # Fallback to file path if storage service unavailable
                file_path = document.get("file_path")
                if file_path and Path(file_path).exists():
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                else:
                    raise DocumentProcessingError("File not found in storage")
            
            # Update download statistics
            await self._update_download_stats(document_id)
            
            self._stats["total_downloads"] += 1
            
            # Log download event
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="download"
            )
            
            return file_content
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            # Log error and convert to appropriate exception
            self.logger.error(f"Document download failed for {document_id}: {str(e)}")
            
            # Log failed access
            await self._log_document_access(
                document_id=document_id,
                user_id=user_id,
                access_type="download"
            )
            
            raise DocumentProcessingError(f"Document download failed: {str(e)}")
    
    # ============= DOCUMENT STATISTICS =============
    
    async def get_document_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive document statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Document statistics and usage information
        """
        
        try:
            if not self.db:
                # Return basic statistics without database
                return {
                    "total_documents": 0,
                    "total_storage_mb": 0,
                    "documents_by_type": {},
                    "documents_by_status": {},
                    "ocr_completed": 0,
                    "processing_queue": 0,
                    "upload_count_today": 0,
                    "download_count_today": 0,
                    "storage_quota_mb": getattr(settings, 'DEFAULT_STORAGE_QUOTA_MB', 1000),
                    "storage_used_percent": 0.0
                }
            
            # Calculate document statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_documents,
                SUM(file_size) as total_storage_bytes,
                COUNT(CASE WHEN ocr_completed = true THEN 1 END) as ocr_completed_count
            FROM documents 
            WHERE uploaded_by = %(user_id)s AND deleted_at IS NULL
            """
            stats_result = await self.db.fetchrow(stats_query, {"user_id": user_id})
            
            # Count documents by status
            status_query = """
            SELECT status, COUNT(*) as count
            FROM documents 
            WHERE uploaded_by = %(user_id)s AND deleted_at IS NULL
            GROUP BY status
            """
            status_results = await self.db.fetch(status_query, {"user_id": user_id})
            
            # Count documents by type
            type_query = """
            SELECT document_type, COUNT(*) as count
            FROM documents 
            WHERE uploaded_by = %(user_id)s AND deleted_at IS NULL AND document_type IS NOT NULL
            GROUP BY document_type
            """
            type_results = await self.db.fetch(type_query, {"user_id": user_id})
            
            # Get today's upload count
            today_upload_query = """
            SELECT COUNT(*) as upload_count
            FROM documents 
            WHERE uploaded_by = %(user_id)s 
            AND created_at >= CURRENT_DATE 
            AND deleted_at IS NULL
            """
            today_upload_result = await self.db.fetchrow(today_upload_query, {"user_id": user_id})
            
            # Get today's download count from access log
            today_download_query = """
            SELECT COUNT(*) as download_count
            FROM document_access_log dal
            JOIN documents d ON dal.document_id = d.id
            WHERE d.uploaded_by = %(user_id)s 
            AND dal.access_type = 'download'
            AND dal.accessed_at >= CURRENT_DATE
            AND dal.success = true
            """
            today_download_result = await self.db.fetchrow(today_download_query, {"user_id": user_id})
            
            # Calculate processing metrics
            total_storage_bytes = stats_result['total_storage_bytes'] or 0
            total_storage_mb = total_storage_bytes / (1024 * 1024)
            storage_quota_mb = getattr(settings, 'DEFAULT_STORAGE_QUOTA_MB', 1000)
            storage_used_percent = (total_storage_mb / storage_quota_mb * 100) if storage_quota_mb > 0 else 0.0
            
            # Format results
            documents_by_status = {row['status']: row['count'] for row in status_results}
            documents_by_type = {row['document_type']: row['count'] for row in type_results}
            
            return {
                "total_documents": stats_result['total_documents'] or 0,
                "total_storage_mb": round(total_storage_mb, 2),
                "documents_by_type": documents_by_type,
                "documents_by_status": documents_by_status,
                "ocr_completed": stats_result['ocr_completed_count'] or 0,
                "processing_queue": documents_by_status.get('processing', 0),
                "upload_count_today": today_upload_result['upload_count'] or 0,
                "download_count_today": today_download_result['download_count'] or 0,
                "storage_quota_mb": storage_quota_mb,
                "storage_used_percent": round(storage_used_percent, 2),
                "last_calculated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate document statistics for user {user_id}: {str(e)}")
            # Return safe fallback statistics
            return {
                "total_documents": 0,
                "total_storage_mb": 0,
                "documents_by_type": {},
                "documents_by_status": {},
                "ocr_completed": 0,
                "processing_queue": 0,
                "upload_count_today": 0,
                "download_count_today": 0,
                "storage_quota_mb": getattr(settings, 'DEFAULT_STORAGE_QUOTA_MB', 1000),
                "storage_used_percent": 0.0,
                "error": "Statistics calculation failed"
            }
    
    # ============= HELPER METHODS =============
    
    async def _get_user_storage_usage(self, user_id: str) -> int:
        """Get current storage usage for user in bytes"""
        if not self.db:
            return 0
            
        try:
            query = """
            SELECT COALESCE(SUM(file_size), 0) as total_storage_bytes
            FROM documents 
            WHERE uploaded_by = %(user_id)s AND deleted_at IS NULL
            """
            result = await self.db.fetchrow(query, {"user_id": user_id})
            return int(result['total_storage_bytes']) if result else 0
            
        except Exception as e:
            self.logger.error(f"Failed to get storage usage for user {user_id}: {str(e)}")
            return 0
        if self.db:
            # Placeholder for database query
            # result = await self.db.execute(
            #     "SELECT SUM(file_size) FROM documents WHERE user_id = ?", user_id
            # )
            # return result.scalar() or 0
            pass
        return 0  # Default for now
    
    async def _save_document_metadata(
        self,
        document_id: str,
        filename: str,
        user_id: str,
        storage_result: Optional[Dict[str, Any]],
        tags: List[str],
        content_type: Optional[str],
        file_size: int,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save document metadata to database"""
        document_record = {
            "id": document_id,
            "file_name": filename,  # Updated to match DB schema
            "original_filename": filename,  # Updated to match DB schema
            "uploaded_by": user_id,  # Updated to match DB schema
            "status": DocumentStatus.UPLOADED.value,
            "file_size": file_size,
            "file_type": Path(filename).suffix.lower().lstrip('.') or 'unknown',  # Extract file extension
            "mime_type": content_type or "application/octet-stream",
            "file_path": storage_result.get("file_path") if storage_result else f"/temp/{document_id}",
            "storage_bucket": storage_result.get("bucket") if storage_result else "documents",
            "storage_key": storage_result.get("key") if storage_result else f"documents/{document_id}/{filename}",
            "file_hash": None,  # Will be auto-generated by DB trigger
            "document_type": self._detect_document_type(filename, content_type),
            "version": 1,
            "etag": None,  # Will be auto-generated by DB trigger
            "security_scan_status": "pending",
            "virus_scan_status": "pending",
            "content_validated": False,
            "ocr_completed": False,
            "ocr_job_id": None,
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_language": None,
            "ocr_page_count": None,
            "ocr_word_count": None,
            "upload_url": None,
            "download_url": None,
            "thumbnail_url": None,
            "url_expires_at": None,
            "download_count": 0,
            "last_accessed": None,
            "metadata": metadata,
            "tags": tags,
            "upload_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_modified": datetime.utcnow(),
            "deleted_at": None
        }
        
        # Save to database if available
        if self.db:
            try:
                # Using raw SQL aligned with our unified schema
                query = """
                INSERT INTO documents (
                    id, file_name, original_filename, file_size, file_type, mime_type,
                    file_path, storage_bucket, storage_key, document_type, status,
                    uploaded_by, version, metadata, tags, created_at, updated_at
                ) VALUES (
                    %(id)s, %(file_name)s, %(original_filename)s, %(file_size)s, %(file_type)s, %(mime_type)s,
                    %(file_path)s, %(storage_bucket)s, %(storage_key)s, %(document_type)s, %(status)s,
                    %(uploaded_by)s, %(version)s, %(metadata)s, %(tags)s, %(created_at)s, %(updated_at)s
                ) RETURNING id, storage_key, file_hash, etag
                """
                result = await self.db.execute(query, document_record)
                # Update record with auto-generated values
                if result:
                    document_record.update({
                        "storage_key": result.get("storage_key"),
                        "file_hash": result.get("file_hash"),
                        "etag": result.get("etag")
                    })
            except Exception as e:
                self.logger.error(f"Failed to save document metadata: {str(e)}")
                raise DocumentProcessingError(f"Database save failed: {str(e)}")
            
        return document_record

    def _detect_document_type(self, filename: str, content_type: Optional[str]) -> Optional[str]:
        """Detect document type based on filename and content type"""
        # Extract file extension
        ext = Path(filename).suffix.lower().lstrip('.')
        
        # Map extensions to document types
        document_type_mapping = {
            'pdf': 'policy_document',
            'jpg': 'image_document', 
            'jpeg': 'image_document',
            'png': 'image_document',
            'tiff': 'image_document',
            'tif': 'image_document',
            'doc': 'text_document',
            'docx': 'text_document',
            'txt': 'text_document'
        }
        
        # Check content type patterns
        if content_type:
            if 'pdf' in content_type:
                return 'policy_document'
            elif 'image' in content_type:
                return 'image_document'
            elif 'text' in content_type or 'document' in content_type:
                return 'text_document'
        
        return document_type_mapping.get(ext, 'unknown_document')
    
    async def _generate_signed_download_url(self, document_id: str, user_id: str, expires_in: int = 3600) -> Optional[str]:
        """Generate signed download URL for document"""
        if self.storage:
            try:
                # Get document record to determine storage backend
                document = await self._get_document_record(document_id)
                if not document:
                    return None
                
                # Check if user has access
                if not await self._check_document_access(document, user_id):
                    return None
                
                storage_key = document.get('storage_key')
                storage_bucket = document.get('storage_bucket', 'documents')
                
                if storage_key:
                    # Generate signed URL via storage service
                    # This would typically call storage service's generate_presigned_url method
                    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # For S3-like storage, this would generate a presigned URL
                    # For local storage, this would be a time-limited token URL
                    signed_url = f"/api/v1/documents/{document_id}/download"
                    
                    # Add query parameters for validation
                    signed_url += f"?expires={int(expiry_time.timestamp())}"
                    signed_url += f"&user_id={user_id}"
                    signed_url += f"&signature={self._generate_url_signature(document_id, user_id, expiry_time)}"
                    
                    return signed_url
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate download URL for {document_id}: {str(e)}")
        
        # Fallback to direct download endpoint
        return f"/api/v1/documents/{document_id}/download"
    
    def _generate_url_signature(self, document_id: str, user_id: str, expiry_time: datetime) -> str:
        """Generate URL signature for download authentication"""
        import hashlib
        import hmac
        
        # Use a secret key from settings or environment
        secret_key = getattr(settings, 'SECRET_KEY', 'fallback-secret-key').encode('utf-8')
        
        # Create signature payload
        payload = f"{document_id}:{user_id}:{int(expiry_time.timestamp())}"
        
        # Generate HMAC signature
        signature = hmac.new(secret_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
        
        return signature[:16]  # Truncate for URL brevity
    
    async def _validate_upload_file(self, file_content: bytes, filename: str, content_type: Optional[str]) -> Dict[str, Any]:
        """Validate uploaded file content and metadata"""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}
        
        if self.validator:
            # Validate filename
            if not self.validator.validate_filename(filename):
                validation_result["is_valid"] = False
                validation_result["errors"].append("Invalid filename format")
            
            # Validate file size
            if not self.validator.validate_file_size(file_content):
                validation_result["is_valid"] = False
                validation_result["errors"].append("File size exceeds limit")
            
            # Validate file type
            file_type_result = self.validator.validate_file_type(file_content, content_type or "", filename)
            if not file_type_result.get("is_valid", True):
                validation_result["is_valid"] = False
                validation_result["errors"].extend(file_type_result.get("errors", []))
        
        return validation_result
    
    async def _validate_document_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document update data"""
        validated = {}
        
        if "file_name" in updates:
            filename = updates["file_name"]
            if not filename or not isinstance(filename, str):
                raise DocumentProcessingError("Invalid filename")
            validated["file_name"] = filename.strip()
        
        if "document_type" in updates:
            doc_type = updates["document_type"]
            if doc_type is not None:
                validated["document_type"] = str(doc_type)
        
        if "metadata" in updates:
            metadata = updates["metadata"]
            if metadata is not None and isinstance(metadata, dict):
                validated["metadata"] = metadata
        
        if "tags" in updates:
            tags = updates["tags"]
            if tags is not None and isinstance(tags, list):
                validated["tags"] = [str(tag) for tag in tags]
        
        if "status" in updates:
            status = updates["status"]
            allowed_statuses = {'active', 'uploaded', 'processing', 'completed', 'failed', 'deleted'}
            if status in allowed_statuses:
                validated["status"] = status
        
        return validated

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service-level statistics"""
        return self._stats.copy()


# TODO: Add document versioning support
# TODO: Add document sharing functionality
# TODO: Add document templates
# TODO: Add document workflow automation
# TODO: Add document analytics
# TODO: Add document backup and restore

    async def _soft_delete(self, document_id: str) -> None:
        """Perform soft delete by setting deleted_at timestamp"""
        if not self.db:
            raise DocumentProcessingError("Database connection not available")
            
        try:
            query = """
            UPDATE documents 
            SET deleted_at = %(deleted_at)s, updated_at = %(updated_at)s
            WHERE id = %(document_id)s AND deleted_at IS NULL
            """
            timestamp = datetime.utcnow()
            await self.db.execute(query, {
                "document_id": document_id,
                "deleted_at": timestamp,
                "updated_at": timestamp
            })
        except Exception as e:
            raise DocumentProcessingError(f"Soft delete failed: {str(e)}")
    
    async def _permanent_delete(self, document_id: str) -> None:
        """Perform permanent delete - removes all document data"""
        if not self.db:
            raise DocumentProcessingError("Database connection not available")
            
        try:
            # First clean up associated OCR jobs
            ocr_cleanup_query = """
            DELETE FROM ocr_jobs WHERE document_id = %(document_id)s
            """
            await self.db.execute(ocr_cleanup_query, {"document_id": document_id})
            
            # Then delete document record
            document_query = """
            DELETE FROM documents WHERE id = %(document_id)s
            """
            await self.db.execute(document_query, {"document_id": document_id})
            
            # Note: document_access_log entries are kept for audit purposes
            # They will be cleaned up by scheduled maintenance
            
        except Exception as e:
            raise DocumentProcessingError(f"Permanent delete failed: {str(e)}")

    async def _update_download_stats(self, document_id: str) -> None:
        """Update document download statistics"""
        if not self.db:
            return
            
        try:
            query = """
            UPDATE documents 
            SET download_count = download_count + 1, 
                last_accessed = %(timestamp)s, 
                updated_at = %(timestamp)s
            WHERE id = %(document_id)s AND deleted_at IS NULL
            """
            await self.db.execute(query, {
                "document_id": document_id,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            self.logger.warning(f"Failed to update download stats: {str(e)}")
