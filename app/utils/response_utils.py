"""
Response utility functions for API responses.

This module provides helper functions for creating consistent API responses.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import status
import logging

logger = logging.getLogger(__name__)


def create_success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        meta: Additional metadata
        
    Returns:
        JSONResponse with standardized format
        
    TODO:
    - Add response versioning
    - Implement response compression
    - Add response caching headers
    - Implement response transformation
    """
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }
    
    if meta:
        response_data["meta"] = meta
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )


def create_error_response(
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, str]]] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details
        errors: List of field-specific errors
        
    Returns:
        JSONResponse with standardized error format
        
    TODO:
    - Add error categorization
    - Implement error tracking IDs
    - Add localization support
    - Implement error reporting integration
    """
    response_data = {
        "success": False,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }
    
    if error_code:
        response_data["error_code"] = error_code
    
    if details:
        response_data["details"] = details
    
    if errors:
        response_data["errors"] = errors
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )


def create_validation_error_response(
    validation_errors: Dict[str, List[str]],
    message: str = "Validation failed"
) -> JSONResponse:
    """
    Create validation error response.
    
    TODO:
    - Add field-specific error formatting
    - Implement error aggregation
    - Add validation rule information
    """
    formatted_errors = []
    for field, field_errors in validation_errors.items():
        for error in field_errors:
            formatted_errors.append({
                "field": field,
                "message": error,
                "type": "validation_error"
            })
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        errors=formatted_errors
    )


def create_not_found_response(
    resource: str = "Resource",
    resource_id: Optional[str] = None
) -> JSONResponse:
    """
    Create not found error response.
    
    TODO:
    - Add resource type categorization
    - Implement suggestion system for similar resources
    - Add audit logging for not found requests
    """
    message = f"{resource} not found"
    if resource_id:
        message += f" with ID: {resource_id}"
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="RESOURCE_NOT_FOUND",
        details={"resource": resource, "resource_id": resource_id}
    )


def create_unauthorized_response(
    message: str = "Authentication required"
) -> JSONResponse:
    """
    Create unauthorized error response.
    
    TODO:
    - Add authentication method hints
    - Implement rate limiting information
    - Add security audit logging
    """
    return create_error_response(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="AUTHENTICATION_REQUIRED"
    )


def create_forbidden_response(
    message: str = "Access denied",
    required_permissions: Optional[List[str]] = None
) -> JSONResponse:
    """
    Create forbidden error response.
    
    TODO:
    - Add permission requirement details
    - Implement access audit logging
    - Add permission upgrade suggestions
    """
    details = {}
    if required_permissions:
        details["required_permissions"] = required_permissions
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="ACCESS_DENIED",
        details=details if details else None
    )


def create_rate_limit_response(
    retry_after: Optional[int] = None,
    limit: Optional[int] = None,
    remaining: Optional[int] = None
) -> JSONResponse:
    """
    Create rate limit error response.
    
    TODO:
    - Add rate limit window information
    - Implement dynamic retry suggestions
    - Add rate limit upgrade options
    """
    details = {}
    if retry_after:
        details["retry_after"] = retry_after
    if limit:
        details["limit"] = limit
    if remaining:
        details["remaining"] = remaining
    
    response = create_error_response(
        message="Rate limit exceeded",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code="RATE_LIMIT_EXCEEDED",
        details=details if details else None
    )
    
    if retry_after:
        response.headers["Retry-After"] = str(retry_after)
    
    return response


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success"
) -> JSONResponse:
    """
    Create paginated response.
    
    TODO:
    - Add next/previous page URLs
    - Implement cursor-based pagination
    - Add pagination metadata validation
    - Implement lazy loading support
    """
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    meta = {
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        }
    }
    
    return create_success_response(
        data=data,
        message=message,
        meta=meta
    )


def create_file_upload_response(
    file_id: str,
    filename: str,
    size: int,
    content_type: str,
    upload_url: Optional[str] = None
) -> JSONResponse:
    """
    Create file upload success response.
    
    TODO:
    - Add file processing status
    - Implement upload progress tracking
    - Add file validation results
    """
    data = {
        "file_id": file_id,
        "filename": filename,
        "size": size,
        "content_type": content_type,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    if upload_url:
        data["url"] = upload_url
    
    return create_success_response(
        data=data,
        message="File uploaded successfully",
        status_code=status.HTTP_201_CREATED
    )


def create_processing_response(
    task_id: str,
    status: str = "processing",
    estimated_completion: Optional[datetime] = None
) -> JSONResponse:
    """
    Create async processing response.
    
    TODO:
    - Add progress percentage
    - Implement real-time updates
    - Add error handling for failed tasks
    """
    data = {
        "task_id": task_id,
        "status": status,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if estimated_completion:
        data["estimated_completion"] = estimated_completion.isoformat()
    
    return create_success_response(
        data=data,
        message="Processing started",
        status_code=202  # HTTP_202_ACCEPTED
    )


def add_cors_headers(response: JSONResponse, origins: Optional[List[str]] = None) -> JSONResponse:
    """
    Add CORS headers to response.
    
    TODO:
    - Add origin validation
    - Implement preflight handling
    - Add credential support
    """
    if origins is None:
        origins = ["*"]
    
    response.headers["Access-Control-Allow-Origin"] = ", ".join(origins)
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


def add_security_headers(response: JSONResponse) -> JSONResponse:
    """
    Add security headers to response.
    
    TODO:
    - Add CSP (Content Security Policy)
    - Implement HSTS headers
    - Add frame options
    - Implement referrer policy
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


def add_cache_headers(
    response: JSONResponse,
    max_age: int = 3600,
    private: bool = False
) -> JSONResponse:
    """
    Add cache control headers.
    
    TODO:
    - Add ETags for conditional requests
    - Implement Last-Modified headers
    - Add cache validation
    """
    cache_control = f"{'private' if private else 'public'}, max-age={max_age}"
    response.headers["Cache-Control"] = cache_control
    
    return response


class ResponseBuilder:
    """
    Builder pattern for creating complex responses.
    
    TODO:
    - Add response templates
    - Implement response transformation pipelines
    - Add response validation
    - Implement response caching
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset builder state."""
        self._data = None
        self._message = "Success"
        self._status_code = status.HTTP_200_OK
        self._meta = {}
        self._headers = {}
        self._errors = []
        self._success = True
    
    def success(self, message: str = "Success") -> 'ResponseBuilder':
        """Set success state."""
        self._success = True
        self._message = message
        return self
    
    def error(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> 'ResponseBuilder':
        """Set error state."""
        self._success = False
        self._message = message
        self._status_code = status_code
        return self
    
    def data(self, data: Any) -> 'ResponseBuilder':
        """Set response data."""
        self._data = data
        return self
    
    def meta(self, key: str, value: Any) -> 'ResponseBuilder':
        """Add metadata."""
        self._meta[key] = value
        return self
    
    def header(self, key: str, value: str) -> 'ResponseBuilder':
        """Add header."""
        self._headers[key] = value
        return self
    
    def add_error(self, field: str, message: str) -> 'ResponseBuilder':
        """Add field error."""
        self._errors.append({"field": field, "message": message})
        return self
    
    def build(self) -> JSONResponse:
        """Build final response."""
        if self._success:
            response = create_success_response(
                data=self._data,
                message=self._message,
                status_code=self._status_code,
                meta=self._meta if self._meta else None
            )
        else:
            response = create_error_response(
                message=self._message,
                status_code=self._status_code,
                errors=self._errors if self._errors else None
            )
        
        # Add custom headers
        for key, value in self._headers.items():
            response.headers[key] = value
        
        return response


class APIResponseFormatter:
    """
    Formatter for standardizing API responses across the application.
    
    TODO:
    - Add response version management
    - Implement response transformation rules
    - Add response analytics
    - Implement response optimization
    """
    
    def __init__(self, version: str = "1.0"):
        self.version = version
    
    def format_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response according to API standards."""
        formatted = {
            "api_version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            **response_data
        }
        
        return formatted
    
    def format_error(self, error: Exception, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Format error response."""
        formatted = self.format_response({
            "success": False,
            "error": {
                "type": error.__class__.__name__,
                "message": str(error)
            }
        })
        
        if request_id:
            formatted["request_id"] = request_id
        
        return formatted
