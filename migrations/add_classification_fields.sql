-- Migration: Add intelligent classification fields to requests table
-- Date: 2026-02-18
-- Description: Adds fields for tracking *arr service routing, external IDs, 
--              confidence scores, and classification metadata

-- Add arr_service column (tracks which *arr service to use)
ALTER TABLE requests ADD COLUMN arr_service VARCHAR(20);

-- Add arr_id column (ID in the target *arr service after successful add)
ALTER TABLE requests ADD COLUMN arr_id VARCHAR(100);

-- Add external_id column (TMDB/TVDB/MusicBrainz ID)
ALTER TABLE requests ADD COLUMN external_id VARCHAR(100);

-- Add confidence_score column (classification confidence 0.0-1.0)
ALTER TABLE requests ADD COLUMN confidence_score REAL;

-- Add classification_data column (JSON blob with full classification metadata)
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create index on arr_service for faster filtering
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);

-- Create index on external_id for deduplication checks
CREATE INDEX IF NOT EXISTS idx_requests_external_id ON requests(external_id);

-- Create index on confidence_score for quality monitoring
CREATE INDEX IF NOT EXISTS idx_requests_confidence ON requests(confidence_score);

-- Add comments explaining new fields (SQLite comment simulation via separate table)
CREATE TABLE IF NOT EXISTS migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO migration_log (migration_name, description) VALUES (
    'add_classification_fields',
    'Added intelligent classification fields to requests table for unified *arr routing with confidence scoring and metadata tracking'
);
