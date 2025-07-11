# Document Service Database Schema Reference

**Version:** 1.0  
**Date:** July 9, 2025  
**Purpose:** Comprehensive database schema reference for InsureCove Document Service  

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Core Tables](#core-tables)
   - [documents](#documents-table)
   - [ocr_jobs](#ocr_jobs-table)
   - [document_access_log](#document_access_log-table)
3. [Relationships](#table-relationships)
4. [Field Usage Guide](#field-usage-guide)
5. [Service Integration](#service-integration)
6. [Query Examples](#query-examples)
7. [Performance Notes](#performance-notes)

---

## 🎯 **Overview**

The Document Service uses a **unified schema** approach with three main tables that handle all document management, OCR processing, and audit trail functionality. The schema is designed for high performance, scalability, and service integration.

### **Design Principles**
- ✅ **Single source of truth** - One unified documents table
- ✅ **Backward compatibility** - Legacy field names preserved
- ✅ **Service-ready** - All modern service requirements supported
- ✅ **Performance optimized** - Comprehensive indexing strategy
- ✅ **Audit complete** - Full activity tracking

---

## 📊 **Core Tables**

### **`documents` Table**
*Primary table for all document storage and metadata*

| Field Name | Type | Nullable | Default | Purpose | Service Usage |
|------------|------|----------|---------|---------|---------------|
| **Primary Key** |
| `id` | UUID | NO | `uuid_generate_v4()` | Unique document identifier | All services |
| **File Identification** |
| `file_name` | TEXT | NO | - | Current filename (may be sanitized) | Document Service |
| `original_filename` | TEXT | NO | - | User's original filename as uploaded | Document Service |
| `file_size` | INTEGER | NO | - | File size in bytes | Storage/Validation |
| `file_type` | TEXT | NO | - | File extension/type | Validation Service |
| `mime_type` | TEXT | YES | Auto-generated | Proper MIME type | Storage Service |
| `file_path` | TEXT | NO | - | Current file path in storage | Storage Service |
| **Storage Backend** |
| `storage_bucket` | TEXT | YES | 'documents' | S3/storage bucket name | Storage Service |
| `storage_key` | TEXT | YES | Auto-generated | Unique storage identifier | Storage Service |
| `file_hash` | TEXT | YES | Auto-generated | SHA-256 for deduplication | Storage Service |
| **Document Classification** |
| `document_type` | TEXT | YES | - | Business document type | Document Service |
| `status` | TEXT | NO | 'active' | Document status | All Services |
| **Ownership & Access** |
| `uploaded_by` | TEXT | YES | - | Username/ID of uploader | Document Service |
| `client_id` | UUID | YES | - | Associated client | Document Service |
| `insurer_id` | UUID | YES | - | Associated insurer | Document Service |
| **Versioning & Caching** |
| `version` | INTEGER | NO | 1 | Document version number | Document Service |
| `etag` | TEXT | YES | Auto-generated | Entity tag for caching | Storage Service |
| **Security & Validation** |
| `security_scan_status` | TEXT | NO | 'pending' | Security scan result | Security Service |
| `virus_scan_status` | TEXT | NO | 'pending' | Virus scan result | Security Service |
| `content_validated` | BOOLEAN | NO | FALSE | Content validation flag | Validation Service |
| **OCR Integration** |
| `ocr_completed` | BOOLEAN | NO | FALSE | OCR processing status | OCR Service |
| `ocr_job_id` | UUID | YES | - | Reference to OCR job | OCR Service |
| `ocr_text` | TEXT | YES | - | Extracted text content | OCR Service |
| `ocr_confidence` | DECIMAL(3,2) | YES | - | OCR confidence score (0-1) | OCR Service |
| `ocr_language` | TEXT | YES | - | Detected language | OCR Service |
| `ocr_page_count` | INTEGER | YES | - | Number of pages processed | OCR Service |
| `ocr_word_count` | INTEGER | YES | - | Word count in extracted text | OCR Service |
| **URL Management** |
| `upload_url` | TEXT | YES | - | Temporary upload URL | Storage Service |
| `download_url` | TEXT | YES | - | Temporary download URL | Storage Service |
| `thumbnail_url` | TEXT | YES | - | Thumbnail/preview URL | Storage Service |
| `url_expires_at` | TIMESTAMPTZ | YES | - | URL expiration time | Storage Service |
| **Usage Tracking** |
| `download_count` | INTEGER | NO | 0 | Number of downloads | Analytics Service |
| `last_accessed` | TIMESTAMPTZ | YES | - | Last access timestamp | Analytics Service |
| **Metadata & Tags** |
| `metadata` | JSONB | NO | '{}' | Flexible document metadata | All Services |
| `tags` | TEXT[] | NO | '{}' | Document tags/categories | Search Service |
| **Timestamps** |
| `upload_date` | TIMESTAMPTZ | YES | NOW() | Upload timestamp (legacy) | Document Service |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Record creation time | All Services |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last update time | All Services |
| `last_modified` | TIMESTAMPTZ | YES | NOW() | Last modification time | Document Service |
| `deleted_at` | TIMESTAMPTZ | YES | - | Soft delete timestamp | All Services |

#### **Status Values**
- `active` - Document is available and ready
- `uploaded` - Recently uploaded, processing pending
- `processing` - Currently being processed
- `completed` - All processing complete
- `failed` - Processing failed
- `deleted` - Marked for deletion

#### **Security Scan Status Values**
- `pending` - Scan not started
- `scanning` - Currently scanning
- `clean` - No threats detected
- `threat` - Security threat found
- `error` - Scan failed

#### **Virus Scan Status Values**
- `pending` - Scan not started
- `scanning` - Currently scanning
- `clean` - No virus detected
- `infected` - Virus found
- `error` - Scan failed

---

### **`ocr_jobs` Table**
*OCR processing job queue and results*

| Field Name | Type | Nullable | Default | Purpose |
|------------|------|----------|---------|---------|
| **Primary Key** |
| `id` | UUID | NO | `uuid_generate_v4()` | Unique job identifier |
| **Job Reference** |
| `document_id` | UUID | NO | - | Reference to documents.id |
| **Job Configuration** |
| `status` | TEXT | NO | 'pending' | Job processing status |
| `priority` | INTEGER | NO | 5 | Job priority (1-10, 1=highest) |
| `language` | TEXT | NO | 'auto' | OCR language hint |
| `engine` | TEXT | NO | 'mistral' | OCR engine to use |
| `options` | JSONB | NO | '{}' | Engine-specific options |
| **Processing Results** |
| `result` | JSONB | YES | - | Full OCR result data |
| `extracted_text` | TEXT | YES | - | Plain text content |
| `confidence_score` | DECIMAL(3,2) | YES | - | Overall confidence (0-1) |
| `page_count` | INTEGER | YES | - | Pages processed |
| `word_count` | INTEGER | YES | - | Words extracted |
| `character_count` | INTEGER | YES | - | Characters extracted |
| **Error Handling** |
| `error_message` | TEXT | YES | - | Error description |
| `retry_count` | INTEGER | NO | 0 | Current retry attempt |
| `max_retries` | INTEGER | NO | 3 | Maximum retry attempts |
| **Timestamps** |
| `processing_started_at` | TIMESTAMPTZ | YES | - | When processing began |
| `processing_completed_at` | TIMESTAMPTZ | YES | - | When processing finished |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Job creation time |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Last update time |

#### **Job Status Values**
- `pending` - Waiting to be processed
- `processing` - Currently being processed
- `completed` - Successfully completed
- `failed` - Processing failed
- `cancelled` - Job was cancelled

#### **OCR Engine Options**
- `mistral` - Mistral AI OCR engine
- `tesseract` - Tesseract open source OCR
- `aws_textract` - AWS Textract service
- `google_vision` - Google Vision API

---

### **`document_access_log` Table**
*Audit trail for all document operations*

| Field Name | Type | Nullable | Default | Purpose |
|------------|------|----------|---------|---------|
| **Primary Key** |
| `id` | UUID | NO | `uuid_generate_v4()` | Unique log entry ID |
| **References** |
| `document_id` | UUID | NO | - | Reference to documents.id |
| `user_id` | TEXT | NO | - | User performing action |
| **Access Details** |
| `access_type` | TEXT | NO | - | Type of operation |
| `access_method` | TEXT | YES | - | How access was made |
| **Request Context** |
| `ip_address` | INET | YES | - | Client IP address |
| `user_agent` | TEXT | YES | - | Client user agent |
| `request_id` | TEXT | YES | - | Request tracing ID |
| `session_id` | TEXT | YES | - | User session ID |
| **Response Details** |
| `success` | BOOLEAN | NO | TRUE | Operation success flag |
| `http_status_code` | INTEGER | YES | - | HTTP response code |
| `error_message` | TEXT | YES | - | Error description |
| `error_code` | TEXT | YES | - | Error code |
| **Performance Metrics** |
| `response_time_ms` | INTEGER | YES | - | Response time in milliseconds |
| `file_size_downloaded` | INTEGER | YES | - | Bytes downloaded |
| **Geolocation** |
| `country_code` | TEXT | YES | - | Country code (optional) |
| `region` | TEXT | YES | - | Region/state (optional) |
| **Timestamp** |
| `accessed_at` | TIMESTAMPTZ | NO | NOW() | When access occurred |

#### **Access Type Values**
- `view` - Document viewed/accessed
- `download` - Document downloaded
- `upload` - Document uploaded
- `update` - Document modified
- `delete` - Document deleted
- `share` - Document shared
- `copy` - Document copied

#### **Access Method Values**
- `api` - REST API access
- `web` - Web interface
- `mobile` - Mobile app
- `bulk` - Bulk operation

---

## 🔗 **Table Relationships**

```
documents (1) ←→ (0..1) ocr_jobs
    ↓
    └─ (1) ←→ (0..*) document_access_log

clients (1) ←→ (0..*) documents
insurers (1) ←→ (0..*) documents
```

### **Foreign Key Constraints**
- `ocr_jobs.document_id` → `documents.id` (CASCADE DELETE)
- `document_access_log.document_id` → `documents.id` (CASCADE DELETE)
- `documents.client_id` → `clients.id`
- `documents.insurer_id` → `insurers.id`

---

## 📖 **Field Usage Guide**

### **For Document Upload**
```typescript
// Required fields for new document
{
  file_name: "policy_document.pdf",
  original_filename: "My Policy Document.pdf", 
  file_size: 2048576,
  file_type: "pdf",
  file_path: "/uploads/temp/xyz123.pdf",
  uploaded_by: "user123",
  client_id: "uuid-client-id"
}

// Auto-generated fields (via triggers)
{
  id: "auto-generated-uuid",
  storage_key: "documents/{id}/{file_name}",
  file_hash: "sha256-hash",
  etag: "timestamp-based",
  mime_type: "application/pdf", // from file_type
  created_at: "2025-07-09T10:00:00Z"
}
```

### **For OCR Processing**
```typescript
// Create OCR job
{
  document_id: "document-uuid",
  priority: 7, // Higher priority
  language: "en",
  engine: "mistral",
  options: {
    enhance_image: true,
    detect_tables: true
  }
}

// Update document after OCR completion
{
  ocr_completed: true,
  ocr_job_id: "job-uuid",
  ocr_text: "Extracted text content...",
  ocr_confidence: 0.95,
  ocr_page_count: 3,
  ocr_word_count: 1250
}
```

### **For Access Logging**
```typescript
// Log document access
{
  document_id: "document-uuid",
  user_id: "user123",
  access_type: "download",
  access_method: "api",
  ip_address: "192.168.1.100",
  user_agent: "Mozilla/5.0...",
  request_id: "req-xyz789",
  success: true,
  http_status_code: 200,
  response_time_ms: 150,
  file_size_downloaded: 2048576
}
```

---

## 🔧 **Service Integration**

### **Document Service**
**Primary Tables:** `documents`  
**Key Fields:** `id`, `file_name`, `file_size`, `status`, `uploaded_by`, `metadata`

```sql
-- Create new document
INSERT INTO documents (file_name, original_filename, file_size, file_type, file_path, uploaded_by, client_id)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- Get user documents
SELECT * FROM documents 
WHERE uploaded_by = $1 AND deleted_at IS NULL 
ORDER BY created_at DESC;
```

### **OCR Service**
**Primary Tables:** `documents`, `ocr_jobs`  
**Key Fields:** `ocr_completed`, `ocr_job_id`, `ocr_text`, `ocr_confidence`

```sql
-- Queue OCR job
INSERT INTO ocr_jobs (document_id, priority, language, engine)
VALUES ($1, $2, $3, $4);

-- Get pending OCR jobs
SELECT * FROM ocr_jobs 
WHERE status = 'pending' AND retry_count < max_retries
ORDER BY priority DESC, created_at ASC;

-- Update document with OCR results
UPDATE documents 
SET ocr_completed = true, ocr_job_id = $1, ocr_text = $2, ocr_confidence = $3
WHERE id = $4;
```

### **Storage Service**
**Primary Tables:** `documents`  
**Key Fields:** `storage_key`, `storage_bucket`, `file_hash`, `etag`

```sql
-- Check for duplicate files
SELECT id FROM documents 
WHERE file_hash = $1 AND uploaded_by = $2 AND deleted_at IS NULL;

-- Update storage information
UPDATE documents 
SET storage_bucket = $1, storage_key = $2, etag = $3
WHERE id = $4;
```

### **Security Service**
**Primary Tables:** `documents`  
**Key Fields:** `security_scan_status`, `virus_scan_status`, `content_validated`

```sql
-- Update security scan results
UPDATE documents 
SET security_scan_status = $1, virus_scan_status = $2, content_validated = $3
WHERE id = $4;

-- Get documents needing security scan
SELECT id, storage_key FROM documents 
WHERE security_scan_status = 'pending' OR virus_scan_status = 'pending';
```

### **Analytics Service**
**Primary Tables:** `document_access_log`, `documents`  
**Key Fields:** `download_count`, `last_accessed`, `access_type`

```sql
-- Log document access
INSERT INTO document_access_log 
(document_id, user_id, access_type, ip_address, response_time_ms)
VALUES ($1, $2, $3, $4, $5);

-- Update document usage stats
UPDATE documents 
SET download_count = download_count + 1, last_accessed = NOW()
WHERE id = $1;
```

---

## 🔍 **Query Examples**

### **Common Document Operations**

```sql
-- Get document with OCR status
SELECT d.*, oj.status as ocr_status, oj.confidence_score
FROM documents d
LEFT JOIN ocr_jobs oj ON d.ocr_job_id = oj.id
WHERE d.id = $1;

-- Search documents by content
SELECT * FROM documents 
WHERE ocr_text ILIKE '%insurance policy%' 
  AND user_id = $1 
  AND deleted_at IS NULL;

-- Get documents by client with access stats
SELECT d.*, 
       COUNT(dal.id) as access_count,
       MAX(dal.accessed_at) as last_access
FROM documents d
LEFT JOIN document_access_log dal ON d.id = dal.document_id
WHERE d.client_id = $1 AND d.deleted_at IS NULL
GROUP BY d.id
ORDER BY d.created_at DESC;
```

### **OCR Management**

```sql
-- Get OCR job queue status
SELECT 
  status,
  COUNT(*) as job_count,
  AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time
FROM ocr_jobs 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Retry failed OCR jobs
UPDATE ocr_jobs 
SET status = 'pending', retry_count = retry_count + 1, updated_at = NOW()
WHERE status = 'failed' AND retry_count < max_retries;
```

### **Analytics & Reporting**

```sql
-- Document usage report
SELECT 
  DATE_TRUNC('day', accessed_at) as access_date,
  access_type,
  COUNT(*) as access_count,
  COUNT(DISTINCT user_id) as unique_users,
  COUNT(DISTINCT document_id) as unique_documents
FROM document_access_log 
WHERE accessed_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', accessed_at), access_type
ORDER BY access_date DESC;

-- Storage usage by user
SELECT 
  user_id,
  COUNT(*) as document_count,
  SUM(file_size) as total_size_bytes,
  ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as total_size_mb
FROM documents 
WHERE deleted_at IS NULL
GROUP BY user_id
ORDER BY total_size_bytes DESC;
```

---

## ⚡ **Performance Notes**

### **Indexes Available**
- Primary keys on all `id` fields
- Foreign key indexes on all reference fields
- Composite indexes for common query patterns
- Text search indexes (GIN) for `ocr_text` and `file_name`
- Metadata search indexes (GIN) for `metadata` and `tags`

### **Query Optimization Tips**

1. **Always filter by `deleted_at IS NULL`** for active documents
2. **Use `user_id` in WHERE clauses** for user-scoped queries
3. **Leverage composite indexes** for multi-field filters
4. **Use LIMIT** for pagination on large result sets
5. **Consider `created_at` for time-based filtering**

### **Maintenance Recommendations**

```sql
-- Clean up expired URLs (run daily)
UPDATE documents 
SET upload_url = NULL, download_url = NULL, thumbnail_url = NULL, url_expires_at = NULL
WHERE url_expires_at < NOW();

-- Archive old access logs (run monthly)
DELETE FROM document_access_log 
WHERE accessed_at < NOW() - INTERVAL '1 year';

-- Update document statistics (run hourly)
ANALYZE documents, ocr_jobs, document_access_log;
```

---

## 🚀 **Getting Started**

1. **Run the schema scripts** in this order:
   ```bash
   20250708001_CREATE_TABLE_DOCUMENTS.sql
   20250709009_CREATE_TABLE_OCR_JOBS.sql
   20250709010_CREATE_TABLE_DOCUMENT_ACCESS_LOG.sql
   20250709011_UPDATE_TABLE_DOCUMENTS_INDEXES.sql
   ```

2. **Verify the installation:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('documents', 'ocr_jobs', 'document_access_log');
   ```

3. **Start using the service** with confidence that all required fields and relationships are properly configured!

---

*This document serves as the authoritative reference for the Document Service database schema. Keep it updated as the schema evolves.*
