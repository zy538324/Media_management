-- Migration: Add intelligent classification fields to requests table
-- Date: 2026-02-18
-- Description: Adds fields for storing media classification metadata from the intelligent routing system

-- Check if columns already exist before adding (SQLite compatible)
-- This migration is idempotent and can be run multiple times safely

BEGIN TRANSACTION;

-- Add arr_service column if it doesn't exist
-- Stores which *arr service should handle this request: 'sonarr', 'radarr', or 'lidarr'
ALTER TABLE requests ADD COLUMN arr_service TEXT;

-- Add external_id column if it doesn't exist  
-- Stores TMDB ID, TVDB ID, or MusicBrainz ID depending on media type
ALTER TABLE requests ADD COLUMN external_id TEXT;

-- Add confidence_score column if it doesn't exist
-- Stores classification confidence from 0.0 to 1.0
ALTER TABLE requests ADD COLUMN confidence_score REAL;

-- Add classification_data column if it doesn't exist
-- Stores full classification metadata as JSON for debugging and UI display
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Add arr_id column if it doesn't exist
-- Stores the ID assigned by the target *arr service after successful addition
ALTER TABLE requests ADD COLUMN arr_id TEXT;

-- Create index on arr_service for faster queries
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);

-- Create index on confidence_score for analytics
CREATE INDEX IF NOT EXISTS idx_requests_confidence ON requests(confidence_score);

COMMIT;

-- Example queries after migration:

-- Get all requests routed to each service
-- SELECT arr_service, COUNT(*) FROM requests WHERE arr_service IS NOT NULL GROUP BY arr_service;

-- Get requests with low confidence that might need review
-- SELECT id, title, arr_service, confidence_score FROM requests WHERE confidence_score < 0.7 AND confidence_score IS NOT NULL;

-- Get average classification confidence by service
-- SELECT arr_service, AVG(confidence_score) as avg_confidence FROM requests WHERE arr_service IS NOT NULL GROUP BY arr_service;
