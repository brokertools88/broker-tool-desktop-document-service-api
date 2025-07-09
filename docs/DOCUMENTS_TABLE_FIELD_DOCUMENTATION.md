# Database Field Documentation - Enhanced Documents Table

## 📋 **Overview**

This document provides comprehensive documentation for all fields in the enhanced `documents` table after the migration. It explains the purpose, usage, and data storage for each field, along with code references where these fields are populated.

---

## 🗃️ **ORIGINAL FIELDS (Pre-Migration)**

### Core Identity Fields

#### `id` (UUID, PRIMARY KEY)
- **Purpose**: Unique identifier for each document record
- **Data Type**: `UUID NOT NULL DEFAULT extensions.uuid_generate_v4()`
- **Stores**: Auto-generated UUID (e.g., `123e4567-e89b-12d3-a456-426614174000`)
- **Populated By**: Database auto-generation
- **Usage**: Primary key for all document operations

#### `file_name` (TEXT)
- **Purpose**: Current/processed filename used by the system
- **Data Type**: `TEXT NOT NULL`
- **Stores**: Sanitized filename (e.g., `document_2025_07_09.pdf`)
- **Populated By**: `ValidationService.sanitize_filename()`
- **Code Location**: `app/services/validation_service.py:_sanitize_filename()`

#### `original_file_name` (TEXT)
- **Purpose**: Original filename as uploaded by user
- **Data Type**: `TEXT NOT NULL`
- **Stores**: Unmodified original name (e.g., `My Document (1).pdf`)
- **Populated By**: Direct from upload request
- **Code Location**: `app/services/document_service.py:upload_document()`

#### `file_size` (INTEGER)
- **Purpose**: Document size in bytes for storage planning and validation
- **Data Type**: `INTEGER NOT NULL`
- **Stores**: File size in bytes (e.g., `2048576` for 2MB file)
- **Populated By**: `len(file_content)` during upload
- **Code Location**: `app/services/storage_service.py:upload_file()`

#### `file_type` (TEXT)
- **Purpose**: File extension/type classification
- **Data Type**: `TEXT NOT NULL`
- **Stores**: File extension (e.g., `pdf`, `jpg`, `docx`)
- **Populated By**: `ValidationService.validate_file_type()`
- **Code Location**: `app/services/validation_service.py:validate_file_type()`

#### `file_path` (TEXT)
- **Purpose**: Legacy field for file system path reference
- **Data Type**: `TEXT NOT NULL`
- **Stores**: File system path (e.g., `/uploads/documents/file.pdf`)
- **Populated By**: Legacy upload process
- **Note**: Superseded by `storage_path` in enhanced schema

### Relationship Fields

#### `client_id` (UUID, FOREIGN KEY)
- **Purpose**: Links document to specific client in insurance context
- **Data Type**: `UUID NULL`
- **Stores**: Client UUID from clients table
- **Populated By**: Business logic based on document context
- **Code Location**: `app/services/document_service.py` (business rules)

#### `insurer_id` (UUID, FOREIGN KEY)
- **Purpose**: Links document to specific insurer in insurance context
- **Data Type**: `UUID NULL`
- **Stores**: Insurer UUID from insurers table
- **Populated By**: Business logic based on document context
- **Code Location**: `app/services/document_service.py` (business rules)

#### `uploaded_by` (TEXT)
- **Purpose**: Legacy field for user identification
- **Data Type**: `TEXT NULL`
- **Stores**: User identifier string
- **Populated By**: Authentication context
- **Note**: Superseded by `user_id` in enhanced schema

### Metadata and Status Fields

#### `document_type` (TEXT)
- **Purpose**: Business classification of document content
- **Data Type**: `TEXT NULL`
- **Stores**: Document category (e.g., `invoice`, `contract`, `claim`)
- **Populated By**: Business logic or AI classification
- **Code Location**: `app/services/document_service.py:_classify_document()`

#### `metadata` (JSONB)
- **Purpose**: Flexible storage for additional document properties
- **Data Type**: `JSONB NULL DEFAULT '{}'::jsonb`
- **Stores**: JSON object with custom properties
```json
{
  "author": "John Doe",
  "department": "Claims",
  "confidentiality": "internal",
  "custom_fields": {...}
}
```
- **Populated By**: Service methods and business logic
- **Code Location**: `app/services/document_service.py:_prepare_metadata()`

#### `status` (TEXT)
- **Purpose**: Document processing lifecycle status
- **Data Type**: `TEXT NULL DEFAULT 'active'`
- **Stores**: Status values (`uploaded`, `processing`, `completed`, `failed`, `deleted`)
- **Populated By**: Service state management
- **Code Location**: `app/services/document_service.py:upload_document()`

### Timestamp Fields

#### `upload_date` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: When document was originally uploaded
- **Data Type**: `TIMESTAMP WITH TIME ZONE NULL DEFAULT now()`
- **Stores**: ISO timestamp (e.g., `2025-07-09T10:30:00Z`)
- **Populated By**: Database default on INSERT
- **Usage**: Audit trail and sorting

#### `last_modified` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: Last modification timestamp
- **Data Type**: `TIMESTAMP WITH TIME ZONE NULL DEFAULT now()`
- **Stores**: ISO timestamp updated on changes
- **Populated By**: Database trigger `update_updated_at_column()`
- **Usage**: Cache invalidation and conflict resolution

#### `created_at` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: Record creation timestamp
- **Data Type**: `TIMESTAMP WITH TIME ZONE NULL DEFAULT now()`
- **Stores**: ISO timestamp of record creation
- **Populated By**: Database default on INSERT
- **Usage**: Audit trail

#### `updated_at` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: Record update timestamp
- **Data Type**: `TIMESTAMP WITH TIME ZONE NULL DEFAULT now()`
- **Stores**: ISO timestamp of last record update
- **Populated By**: Database trigger on UPDATE
- **Usage**: Sync and caching

---

## 🆕 **ENHANCED FIELDS (Post-Migration)**

### Storage Backend Integration

#### `storage_path` (TEXT)
- **Purpose**: Full path to document in cloud storage
- **Data Type**: `TEXT`
- **Stores**: S3 object path (e.g., `documents/user123/456_document.pdf`)
- **Populated By**: `StorageService.upload_file()`
- **Code Location**: `app/services/storage_service.py:upload_file()`
```python
storage_path = f"documents/{user_id}/{file_key}"
```

#### `storage_bucket` (TEXT)
- **Purpose**: Cloud storage bucket name
- **Data Type**: `TEXT`
- **Stores**: S3 bucket name (e.g., `insurecove-documents`)
- **Populated By**: Configuration settings
- **Code Location**: `app/core/config.py:AWS_S3_BUCKET`
```python
storage_bucket = settings.AWS_S3_BUCKET
```

#### `storage_key` (TEXT, UNIQUE)
- **Purpose**: Unique key for storage backend operations
- **Data Type**: `TEXT UNIQUE`
- **Stores**: Collision-resistant storage key (e.g., `user123_456_20250709_document.pdf`)
- **Populated By**: `StorageService._generate_file_key()`
- **Code Location**: `app/services/storage_service.py:_generate_file_key()`
```python
file_key = f"{user_id}_{timestamp}_{sanitized_filename}"
```

#### `file_hash` (TEXT)
- **Purpose**: Content hash for deduplication and integrity
- **Data Type**: `TEXT`
- **Stores**: SHA-256 hash of file content (e.g., `a1b2c3d4e5f6...`)
- **Populated By**: `FileProcessor.calculate_hash()`
- **Code Location**: `app/utils/file_utils.py:calculate_hash()`
```python
file_hash = hashlib.sha256(file_content).hexdigest()
```

#### `mime_type` (TEXT)
- **Purpose**: Accurate MIME type for proper handling
- **Data Type**: `TEXT`
- **Stores**: MIME type (e.g., `application/pdf`, `image/jpeg`)
- **Populated By**: `ValidationService.detect_mime_type()`
- **Code Location**: `app/services/validation_service.py:detect_mime_type()`
```python
mime_type = magic.from_buffer(file_content, mime=True)
```

### Service Compatibility

#### `user_id` (TEXT)
- **Purpose**: Modern user identification (replaces uploaded_by)
- **Data Type**: `TEXT`
- **Stores**: User ID from authentication system
- **Populated By**: Authentication service
- **Code Location**: `app/services/document_service.py:upload_document()`
```python
user_id = auth_context.get_user_id()
```

### Versioning and Caching

#### `version` (INTEGER)
- **Purpose**: Document version number for revision control
- **Data Type**: `INTEGER DEFAULT 1`
- **Stores**: Version number (e.g., `1`, `2`, `3`)
- **Populated By**: Version management logic
- **Code Location**: `app/services/document_service.py:_increment_version()`
```python
version = existing_document.version + 1
```

#### `etag` (TEXT)
- **Purpose**: Entity tag for HTTP caching and change detection
- **Data Type**: `TEXT`
- **Stores**: ETag value (e.g., `"a1b2c3d4e5f6"`)
- **Populated By**: `TokenGenerator.generate_api_key()`
- **Code Location**: `app/services/document_service.py:_save_document_metadata()`
```python
etag = self.token_generator.generate_api_key(16)
```

### Security and Validation

#### `security_scan_status` (TEXT)
- **Purpose**: Security scan result status
- **Data Type**: `TEXT DEFAULT 'pending'`
- **Stores**: Status (`pending`, `scanning`, `clean`, `threat`, `error`)
- **Populated By**: `ValidationService.validate_file_security()`
- **Code Location**: `app/services/validation_service.py:validate_file_security()`
```python
security_scan_status = "clean" if scan_result.is_safe else "threat"
```

#### `virus_scan_status` (TEXT)
- **Purpose**: Antivirus scan result status
- **Data Type**: `TEXT DEFAULT 'pending'`
- **Stores**: Status (`pending`, `scanning`, `clean`, `infected`, `error`)
- **Populated By**: `ValidationService.scan_for_malware()`
- **Code Location**: `app/services/validation_service.py:scan_for_malware()`
```python
virus_scan_status = "clean" if not virus_detected else "infected"
```

#### `content_validated` (BOOLEAN)
- **Purpose**: Flag indicating content validation completion
- **Data Type**: `BOOLEAN DEFAULT FALSE`
- **Stores**: Boolean (`TRUE` for validated, `FALSE` for pending)
- **Populated By**: `ValidationService.validate_file_content()`
- **Code Location**: `app/services/validation_service.py:validate_file_content()`
```python
content_validated = all([
    filename_valid, size_valid, type_valid, security_clean
])
```

### OCR Integration

#### `ocr_completed` (BOOLEAN)
- **Purpose**: Flag indicating OCR processing completion
- **Data Type**: `BOOLEAN DEFAULT FALSE`
- **Stores**: Boolean (`TRUE` when OCR is done)
- **Populated By**: `OCRService.process_document()`
- **Code Location**: `app/services/ocr_service.py:process_document()`
```python
ocr_completed = True if ocr_result.status == "completed" else False
```

#### `ocr_job_id` (UUID)
- **Purpose**: Reference to OCR processing job
- **Data Type**: `UUID`
- **Stores**: UUID linking to `ocr_jobs` table
- **Populated By**: `OCRService.create_job()`
- **Code Location**: `app/services/ocr_service.py:create_job()`
```python
ocr_job_id = await self.create_ocr_job(document_id)
```

#### `ocr_text` (TEXT)
- **Purpose**: Extracted text content from OCR
- **Data Type**: `TEXT`
- **Stores**: Full text extracted from document
- **Populated By**: `OCRService.extract_text()`
- **Code Location**: `app/services/ocr_service.py:extract_text()`
```python
ocr_text = mistral_response.get("extracted_text", "")
```

#### `ocr_confidence` (DECIMAL)
- **Purpose**: OCR accuracy confidence score
- **Data Type**: `DECIMAL(3,2)`
- **Stores**: Confidence percentage (e.g., `0.95` for 95%)
- **Populated By**: `OCRService.calculate_confidence()`
- **Code Location**: `app/services/ocr_service.py:calculate_confidence()`
```python
ocr_confidence = ocr_result.get("confidence_score", 0.0)
```

#### `ocr_language` (TEXT)
- **Purpose**: Detected document language during OCR
- **Data Type**: `TEXT`
- **Stores**: Language code (e.g., `en`, `es`, `fr`)
- **Populated By**: `OCRService.detect_language()`
- **Code Location**: `app/services/ocr_service.py:detect_language()`
```python
ocr_language = ocr_result.get("detected_language", "unknown")
```

#### `ocr_page_count` (INTEGER)
- **Purpose**: Number of pages processed by OCR
- **Data Type**: `INTEGER`
- **Stores**: Page count (e.g., `5` for 5-page document)
- **Populated By**: `OCRService.count_pages()`
- **Code Location**: `app/services/ocr_service.py:process_document()`
```python
ocr_page_count = len(ocr_result.get("pages", []))
```

#### `ocr_word_count` (INTEGER)
- **Purpose**: Total word count from extracted text
- **Data Type**: `INTEGER`
- **Stores**: Word count (e.g., `1250`)
- **Populated By**: `OCRService.count_words()`
- **Code Location**: `app/services/ocr_service.py:process_document()`
```python
ocr_word_count = len(ocr_text.split()) if ocr_text else 0
```

### URL Management (Temporary Fields)

#### `upload_url` (TEXT)
- **Purpose**: Temporary signed URL for document upload
- **Data Type**: `TEXT`
- **Stores**: Pre-signed S3 URL for uploads
- **Populated By**: `StorageService.generate_upload_url()`
- **Code Location**: `app/services/storage_service.py:generate_upload_url()`
```python
upload_url = await self.storage.generate_presigned_url("PUT", file_key)
```

#### `download_url` (TEXT)
- **Purpose**: Temporary signed URL for document download
- **Data Type**: `TEXT`
- **Stores**: Pre-signed S3 URL for downloads
- **Populated By**: `DocumentService._generate_signed_download_url()`
- **Code Location**: `app/services/document_service.py:_generate_signed_download_url()`
```python
download_url = await self.storage.generate_download_url(storage_key)
```

#### `thumbnail_url` (TEXT)
- **Purpose**: URL to document thumbnail/preview
- **Data Type**: `TEXT`
- **Stores**: URL to generated thumbnail image
- **Populated By**: Thumbnail generation service
- **Code Location**: Future implementation

#### `url_expires_at` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: Expiration time for temporary URLs
- **Data Type**: `TIMESTAMP WITH TIME ZONE`
- **Stores**: Expiration timestamp for signed URLs
- **Populated By**: URL generation logic
- **Code Location**: `app/services/storage_service.py:generate_presigned_url()`
```python
url_expires_at = datetime.utcnow() + timedelta(hours=1)
```

### Usage Tracking

#### `download_count` (INTEGER)
- **Purpose**: Track how many times document was downloaded
- **Data Type**: `INTEGER DEFAULT 0`
- **Stores**: Download counter (e.g., `15`)
- **Populated By**: Download tracking middleware
- **Code Location**: `app/api/document_routes.py:download_document()`
```python
download_count += 1  # Incremented on each download
```

#### `last_accessed` (TIMESTAMP WITH TIME ZONE)
- **Purpose**: Timestamp of last document access
- **Data Type**: `TIMESTAMP WITH TIME ZONE`
- **Stores**: Last access timestamp
- **Populated By**: Access tracking middleware
- **Code Location**: `app/api/document_routes.py` (middleware)
```python
last_accessed = datetime.utcnow()  # Updated on access
```

### Enhanced Tagging

#### `tags` (TEXT[])
- **Purpose**: Array of tags for document categorization
- **Data Type**: `TEXT[] DEFAULT ARRAY[]::TEXT[]`
- **Stores**: Array of tag strings (e.g., `["urgent", "financial", "q4-2025"]`)
- **Populated By**: Business logic and user input
- **Code Location**: `app/services/document_service.py:upload_document()`
```python
tags = request.tags or []  # From user input or auto-classification
```

---

## 🔍 **CODE LOCATIONS FOR DATABASE OPERATIONS**

### Document Creation/Population

#### Primary Document Upload
**File**: `app/services/document_service.py`
**Method**: `upload_document()`
**Lines**: ~85-150
```python
async def upload_document(self, file_content: bytes, filename: str, user_id: str, ...):
    # Document record creation happens here
    document_record = await self._save_document_metadata(...)
```

#### Document Metadata Creation
**File**: `app/services/document_service.py`
**Method**: `_save_document_metadata()`
**Lines**: ~670-705
```python
async def _save_document_metadata(self, ...):
    document_record = {
        "id": document_id,
        "filename": filename,
        "original_filename": filename,
        "user_id": user_id,
        "status": DocumentStatus.UPLOADED.value,
        # ... all other fields populated here
    }
```

### Storage Integration
**File**: `app/services/storage_service.py`
**Method**: `upload_file()`
**Lines**: ~80-130
```python
async def upload_file(self, file_content: bytes, filename: str, ...):
    # Storage-related fields populated here
    file_key = await self._generate_file_key(filename, user_id)
    file_hash = await self._calculate_file_hash(file_content)
```

### OCR Integration
**File**: `app/services/ocr_service.py`
**Method**: `process_document()`
**Lines**: ~85-150
```python
async def process_document(self, document_id: str, ...):
    # OCR-related fields populated here
    ocr_result = await self._extract_text_content(file_content)
```

### Validation Fields
**File**: `app/services/validation_service.py`
**Methods**: Various validation methods
```python
# Security validation
async def validate_file_security(self, file_content: bytes) -> Dict[str, Any]

# Content validation  
async def validate_file_content(self, file_content: bytes, ...) -> Dict[str, Any]

# MIME type detection
def detect_mime_type(self, file_content: bytes) -> str
```

---

## 📊 **DATABASE OPERATIONS SUMMARY**

### Insert Operations
- **Primary**: `app/services/document_service.py:_save_document_metadata()`
- **Secondary**: Storage, OCR, and validation services populate specific fields

### Update Operations
- **Status Updates**: Throughout service lifecycle methods
- **OCR Completion**: `app/services/ocr_service.py:complete_ocr_job()`
- **Download Tracking**: `app/api/document_routes.py:download_document()`

### Query Operations
- **Document Retrieval**: `app/services/document_service.py:get_document()`
- **Listing**: `app/services/document_service.py:list_documents()`
- **Search**: Enhanced with new indexed fields

This documentation provides complete coverage of all database fields, their purposes, data types, and the exact code locations where they are populated in your enhanced document service.
