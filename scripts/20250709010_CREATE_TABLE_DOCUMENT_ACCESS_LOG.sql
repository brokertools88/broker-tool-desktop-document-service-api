-- ======================================================================
-- Document Access Log Table Creation Script
-- Script: 20250709010_CREATE_TABLE_DOCUMENT_ACCESS_LOG.sql
-- Date: July 9, 2025
-- Purpose: Create table for document access audit trail
-- Dependencies: documents table
-- References: DATABASE_ANALYSIS.md
-- ======================================================================

-- Document access log for audit trail and analytics
CREATE TABLE IF NOT EXISTS public.document_access_log (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  document_id UUID NOT NULL,
  user_id TEXT NOT NULL,
  
  -- Access details
  access_type TEXT NOT NULL, -- 'view', 'download', 'update', 'delete', 'upload'
  access_method TEXT NULL, -- 'api', 'web', 'mobile', 'bulk'
  
  -- Request metadata
  ip_address INET NULL,
  user_agent TEXT NULL,
  request_id TEXT NULL, -- For tracing requests across services
  session_id TEXT NULL,
  
  -- Response details
  success BOOLEAN NOT NULL DEFAULT TRUE,
  http_status_code INTEGER NULL,
  error_message TEXT NULL,
  error_code TEXT NULL,
  
  -- Performance metrics
  response_time_ms INTEGER NULL,
  file_size_downloaded INTEGER NULL, -- For download operations
  
  -- Geolocation (optional)
  country_code TEXT NULL,
  region TEXT NULL,
  
  -- Timestamps
  accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT document_access_log_pkey PRIMARY KEY (id),
  CONSTRAINT document_access_log_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
  CONSTRAINT document_access_log_access_type_check CHECK (access_type IN ('view', 'download', 'upload', 'update', 'delete', 'share', 'copy')),
  CONSTRAINT document_access_log_http_status_check CHECK (http_status_code BETWEEN 100 AND 599)
);

-- Indexes for performance and analytics
CREATE INDEX IF NOT EXISTS idx_document_access_log_document_id ON public.document_access_log USING btree (document_id);
CREATE INDEX IF NOT EXISTS idx_document_access_log_user_id ON public.document_access_log USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_document_access_log_accessed_at ON public.document_access_log USING btree (accessed_at);
CREATE INDEX IF NOT EXISTS idx_document_access_log_access_type ON public.document_access_log USING btree (access_type);
CREATE INDEX IF NOT EXISTS idx_document_access_log_success ON public.document_access_log USING btree (success);
CREATE INDEX IF NOT EXISTS idx_document_access_log_ip_address ON public.document_access_log USING btree (ip_address);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_document_access_log_user_date ON public.document_access_log USING btree (user_id, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_access_log_doc_date ON public.document_access_log USING btree (document_id, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_access_log_type_date ON public.document_access_log USING btree (access_type, accessed_at DESC);

-- Partial indexes for failed requests (for monitoring)
CREATE INDEX IF NOT EXISTS idx_document_access_log_errors ON public.document_access_log USING btree (accessed_at DESC, error_code) 
    WHERE success = FALSE;

-- Partial indexes for downloads (for analytics)
CREATE INDEX IF NOT EXISTS idx_document_access_log_downloads ON public.document_access_log USING btree (document_id, accessed_at DESC) 
    WHERE access_type = 'download' AND success = TRUE;

-- Function to automatically update document last_accessed timestamp
CREATE OR REPLACE FUNCTION update_document_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the document's last_accessed timestamp for successful view/download operations
    IF NEW.success = TRUE AND NEW.access_type IN ('view', 'download') THEN
        UPDATE documents_enhanced 
        SET last_accessed = NEW.accessed_at,
            download_count = CASE 
                WHEN NEW.access_type = 'download' THEN download_count + 1 
                ELSE download_count 
            END
        WHERE id = NEW.document_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update document access statistics
CREATE TRIGGER update_document_access_stats 
    AFTER INSERT ON public.document_access_log 
    FOR EACH ROW 
    EXECUTE FUNCTION update_document_last_accessed();

-- Grant permissions
GRANT SELECT, INSERT ON public.document_access_log TO authenticated;
GRANT UPDATE, DELETE ON public.document_access_log TO service_role;

-- Enable Row Level Security
ALTER TABLE public.document_access_log ENABLE ROW LEVEL SECURITY;

-- Create a view for common access analytics
CREATE OR REPLACE VIEW document_access_analytics AS
SELECT 
    d.id as document_id,
    d.filename,
    d.user_id as owner_id,
    COUNT(*) as total_accesses,
    COUNT(*) FILTER (WHERE dal.access_type = 'view') as view_count,
    COUNT(*) FILTER (WHERE dal.access_type = 'download') as download_count,
    COUNT(DISTINCT dal.user_id) as unique_users,
    MAX(dal.accessed_at) as last_accessed,
    COUNT(*) FILTER (WHERE dal.success = FALSE) as error_count
FROM documents_enhanced d
LEFT JOIN document_access_log dal ON d.id = dal.document_id
WHERE d.deleted_at IS NULL
GROUP BY d.id, d.filename, d.user_id;

-- Grant access to the view
GRANT SELECT ON document_access_analytics TO authenticated;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Document Access Log table created successfully';
    RAISE NOTICE 'Features included:';
    RAISE NOTICE '- Comprehensive access audit trail';
    RAISE NOTICE '- Performance and error tracking';
    RAISE NOTICE '- Automatic document statistics updates';
    RAISE NOTICE '- Analytics view for reporting';
    RAISE NOTICE '- Geolocation support for security monitoring';
END $$;
