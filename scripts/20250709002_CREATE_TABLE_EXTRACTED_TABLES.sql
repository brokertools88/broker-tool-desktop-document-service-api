-- ======================================================================
-- Create Extracted Tables Table
-- Script: CREATE_TABLE_extracted_tables_20250709_003.sql
-- Date: July 9, 2025
-- Purpose: Store structured table data extracted from documents
-- Dependencies: documents table, ocr_results table, document_chunks table
-- ======================================================================

CREATE TABLE IF NOT EXISTS public.extracted_tables (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  document_id UUID NOT NULL,
  ocr_result_id UUID NOT NULL,
  chunk_id UUID,
  
  -- Table Identification
  table_index INTEGER NOT NULL, -- Table number within document
  page_number INTEGER,
  
  -- Table Structure
  rows_count INTEGER NOT NULL,
  columns_count INTEGER NOT NULL,
  has_headers BOOLEAN DEFAULT FALSE,
  
  -- Content Storage
  table_data JSONB NOT NULL, -- Structured table data as JSON
  headers JSONB, -- Column headers if detected
  table_html TEXT, -- HTML representation
  table_markdown TEXT, -- Markdown representation
  raw_text TEXT, -- Plain text version
  
  -- Position and Layout
  bounding_box JSONB, -- Table coordinates
  confidence_score DECIMAL(3,2),
  
  -- Processing Metadata
  extraction_method TEXT, -- 'ocr', 'layout', 'hybrid'
  needs_verification BOOLEAN DEFAULT FALSE,
  
  -- AI Enhancement
  table_summary TEXT, -- AI-generated summary
  table_type TEXT, -- 'financial', 'data', 'schedule', etc.
  column_types JSONB, -- Detected data types for columns
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  CONSTRAINT extracted_tables_pkey PRIMARY KEY (id),
  CONSTRAINT extracted_tables_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
  CONSTRAINT extracted_tables_ocr_result_id_fkey FOREIGN KEY (ocr_result_id) REFERENCES ocr_results (id) ON DELETE CASCADE,
  CONSTRAINT extracted_tables_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES document_chunks (id)
);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.extracted_tables TO authenticated;

-- Enable Row Level Security
ALTER TABLE public.extracted_tables ENABLE ROW LEVEL SECURITY;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Table extracted_tables created successfully';
    RAISE NOTICE 'Preserves table structure and enables structured data analysis';
END $$;
