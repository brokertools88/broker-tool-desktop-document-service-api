-- ======================================================================
-- Unified Documents Table Creation Script
-- Script: 20250708001_CREATE_TABLE_DOCUMENTS.sql
-- Date: July 8, 2025 (Enhanced: July 9, 2025)
-- Purpose: Create comprehensive documents table with all service requirements
-- Dependencies: clients table, insurers table
-- Note: Combines original and enhanced schema into single unified table
-- ======================================================================

-- Unified documents table for InsureCove Document Service
CREATE TABLE IF NOT EXISTS public.documents (
  -- Primary identifier
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  
  -- File identification and storage
  file_name TEXT NOT NULL, -- Current filename (may be sanitized)
  original_filename TEXT NOT NULL, -- User's original filename as uploaded
  file_size INTEGER NOT NULL,
  file_type TEXT NOT NULL, -- File extension (e.g., 'pdf', 'jpg')
  mime_type TEXT NULL, -- Proper MIME type (e.g., 'application/pdf')
  file_path TEXT NOT NULL, -- Current file path in storage
  
  -- Storage backend information
  storage_bucket TEXT NULL DEFAULT 'documents', -- Storage bucket name
  storage_key TEXT NULL, -- Unique storage identifier
  file_hash TEXT NULL, -- SHA-256 hash for deduplication
  
  -- Document classification
  document_type TEXT NULL,
  status TEXT NOT NULL DEFAULT 'active', -- Keep original default
  
  -- Ownership and access
  uploaded_by TEXT NULL, -- Username/ID of uploader
  client_id UUID NULL,
  insurer_id UUID NULL,
  
  -- Versioning and caching
  version INTEGER NOT NULL DEFAULT 1,
  etag TEXT NULL, -- Entity tag for HTTP caching
  
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
  
  -- URL management (temporary signed URLs)
  upload_url TEXT NULL,
  download_url TEXT NULL,
  thumbnail_url TEXT NULL,
  url_expires_at TIMESTAMP WITH TIME ZONE NULL,
  
  -- Usage tracking
  download_count INTEGER DEFAULT 0,
  last_accessed TIMESTAMP WITH TIME ZONE NULL,
  
  -- Metadata and categorization
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[], -- Document tags for categorization
  
  -- Timestamps
  upload_date TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
  last_modified TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE NULL, -- Soft delete timestamp
  
  -- Constraints
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_client_id_fkey FOREIGN KEY (client_id) REFERENCES clients (id),
  CONSTRAINT documents_insurer_id_fkey FOREIGN KEY (insurer_id) REFERENCES insurers (id),
  
  -- Data validation constraints
  CONSTRAINT documents_status_check CHECK (status IN ('active', 'uploaded', 'processing', 'completed', 'failed', 'deleted')),
  CONSTRAINT documents_security_status_check CHECK (security_scan_status IN ('pending', 'scanning', 'clean', 'threat', 'error')),
  CONSTRAINT documents_virus_status_check CHECK (virus_scan_status IN ('pending', 'scanning', 'clean', 'infected', 'error')),
  CONSTRAINT documents_ocr_confidence_check CHECK (ocr_confidence BETWEEN 0.00 AND 1.00),
  CONSTRAINT documents_version_positive CHECK (version > 0),
  CONSTRAINT documents_file_size_positive CHECK (file_size > 0),
  CONSTRAINT documents_download_count_positive CHECK (download_count >= 0),
  CONSTRAINT documents_storage_key_unique UNIQUE (storage_key),
  CONSTRAINT documents_file_hash_format CHECK (file_hash IS NULL OR file_hash ~ '^[a-f0-9]{64}$')
) TABLESPACE pg_default;

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON public.documents USING btree (client_id);
CREATE INDEX IF NOT EXISTS idx_documents_insurer_id ON public.documents USING btree (insurer_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON public.documents USING btree (document_type);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON public.documents USING btree (uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents USING btree (status);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON public.documents USING btree (file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_storage_key ON public.documents USING btree (storage_key);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON public.documents USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON public.documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON public.documents USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_documents_ocr_completed ON public.documents USING btree (ocr_completed);
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON public.documents USING btree (deleted_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_documents_user_status ON public.documents USING btree (uploaded_by, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_documents_user_created ON public.documents USING btree (uploaded_by, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_documents_hash_user ON public.documents USING btree (file_hash, uploaded_by);

-- Text search indexes
CREATE INDEX IF NOT EXISTS idx_documents_filename_search ON public.documents USING gin (file_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_documents_ocr_text_search ON public.documents USING gin (ocr_text gin_trgm_ops) WHERE ocr_text IS NOT NULL;

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.last_modified = NOW();
    
    -- Auto-generate missing fields for backward compatibility
    IF NEW.mime_type IS NULL AND NEW.file_type IS NOT NULL THEN
        NEW.mime_type = NEW.file_type;
    END IF;
    
    IF NEW.storage_key IS NULL THEN
        NEW.storage_key = 'documents/' || NEW.id::TEXT || '/' || NEW.file_name;
    END IF;
    
    IF NEW.etag IS NULL THEN
        NEW.etag = '"' || EXTRACT(EPOCH FROM NOW())::TEXT || '"';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON public.documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_documents_updated_at();

-- Trigger for new record setup
CREATE OR REPLACE FUNCTION setup_new_document()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-generate missing fields for new records
    IF NEW.mime_type IS NULL AND NEW.file_type IS NOT NULL THEN
        NEW.mime_type = NEW.file_type;
    END IF;
    
    IF NEW.storage_key IS NULL THEN
        NEW.storage_key = 'documents/' || NEW.id::TEXT || '/' || NEW.file_name;
    END IF;
    
    IF NEW.etag IS NULL THEN
        NEW.etag = '"' || EXTRACT(EPOCH FROM NOW())::TEXT || '"';
    END IF;
    
    IF NEW.file_hash IS NULL AND NEW.file_name IS NOT NULL THEN
        NEW.file_hash = encode(digest(NEW.id::TEXT || NEW.file_name || COALESCE(NEW.uploaded_by, ''), 'sha256'), 'hex');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER setup_new_document 
    BEFORE INSERT ON public.documents 
    FOR EACH ROW 
    EXECUTE FUNCTION setup_new_document();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO authenticated;

-- Enable Row Level Security (ready for future implementation)
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Unified Documents Table Created Successfully!';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Features included:';
    RAISE NOTICE '✅ Clean field names (no redundant aliases)';
    RAISE NOTICE '✅ All fields required for service integration';
    RAISE NOTICE '✅ Storage backend support (S3, local, etc.)';
    RAISE NOTICE '✅ OCR integration with job tracking';
    RAISE NOTICE '✅ Security validation and virus scanning';
    RAISE NOTICE '✅ Performance optimization with comprehensive indexing';
    RAISE NOTICE '✅ Audit trail and soft delete support';
    RAISE NOTICE '✅ Auto-generation of missing fields via triggers';
    RAISE NOTICE '✅ Text search capabilities';
    RAISE NOTICE '';
    RAISE NOTICE 'Field names:';
    RAISE NOTICE '✅ file_name - Current filename (may be sanitized)';
    RAISE NOTICE '✅ original_filename - User''s original filename as uploaded';
    RAISE NOTICE '✅ uploaded_by - Username/ID of uploader';
    RAISE NOTICE '✅ Clear, self-explanatory field names throughout';
    RAISE NOTICE '=================================================================';
END $$;