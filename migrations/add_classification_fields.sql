-- Migration script to add intelligent classification fields to requests table
-- Run this migration with: sqlite3 media_management.db < migrations/add_classification_fields.sql

-- Add classification fields to requests table (if they don't exist)
ALTER TABLE requests ADD COLUMN arr_service TEXT;
ALTER TABLE requests ADD COLUMN arr_id TEXT;
ALTER TABLE requests ADD COLUMN external_id TEXT;
ALTER TABLE requests ADD COLUMN confidence_score REAL;
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_confidence ON requests(confidence_score);
CREATE INDEX IF NOT EXISTS idx_requests_external_id ON requests(external_id);

-- Update existing records to have default values
UPDATE requests 
SET arr_service = CASE 
    WHEN LOWER(media_type) = 'movie' THEN 'radarr'
    WHEN LOWER(media_type) IN ('tv show', 'series', 'tv') THEN 'sonarr'
    WHEN LOWER(media_type) IN ('music', 'album', 'artist') THEN 'lidarr'
    ELSE NULL
END
WHERE arr_service IS NULL;

-- Set default confidence for migrated records
UPDATE requests 
SET confidence_score = 0.7
WHERE arr_service IS NOT NULL AND confidence_score IS NULL;
