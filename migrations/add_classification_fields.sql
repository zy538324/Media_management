-- Migration: Add classification fields to requests table
-- Date: 2026-02-18
-- Description: Adds intelligent classification metadata fields for *arr routing

-- Add classification fields if they don't exist
-- SQLite doesn't support conditional ALTER TABLE, so check manually before running

ALTER TABLE requests ADD COLUMN arr_service TEXT;
ALTER TABLE requests ADD COLUMN arr_id TEXT;
ALTER TABLE requests ADD COLUMN external_id TEXT;
ALTER TABLE requests ADD COLUMN confidence_score REAL;
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_confidence ON requests(confidence_score);

-- Verify migration
SELECT 'Migration completed successfully' AS status;
