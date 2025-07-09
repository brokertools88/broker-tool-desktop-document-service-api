-- ======================================================================
-- Add Indexes for OCR Results Table
-- Script: UPDATE_TABLE_ocr_results_20250709_006.sql
-- Date: July 9, 2025
-- Purpose: Create performance indexes for ocr_results table
-- Dependencies: ocr_results table must exist
-- ======================================================================

-- Performance indexes for OCR Results
CREATE INDEX IF NOT EXISTS idx_ocr_results_document_id ON public.ocr_results (document_id);
CREATE INDEX IF NOT EXISTS idx_ocr_results_ocr_job_id ON public.ocr_results (ocr_job_id);
CREATE INDEX IF NOT EXISTS idx_ocr_results_confidence ON public.ocr_results (overall_confidence);
CREATE INDEX IF NOT EXISTS idx_ocr_results_language ON public.ocr_results (detected_language);
CREATE INDEX IF NOT EXISTS idx_ocr_results_created_at ON public.ocr_results (created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_results_page_count ON public.ocr_results (page_count);
CREATE INDEX IF NOT EXISTS idx_ocr_results_has_tables ON public.ocr_results (has_tables);
CREATE INDEX IF NOT EXISTS idx_ocr_results_has_images ON public.ocr_results (has_images);

-- Full-text search index for extracted text
CREATE INDEX IF NOT EXISTS idx_ocr_results_text_search ON public.ocr_results 
USING gin (to_tsvector('english', extracted_text));

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Indexes created for ocr_results table';
    RAISE NOTICE 'Added 9 indexes including full-text search capability';
END $$;
