#!/usr/bin/env python3
"""
Database Schema Fix Script - Missing Date Column in stock_analysis table

This script safely adds the missing date column to the stock_analysis table
Works with both PostgreSQL (production) and SQLite (development)

Usage:
    python3 fix_database_schema.py

Requirements:
    - DATABASE_URL environment variable (for production)
    - psycopg (for PostgreSQL) or sqlite3 (for SQLite)
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def detect_database_type():
    """Detect if we're using PostgreSQL or SQLite"""
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        return 'postgresql', database_url
    else:
        # Default to SQLite for local development
        return 'sqlite', 'investment_bot.db'

def fix_postgresql_schema(database_url):
    """Fix PostgreSQL database schema"""
    try:
        import psycopg
        logger.info("Connecting to PostgreSQL database...")

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                logger.info("Checking for existing date column...")

                # Check if date column exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'stock_analysis'
                        AND column_name = 'date'
                        AND table_schema = 'public'
                    )
                """)
                column_exists = cur.fetchone()[0]

                if not column_exists:
                    logger.info("Adding date column to stock_analysis table...")
                    cur.execute("""
                        ALTER TABLE stock_analysis
                        ADD COLUMN date TIMESTAMP DEFAULT NOW()
                    """)

                    # Update existing records
                    cur.execute("""
                        UPDATE stock_analysis
                        SET date = NOW()
                        WHERE date IS NULL
                    """)

                    logger.info("✅ Successfully added date column")
                else:
                    logger.info("Date column already exists")

                    # Still update any null values
                    cur.execute("""
                        UPDATE stock_analysis
                        SET date = NOW()
                        WHERE date IS NULL
                    """)

                # Create index for performance
                logger.info("Creating index on date column...")
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stock_analysis_date
                    ON stock_analysis(date DESC)
                """)

                # Get record count for verification
                cur.execute("SELECT COUNT(*) FROM stock_analysis WHERE date IS NOT NULL")
                record_count = cur.fetchone()[0]
                logger.info(f"✅ Verification: {record_count} records have valid dates")

                conn.commit()
                logger.info("✅ PostgreSQL schema fix completed successfully")

    except ImportError:
        logger.error("psycopg not available. Install with: pip install psycopg")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL schema fix failed: {str(e)}")
        return False

    return True

def fix_sqlite_schema(db_path):
    """Fix SQLite database schema"""
    try:
        import sqlite3
        logger.info(f"Connecting to SQLite database: {db_path}")

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()

            # Check if date column exists
            cur.execute("PRAGMA table_info(stock_analysis)")
            columns = [row[1] for row in cur.fetchall()]

            if 'date' not in columns:
                logger.info("Adding date column to stock_analysis table...")
                cur.execute("""
                    ALTER TABLE stock_analysis
                    ADD COLUMN date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)

                # Update existing records
                cur.execute("""
                    UPDATE stock_analysis
                    SET date = CURRENT_TIMESTAMP
                    WHERE date IS NULL OR date = ''
                """)

                logger.info("✅ Successfully added date column")
            else:
                logger.info("Date column already exists")

                # Still update any null values
                cur.execute("""
                    UPDATE stock_analysis
                    SET date = CURRENT_TIMESTAMP
                    WHERE date IS NULL OR date = ''
                """)

            # Create index for performance
            logger.info("Creating index on date column...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_analysis_date
                ON stock_analysis(date DESC)
            """)

            # Get record count for verification
            cur.execute("SELECT COUNT(*) FROM stock_analysis WHERE date IS NOT NULL")
            record_count = cur.fetchone()[0]
            logger.info(f"✅ Verification: {record_count} records have valid dates")

            conn.commit()
            logger.info("✅ SQLite schema fix completed successfully")

    except sqlite3.Error as e:
        logger.error(f"❌ SQLite schema fix failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

    return True

def main():
    """Main execution function"""
    logger.info("🔧 Starting database schema fix for stock_analysis table")
    logger.info("=" * 60)

    # Detect database type
    db_type, db_connection = detect_database_type()
    logger.info(f"Detected database type: {db_type}")

    # Apply appropriate fix
    success = False
    if db_type == 'postgresql':
        success = fix_postgresql_schema(db_connection)
    elif db_type == 'sqlite':
        success = fix_sqlite_schema(db_connection)
    else:
        logger.error(f"❌ Unsupported database type: {db_type}")
        sys.exit(1)

    if success:
        logger.info("=" * 60)
        logger.info("✅ DATABASE SCHEMA FIX COMPLETED SUCCESSFULLY")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. The date column is now available in stock_analysis table")
        logger.info("2. All existing records have been updated with timestamps")
        logger.info("3. An index has been created for query performance")
        logger.info("4. You can now deploy the updated container")
        logger.info("")
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ DATABASE SCHEMA FIX FAILED")
        logger.error("Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()