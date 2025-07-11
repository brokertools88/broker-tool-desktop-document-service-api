-- ======================================================================
-- OCR Jobs Table Creation Script
-- Script: 20250709009_CREATE_TABLE_OCR_JOBS.sql
-- Date: July 9, 2025
-- Purpose: Create table for tracking OCR processing jobs
-- Dependencies: documents table
-- References: DATABASE_ANALYSIS.md
-- ======================================================================

-- OCR Jobs table for tracking OCR processing
CREATE TABLE IF NOT EXISTS public.ocr_jobs (
  id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
  document_id UUID NOT NULL,
  
  -- Job configuration
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER DEFAULT 5,
  language TEXT DEFAULT 'auto',
  engine TEXT DEFAULT 'mistral', -- 'mistral', 'tesseract', 'aws_textract', etc.
  options JSONB DEFAULT '{}'::jsonb,
  
  -- Processing results
  result JSONB NULL,
  extracted_text TEXT NULL,
  confidence_score DECIMAL(3,2) NULL,
  page_count INTEGER NULL,
  word_count INTEGER NULL,
  character_count INTEGER NULL,
  
  -- Error handling
  error_message TEXT NULL,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  
  -- Timestamps
  processing_started_at TIMESTAMP WITH TIME ZONE NULL,
  processing_completed_at TIMESTAMP WITH TIME ZONE NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT ocr_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT ocr_jobs_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
  CONSTRAINT ocr_jobs_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
  CONSTRAINT ocr_jobs_priority_check CHECK (priority BETWEEN 1 AND 10),
  CONSTRAINT ocr_jobs_confidence_check CHECK (confidence_score BETWEEN 0.00 AND 1.00),
  CONSTRAINT ocr_jobs_retry_check CHECK (retry_count <= max_retries)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_document_id ON public.ocr_jobs USING btree (document_id);
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_status ON public.ocr_jobs USING btree (status);
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_priority ON public.ocr_jobs USING btree (priority, created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_created_at ON public.ocr_jobs USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_engine ON public.ocr_jobs USING btree (engine);

-- Composite indexes for queue management
CREATE INDEX IF NOT EXISTS idx_ocr_jobs_queue ON public.ocr_jobs USING btree (status, priority, created_at) 
    WHERE status IN ('pending', 'processing');

-- Trigger for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_ocr_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Automatically set processing timestamps
    IF OLD.status != NEW.status THEN
        CASE NEW.status
            WHEN 'processing' THEN 
                NEW.processing_started_at = NOW();
            WHEN 'completed', 'failed', 'cancelled' THEN 
                NEW.processing_completed_at = NOW();
            ELSE 
                -- Keep existing timestamps
        END CASE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ocr_jobs_updated_at 
    BEFORE UPDATE ON public.ocr_jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_ocr_jobs_updated_at();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ocr_jobs TO authenticated;

-- Enable Row Level Security
ALTER TABLE public.ocr_jobs ENABLE ROW LEVEL SECURITY;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'OCR Jobs table created successfully';
    RAISE NOTICE 'Features included:';
    RAISE NOTICE '- Job queue management with priority';
    RAISE NOTICE '- Multiple OCR engine support';
    RAISE NOTICE '- Retry mechanism with configurable limits';
    RAISE NOTICE '- Comprehensive result storage';
    RAISE NOTICE '- Automatic timestamp management';
END $$;
