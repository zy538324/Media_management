-- Migration: Add intelligent classification fields to requests table
-- Run this migration to add support for automatic media classification
-- Date: 2026-02-18

-- Add classification metadata columns to requests table
ALTER TABLE requests ADD COLUMN arr_service VARCHAR(20);      -- Target service: 'sonarr', 'radarr', or 'lidarr'
ALTER TABLE requests ADD COLUMN arr_id VARCHAR(100);          -- ID in the target *arr service
ALTER TABLE requests ADD COLUMN external_id VARCHAR(100);     -- TMDB/TVDB/MusicBrainz ID  
ALTER TABLE requests ADD COLUMN confidence_score FLOAT;       -- Classification confidence (0.0-1.0)
ALTER TABLE requests ADD COLUMN classification_data TEXT;     -- JSON blob with full classification metadata

-- Create index for faster lookups by service
CREATE INDEX idx_requests_arr_service ON requests(arr_service);
CREATE INDEX idx_requests_external_id ON requests(external_id);

-- Add comments (SQLite doesn't support column comments, but keep for documentation)
-- arr_service: Stores which *arr service this request should be routed to
-- external_id: Stores the external API ID (TMDB for movies, TVDB for TV, MusicBrainz for music)
-- confidence_score: Classifier confidence score (1.0 = 100% confident)
-- classification_data: JSON string containing full MediaMatch object for debugging

-- Migration rollback instructions:
-- To rollback, run:
-- DROP INDEX idx_requests_external_id;
-- DROP INDEX idx_requests_arr_service;
-- ALTER TABLE requests DROP COLUMN classification_data;
-- ALTER TABLE requests DROP COLUMN confidence_score;
-- ALTER TABLE requests DROP COLUMN external_id;
-- ALTER TABLE requests DROP COLUMN arr_id;
-- ALTER TABLE requests DROP COLUMN arr_service;
