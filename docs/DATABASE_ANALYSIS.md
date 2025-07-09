# Database Design Analysis: Supabase Documents Table

## Current Database Schema Analysis

### 📋 Existing Schema (`CREATE_TABLE_DOCUMENTS_20250708001.sql`)

The current `documents` table has these fields:
```sql
- id (uuid, primary key)
- file_name (text)
- original_file_name (text) 
- file_size (integer)
- file_type (text)
- file_path (text)
- document_type (text)
- client_id (uuid, foreign key)
- insurer_id (uuid, foreign key)
- uploaded_by (text)
- upload_date (timestamp)
- last_modified (timestamp)
- metadata (jsonb)
- status (text, default 'active')
- created_at (timestamp)
- updated_at (timestamp)
```

## 🚨 **CRITICAL GAPS IDENTIFIED**

### Missing Fields Required by Services

Comparing the database schema with the implemented services, several critical fields are missing:

#### 1. **Storage and File Management**
- ❌ `storage_path` - Path in S3/storage backend
- ❌ `storage_bucket` - Storage bucket name
- ❌ `storage_key` - Unique storage key
- ❌ `file_hash` - SHA-256 hash for deduplication
- ❌ `mime_type` - Proper MIME type field
- ❌ `etag` - Entity tag for caching

#### 2. **Security and Validation**
- ❌ `content_type` - Validated content type
- ❌ `security_scan_status` - File security validation status
- ❌ `virus_scan_status` - Virus scanning results

#### 3. **OCR Integration**
- ❌ `ocr_completed` - OCR processing status
- ❌ `ocr_job_id` - Reference to OCR job
- ❌ `ocr_text` - Extracted text content
- ❌ `ocr_confidence` - OCR confidence score
- ❌ `ocr_language` - Detected language

#### 4. **API and Service Fields**
- ❌ `user_id` - Service uses user_id instead of uploaded_by
- ❌ `version` - Document versioning
- ❌ `tags` - Document tagging (could use JSONB array)
- ❌ `download_count` - Usage tracking
- ❌ `last_accessed` - Access tracking

#### 5. **URL Management**
- ❌ `upload_url` - Signed upload URL (temporary)
- ❌ `download_url` - Signed download URL (temporary) 
- ❌ `thumbnail_url` - Thumbnail reference

## 🔧 **RECOMMENDED DATABASE IMPROVEMENTS**

### Enhanced Documents Table Schema

```sql
-- Enhanced documents table for InsureCove Document Service
CREATE TABLE public.documents (
  -- Primary identifier
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  
  -- File identification
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  file_type TEXT NOT NULL, -- Keep for backward compatibility
  mime_type TEXT NOT NULL, -- Proper MIME type
  
  -- Storage backend information
  storage_path TEXT NOT NULL,
  storage_bucket TEXT NOT NULL,
  storage_key TEXT NOT NULL UNIQUE,
  file_hash TEXT NOT NULL, -- SHA-256 for deduplication
  
  -- Document classification
  document_type TEXT NULL,
  status TEXT NOT NULL DEFAULT 'uploaded',
  
  -- Ownership and access
  user_id TEXT NOT NULL, -- Primary user identifier
  client_id UUID NULL,
  insurer_id UUID NULL,
  uploaded_by TEXT NULL, -- Keep for audit trail
  
  -- Versioning and caching
  version INTEGER NOT NULL DEFAULT 1,
  etag TEXT NOT NULL,
  
  -- Security and validation
  security_scan_status TEXT DEFAULT 'pending',
  virus_scan_status TEXT DEFAULT 'pending',
  content_validated BOOLEAN DEFAULT FALSE,
  
  -- OCR integration
  ocr_completed BOOLEAN DEFAULT FALSE,
  ocr_job_id UUID NULL,
  ocr_text TEXT NULL,
  ocr_confidence DECIMAL(3,2) NULL,
  ocr_language TEXT NULL,
  ocr_page_count INTEGER NULL,
  ocr_word_count INTEGER NULL,
  
  -- URL management (temporary fields)
  upload_url TEXT NULL,
  download_url TEXT NULL,
  thumbnail_url TEXT NULL,
  url_expires_at TIMESTAMP WITH TIME ZONE NULL,
  
  -- Usage tracking
  download_count INTEGER DEFAULT 0,
  last_accessed TIMESTAMP WITH TIME ZONE NULL,
  
  -- Metadata and tags
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[], -- Array for better querying
  
  -- Timestamps
  upload_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_client_id_fkey FOREIGN KEY (client_id) REFERENCES clients (id),
  CONSTRAINT documents_insurer_id_fkey FOREIGN KEY (insurer_id) REFERENCES insurers (id),
  CONSTRAINT documents_status_check CHECK (status IN ('uploaded', 'processing', 'completed', 'failed', 'deleted')),
  CONSTRAINT documents_security_status_check CHECK (security_scan_status IN ('pending', 'scanning', 'clean', 'threat', 'error')),
  CONSTRAINT documents_virus_status_check CHECK (virus_scan_status IN ('pending', 'scanning', 'clean', 'infected', 'error'))
) TABLESPACE pg_default;

-- Enhanced indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON public.documents USING btree (client_id);
CREATE INDEX IF NOT EXISTS idx_documents_insurer_id ON public.documents USING btree (insurer_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON public.documents USING btree (document_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents USING btree (status);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON public.documents USING btree (file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_storage_key ON public.documents USING btree (storage_key);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON public.documents USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON public.documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON public.documents USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_documents_ocr_completed ON public.documents USING btree (ocr_completed);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON public.documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### Additional Supporting Tables

```sql
-- OCR Jobs table for tracking OCR processing
CREATE TABLE public.ocr_jobs (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  document_id UUID NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER DEFAULT 5,
  language TEXT DEFAULT 'auto',
  options JSONB DEFAULT '{}'::jsonb,
  result JSONB NULL,
  error_message TEXT NULL,
  processing_started_at TIMESTAMP WITH TIME ZONE NULL,
  processing_completed_at TIMESTAMP WITH TIME ZONE NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  CONSTRAINT ocr_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT ocr_jobs_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
  CONSTRAINT ocr_jobs_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

-- Document access log for audit trail
CREATE TABLE public.document_access_log (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  document_id UUID NOT NULL,
  user_id TEXT NOT NULL,
  access_type TEXT NOT NULL, -- 'view', 'download', 'update', 'delete'
  ip_address INET NULL,
  user_agent TEXT NULL,
  success BOOLEAN NOT NULL DEFAULT TRUE,
  error_message TEXT NULL,
  accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  CONSTRAINT document_access_log_pkey PRIMARY KEY (id),
  CONSTRAINT document_access_log_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
);

-- Indexes for supporting tables
CREATE INDEX idx_ocr_jobs_document_id ON public.ocr_jobs (document_id);
CREATE INDEX idx_ocr_jobs_status ON public.ocr_jobs (status);
CREATE INDEX idx_document_access_log_document_id ON public.document_access_log (document_id);
CREATE INDEX idx_document_access_log_user_id ON public.document_access_log (user_id);
CREATE INDEX idx_document_access_log_accessed_at ON public.document_access_log (accessed_at);
```

## 🔄 **SERVICE INTEGRATION ALIGNMENT**

### Database Operations Needed in Services

1. **Document Service** requires:
   - ✅ Insert document records with all metadata
   - ✅ Update document status and OCR information
   - ✅ Query by user_id, hash, and various filters
   - ✅ Support for batch operations

2. **Storage Service** requires:
   - ✅ File deduplication by hash
   - ✅ Storage path and key management
   - ✅ File validation status tracking

3. **OCR Service** requires:
   - ✅ OCR job tracking and status updates
   - ✅ Results storage and retrieval
   - ✅ Queue management

4. **Validation Service** requires:
   - ✅ Security scan status tracking
   - ✅ Content validation results

## 📋 **MIGRATION RECOMMENDATIONS**

### Phase 1: Critical Fields (Immediate)
1. Add storage-related fields (`storage_path`, `storage_key`, `file_hash`)
2. Add `user_id` field for service compatibility
3. Add `mime_type` for proper content type handling
4. Add `ocr_completed` and `ocr_job_id` for OCR integration

### Phase 2: Enhanced Features
1. Add OCR-related fields (`ocr_text`, `ocr_confidence`, etc.)
2. Add security scanning fields
3. Add versioning and caching fields (`version`, `etag`)
4. Add usage tracking fields

### Phase 3: Supporting Tables
1. Create `ocr_jobs` table
2. Create `document_access_log` table
3. Add necessary indexes and triggers

## ✅ **CONCLUSION**

**Current Status**: The database schema is **partially compatible** but missing critical fields needed by the implemented services.

**Action Required**: Database schema needs enhancement to fully support the implemented service functionality, especially for:
- Storage backend integration
- OCR processing
- File deduplication
- Security validation
- Performance optimization

The enhanced schema will provide full compatibility with the implemented services and enable all features to work correctly.
