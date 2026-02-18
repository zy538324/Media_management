-- Migration: Add intelligent classification fields to requests table
-- Date: 2026-02-18
-- Description: Adds fields for *arr service routing, external IDs, and confidence scoring

-- Add classification fields to requests table
ALTER TABLE requests ADD COLUMN arr_service TEXT;
ALTER TABLE requests ADD COLUMN arr_id TEXT;
ALTER TABLE requests ADD COLUMN external_id TEXT;
ALTER TABLE requests ADD COLUMN confidence_score REAL;
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_user_status ON requests(user_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_confidence ON requests(confidence_score DESC);

-- Update existing pending requests to be reprocessed with new classifier
-- (Optional - remove this line if you don't want to reprocess existing requests)
-- UPDATE requests SET status = 'Pending' WHERE status = 'Failed (TMDb)';
