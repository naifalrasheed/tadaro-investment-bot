-- URGENT PRODUCTION FIX: Add missing date column to stock_analysis table
-- Execute this directly in AWS RDS PostgreSQL

BEGIN;

-- Add date column if it doesn't exist (production-safe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'stock_analysis'
        AND column_name = 'date'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE stock_analysis ADD COLUMN date TIMESTAMP DEFAULT NOW();
        RAISE NOTICE 'Added date column to stock_analysis table';
    ELSE
        RAISE NOTICE 'Date column already exists';
    END IF;
END $$;

-- Update any existing records that have null dates
UPDATE stock_analysis SET date = NOW() WHERE date IS NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_stock_analysis_date ON stock_analysis(date DESC);

-- Verify the fix
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'stock_analysis'
AND table_schema = 'public'
ORDER BY ordinal_position;

COMMIT;

-- Final verification
SELECT COUNT(*) as total_records,
       COUNT(date) as records_with_date,
       NOW() as current_timestamp
FROM stock_analysis;