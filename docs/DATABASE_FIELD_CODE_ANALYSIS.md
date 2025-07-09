# Database Field Population Code Analysis

## 📋 **Code Locations for Database Field Population**

This document maps each database field to the specific code locations where they are populated or will be populated in the InsureCove Document Service.

---

## 🔍 **PRIMARY DOCUMENT CREATION FLOW**

### **Main Entry Point: `upload_document()`**
**File**: `app/services/document_service.py`  
**Lines**: 85-195  
**Method**: `async def upload_document(...)`

This is the primary method where most database fields are populated during document upload.

---

## 📊 **FIELD POPULATION MAPPING**

### **CORE IDENTITY FIELDS**

#### `id` (UUID)
```python
# File: app/services/document_service.py, Line: ~85
document_id = str(uuid.uuid4())
```
**Population**: Auto-generated UUID in `upload_document()` method
**Status**: ✅ Implemented

#### `filename` & `original_filename`
```python
# File: app/services/document_service.py, Line: ~676-677
document_record = {
    "filename": filename,           # Sanitized filename
    "original_filename": filename,  # Original as uploaded
    # ...
}
```
**Population**: Direct from upload parameters
**Status**: ✅ Implemented

#### `file_size`
```python
# File: app/services/document_service.py, Line: ~681
"file_size": file_size,  # len(file_content) passed from upload

# Also in storage service:
# File: app/services/storage_service.py, Line: ~120
"size": len(file_content),
```
**Population**: Calculated from `len(file_content)`
**Status**: ✅ Implemented

#### `file_type` & `mime_type`
```python
# File: app/services/validation_service.py, Line: ~285-320
def detect_mime_type(self, file_content: bytes) -> str:
    """Detect MIME type from file content"""
    try:
        import magic
        return magic.from_buffer(file_content, mime=True)
    except ImportError:
        # Fallback implementation
        return "application/octet-stream"

# Population in document service:
# File: app/services/document_service.py, Line: ~682
"content_type": content_type or "application/octet-stream",
```
**Population**: MIME type detection in ValidationService
**Status**: ✅ Implemented (ValidationService), ⚠️ TODO in DocumentService

---

### **STORAGE BACKEND FIELDS**

#### `storage_path`, `storage_bucket`, `storage_key`
```python
# File: app/services/document_service.py, Line: ~692-696
if storage_result:
    document_record.update({
        "storage_path": storage_result.get("file_path"),
        "storage_bucket": storage_result.get("bucket"),
        "storage_key": storage_result.get("key")
    })

# Storage service returns these values:
# File: app/services/storage_service.py, Line: ~115-140
document_metadata = {
    "id": file_key,                    # This becomes storage_key
    "filename": filename,
    "storage_url": storage_url,        # This becomes storage_path
    # ...
}
```
**Population**: StorageService.upload_file() returns storage metadata
**Status**: ✅ Implemented in StorageService, ✅ Used in DocumentService

#### `file_hash`
```python
# File: app/utils/file_utils.py (Referenced in services)
class FileProcessor:
    def calculate_hash(self, file_content: bytes) -> str:
        """Calculate file content hash"""
        return hashlib.sha256(file_content).hexdigest()

# File: app/services/storage_service.py, Line: ~95-105
file_hash = await self._calculate_file_hash(file_content)

# Storage service populates:
# File: app/services/storage_service.py, Line: ~123
"file_hash": file_hash,
```
**Population**: FileProcessor.calculate_hash() in StorageService
**Status**: ✅ Implemented

---

### **SERVICE COMPATIBILITY FIELDS**

#### `user_id`
```python
# File: app/services/document_service.py, Line: ~679
"user_id": user_id,  # From upload_document() parameter

# Original call:
# File: app/services/document_service.py, Line: ~85
async def upload_document(self, ..., user_id: str, ...):
```
**Population**: Direct from authentication context
**Status**: ✅ Implemented

---

### **VERSIONING AND CACHING FIELDS**

#### `version`
```python
# File: app/services/document_service.py, Line: ~687
"version": 1,  # Default for new documents

# For updates (TODO implementation):
# version = existing_document.version + 1
```
**Population**: Default 1 for new documents, incremented on updates
**Status**: ✅ Initial version, ⚠️ TODO increment logic

#### `etag`
```python
# File: app/services/document_service.py, Line: ~688
"etag": self.token_generator.generate_api_key(16)

# File: app/utils/crypto_utils.py (TokenGenerator class)
class TokenGenerator:
    def generate_api_key(self, length: int = 32) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(length)
```
**Population**: TokenGenerator.generate_api_key() in DocumentService
**Status**: ✅ Implemented

---

### **SECURITY AND VALIDATION FIELDS**

#### `security_scan_status`, `virus_scan_status`, `content_validated`
```python
# File: app/services/validation_service.py, Line: ~175-200
async def validate_file_security(self, file_content: bytes) -> Dict[str, Any]:
    """Comprehensive security validation"""
    scan_result = {
        "is_safe": True,
        "threats_detected": [],
        "security_score": 1.0,
        "scan_status": "clean"  # This becomes security_scan_status
    }

# File: app/services/validation_service.py, Line: ~580-620
async def scan_for_malware(self, file_content: bytes) -> Dict[str, Any]:
    """Scan file content for malware and threats"""
    return {
        "is_clean": True,
        "virus_detected": False,
        "scan_status": "clean",  # This becomes virus_scan_status
        "threats": []
    }

# File: app/services/validation_service.py, Line: ~160-175
async def validate_file_content(self, file_content: bytes, ...) -> Dict[str, Any]:
    """Comprehensive file content validation"""
    # Returns content_validated boolean
```
**Population**: ValidationService methods during upload validation
**Status**: ✅ Implemented in ValidationService, ⚠️ TODO integration in DocumentService

---

### **OCR INTEGRATION FIELDS**

#### `ocr_completed`, `ocr_job_id`, `ocr_text`, `ocr_confidence`
```python
# File: app/services/document_service.py, Line: ~148-156
if auto_ocr and self.ocr:
    try:
        ocr_result = await self.ocr.extract_text(file_content, filename)
        ocr_job_id = ocr_result.get("job_id", str(uuid.uuid4()))
    except Exception as ocr_error:
        self.logger.warning(f"OCR processing failed...")

# File: app/services/ocr_service.py, Line: ~85-150
async def extract_text(self, file_content: bytes, filename: str) -> Dict[str, Any]:
    """Extract text content using Mistral OCR"""
    return {
        "job_id": str(uuid.uuid4()),
        "text_content": extracted_text,      # Becomes ocr_text
        "confidence_score": confidence,      # Becomes ocr_confidence
        "detected_language": language,       # Becomes ocr_language
        "page_count": page_count,           # Becomes ocr_page_count
        "word_count": len(text.split()),    # Becomes ocr_word_count
        "status": "completed"               # Used for ocr_completed
    }
```
**Population**: OCRService.extract_text() during upload process
**Status**: ✅ Implemented in OCRService, ✅ Partially integrated in DocumentService

---

### **URL MANAGEMENT FIELDS**

#### `upload_url`, `download_url`, `url_expires_at`
```python
# File: app/services/document_service.py, Line: ~158-165
upload_url = None
download_url = None

if storage_result:
    upload_url = storage_result.get("upload_url")
    download_url = await self._generate_signed_download_url(document_id, user_id)

# File: app/services/document_service.py, Line: ~705-715
async def _generate_signed_download_url(self, document_id: str, user_id: str, expires_in: int = 3600):
    """Generate signed download URL for document"""
    # TODO: Implement proper URL generation
    return f"/api/documents/{document_id}/download?expires={expires_in}"
```
**Population**: URL generation methods in DocumentService and StorageService
**Status**: ⚠️ TODO proper implementation

---

### **USAGE TRACKING FIELDS**

#### `download_count`, `last_accessed`
```python
# File: app/services/document_service.py, Line: ~355+ (get_document method)
self._stats["total_downloads"] += 1  # Updates internal stats

# File: app/api/document_routes.py (Future implementation)
@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, ...):
    # Update download_count and last_accessed here
    await update_access_tracking(document_id, "download")
```
**Population**: Download tracking in API routes
**Status**: ⚠️ TODO implementation in API routes

#### `tags`
```python
# File: app/services/document_service.py, Line: ~683
"tags": tags,  # From upload_document() parameter

# From upload call:
# File: app/services/document_service.py, Line: ~85
async def upload_document(self, ..., tags: Optional[List[str]] = None, ...):
    # tags or [] used in document creation
```
**Population**: Direct from user input or business logic
**Status**: ✅ Implemented

---

## 🔄 **DATABASE SAVE OPERATIONS**

### **Primary Save Method**
```python
# File: app/services/document_service.py, Line: ~698-703
async def _save_document_metadata(self, ...):
    """Save document metadata to database"""
    # TODO: Implement database save
    if self.db:
        # await self.db.save_document(document_record)
        pass
    return document_record
```
**Status**: ⚠️ TODO - Database integration pending

### **Update Operations**
```python
# File: app/services/document_service.py, Line: ~497
# updated_document = await self._update_document_record(
#     document_id, validated_updates
# )
```
**Status**: ⚠️ TODO - Update methods pending

---

## 📈 **IMPLEMENTATION STATUS SUMMARY**

### ✅ **Fully Implemented Fields**
- `id`, `filename`, `original_filename`, `file_size`, `user_id`
- `version`, `etag`, `tags`, `status`
- `created_at`, `updated_at` (via database defaults/triggers)
- `file_hash` (in StorageService)
- OCR fields structure (in OCRService)

### ⚠️ **Partially Implemented / TODO Fields**
- **Storage fields**: `storage_path`, `storage_bucket`, `storage_key` (implemented in services, needs DB integration)
- **Security fields**: `security_scan_status`, `virus_scan_status`, `content_validated` (validation implemented, needs DB integration)
- **OCR integration**: Needs connection between OCRService results and database fields
- **URL fields**: Need proper signed URL implementation
- **Tracking fields**: `download_count`, `last_accessed` (needs API route integration)

### 🚀 **Next Steps for Full Implementation**

1. **Database Integration**: Implement actual database save/update operations
2. **Service Integration**: Connect validation and OCR results to database fields
3. **API Integration**: Add tracking fields update in API routes
4. **URL Generation**: Implement proper signed URL generation with expiration
5. **Testing**: Validate all field population flows

---

## 💡 **Key Implementation Notes**

1. **Field Population Flow**: `upload_document()` → `_save_document_metadata()` → Database
2. **Service Dependencies**: DocumentService orchestrates StorageService, ValidationService, and OCRService
3. **Database Operations**: Currently stubbed with TODO comments, ready for implementation
4. **Error Handling**: Comprehensive error handling already in place
5. **Logging**: Structured logging for all operations implemented

The codebase is well-structured and ready for database integration. Most field population logic is implemented; what's needed is connecting the service results to actual database save operations.
