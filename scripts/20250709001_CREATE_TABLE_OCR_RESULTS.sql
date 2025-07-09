-- ======================================================================
-- Create OCR Results Table
-- Script: CREATE_TABLE_ocr_results_20250709_001.sql
-- Date: July 9, 2025
-- Purpose: Store detailed OCR extraction results for each document
-- Dependencies: documents table, ocr_jobs table
-- ======================================================================

CREATE TABLE IF NOT EXISTS public.ocr_results (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  ocr_job_id UUID NOT NULL,
  document_id UUID NOT NULL,
  
  -- Content Results
  extracted_text TEXT NOT NULL,
  text_length INTEGER NOT NULL,
  word_count INTEGER NOT NULL,
  character_count INTEGER NOT NULL,
  
  -- Quality Metrics
  overall_confidence DECIMAL(3,2) NOT NULL,
  text_confidence DECIMAL(3,2),
  layout_confidence DECIMAL(3,2),
  
  -- Language Detection
  detected_language TEXT,
  language_confidence DECIMAL(3,2),
  languages_detected JSONB, -- Multiple languages with confidence scores
  
  -- Document Structure
  page_count INTEGER NOT NULL,
  has_tables BOOLEAN DEFAULT FALSE,
  has_images BOOLEAN DEFAULT FALSE,
  has_forms BOOLEAN DEFAULT FALSE,
  
  -- Processing Statistics
  processing_time_seconds DECIMAL(8,3),
  engine_version TEXT,
  model_version TEXT,
  
  -- Raw Results (for debugging/reprocessing)
  raw_ocr_response JSONB,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  CONSTRAINT ocr_results_pkey PRIMARY KEY (id),
  CONSTRAINT ocr_results_ocr_job_id_fkey FOREIGN KEY (ocr_job_id) REFERENCES ocr_jobs (id) ON DELETE CASCADE,
  CONSTRAINT ocr_results_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
  CONSTRAINT ocr_results_confidence_check CHECK (overall_confidence BETWEEN 0.00 AND 1.00)
);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ocr_results TO authenticated;

-- Enable Row Level Security
ALTER TABLE public.ocr_results ENABLE ROW LEVEL SECURITY;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Table ocr_results created successfully';
    RAISE NOTICE 'Stores detailed OCR extraction results with quality metrics and language detection';
END $$;
