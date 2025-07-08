# 🔗 InsureCove Document Service - File Linkage Documentation

## 📋 **Overview**

This document provides a comprehensive guide to each Python file in the document service, their purposes, dependencies, and how they link together to## 🔐 **Service Layer**

### **📄 `app/services/secrets_service.py`** - AWS Secrets Manager Service ⭐**NEW**

**Purpose**: Centralized secrets management for the document service, providing application-specific secret retrieval and validation.

**Key Functions**:
- Document service specific secret retrieval
- Secret validation and caching
- Environment-aware secret management
- Health checks for secret availability

**Key Methods**:
- `get_mistral_ai_config()` - Mistral AI API configuration
- `get_storage_config()` - AWS S3 storage configuration  
- `get_auth_service_config()` - External auth service credentials
- `get_jwt_config()` - JWT validation configuration
- `get_database_config()` - Database connection details
- `get_monitoring_config()` - Monitoring and logging settings

**Dependencies**:
```python
from app.utils.aws_secrets import AWSSecretsManager, AWSSecretsConfig, SecretValue
from app.core.exceptions import ConfigurationError
from typing import Dict, Any, Optional
import logging
import asyncio
```

**Links to**:
- `app/utils/aws_secrets.py` (core AWS Secrets Manager client)
- `app/core/exceptions.py` (for configuration errors)
- `app/core/secrets_config.py` (configuration integration)

**Used by**:
- `app/core/secrets_config.py` (for configuration loading)
- `app/main.py` (for application startup)
- Health check endpoints
- All modules requiring secure configuration

---

### **📄 `app/services/auth_client_service.py`** - Authentication Clientrm a cohesive document processing and management system.

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
- `app/core/secrets_config.py` (for secrets-based configuration)
- All other modules (for configuration access)

**Used by**:
- Every module that needs configuration
- `get_settings()` dependency injection

---

### **📄 `app/core/secrets_config.py`** - AWS Secrets Manager Configuration ⭐**NEW**

**Purpose**: Secrets-based configuration management that integrates with AWS Secrets Manager for sensitive settings.

**Key Classes**:
- `SecretsBasedConfig`: Configuration class using AWS Secrets Manager
- Environment-aware secret loading
- Property-based access to secrets
- Automatic fallback to environment variables for non-sensitive settings

**Dependencies**:
```python
from app.services.secrets_service import get_secrets_manager
from app.core.exceptions import ConfigurationError
from typing import Dict, Any, Optional, List
import os
import logging
```

**Links to**:
- `app/services/secrets_service.py` (for secret retrieval)
- `app/core/exceptions.py` (for configuration errors)
- `app/utils/aws_secrets.py` (underlying AWS client)

**Used by**:
- `app/main.py` (for application startup configuration)
- All modules requiring secure configuration
- Health check endpoints

---

### **📄 `app/core/exceptions.py`** - Exception Handling

**Purpose**: RFC 9457-compliant error handling with structured exception hierarchy.

**Key Classes**:
- `BaseInsureCoveException`: Base exception class
- `ValidationException`, `AuthenticationException`, etc.
- `ConfigurationError`: AWS Secrets Manager configuration errors ⭐**UPDATED**
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
- `app/services/secrets_service.py` (for secret management errors)

**Used by**:
- All route modules for error handling
- `app/main.py` for exception handler registration
- All service modules for raising specific errors
- AWS Secrets Manager integration modules

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

### **📄 `app/utils/aws_secrets.py`** - AWS Secrets Manager Client ⭐**NEW**

**Purpose**: Core AWS Secrets Manager client providing low-level secret retrieval, caching, and error handling for the document service.

**Key Classes**:
- `AWSSecretsManager`: Main secrets manager client
- `AWSSecretsConfig`: Configuration for AWS Secrets Manager
- `SecretValue`: Container for secret values with metadata

**Key Functions**:
- Document service specific secret retrieval methods
- Connection management and proxy support
- Intelligent caching with TTL
- Error handling and retry logic
- Environment-aware secret naming

**Dependencies**:
```python
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union
from functools import lru_cache
import json
import logging
```

**Links to**:
- `app/services/secrets_service.py` (high-level secrets management)
- AWS Secrets Manager service
- `app/core/exceptions.py` (for AWS-related errors)

**Used by**:
- `app/services/secrets_service.py` (primary consumer)
- `app/core/secrets_config.py` (configuration integration)
- Health check endpoints

---

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

### **📄 `app/api/health_routes.py`** - Health Check Endpoints ⭐**UPDATED**

**Purpose**: Comprehensive health monitoring endpoints with AWS Secrets Manager integration.

**Key Endpoints**:
- `GET /health` - Basic health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe  
- `GET /health/startup` - Startup probe
- `GET /health/detailed` - Detailed health with dependencies

**Health Checks Include**:
- AWS Secrets Manager connectivity
- AWS S3 storage availability
- Mistral AI OCR service status
- External auth service connectivity
- Application configuration validation

**Dependencies**:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.secrets_service import health_check_secrets
from app.models import HealthCheckResponse, ServiceHealthCheck
from app.core.exceptions import ConfigurationError
```

**Links to**:
- `app/services/secrets_service.py` (for secrets health checks)
- `app/models.py` (for health check models)
- `app/core/exceptions.py` (for error handling)
- AWS services (S3, Secrets Manager)
- External services (Mistral AI, Auth service)

**Used by**:
- `app/main.py` (route registration)
- Kubernetes health probes
- Monitoring systems
- Load balancers

---

### **📄 `app/api/metrics_routes.py`** - Metrics and Monitoring Endpoints

**Purpose**: Application metrics and performance monitoring endpoints.

**Key Endpoints**:
- `GET /metrics` - Prometheus metrics
- `GET /metrics/custom` - Custom application metrics

**Dependencies**:
```python
from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
```

**Links to**:
- Prometheus metrics library
- Application performance monitoring

**Used by**:
- `app/main.py` (route registration)
- Prometheus monitoring
- Grafana dashboards

---

## 🎯 **Key Integration Points**

### **1. Configuration Flow**
```
Environment Variables → app/core/config.py → All Modules
AWS Secrets Manager → app/utils/aws_secrets.py → app/services/secrets_service.py → app/core/secrets_config.py → All Modules ⭐**NEW**
AWS S3 Configuration → app/core/storage.py → Storage Operations
```

### **2. Secrets Management Flow** ⭐**NEW**
```
Application Startup → app/services/secrets_service.py → AWS Secrets Manager → Cached Secrets → Configuration
Health Checks → Secrets Validation → AWS Connectivity → Status Reports
```

### **3. Authentication Flow**
```
API Request → Route Handlers → app/services/auth_client_service.py → External Auth Service
JWT Validation → app/core/secrets_config.py → AWS Secrets (JWT Config) → Token Verification ⭐**UPDATED**
```

### **4. Document Processing Flow**
```
Upload Request → app/api/document_routes.py → app/services/document_service.py → Storage/Validation
```

### **5. OCR Processing Flow**
```
OCR Request → app/api/ocr_routes.py → app/services/ocr_service.py → Mistral AI OCR → Results ⭐**UPDATED**
```

### **6. Error Handling Flow**
```
Exception → app/core/exceptions.py → Structured Response → Client
Configuration Errors → ConfigurationError → Secrets Manager Issues → Health Status ⭐**NEW**
```

### **7. Logging Flow**
```
All Modules → app/core/logging_config.py → Structured Logs → CloudWatch
```

### **8. Health Monitoring Flow** ⭐**NEW**
```
Health Endpoint → app/api/health_routes.py → Service Health Checks → AWS Services → Status Response
```

---

## 📋 **Module Summary Table**

| Module | Purpose | Key Dependencies | Used By |
|--------|---------|------------------|---------|
| `main.py` | FastAPI app entry point | All core, API, service modules | ASGI server |
| `core/config.py` | Configuration management | `core/storage.py`, `core/secrets_config.py` | All modules |
| `core/secrets_config.py` ⭐**NEW** | AWS Secrets Manager configuration | `services/secrets_service.py`, `utils/aws_secrets.py` | All modules needing secure config |
| `core/exceptions.py` | Error handling | `models.py` | All modules |
| `core/security.py` | Security & auth integration | `config.py`, `auth_client_service.py` | API routes |
| `core/logging_config.py` | Logging setup | None | All modules |
| `core/storage.py` | AWS S3 configuration | `config.py` | Storage service |
| `models.py` | API models | None | API routes, services |
| `services/secrets_service.py` ⭐**NEW** | Document service secrets management | `utils/aws_secrets.py`, `core/exceptions.py` | `core/secrets_config.py`, health checks |
| `services/auth_client_service.py` | Auth service client | `config.py`, `security.py` | API routes |
| `services/document_service.py` | Document processing | Storage, validation services | Document routes |
| `services/ocr_service.py` | OCR processing | `config.py`, storage service | OCR routes |
| `services/storage_service.py` | File storage operations | `config.py`, `storage.py` | Document/OCR services |
| `services/validation_service.py` | File validation | `config.py`, `file_utils.py` | Document service |
| `utils/aws_secrets.py` ⭐**NEW** | AWS Secrets Manager client | `boto3`, `botocore` | `services/secrets_service.py` |
| `utils/crypto_utils.py` | Cryptographic operations | `config.py` | Document service |
| `utils/date_utils.py` | Date/time utilities | None | All modules |
| `utils/file_utils.py` | File operations | None | Validation service |
| `utils/response_utils.py` | Response formatting | `models.py` | API routes |
| `api/document_routes.py` | Document endpoints | Document service, auth client | `main.py` |
| `api/ocr_routes.py` | OCR endpoints | OCR service, auth client | `main.py` |
| `api/health_routes.py` ⭐**UPDATED** | Health check endpoints | `services/secrets_service.py`, `models.py` | `main.py`, monitoring |
| `api/metrics_routes.py` | Metrics endpoints | Prometheus client | `main.py`, monitoring |

---

## 🚀 **Best Practices for File Usage**

### **1. Import Patterns**
```python
# Core utilities - use from app.core
from app.core import get_settings, get_logger

# Secrets management - use secrets-based configuration ⭐**NEW**
from app.core.secrets_config import get_config, initialize_config
from app.services.secrets_service import get_secrets_manager

# Service operations - use service layer
from app.services.document_service import DocumentService
from app.services.auth_client_service import AuthClientService

# API models - import specific models
from app.models import DocumentResponse, OCRRequest
```

### **2. Configuration Access**
```python
# Traditional configuration access
def some_function(settings: Settings = Depends(get_settings)):
    return settings.aws_s3_bucket

# AWS Secrets Manager configuration access ⭐**NEW**
from app.core.secrets_config import get_config
config = get_config()
api_key = config.mistral_api_key  # Retrieved from AWS Secrets Manager
```

### **3. Secrets Management** ⭐**NEW**
```python
# Application startup - initialize secrets
await initialize_secrets(environment="production")
config = await initialize_config(environment="production")

# Direct secret access when needed
from app.services.secrets_service import get_secrets_manager
secrets = get_secrets_manager()
mistral_config = await secrets.get_mistral_ai_config()
```

### **4. Error Handling**
```python
# Use specific exception types
from app.core.exceptions import ValidationException, StorageException, ConfigurationError
raise ValidationException("Invalid file format")

# Handle configuration errors ⭐**NEW**
try:
    config = await secrets.get_mistral_ai_config()
except ConfigurationError as e:
    logger.error(f"Failed to load Mistral AI configuration: {e}")
```

### **5. Authentication**
```python
# Use auth client service for token validation
from app.services.auth_client_service import AuthClientService
auth_service = AuthClientService()
user = await auth_service.validate_token(token)
```

### **6. Logging**
```python
# Use structured logging
from app.core.logging_config import get_logger
logger = get_logger(__name__)
logger.info("Document processed", extra={"document_id": doc_id, "user_id": user_id})

# Log secrets-related events ⭐**NEW**
logger.info("AWS Secrets Manager initialized", extra={"environment": env, "region": region})
```

### **7. Health Checks** ⭐**NEW**
```python
# Include secrets in health checks
from app.services.secrets_service import health_check_secrets
secrets_health = await health_check_secrets()
overall_health = secrets_health["status"] == "healthy"
```

---

**Last Updated**: July 8, 2025  
**Documentation Version**: 3.0.0 ⭐**UPDATED for AWS Secrets Manager Integration**
