-- Emergency Database Schema Fix
-- Adds missing 'date' column to stock_analysis table

-- Check if the column already exists before adding it
DO $$
BEGIN
    -- Check if the date column exists
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'stock_analysis'
        AND column_name = 'date'
    ) THEN
        -- Add the missing date column
        ALTER TABLE stock_analysis
        ADD COLUMN date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

        RAISE NOTICE 'Added date column to stock_analysis table';
    ELSE
        RAISE NOTICE 'Date column already exists in stock_analysis table';
    END IF;
END $$;

-- Update existing records to have a date if they don't have one
UPDATE stock_analysis
SET date = CURRENT_TIMESTAMP
WHERE date IS NULL;

-- Create index on date column for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_analysis_date ON stock_analysis(date);

-- Verify the fix
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'stock_analysis'
AND column_name = 'date';

-- Show sample of updated data
SELECT
    id,
    symbol,
    date,
    current_price,
    data_source
FROM stock_analysis
ORDER BY date DESC
LIMIT 5;