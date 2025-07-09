-- ======================================================================
-- Add Indexes for Extracted Tables Table
-- Script: UPDATE_TABLE_extracted_tables_20250709_008.sql
-- Date: July 9, 2025
-- Purpose: Create performance indexes for extracted_tables table
-- Dependencies: extracted_tables table must exist
-- ======================================================================

-- Performance indexes for Extracted Tables
CREATE INDEX IF NOT EXISTS idx_extracted_tables_document_id ON public.extracted_tables (document_id);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_ocr_result_id ON public.extracted_tables (ocr_result_id);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_chunk_id ON public.extracted_tables (chunk_id);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_page_number ON public.extracted_tables (page_number);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_table_type ON public.extracted_tables (table_type);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_table_index ON public.extracted_tables (document_id, table_index);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_has_headers ON public.extracted_tables (has_headers);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_extraction_method ON public.extracted_tables (extraction_method);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_needs_verification ON public.extracted_tables (needs_verification);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_confidence ON public.extracted_tables (confidence_score);

-- JSONB indexes for structured data
CREATE INDEX IF NOT EXISTS idx_extracted_tables_table_data ON public.extracted_tables 
USING gin (table_data);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_headers ON public.extracted_tables 
USING gin (headers);
CREATE INDEX IF NOT EXISTS idx_extracted_tables_column_types ON public.extracted_tables 
USING gin (column_types);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_extracted_tables_summary_search ON public.extracted_tables 
USING gin (to_tsvector('english', table_summary));
CREATE INDEX IF NOT EXISTS idx_extracted_tables_raw_text_search ON public.extracted_tables 
USING gin (to_tsvector('english', raw_text));

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Indexes created for extracted_tables table';
    RAISE NOTICE 'Added 15 indexes including JSONB and full-text search capabilities';
END $$;
