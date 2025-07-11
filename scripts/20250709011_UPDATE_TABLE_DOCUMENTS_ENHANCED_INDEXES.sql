-- ======================================================================
-- Enhanced Documents Tables - Additional Indexes and Constraints
-- Script: 20250709011_UPDATE_TABLE_DOCUMENTS_INDEXES.sql
-- Date: July 9, 2025
-- Purpose: Add additional performance indexes and constraints for unified documents table
-- Dependencies: documents, ocr_jobs, document_access_log tables
-- ======================================================================

-- Additional performance indexes for documents table (unified schema)

-- Text search indexes for content search
CREATE INDEX IF NOT EXISTS idx_documents_filename_trgm ON public.documents 
    USING gin (file_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_documents_ocr_text_trgm ON public.documents 
    USING gin (ocr_text gin_trgm_ops) 
    WHERE ocr_text IS NOT NULL;

-- Indexes for file management and deduplication
CREATE INDEX IF NOT EXISTS idx_documents_file_type_size ON public.documents 
    USING btree (file_type, file_size);

CREATE INDEX IF NOT EXISTS idx_documents_storage_bucket ON public.documents 
    USING btree (storage_bucket);

-- Indexes for OCR workflow
CREATE INDEX IF NOT EXISTS idx_documents_ocr_status ON public.documents 
    USING btree (ocr_completed, ocr_job_id) 
    WHERE ocr_job_id IS NOT NULL;

-- Indexes for security and validation workflow
CREATE INDEX IF NOT EXISTS idx_documents_security_status ON public.documents 
    USING btree (security_scan_status, virus_scan_status);

-- Indexes for URL management and expiration
CREATE INDEX IF NOT EXISTS idx_documents_url_expires ON public.documents 
    USING btree (url_expires_at) 
    WHERE url_expires_at IS NOT NULL;

-- Performance indexes for common service queries

-- User document listing with filters
CREATE INDEX IF NOT EXISTS idx_documents_user_type_status ON public.documents 
    USING btree (user_id, document_type, status, created_at DESC) 
    WHERE deleted_at IS NULL;

-- Client/Insurer document queries
CREATE INDEX IF NOT EXISTS idx_documents_client_status ON public.documents 
    USING btree (client_id, status, created_at DESC) 
    WHERE client_id IS NOT NULL AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_documents_insurer_status ON public.documents 
    USING btree (insurer_id, status, created_at DESC) 
    WHERE insurer_id IS NOT NULL AND deleted_at IS NULL;

-- Storage and cleanup queries
CREATE INDEX IF NOT EXISTS idx_documents_storage_cleanup ON public.documents 
    USING btree (status, last_accessed) 
    WHERE status IN ('failed', 'deleted') OR last_accessed < NOW() - INTERVAL '90 days';

-- ============================================================================
-- Additional constraints and validations
-- ============================================================================

-- Add constraint for storage key format validation
ALTER TABLE public.documents 
ADD CONSTRAINT documents_storage_key_format 
CHECK (storage_key ~ '^[a-zA-Z0-9/_-]+$');

-- Add constraint for file hash format (SHA-256)
ALTER TABLE public.documents 
ADD CONSTRAINT documents_file_hash_format 
CHECK (file_hash ~ '^[a-f0-9]{64}$');

-- Add constraint for version sequencing
ALTER TABLE public.documents 
ADD CONSTRAINT documents_version_positive 
CHECK (version > 0);

-- Add constraint for file size limits (500MB max)
ALTER TABLE public.documents 
ADD CONSTRAINT documents_file_size_limit 
CHECK (file_size > 0 AND file_size <= 524288000);

-- Add constraint for download count
ALTER TABLE public.documents 
ADD CONSTRAINT documents_download_count_positive 
CHECK (download_count >= 0);

-- ============================================================================
-- Performance improvements for OCR Jobs table
-- ============================================================================

-- Index for job queue processing optimization
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_queue_processing ON public.ocr_jobs 
    USING btree (status, priority, created_at, retry_count) 
    WHERE status = 'pending' AND retry_count < max_retries;

-- Index for job monitoring and cleanup
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_cleanup ON public.ocr_jobs 
    USING btree (status, processing_completed_at) 
    WHERE status IN ('completed', 'failed', 'cancelled');

-- ============================================================================
-- Statistics and maintenance functions
-- ============================================================================

-- Function to calculate storage usage by user
CREATE OR REPLACE FUNCTION get_user_storage_usage(p_user_id TEXT)
RETURNS TABLE (
    total_files INTEGER,
    total_size_bytes BIGINT,
    total_size_mb DECIMAL(10,2),
    completed_files INTEGER,
    processing_files INTEGER,
    failed_files INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_files,
        COALESCE(SUM(file_size), 0)::BIGINT as total_size_bytes,
        ROUND(COALESCE(SUM(file_size), 0) / 1024.0 / 1024.0, 2) as total_size_mb,
        COUNT(*) FILTER (WHERE status = 'completed')::INTEGER as completed_files,
        COUNT(*) FILTER (WHERE status = 'processing')::INTEGER as processing_files,
        COUNT(*) FILTER (WHERE status = 'failed')::INTEGER as failed_files
    FROM documents 
    WHERE user_id = p_user_id AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending OCR jobs queue status
CREATE OR REPLACE FUNCTION get_ocr_queue_status()
RETURNS TABLE (
    pending_jobs INTEGER,
    processing_jobs INTEGER,
    avg_processing_time_minutes DECIMAL(10,2),
    oldest_pending_age_minutes INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) FILTER (WHERE status = 'pending')::INTEGER as pending_jobs,
        COUNT(*) FILTER (WHERE status = 'processing')::INTEGER as processing_jobs,
        ROUND(AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at)) / 60.0) 
              FILTER (WHERE status = 'completed' AND processing_started_at IS NOT NULL AND processing_completed_at IS NOT NULL), 2) as avg_processing_time_minutes,
        ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(created_at) FILTER (WHERE status = 'pending'))) / 60.0)::INTEGER as oldest_pending_age_minutes
    FROM ocr_jobs;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_user_storage_usage(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_ocr_queue_status() TO authenticated;

-- ============================================================================
-- Cleanup and maintenance procedures
-- ============================================================================

-- Procedure to clean up expired temporary URLs
CREATE OR REPLACE FUNCTION cleanup_expired_urls()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE documents 
    SET 
        upload_url = NULL,
        download_url = NULL,
        thumbnail_url = NULL,
        url_expires_at = NULL
    WHERE url_expires_at IS NOT NULL AND url_expires_at < NOW();
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned up % expired URLs', updated_count;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION cleanup_expired_urls() TO service_role;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Enhanced Documents Tables indexes and constraints completed';
    RAISE NOTICE 'Added features:';
    RAISE NOTICE '- Text search indexes for filename and OCR content';
    RAISE NOTICE '- Performance indexes for all common query patterns';
    RAISE NOTICE '- Data validation constraints';
    RAISE NOTICE '- Storage usage calculation functions';
    RAISE NOTICE '- OCR queue monitoring functions';
    RAISE NOTICE '- Cleanup procedures for maintenance';
END $$;
