-- Fix missing date column in stock_analysis table
DO $$
BEGIN
    -- Add date column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='stock_analysis' AND column_name='date') THEN
        ALTER TABLE stock_analysis ADD COLUMN date TIMESTAMP DEFAULT NOW();
        RAISE NOTICE 'Added date column to stock_analysis table';
    ELSE
        RAISE NOTICE 'Date column already exists in stock_analysis table';
    END IF;

    -- Update existing rows to have a date if NULL
    UPDATE stock_analysis SET date = NOW() WHERE date IS NULL;

    RAISE NOTICE 'Database schema fix completed';
END $$;