-- ======================================================================
-- Add Row Level Security Policies for OCR Tables
-- Script: UPDATE_TABLE_ocr_security_policies_20250709_011.sql
-- Date: July 9, 2025
-- Purpose: Create RLS policies for OCR-related tables
-- Dependencies: All OCR tables must exist
-- ======================================================================

-- Create RLS policy for OCR Results
CREATE POLICY ocr_results_user_policy ON public.ocr_results
    FOR ALL USING (
        document_id IN (
            SELECT id FROM public.documents 
            WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
        OR 
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- Create RLS policy for Document Chunks
CREATE POLICY document_chunks_user_policy ON public.document_chunks
    FOR ALL USING (
        document_id IN (
            SELECT id FROM public.documents 
            WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
        OR 
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- Create RLS policy for Extracted Tables
CREATE POLICY extracted_tables_user_policy ON public.extracted_tables
    FOR ALL USING (
        document_id IN (
            SELECT id FROM public.documents 
            WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
        OR 
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- Create RLS policy for Extracted Entities
CREATE POLICY extracted_entities_user_policy ON public.extracted_entities
    FOR ALL USING (
        document_id IN (
            SELECT id FROM public.documents 
            WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
        OR 
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- Create RLS policy for Human Corrections
CREATE POLICY human_corrections_user_policy ON public.human_corrections
    FOR ALL USING (
        document_id IN (
            SELECT id FROM public.documents 
            WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
        OR 
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Row Level Security policies created for OCR tables';
    RAISE NOTICE 'Users can only access data for their own documents';
    RAISE NOTICE 'Service role has full access for processing operations';
END $$;
