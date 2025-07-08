# 🔗 InsureCove Document Service - File Linkage Documentation

## 📋 **Overview**

This document provides a comprehensive guide to each Python file in the document service, their purposes, dependencies, and how they link together to form a cohesive document processing and management system.

---

## 🏠 **Main Application Entry Point**

### **📄 `app/main.py`** - FastAPI Application Entry Point

**Purpose**: Main FastAPI application with middleware, error handlers, and route registration.

**Key Functions**:
- Application lifecycle management
- Middleware configuration (CORS, security, logging)
- Exception handler registration
- Route mounting and API versioning
- Document processing service integration
- Health and metrics endpoints

**Dependencies**:
```python
# Internal dependencies
from app.core.config import get_settings
from app.core.logging_config import setup_logging, RequestLoggingMiddleware
from app.core.security import SecurityMiddleware
from app.core.exceptions import (exception handlers)
from app.api.document_routes import router as document_router
from app.api.ocr_routes import router as ocr_router

# External dependencies
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
```

**Links to**:
- All route modules (`app/api/*.py`)
- All core modules (`app/core/*.py`)
- All service modules (`app/services/*.py`)
- Configuration and settings management

**Used by**:
- ASGI server (uvicorn/gunicorn)
- Docker container startup
- Development server

---

## 🎯 **Core System Components**

### **📄 `app/core/config.py`** - Configuration Management

**Purpose**: Centralized configuration using Pydantic Settings with environment variable support.

**Key Classes**:
- `Settings`: Main configuration class
- Environment-based configuration loading
- Type validation and default values
- Secret management integration

**Dependencies**:
```python
from pydantic import BaseSettings, Field, validator
from typing import List, Optional, Union
import os
```

**Links to**:
- `app/core/storage.py` (for AWS S3 configuration)
- All other modules (for configuration access)

**Used by**:
- Every module that needs configuration
- `get_settings()` dependency injection

---

### **📄 `app/core/exceptions.py`** - Exception Handling

**Purpose**: RFC 9457-compliant error handling with structured exception hierarchy.

**Key Classes**:
- `BaseInsureCoveException`: Base exception class
- `ValidationException`, `AuthenticationException`, etc.
- `ProblemDetails`: RFC 9457 error response model
- Exception handlers for FastAPI

**Dependencies**:
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
```

**Links to**:
- `app/models.py` (for error response models)
- `app/core/logging_config.py` (for error logging)

**Used by**:
- All route modules for error handling
- `app/main.py` for exception handler registration
- All service modules for raising specific errors

---

### **📄 `app/core/security.py`** - Security and Authentication Integration

**Purpose**: Security utilities, authentication middleware, and integration with external auth service.

**Key Functions**:
- JWT token validation (from external auth service)
- Security middleware implementation
- API key validation
- Request authentication and authorization

**Dependencies**:
```python
from jose import jwt, JWTError
from datetime import datetime
from app.core.config import get_settings
from app.services.auth_client_service import AuthClientService
```

**Links to**:
- `app/core/config.py` (for security settings)
- `app/services/auth_client_service.py` (for auth service integration)
- `app/core/exceptions.py` (for security exceptions)

**Used by**:
- `app/api/document_routes.py` (for authentication)
- `app/api/ocr_routes.py` (for authentication)
- `app/main.py` (for security middleware)

---

### **📄 `app/core/logging_config.py`** - Logging Configuration

**Purpose**: Structured logging setup with correlation IDs, security event logging, and performance monitoring.

**Key Components**:
- Structured JSON logging
- Request/response logging middleware
- Security event logging
- Performance monitoring
- Log correlation IDs

**Dependencies**:
```python
import logging
import time
import uuid
from fastapi import Request, Response
from typing import Callable, Dict, Any
```

**Links to**:
- `app/core/config.py` (for logging settings)
- All modules (for logging instances)

**Used by**:
- `app/main.py` (for logging middleware)
- All route and business logic modules
- Error handling and monitoring

---

## 📋 **API Models and Schemas**

### **📄 `app/models.py`** - Pydantic API Models

**Purpose**: All Pydantic models for API requests, responses, and data validation.

**Key Model Categories**:
- **Document Models**: `DocumentUploadRequest`, `DocumentResponse`, `DocumentMetadata`, etc.
- **OCR Models**: `OCRRequest`, `OCRResponse`, `OCRResult`, etc.
- **Response Models**: `UploadResponse`, `ProcessingResponse`, `ErrorResponse`, etc.
- **Validation Models**: File type validation, size limits, etc.

**Dependencies**:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
```

**Links to**:
- All API route modules (for request/response typing)
- `app/core/exceptions.py` (for error models)

**Used by**:
- All route modules (`app/api/*.py`)
- All service modules (`app/services/*.py`)
- API documentation generation

---

## � **Service Layer**

### **📄 `app/services/auth_client_service.py`** - Authentication Client

**Purpose**: Client service for integrating with external authentication microservice.

**Key Functions**:
- JWT token validation
- User authentication verification
- Auth service communication
- Token introspection

**Dependencies**:
```python
import httpx
from app.core.config import get_settings
from app.core.exceptions import AuthenticationException
```

**Links to**:
- `app.core.config.py` (for auth service settings)
- `app/core/exceptions.py` (for authentication errors)
- `app/core/security.py` (for security operations)

**Used by**:
- `app/api/document_routes.py` (for user authentication)
- `app/api/ocr_routes.py` (for user authentication)
- `app/core/security.py` (for token validation)

---

### **📄 `app/services/document_service.py`** - Document Processing Service

**Purpose**: Core document processing business logic and workflow management.

**Key Functions**:
- Document upload processing
- File metadata extraction
- Document validation and verification
- Processing status management
- Document retrieval and management

**Dependencies**:
```python
from app.services.storage_service import StorageService
from app.services.validation_service import ValidationService
from app.core.config import get_settings
from app.models import DocumentResponse, DocumentMetadata
```

**Links to**:
- `app/services/storage_service.py` (for file storage)
- `app/services/validation_service.py` (for file validation)
- `app/models.py` (for document models)
- `app/core/exceptions.py` (for document errors)

**Used by**:
- `app/api/document_routes.py` (for document operations)
- Document processing workflows

---

### **📄 `app/services/ocr_service.py`** - OCR Processing Service

**Purpose**: Optical Character Recognition processing using AWS Textract and other OCR engines.

**Key Functions**:
- OCR text extraction
- Document analysis and structure detection
- Multi-format OCR support
- OCR result processing and formatting

**Dependencies**:
```python
import boto3
from app.core.config import get_settings
from app.services.storage_service import StorageService
from app.models import OCRRequest, OCRResponse
```
**Links to**:
- `app/core/config.py` (for AWS Textract settings)
- `app/services/storage_service.py` (for file access)
- `app/models.py` (for OCR models)
- `app/core/exceptions.py` (for OCR errors)

**Used by**:
- `app/api/ocr_routes.py` (for OCR operations)
- Document processing workflows

---

### **📄 `app/services/storage_service.py`** - File Storage Service

**Purpose**: File storage operations using AWS S3 with comprehensive file management.

**Key Functions**:
- File upload to S3
- File download and retrieval
- File deletion and cleanup
- Presigned URL generation
- Storage quota management

**Dependencies**:
```python
import boto3
from app.core.config import get_settings
from app.core.storage import get_s3_client
from app.models import FileMetadata
```

**Links to**:
- `app/core/config.py` (for S3 settings)
- `app/core/storage.py` (for S3 client)
- `app/models.py` (for file models)
- `app/core/exceptions.py` (for storage errors)

**Used by**:
- `app/services/document_service.py` (for document storage)
- `app/services/ocr_service.py` (for OCR file access)
- `app/api/document_routes.py` (for file operations)

---

### **📄 `app/services/validation_service.py`** - File Validation Service

**Purpose**: Comprehensive file validation including type checking, security scanning, and content validation.

**Key Functions**:
- File type validation
- File size and format checking
- Security scanning for malicious content
- Content validation and verification
- Metadata extraction

**Dependencies**:
```python
from app.core.config import get_settings
from app.models import ValidationResult
from app.utils.file_utils import get_file_info
```

**Links to**:
- `app/core/config.py` (for validation settings)
- `app/utils/file_utils.py` (for file operations)
- `app/models.py` (for validation models)
- `app/core/exceptions.py` (for validation errors)

**Used by**:
- `app/services/document_service.py` (for document validation)
- `app/api/document_routes.py` (for upload validation)

---

## 🛠️ **Utility Modules**

### **📄 `app/utils/crypto_utils.py`** - Cryptographic Utilities

**Purpose**: Cryptographic operations for file encryption, hashing, and security.

**Key Functions**:
- File encryption and decryption
- Secure hash generation
- Digital signatures
- Key management utilities

**Dependencies**:
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from app.core.config import get_settings
```

**Links to**:
- `app/core/config.py` (for crypto settings)
- `app/services/document_service.py` (for file security)

**Used by**:
- Document processing workflows
- Secure file storage operations

---

### **📄 `app/utils/date_utils.py`** - Date and Time Utilities

**Purpose**: Date and time formatting, timezone handling, and temporal operations.

**Key Functions**:
- Date formatting and parsing
- Timezone conversions
- Timestamp generation
- Date range calculations

**Dependencies**:
```python
from datetime import datetime, timezone
import pytz
```

**Links to**:
- All modules requiring date operations

**Used by**:
- Document metadata processing
- OCR timestamp handling
- API response formatting

---

### **📄 `app/utils/file_utils.py`** - File Operation Utilities

**Purpose**: File system operations, metadata extraction, and file processing utilities.

**Key Functions**:
- File metadata extraction
- File type detection
- File size calculations
- Temporary file management

**Dependencies**:
```python
import os
import mimetypes
from pathlib import Path
```

**Links to**:
- `app/services/validation_service.py` (for file validation)
- `app/services/document_service.py` (for file processing)

**Used by**:
- File upload processing
- Document validation workflows

---

### **📄 `app/utils/response_utils.py`** - Response Utilities

**Purpose**: Standardized API response formatting and helper functions.

**Key Functions**:
- Success response formatting
- Error response standardization
- Pagination utilities
- Response metadata handling

**Dependencies**:
```python
from fastapi import Response
from app.models import ResponseModel
```

**Links to**:
- All API route modules
- `app/models.py` (for response models)

**Used by**:
- All API endpoints for consistent responses
- Error handling workflows

---

## 🌐 **API Route Modules**

### **📄 `app/api/document_routes.py`** - Document Management Endpoints

**Purpose**: RESTful document management endpoints following 2024 API standards.

**Key Endpoints**:
- `POST /documents/upload` - Upload documents
- `GET /documents/{id}` - Retrieve document
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document
- `PUT /documents/{id}` - Update document metadata
- `GET /documents/{id}/download` - Download document

**Dependencies**:
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.document_service import DocumentService
from app.services.auth_client_service import AuthClientService
from app.models import DocumentResponse, DocumentMetadata
```

**Links to**:
- `app/services/document_service.py` (for document operations)
- `app/services/auth_client_service.py` (for authentication)
- `app/models.py` (for request/response models)
- `app/core/exceptions.py` (for error handling)

**Used by**:
- `app/main.py` (route registration)
- Client applications (API consumers)

---

### **📄 `app/api/ocr_routes.py`** - OCR Processing Endpoints

**Purpose**: OCR processing endpoints for text extraction and document analysis.

**Key Endpoints**:
- `POST /ocr/extract` - Extract text from document
- `POST /ocr/analyze` - Analyze document structure
- `GET /ocr/results/{job_id}` - Get OCR processing results
- `GET /ocr/status/{job_id}` - Check OCR processing status

**Dependencies**:
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.ocr_service import OCRService
from app.services.auth_client_service import AuthClientService
from app.models import OCRRequest, OCRResponse
```

**Links to**:
- `app/services/ocr_service.py` (for OCR operations)
- `app/services/auth_client_service.py` (for authentication)
- `app/models.py` (for request/response models)
- `app/core/exceptions.py` (for error handling)

**Used by**:
- `app/main.py` (route registration)
- Client applications (API consumers)

---

## 🎯 **Key Integration Points**

### **1. Configuration Flow**
```
Environment Variables → app/core/config.py → All Modules
AWS S3 Configuration → app/core/storage.py → Storage Operations
```

### **2. Authentication Flow**
```
API Request → Route Handlers → app/services/auth_client_service.py → External Auth Service
```

### **3. Document Processing Flow**
```
Upload Request → app/api/document_routes.py → app/services/document_service.py → Storage/Validation
```

### **4. OCR Processing Flow**
```
OCR Request → app/api/ocr_routes.py → app/services/ocr_service.py → AWS Textract → Results
```

### **5. Error Handling Flow**
```
Exception → app/core/exceptions.py → Structured Response → Client
```

### **6. Logging Flow**
```
All Modules → app/core/logging_config.py → Structured Logs → CloudWatch
```

---

## 📋 **Module Summary Table**

| Module | Purpose | Key Dependencies | Used By |
|--------|---------|------------------|---------|
| `main.py` | FastAPI app entry point | All core, API, service modules | ASGI server |
| `core/config.py` | Configuration management | `core/storage.py` | All modules |
| `core/exceptions.py` | Error handling | `models.py` | All modules |
| `core/security.py` | Security & auth integration | `config.py`, `auth_client_service.py` | API routes |
| `core/logging_config.py` | Logging setup | None | All modules |
| `core/storage.py` | AWS S3 configuration | `config.py` | Storage service |
| `models.py` | API models | None | API routes, services |
| `services/auth_client_service.py` | Auth service client | `config.py`, `security.py` | API routes |
| `services/document_service.py` | Document processing | Storage, validation services | Document routes |
| `services/ocr_service.py` | OCR processing | `config.py`, storage service | OCR routes |
| `services/storage_service.py` | File storage operations | `config.py`, `storage.py` | Document/OCR services |
| `services/validation_service.py` | File validation | `config.py`, `file_utils.py` | Document service |
| `utils/crypto_utils.py` | Cryptographic operations | `config.py` | Document service |
| `utils/date_utils.py` | Date/time utilities | None | All modules |
| `utils/file_utils.py` | File operations | None | Validation service |
| `utils/response_utils.py` | Response formatting | `models.py` | API routes |
| `api/document_routes.py` | Document endpoints | Document service, auth client | `main.py` |
| `api/ocr_routes.py` | OCR endpoints | OCR service, auth client | `main.py` |

---

## 🚀 **Best Practices for File Usage**

### **1. Import Patterns**
```python
# Core utilities - use from app.core
from app.core import get_settings, get_logger

# Service operations - use service layer
from app.services.document_service import DocumentService
from app.services.auth_client_service import AuthClientService

# API models - import specific models
from app.models import DocumentResponse, OCRRequest
```

### **2. Configuration Access**
```python
# Always use dependency injection
def some_function(settings: Settings = Depends(get_settings)):
    return settings.aws_s3_bucket
```

### **3. Error Handling**
```python
# Use specific exception types
from app.core.exceptions import ValidationException, StorageException
raise ValidationException("Invalid file format")
```

### **4. Authentication**
```python
# Use auth client service for token validation
from app.services.auth_client_service import AuthClientService
auth_service = AuthClientService()
user = await auth_service.validate_token(token)
```

### **5. Logging**
```python
# Use structured logging
from app.core.logging_config import get_logger
logger = get_logger(__name__)
logger.info("Document processed", extra={"document_id": doc_id, "user_id": user_id})
```

---

**Last Updated**: July 8, 2025  
**Documentation Version**: 2.0.0
