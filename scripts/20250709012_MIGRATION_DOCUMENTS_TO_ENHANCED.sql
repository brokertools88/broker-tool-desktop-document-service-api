-- ======================================================================
-- Migration Script: Legacy Documents Table to Unified Documents Table
-- Script: 20250709012_MIGRATION_DOCUMENTS_TO_UNIFIED.sql
-- Date: July 9, 2025
-- Purpose: Safely migrate data from legacy documents table to unified structure
-- Dependencies: documents table (unified schema with all fields)
-- Note: This script handles migration from legacy systems only
-- ======================================================================

-- Step 1: Create migration tracking table
CREATE TABLE IF NOT EXISTS public.migration_log (
    id UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
    migration_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    records_processed INTEGER DEFAULT 0,
    records_migrated INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT migration_log_pkey PRIMARY KEY (id),
    CONSTRAINT migration_log_status_check CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'rolled_back'))
);

-- Step 2: Log migration start
INSERT INTO public.migration_log (migration_name, status)
VALUES ('legacy_documents_to_unified', 'started');

-- Step 3: Legacy compatibility note
-- NOTE: This migration script is preserved for reference only.
-- The unified documents table (created by 20250708001_CREATE_TABLE_DOCUMENTS.sql)
-- now includes all fields from both the original and enhanced schemas.
-- 
-- If you have an existing legacy documents table that needs migration,
-- you can adapt this script to migrate to the unified documents table.

CREATE OR REPLACE FUNCTION check_documents_schema_compatibility()
RETURNS TABLE (
    table_exists BOOLEAN,
    has_unified_schema BOOLEAN,
    missing_fields TEXT[],
    recommendations TEXT
) AS $$
DECLARE
    legacy_table_exists BOOLEAN := FALSE;
    unified_fields_present BOOLEAN := TRUE;
    missing_field_list TEXT[] := ARRAY[]::TEXT[];
    recommendation_text TEXT;
BEGIN
    -- Check if legacy documents table exists (without enhanced fields)
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'documents'
    ) INTO legacy_table_exists;
    
    -- Check for key unified schema fields
    IF legacy_table_exists THEN
        -- Check for enhanced fields in documents table
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'documents' 
            AND column_name = 'storage_key'
        ) THEN
            unified_fields_present := FALSE;
            missing_field_list := array_append(missing_field_list, 'storage_key');
        END IF;
        
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'documents' 
            AND column_name = 'file_hash'
        ) THEN
            unified_fields_present := FALSE;
            missing_field_list := array_append(missing_field_list, 'file_hash');
        END IF;
        
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'documents' 
            AND column_name = 'ocr_completed'
        ) THEN
            unified_fields_present := FALSE;
            missing_field_list := array_append(missing_field_list, 'ocr_completed');
        END IF;
    END IF;
    
    -- Generate recommendations
    IF NOT legacy_table_exists THEN
        recommendation_text := 'Documents table does not exist. Run 20250708001_CREATE_TABLE_DOCUMENTS.sql to create unified schema.';
    ELSIF unified_fields_present THEN
        recommendation_text := 'Documents table has unified schema - no migration needed!';
    ELSE
        recommendation_text := 'Legacy documents table detected. Consider upgrading to unified schema by running 20250708001_CREATE_TABLE_DOCUMENTS.sql (will require data migration).';
    END IF;
    
    RETURN QUERY SELECT 
        legacy_table_exists,
        unified_fields_present,
        missing_field_list,
        recommendation_text;
END;
$$ LANGUAGE plpgsql;
                insurer_id,
                uploaded_by,
                version,
                etag,
                metadata,
                tags,
                upload_date,
                created_at,
                updated_at,
                last_modified
            ) VALUES (
                rec.id,
                rec.file_name,
                rec.original_file_name,
                rec.file_size,
                rec.file_type,
                COALESCE(rec.file_type, 'application/octet-stream'), -- Default MIME type
                COALESCE(rec.file_path, 'legacy/' || rec.id::TEXT), -- Generate storage path
                COALESCE((SELECT setting FROM pg_settings WHERE name = 'default_bucket'), 'documents'), -- Default bucket
                'legacy/' || rec.id::TEXT || '/' || rec.file_name, -- Generate storage key
                encode(digest(rec.id::TEXT || rec.file_name, 'sha256'), 'hex'), -- Generate file hash
                rec.document_type,
                CASE 
                    WHEN rec.status = 'active' THEN 'completed'
                    ELSE COALESCE(rec.status, 'uploaded')
                END,
                COALESCE(rec.uploaded_by, 'legacy_user'), -- Map uploaded_by to user_id
                rec.client_id,
                rec.insurer_id,
                rec.uploaded_by,
                1, -- Default version
                '"' || EXTRACT(EPOCH FROM COALESCE(rec.updated_at, rec.created_at, NOW()))::TEXT || '"', -- Generate ETag
                COALESCE(rec.metadata, '{}'::jsonb),
                ARRAY[]::TEXT[], -- Empty tags array
                COALESCE(rec.upload_date, rec.created_at, NOW()),
                COALESCE(rec.created_at, NOW()),
                COALESCE(rec.updated_at, rec.created_at, NOW()),
                COALESCE(rec.last_modified, rec.updated_at, rec.created_at, NOW())
            );
            
            migrated_count := migrated_count + 1;
            
        EXCEPTION WHEN OTHERS THEN
            error_count := error_count + 1;
            migration_details := migration_details || jsonb_build_object(
                'error_' || error_count::TEXT, 
                jsonb_build_object(
                    'document_id', rec.id,
                    'error_message', SQLERRM,
                    'error_detail', SQLSTATE
                )
            );
            
            -- Log error but continue migration
            RAISE NOTICE 'Error migrating document %: %', rec.id, SQLERRM;
        END;
    END LOOP;
    
    -- Update migration log
    UPDATE migration_log 
    SET 
        status = CASE WHEN error_count = 0 THEN 'completed' ELSE 'completed_with_errors' END,
        completed_at = NOW(),
        records_processed = migrated_count + error_count,
        records_migrated = migrated_count,
        errors_encountered = error_count,
        error_details = migration_details
    WHERE id = current_migration_id;
    
    RETURN QUERY SELECT migrated_count, error_count, migration_details;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Execute migration
DO $$
DECLARE
    migration_result RECORD;
BEGIN
    -- Run migration
    SELECT * INTO migration_result FROM migrate_documents_to_enhanced();
    
    RAISE NOTICE 'Migration completed:';
    RAISE NOTICE 'Records migrated: %', migration_result.migrated_count;
    RAISE NOTICE 'Errors encountered: %', migration_result.error_count;
    
    IF migration_result.error_count > 0 THEN
        RAISE NOTICE 'Error details: %', migration_result.details;
    END IF;
END $$;

-- Step 5: Validation queries
-- Verify migration completeness
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM public.documents;
    SELECT COUNT(*) INTO new_count FROM public.documents_enhanced;
    
    SELECT COUNT(*) INTO missing_count 
    FROM public.documents d
    WHERE NOT EXISTS (
        SELECT 1 FROM public.documents_enhanced de 
        WHERE de.id = d.id
    );
    
    RAISE NOTICE 'Migration validation:';
    RAISE NOTICE 'Original documents count: %', old_count;
    RAISE NOTICE 'Enhanced documents count: %', new_count;
    RAISE NOTICE 'Missing documents: %', missing_count;
    
    IF missing_count > 0 THEN
        RAISE WARNING 'Some documents were not migrated. Check migration_log for details.';
    ELSE
        RAISE NOTICE 'All documents successfully migrated!';
    END IF;
END $$;

-- Step 6: Create view for backward compatibility
CREATE OR REPLACE VIEW documents_legacy_compatibility AS
SELECT 
    id,
    filename as file_name,
    original_filename as original_file_name,
    file_size,
    file_type,
    storage_path as file_path,
    document_type,
    client_id,
    insurer_id,
    uploaded_by,
    upload_date,
    last_modified,
    metadata,
    status,
    created_at,
    updated_at
FROM public.documents_enhanced
WHERE deleted_at IS NULL;

-- Grant permissions on compatibility view
GRANT SELECT ON documents_legacy_compatibility TO authenticated;

-- Step 7: Create rollback function (for emergencies)
CREATE OR REPLACE FUNCTION rollback_documents_migration()
RETURNS INTEGER AS $$
DECLARE
    rollback_count INTEGER := 0;
    current_migration_id UUID;
BEGIN
    -- Get current migration ID
    SELECT id INTO current_migration_id 
    FROM migration_log 
    WHERE migration_name = 'documents_to_enhanced' 
    ORDER BY started_at DESC 
    LIMIT 1;
    
    -- WARNING: This will delete all migrated data!
    -- Only use in emergency situations
    DELETE FROM public.documents_enhanced 
    WHERE id IN (
        SELECT id FROM public.documents
    );
    
    GET DIAGNOSTICS rollback_count = ROW_COUNT;
    
    -- Update migration log
    UPDATE migration_log 
    SET status = 'rolled_back', completed_at = NOW()
    WHERE id = current_migration_id;
    
    RAISE NOTICE 'Rolled back % records', rollback_count;
    RETURN rollback_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION migrate_documents_to_enhanced() TO service_role;
GRANT EXECUTE ON FUNCTION rollback_documents_migration() TO service_role;

-- Migration completion notification
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Documents Migration to Enhanced Table Completed!';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Migration features:';
    RAISE NOTICE '- Safe data migration with error handling';
    RAISE NOTICE '- Backward compatibility view created';
    RAISE NOTICE '- Migration tracking and validation';
    RAISE NOTICE '- Rollback function available (emergency use only)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify all data migrated correctly';
    RAISE NOTICE '2. Update application to use documents_enhanced table';
    RAISE NOTICE '3. Test all functionality thoroughly';
    RAISE NOTICE '4. When ready, rename tables: documents -> documents_old, documents_enhanced -> documents';
    RAISE NOTICE '=================================================================';
END $$;
