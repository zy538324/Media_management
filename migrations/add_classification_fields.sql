-- Database migration to add intelligent classification fields to requests table
-- Run this with: sqlite3 media_management.db < migrations/add_classification_fields.sql

-- Check if columns already exist before adding (SQLite doesn't have IF NOT EXISTS for ALTER TABLE)
-- If you get "duplicate column" errors, the migration has already been applied

-- Add classification fields to requests table
ALTER TABLE requests ADD COLUMN arr_service TEXT;
ALTER TABLE requests ADD COLUMN arr_id TEXT;
ALTER TABLE requests ADD COLUMN external_id TEXT;
ALTER TABLE requests ADD COLUMN confidence_score REAL;
ALTER TABLE requests ADD COLUMN classification_data TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requests_arr_service ON requests(arr_service);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_external_id ON requests(external_id);
CREATE INDEX IF NOT EXISTS idx_requests_confidence_score ON requests(confidence_score);

-- Display migration completion message
SELECT 'Classification fields migration completed successfully!' AS result;
