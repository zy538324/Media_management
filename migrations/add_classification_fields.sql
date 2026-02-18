-- Migration: Add classification fields to requests table
-- Date: 2026-02-18
-- Description: Adds intelligent classification metadata to track *arr service routing

-- Add new columns for classification tracking
ALTER TABLE requests ADD COLUMN arr_service VARCHAR(20);
ALTER TABLE requests ADD COLUMN arr_id VARCHAR(100);
ALTER TABLE requests ADD COLUMN external_id VARCHAR(100);
ALTER TABLE requests ADD COLUMN confidence_score REAL;
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create index for faster queries on arr_service
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);
CREATE INDEX IF NOT EXISTS idx_requests_external_id ON requests(external_id);

-- Update existing records to set arr_service based on media_type
-- This provides backward compatibility with existing requests
UPDATE requests 
SET arr_service = 'radarr' 
WHERE media_type = 'movie' AND arr_service IS NULL;

UPDATE requests 
SET arr_service = 'sonarr' 
WHERE media_type IN ('tv show', 'series', 'tv') AND arr_service IS NULL;

UPDATE requests 
SET arr_service = 'lidarr' 
WHERE media_type IN ('music', 'album', 'artist') AND arr_service IS NULL;
