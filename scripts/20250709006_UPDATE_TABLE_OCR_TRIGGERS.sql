-- ======================================================================
-- Add Triggers for OCR Tables
-- Script: UPDATE_TABLE_ocr_triggers_20250709_012.sql
-- Date: July 9, 2025
-- Purpose: Create automatic timestamp update triggers for OCR tables
-- Dependencies: All OCR tables must exist, update_updated_at_column function must exist
-- ======================================================================

-- Create trigger for OCR Results automatic timestamp updates
DROP TRIGGER IF EXISTS update_ocr_results_updated_at ON public.ocr_results;
CREATE TRIGGER update_ocr_results_updated_at 
    BEFORE UPDATE ON public.ocr_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for Document Chunks automatic timestamp updates
DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON public.document_chunks;
CREATE TRIGGER update_document_chunks_updated_at 
    BEFORE UPDATE ON public.document_chunks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for Extracted Tables automatic timestamp updates
DROP TRIGGER IF EXISTS update_extracted_tables_updated_at ON public.extracted_tables;
CREATE TRIGGER update_extracted_tables_updated_at 
    BEFORE UPDATE ON public.extracted_tables 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for Extracted Entities automatic timestamp updates
DROP TRIGGER IF EXISTS update_extracted_entities_updated_at ON public.extracted_entities;
CREATE TRIGGER update_extracted_entities_updated_at 
    BEFORE UPDATE ON public.extracted_entities 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Automatic timestamp update triggers created for OCR tables';
    RAISE NOTICE 'Updated_at columns will be automatically maintained on record updates';
END $$;
