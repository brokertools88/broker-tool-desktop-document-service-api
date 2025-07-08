"""
RFC 9457 Compliant Exception Handling for InsureCove Document Service

This module implements standardized error handling following RFC 9457 Problem Details
specification with custom exception classes and error response formatting.

Author: InsureCove Team
Date: July 8, 2025
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from enum import Enum


class ErrorType(str, Enum):
    """Standard error type URIs"""
    # Generic errors
    VALIDATION_ERROR = "https://insurecove.com/problems/validation-error"
    AUTHENTICATION_ERROR = "https://insurecove.com/problems/authentication-error"
    AUTHORIZATION_ERROR = "https://insurecove.com/problems/authorization-error"
    NOT_FOUND_ERROR = "https://insurecove.com/problems/not-found"
    CONFLICT_ERROR = "https://insurecove.com/problems/conflict"
    RATE_LIMIT_ERROR = "https://insurecove.com/problems/rate-limit-exceeded"
    
    # Document-specific errors
    DOCUMENT_NOT_FOUND = "https://insurecove.com/problems/document-not-found"
    DOCUMENT_TOO_LARGE = "https://insurecove.com/problems/document-too-large"
    INVALID_DOCUMENT_TYPE = "https://insurecove.com/problems/invalid-document-type"
    DOCUMENT_PROCESSING_ERROR = "https://insurecove.com/problems/document-processing-error"
    DOCUMENT_UPLOAD_ERROR = "https://insurecove.com/problems/document-upload-error"
    
    # OCR-specific errors
    OCR_SERVICE_UNAVAILABLE = "https://insurecove.com/problems/ocr-service-unavailable"
    OCR_PROCESSING_FAILED = "https://insurecove.com/problems/ocr-processing-failed"
    OCR_JOB_NOT_FOUND = "https://insurecove.com/problems/ocr-job-not-found"
    OCR_TIMEOUT = "https://insurecove.com/problems/ocr-timeout"
    
    # Storage errors
    STORAGE_ERROR = "https://insurecove.com/problems/storage-error"
    STORAGE_QUOTA_EXCEEDED = "https://insurecove.com/problems/storage-quota-exceeded"
    
    # Service errors
    INTERNAL_SERVER_ERROR = "https://insurecove.com/problems/internal-server-error"
    SERVICE_UNAVAILABLE = "https://insurecove.com/problems/service-unavailable"
    EXTERNAL_SERVICE_ERROR = "https://insurecove.com/problems/external-service-error"


class APIException(Exception):
    """Base API exception following RFC 9457 Problem Details specification"""
    
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        type_uri: str = ErrorType.INTERNAL_SERVER_ERROR,
        instance: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type = type_uri
        self.instance = instance
        self.errors = errors or []
        self.timestamp = datetime.utcnow()
        self.request_id = str(uuid.uuid4())
        self.extra_data = kwargs
        
        super().__init__(detail)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to RFC 9457 compliant dictionary"""
        problem_detail = {
            "type": self.type,
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id
        }
        
        if self.instance:
            problem_detail["instance"] = self.instance
        
        if self.errors:
            problem_detail["errors"] = self.errors
        
        # Add any extra data
        problem_detail.update(self.extra_data)
        
        return problem_detail


# ============= AUTHENTICATION & AUTHORIZATION EXCEPTIONS =============

class AuthenticationError(APIException):
    """Authentication required or failed"""
    
    def __init__(self, detail: str = "Authentication required", **kwargs):
        super().__init__(
            status_code=401,
            title="Authentication Required",
            detail=detail,
            type_uri=ErrorType.AUTHENTICATION_ERROR,
            **kwargs
        )


class AuthorizationError(APIException):
    """Insufficient permissions"""
    
    def __init__(self, detail: str = "Access denied", **kwargs):
        super().__init__(
            status_code=403,
            title="Access Denied",
            detail=detail,
            type_uri=ErrorType.AUTHORIZATION_ERROR,
            **kwargs
        )


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token"""
    
    def __init__(self, detail: str = "Invalid or expired authentication token", **kwargs):
        super().__init__(detail=detail, **kwargs)


# ============= VALIDATION EXCEPTIONS =============

class ValidationError(APIException):
    """Request validation failed"""
    
    def __init__(
        self,
        detail: str = "Request validation failed",
        errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(
            status_code=422,
            title="Validation Error",
            detail=detail,
            type_uri=ErrorType.VALIDATION_ERROR,
            errors=errors,
            **kwargs
        )


class InvalidFileTypeError(ValidationError):
    """Unsupported file type"""
    
    def __init__(self, file_type: str, allowed_types: List[str], **kwargs):
        detail = f"File type '{file_type}' not supported. Allowed types: {', '.join(allowed_types)}"
        super().__init__(
            detail=detail,
            type_uri=ErrorType.INVALID_DOCUMENT_TYPE,
            file_type=file_type,
            allowed_types=allowed_types,
            **kwargs
        )


class FileTooLargeError(ValidationError):
    """File size exceeds limit"""
    
    def __init__(self, file_size: int, max_size: int, **kwargs):
        detail = f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes"
        super().__init__(
            detail=detail,
            type_uri=ErrorType.DOCUMENT_TOO_LARGE,
            file_size=file_size,
            max_size=max_size,
            **kwargs
        )


# ============= NOT FOUND EXCEPTIONS =============

class NotFoundError(APIException):
    """Resource not found"""
    
    def __init__(self, resource: str = "Resource", **kwargs):
        super().__init__(
            status_code=404,
            title="Not Found",
            detail=f"{resource} not found",
            type_uri=ErrorType.NOT_FOUND_ERROR,
            **kwargs
        )


class DocumentNotFoundError(NotFoundError):
    """Document not found"""
    
    def __init__(self, document_id: str, **kwargs):
        super().__init__(
            resource="Document",
            type_uri=ErrorType.DOCUMENT_NOT_FOUND,
            document_id=document_id,
            **kwargs
        )


class OCRJobNotFoundError(NotFoundError):
    """OCR job not found"""
    
    def __init__(self, job_id: str, **kwargs):
        super().__init__(
            resource="OCR job",
            type_uri=ErrorType.OCR_JOB_NOT_FOUND,
            job_id=job_id,
            **kwargs
        )


# ============= CONFLICT EXCEPTIONS =============

class ConflictError(APIException):
    """Resource conflict"""
    
    def __init__(self, detail: str = "Resource conflict", **kwargs):
        super().__init__(
            status_code=409,
            title="Conflict",
            detail=detail,
            type_uri=ErrorType.CONFLICT_ERROR,
            **kwargs
        )


class DocumentAlreadyExistsError(ConflictError):
    """Document already exists"""
    
    def __init__(self, filename: str, **kwargs):
        super().__init__(
            detail=f"Document with filename '{filename}' already exists",
            filename=filename,
            **kwargs
        )


# ============= RATE LIMITING EXCEPTIONS =============

class RateLimitExceededError(APIException):
    """Rate limit exceeded"""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            status_code=429,
            title="Too Many Requests",
            detail=detail,
            type_uri=ErrorType.RATE_LIMIT_ERROR,
            retry_after=retry_after,
            **kwargs
        )


# ============= DOCUMENT PROCESSING EXCEPTIONS =============

class DocumentProcessingError(APIException):
    """Document processing failed"""
    
    def __init__(self, detail: str = "Document processing failed", **kwargs):
        super().__init__(
            status_code=422,
            title="Document Processing Error",
            detail=detail,
            type_uri=ErrorType.DOCUMENT_PROCESSING_ERROR,
            **kwargs
        )


class DocumentUploadError(APIException):
    """Document upload failed"""
    
    def __init__(self, detail: str = "Document upload failed", **kwargs):
        super().__init__(
            status_code=400,
            title="Upload Error",
            detail=detail,
            type_uri=ErrorType.DOCUMENT_UPLOAD_ERROR,
            **kwargs
        )


# ============= OCR EXCEPTIONS =============

class OCRServiceError(APIException):
    """OCR service error"""
    
    def __init__(self, detail: str = "OCR service error", **kwargs):
        super().__init__(
            status_code=502,
            title="OCR Service Error",
            detail=detail,
            type_uri=ErrorType.OCR_SERVICE_UNAVAILABLE,
            **kwargs
        )


class OCRProcessingError(APIException):
    """OCR processing failed"""
    
    def __init__(self, detail: str = "OCR processing failed", **kwargs):
        super().__init__(
            status_code=422,
            title="OCR Processing Failed",
            detail=detail,
            type_uri=ErrorType.OCR_PROCESSING_FAILED,
            **kwargs
        )


class OCRTimeoutError(APIException):
    """OCR processing timeout"""
    
    def __init__(self, timeout_seconds: int, **kwargs):
        detail = f"OCR processing timed out after {timeout_seconds} seconds"
        super().__init__(
            status_code=408,
            title="OCR Timeout",
            detail=detail,
            type_uri=ErrorType.OCR_TIMEOUT,
            timeout_seconds=timeout_seconds,
            **kwargs
        )


# ============= STORAGE EXCEPTIONS =============

class StorageError(APIException):
    """Storage operation failed"""
    
    def __init__(self, detail: str = "Storage operation failed", **kwargs):
        super().__init__(
            status_code=502,
            title="Storage Error",
            detail=detail,
            type_uri=ErrorType.STORAGE_ERROR,
            **kwargs
        )


class StorageQuotaExceededError(APIException):
    """Storage quota exceeded"""
    
    def __init__(self, quota_limit: int, current_usage: int, **kwargs):
        detail = f"Storage quota exceeded. Used: {current_usage}, Limit: {quota_limit}"
        super().__init__(
            status_code=413,
            title="Storage Quota Exceeded",
            detail=detail,
            type_uri=ErrorType.STORAGE_QUOTA_EXCEEDED,
            quota_limit=quota_limit,
            current_usage=current_usage,
            **kwargs
        )


# ============= SERVICE EXCEPTIONS =============

class ServiceUnavailableError(APIException):
    """Service temporarily unavailable"""
    
    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            status_code=503,
            title="Service Unavailable",
            detail=detail,
            type_uri=ErrorType.SERVICE_UNAVAILABLE,
            retry_after=retry_after,
            **kwargs
        )


class ExternalServiceError(APIException):
    """External service error"""
    
    def __init__(self, service_name: str, detail: str, **kwargs):
        super().__init__(
            status_code=502,
            title="External Service Error",
            detail=f"{service_name}: {detail}",
            type_uri=ErrorType.EXTERNAL_SERVICE_ERROR,
            service_name=service_name,
            **kwargs
        )


# ============= UTILITY FUNCTIONS =============

def create_validation_error(
    field_errors: List[Dict[str, str]],
    detail: str = "Request validation failed"
) -> ValidationError:
    """Create a validation error with field-specific errors"""
    errors = [
        {
            "field": error.get("field"),
            "message": error.get("message"),
            "code": error.get("code", "validation_error")
        }
        for error in field_errors
    ]
    
    return ValidationError(detail=detail, errors=errors)


def handle_pydantic_validation_error(exc: Exception) -> ValidationError:
    """Convert Pydantic validation error to API validation error"""
    # TODO: Parse Pydantic validation errors
    # TODO: Format field-specific error messages
    # TODO: Map error types to codes
    
    errors = []
    # Extract errors from Pydantic exception
    # for error in exc.errors():
    #     errors.append({
    #         "field": ".".join(str(loc) for loc in error["loc"]),
    #         "message": error["msg"],
    #         "code": error["type"]
    #     })
    
    return ValidationError(
        detail="Request validation failed",
        errors=errors
    )


def create_error_response(
    exception: APIException,
    instance: Optional[str] = None
) -> Dict[str, Any]:
    """Create RFC 9457 compliant error response"""
    if instance and not exception.instance:
        exception.instance = instance
    
    return exception.to_dict()


# TODO: Add exception logging
# TODO: Add error tracking/monitoring integration
# TODO: Add user-friendly error messages
# TODO: Add localization support
# TODO: Add error recovery suggestions
