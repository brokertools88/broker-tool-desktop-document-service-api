-- ======================================================================
-- Add Utility Functions for OCR and Search
-- Script: UPDATE_TABLE_ocr_functions_20250709_013.sql
-- Date: July 9, 2025
-- Purpose: Create utility functions for OCR processing and search
-- Dependencies: All OCR tables must exist, pgvector extension
-- ======================================================================

-- Function to search documents by semantic similarity
CREATE OR REPLACE FUNCTION search_documents_by_similarity(
    query_embedding vector(1536),
    similarity_threshold DECIMAL(3,2) DEFAULT 0.70,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity_score DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id as chunk_id,
        dc.document_id,
        dc.content,
        (1 - (dc.embedding_vector <=> query_embedding))::DECIMAL(3,2) as similarity_score
    FROM document_chunks dc
    WHERE dc.embedding_vector IS NOT NULL
    AND (1 - (dc.embedding_vector <=> query_embedding)) >= similarity_threshold
    ORDER BY dc.embedding_vector <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get document OCR statistics
CREATE OR REPLACE FUNCTION get_document_ocr_stats(p_document_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_chunks', COUNT(dc.id),
        'total_entities', (SELECT COUNT(*) FROM extracted_entities WHERE document_id = p_document_id),
        'total_tables', (SELECT COUNT(*) FROM extracted_tables WHERE document_id = p_document_id),
        'average_confidence', AVG(or_result.overall_confidence),
        'total_pages', MAX(or_result.page_count),
        'total_words', SUM(dc.word_count),
        'processing_complete', bool_and(dc.embedding_vector IS NOT NULL),
        'languages_detected', or_result.languages_detected,
        'has_tables', bool_or(or_result.has_tables),
        'has_images', bool_or(or_result.has_images),
        'has_forms', bool_or(or_result.has_forms)
    ) INTO stats
    FROM document_chunks dc
    LEFT JOIN ocr_results or_result ON dc.ocr_result_id = or_result.id
    WHERE dc.document_id = p_document_id;
    
    RETURN COALESCE(stats, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to get entity summary for a document
CREATE OR REPLACE FUNCTION get_document_entity_summary(p_document_id UUID)
RETURNS JSONB AS $$
DECLARE
    entity_stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_entities', COUNT(*),
        'verified_entities', COUNT(*) FILTER (WHERE is_verified = true),
        'high_confidence_entities', COUNT(*) FILTER (WHERE confidence_score >= 0.90),
        'entity_types', jsonb_agg(DISTINCT entity_type),
        'top_entities_by_importance', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'text', entity_text,
                    'type', entity_type,
                    'importance', importance_score
                )
            )
            FROM (
                SELECT entity_text, entity_type, importance_score
                FROM extracted_entities 
                WHERE document_id = p_document_id
                ORDER BY importance_score DESC NULLS LAST
                LIMIT 10
            ) top_entities
        )
    ) INTO entity_stats
    FROM extracted_entities
    WHERE document_id = p_document_id;
    
    RETURN COALESCE(entity_stats, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to search entities across documents
CREATE OR REPLACE FUNCTION search_entities_by_text(
    search_text TEXT,
    entity_types TEXT[] DEFAULT NULL,
    min_confidence DECIMAL(3,2) DEFAULT 0.50,
    max_results INTEGER DEFAULT 50
)
RETURNS TABLE(
    entity_id UUID,
    document_id UUID,
    entity_text TEXT,
    entity_type TEXT,
    confidence_score DECIMAL(3,2),
    normalized_value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ee.id as entity_id,
        ee.document_id,
        ee.entity_text,
        ee.entity_type,
        ee.confidence_score,
        ee.normalized_value
    FROM extracted_entities ee
    WHERE (
        ee.entity_text ILIKE '%' || search_text || '%'
        OR ee.normalized_value ILIKE '%' || search_text || '%'
    )
    AND (entity_types IS NULL OR ee.entity_type = ANY(entity_types))
    AND ee.confidence_score >= min_confidence
    ORDER BY ee.confidence_score DESC, ee.importance_score DESC NULLS LAST
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get correction statistics
CREATE OR REPLACE FUNCTION get_correction_statistics(
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_corrections', COUNT(*),
        'validated_corrections', COUNT(*) FILTER (WHERE is_validated = true),
        'learning_applied', COUNT(*) FILTER (WHERE learning_applied = true),
        'corrections_by_type', jsonb_object_agg(correction_type, type_count),
        'top_correctors', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'user_id', corrected_by,
                    'correction_count', correction_count
                )
            )
            FROM (
                SELECT corrected_by, COUNT(*) as correction_count
                FROM human_corrections 
                WHERE created_at BETWEEN start_date AND end_date
                GROUP BY corrected_by
                ORDER BY correction_count DESC
                LIMIT 10
            ) top_users
        )
    ) INTO stats
    FROM (
        SELECT 
            correction_type,
            COUNT(*) as type_count
        FROM human_corrections
        WHERE created_at BETWEEN start_date AND end_date
        GROUP BY correction_type
    ) type_counts;
    
    RETURN COALESCE(stats, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION search_documents_by_similarity TO authenticated;
GRANT EXECUTE ON FUNCTION get_document_ocr_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_document_entity_summary TO authenticated;
GRANT EXECUTE ON FUNCTION search_entities_by_text TO authenticated;
GRANT EXECUTE ON FUNCTION get_correction_statistics TO authenticated;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE 'Utility functions created for OCR and search operations';
    RAISE NOTICE 'Added 5 functions: similarity search, OCR stats, entity summary, entity search, correction stats';
END $$;
