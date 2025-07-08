"""
Pydantic Models for InsureCove Document Service

This module contains all request/response models, enums, and data validation
schemas for the document service API endpoints.

Author: InsureCove Team
Date: July 8, 2025
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import re

# TODO: Add custom validators
# TODO: Add model configuration
# TODO: Add serialization methods


class DocumentType(str, Enum):
    """Supported document file types"""
    PDF = "pdf"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    TIFF = "tiff"
    TIF = "tif"


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class OCRJobStatus(str, Enum):
    """OCR job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OCRLanguage(str, Enum):
    """Supported OCR languages"""
    AUTO = "auto"
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


# TODO: Add base model with common configuration
class BaseAPIModel(BaseModel):
    """Base model with common configuration"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )


# ============= REQUEST MODELS =============

class DocumentUploadRequest(BaseAPIModel):
    """Document upload request schema"""
    filename: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Original filename with extension"
    )
    document_type: Optional[DocumentType] = Field(
        None,
        description="Document type (auto-detected if not provided)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the document"
    )
    auto_ocr: bool = Field(
        default=True,
        description="Automatically trigger OCR processing after upload"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Document tags for categorization"
    )
    
    # TODO: Add filename validation
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename format and security"""
        # TODO: Implement filename sanitization
        # TODO: Check for malicious patterns
        # TODO: Validate file extension
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()
    
    # TODO: Add metadata validation
    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate metadata structure"""
        # TODO: Implement metadata size limits
        # TODO: Validate metadata keys
        return v


class DocumentUpdateRequest(BaseAPIModel):
    """Document metadata update request"""
    filename: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated filename"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated metadata"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Updated tags"
    )
    
    # TODO: Add validation for updates
    # TODO: Ensure at least one field is provided


class OCRProcessRequest(BaseAPIModel):
    """OCR processing configuration request"""
    language: OCRLanguage = Field(
        default=OCRLanguage.AUTO,
        description="Document language for OCR processing"
    )
    extract_tables: bool = Field(
        default=False,
        description="Extract table data from document"
    )
    extract_images: bool = Field(
        default=False,
        description="Extract embedded images"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for text extraction"
    )
    output_format: str = Field(
        default="json",
        pattern="^(json|txt|markdown)$",
        description="Output format for OCR results"
    )
    
    # TODO: Add advanced OCR options
    # TODO: Add custom model selection


class BatchOCRRequest(BaseAPIModel):
    """Batch OCR processing request"""
    document_ids: List[uuid.UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of document IDs to process"
    )
    ocr_options: OCRProcessRequest = Field(
        default_factory=OCRProcessRequest,
        description="OCR processing configuration"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Processing priority (1=highest, 10=lowest)"
    )
    
    # TODO: Add batch size validation
    # TODO: Add user quota validation


class DocumentFilters(BaseAPIModel):
    """Document filtering options for list endpoint"""
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    filename_contains: Optional[str] = None
    has_ocr: Optional[bool] = None
    
    # TODO: Add advanced filtering options
    # TODO: Add search functionality


# ============= RESPONSE MODELS =============

class DocumentResponse(BaseAPIModel):
    """Document response schema"""
    id: uuid.UUID = Field(description="Unique document identifier")
    filename: str = Field(description="Document filename")
    original_filename: str = Field(description="Original uploaded filename")
    document_type: DocumentType = Field(description="Document file type")
    status: DocumentStatus = Field(description="Document processing status")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type of the document")
    
    # URLs
    upload_url: Optional[str] = Field(None, description="Signed upload URL")
    download_url: Optional[str] = Field(None, description="Signed download URL")
    thumbnail_url: Optional[str] = Field(None, description="Document thumbnail URL")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    
    # Ownership and timestamps
    user_id: str = Field(description="Owner user ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Versioning and caching
    etag: str = Field(description="Entity tag for caching")
    version: int = Field(default=1, description="Document version")
    
    # OCR status
    ocr_completed: bool = Field(default=False, description="OCR processing completed")
    ocr_job_id: Optional[uuid.UUID] = Field(None, description="Associated OCR job ID")
    
    # TODO: Add computed fields
    # TODO: Add URL generation methods


class OCRResultResponse(BaseAPIModel):
    """OCR processing result response"""
    # Job information
    document_id: uuid.UUID = Field(description="Source document ID")
    job_id: uuid.UUID = Field(description="OCR job ID")
    status: OCRJobStatus = Field(description="Processing status")
    
    # Processing results
    text_content: Optional[str] = Field(None, description="Extracted text content")
    confidence_score: Optional[float] = Field(None, description="Overall confidence score")
    processing_time_seconds: Optional[float] = Field(None, description="Processing duration")
    
    # Advanced extraction results
    extracted_tables: Optional[List[Dict]] = Field(None, description="Extracted table data")
    extracted_images: Optional[List[str]] = Field(None, description="Extracted image URLs")
    detected_language: Optional[str] = Field(None, description="Detected document language")
    
    # Metadata
    page_count: Optional[int] = Field(None, description="Number of pages processed")
    word_count: Optional[int] = Field(None, description="Total word count")
    character_count: Optional[int] = Field(None, description="Total character count")
    
    # Timestamps
    created_at: datetime = Field(description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error details if failed")
    error_code: Optional[str] = Field(None, description="Error classification code")
    
    # TODO: Add result validation
    # TODO: Add confidence metrics per page


class OCRJobResponse(BaseAPIModel):
    """OCR job status response"""
    job_id: uuid.UUID = Field(description="Unique job identifier")
    document_id: uuid.UUID = Field(description="Source document ID")
    status: OCRJobStatus = Field(description="Current job status")
    progress_percentage: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Processing progress (0-100%)"
    )
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    created_at: datetime = Field(description="Job creation time")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    
    # TODO: Add queue position
    # TODO: Add resource usage metrics


class BatchOCRResponse(BaseAPIModel):
    """Batch OCR processing response"""
    batch_id: uuid.UUID = Field(description="Batch processing ID")
    document_count: int = Field(description="Total documents in batch")
    jobs: List[OCRJobResponse] = Field(description="Individual job details")
    created_at: datetime = Field(description="Batch creation time")
    
    # TODO: Add batch progress tracking
    # TODO: Add estimated completion time


class DocumentListResponse(BaseAPIModel):
    """Paginated document list response"""
    items: List[DocumentResponse] = Field(description="Document items")
    total_count: int = Field(description="Total number of documents")
    page_count: int = Field(description="Total number of pages")
    current_page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    has_more: bool = Field(description="More items available")
    next_cursor: Optional[str] = Field(None, description="Next page cursor")
    previous_cursor: Optional[str] = Field(None, description="Previous page cursor")
    
    # TODO: Add filtering summary
    # TODO: Add sorting options


# ============= HEALTH & MONITORING MODELS =============

class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealthCheck(BaseAPIModel):
    """Individual service health status"""
    name: str = Field(description="Service name")
    status: HealthStatus = Field(description="Service status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error details if unhealthy")
    last_check: datetime = Field(description="Last health check timestamp")


class HealthCheckResponse(BaseAPIModel):
    """Comprehensive health check response"""
    status: HealthStatus = Field(description="Overall service status")
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="Service version")
    uptime_seconds: float = Field(description="Service uptime in seconds")
    
    # Service dependencies
    dependencies: List[ServiceHealthCheck] = Field(description="Dependency health status")
    
    # Resource status
    storage_health: Dict[str, Any] = Field(description="Storage system health")
    ocr_service_health: Dict[str, Any] = Field(description="OCR service health")
    cache_health: Dict[str, Any] = Field(description="Cache system health")
    
    # System resources
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")
    disk_usage_percent: Optional[float] = Field(None, description="Disk usage percentage")
    
    # TODO: Add detailed diagnostics
    # TODO: Add performance metrics


class MetricsResponse(BaseAPIModel):
    """Service metrics response"""
    # Request metrics
    total_requests: int = Field(description="Total requests processed")
    requests_per_minute: float = Field(description="Current requests per minute")
    average_response_time_ms: float = Field(description="Average response time")
    error_rate_percent: float = Field(description="Error rate percentage")
    
    # Document metrics
    total_documents: int = Field(description="Total documents uploaded")
    documents_processed_today: int = Field(description="Documents processed today")
    total_storage_used_mb: float = Field(description="Total storage used in MB")
    
    # OCR metrics
    total_ocr_jobs: int = Field(description="Total OCR jobs processed")
    ocr_success_rate_percent: float = Field(description="OCR success rate")
    average_ocr_time_seconds: float = Field(description="Average OCR processing time")
    
    # System metrics
    timestamp: datetime = Field(description="Metrics collection timestamp")
    
    # TODO: Add business metrics
    # TODO: Add cost metrics


# ============= ERROR MODELS =============

class ErrorDetail(BaseAPIModel):
    """Individual error detail"""
    field: Optional[str] = Field(None, description="Field name causing error")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class APIErrorResponse(BaseAPIModel):
    """RFC 9457 compliant error response"""
    type: str = Field(description="Error type URI")
    title: str = Field(description="Short error description")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Detailed error description")
    instance: str = Field(description="Request URI that caused the error")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    
    # Additional error details
    errors: Optional[List[ErrorDetail]] = Field(None, description="Specific error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    # TODO: Add error tracking
    # TODO: Add suggested actions


# TODO: Add pagination models
# TODO: Add webhook models  
# TODO: Add analytics models
# TODO: Add audit log models
