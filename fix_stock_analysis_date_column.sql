-- Fix missing date column in stock_analysis table
-- This script can be run safely multiple times (idempotent)
-- Production-safe migration script for AWS RDS PostgreSQL

-- Add date column if it doesn't exist
DO $$
BEGIN
    -- Check if the date column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'stock_analysis'
        AND column_name = 'date'
        AND table_schema = 'public'
    ) THEN
        -- Add the date column with default value
        ALTER TABLE stock_analysis ADD COLUMN date TIMESTAMP DEFAULT NOW();

        -- Update existing rows to have current timestamp where date is null
        UPDATE stock_analysis SET date = NOW() WHERE date IS NULL;

        -- Add a comment to document the change
        COMMENT ON COLUMN stock_analysis.date IS 'Analysis timestamp - added via performance optimization migration';

        RAISE NOTICE 'Successfully added date column to stock_analysis table';
    ELSE
        RAISE NOTICE 'Date column already exists in stock_analysis table';
    END IF;

    -- Ensure any null values are updated (in case column existed but had nulls)
    UPDATE stock_analysis SET date = NOW() WHERE date IS NULL;

    -- Verify the column exists and get count of records
    PERFORM 1 FROM information_schema.columns
    WHERE table_name = 'stock_analysis' AND column_name = 'date';

    IF FOUND THEN
        -- Get count of records with proper dates
        DECLARE
            record_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO record_count FROM stock_analysis WHERE date IS NOT NULL;
            RAISE NOTICE 'Verification: stock_analysis table has % records with valid dates', record_count;
        END;
    END IF;

END $$;

-- Create an index on the date column for better performance
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'stock_analysis'
        AND indexname = 'idx_stock_analysis_date'
    ) THEN
        CREATE INDEX idx_stock_analysis_date ON stock_analysis(date DESC);
        RAISE NOTICE 'Created index on stock_analysis.date column';
    ELSE
        RAISE NOTICE 'Index on stock_analysis.date already exists';
    END IF;
END $$;

-- Display final table structure for verification
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'stock_analysis'
ORDER BY ordinal_position;