#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL (psycopg v3 compatible)
Migrates all data from local SQLite database to AWS RDS PostgreSQL
Python 3.13 Compatible Version
"""

import os
import sys
import sqlite3
import psycopg  # psycopg v3
import json
from datetime import datetime
from psycopg.rows import dict_row

# Production PostgreSQL connection details
POSTGRESQL_CONFIG = {
    'host': 'db-tradaro-ai.cmp4q2awn0qu.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'dbname': 'postgres',
    'user': 'naif_alrasheed',
    'password': 'CodeNaif123'
}

# Local SQLite database path
SQLITE_DB_PATH = 'investment_bot.db'

def connect_sqlite():
    """Connect to SQLite database"""
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite database not found: {SQLITE_DB_PATH}")
        return None

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        print(f"✅ Connected to SQLite database: {SQLITE_DB_PATH}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to SQLite: {e}")
        return None

def connect_postgresql():
    """Connect to PostgreSQL database using psycopg v3"""
    try:
        # Create connection string
        conn_string = (
            f"host={POSTGRESQL_CONFIG['host']} "
            f"port={POSTGRESQL_CONFIG['port']} "
            f"dbname={POSTGRESQL_CONFIG['dbname']} "
            f"user={POSTGRESQL_CONFIG['user']} "
            f"password={POSTGRESQL_CONFIG['password']}"
        )

        conn = psycopg.connect(conn_string, row_factory=dict_row)
        print(f"✅ Connected to PostgreSQL database: {POSTGRESQL_CONFIG['host']}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return None

def create_postgresql_tables(pg_conn):
    """Create PostgreSQL tables with proper schema"""
    tables_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(200),
        google_id VARCHAR(50),
        has_completed_profiling BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Feature weights table
    CREATE TABLE IF NOT EXISTS feature_weights (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        feature_name VARCHAR(100) NOT NULL,
        weight DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Stock preferences table
    CREATE TABLE IF NOT EXISTS stock_preferences (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        symbol VARCHAR(10) NOT NULL,
        preference_type VARCHAR(20) NOT NULL,
        preference_score DECIMAL(5,4) DEFAULT 0.0000,
        feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        analysis_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Portfolios table
    CREATE TABLE IF NOT EXISTS portfolios (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        holdings JSON NOT NULL,
        total_value DECIMAL(15,2) DEFAULT 0.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Stock analysis table
    CREATE TABLE IF NOT EXISTS stock_analysis (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        symbol VARCHAR(10) NOT NULL,
        analysis_type VARCHAR(50) NOT NULL,
        analysis_data JSON NOT NULL,
        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- User bias profiles table (CFA integration)
    CREATE TABLE IF NOT EXISTS user_bias_profiles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        bias_type VARCHAR(100) NOT NULL,
        bias_score DECIMAL(5,2) NOT NULL,
        detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        mitigation_strategy TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Investment decisions table
    CREATE TABLE IF NOT EXISTS investment_decisions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        symbol VARCHAR(10) NOT NULL,
        decision_type VARCHAR(20) NOT NULL,
        amount DECIMAL(15,2),
        reasoning TEXT,
        biases_detected JSON,
        decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- User risk profiles table
    CREATE TABLE IF NOT EXISTS user_risk_profiles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        risk_tolerance VARCHAR(20) NOT NULL,
        time_horizon INTEGER NOT NULL,
        investment_experience VARCHAR(20) NOT NULL,
        financial_situation VARCHAR(20) NOT NULL,
        profile_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_feature_weights_user ON feature_weights(user_id);
    CREATE INDEX IF NOT EXISTS idx_stock_preferences_user ON stock_preferences(user_id);
    CREATE INDEX IF NOT EXISTS idx_stock_preferences_symbol ON stock_preferences(symbol);
    CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);
    CREATE INDEX IF NOT EXISTS idx_stock_analysis_user ON stock_analysis(user_id);
    CREATE INDEX IF NOT EXISTS idx_stock_analysis_symbol ON stock_analysis(symbol);
    """

    try:
        with pg_conn.cursor() as cursor:
            cursor.execute(tables_sql)
        pg_conn.commit()
        print("✅ PostgreSQL tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating PostgreSQL tables: {e}")
        return False

def migrate_table(sqlite_conn, pg_conn, table_name, columns_mapping=None):
    """Migrate a single table from SQLite to PostgreSQL"""
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            print(f"⚠️  No data found in table: {table_name}")
            return True

        # Prepare PostgreSQL insertion
        with pg_conn.cursor() as pg_cursor:
            # Get column names from first row
            column_names = [description[0] for description in sqlite_cursor.description]

            # Apply column mapping if provided
            if columns_mapping:
                mapped_columns = []
                for col in column_names:
                    mapped_columns.append(columns_mapping.get(col, col))
                column_names = mapped_columns

            placeholders = ', '.join(['%s'] * len(column_names))
            columns_str = ', '.join(column_names)

            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            # Insert data row by row
            successful_inserts = 0
            for row in rows:
                try:
                    # Convert Row object to list
                    row_data = list(row)

                    # Handle JSON fields if necessary
                    for i, value in enumerate(row_data):
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                # Try to parse as JSON
                                json.loads(value)
                                # If successful, keep as string (PostgreSQL will handle JSON)
                            except json.JSONDecodeError:
                                # Not valid JSON, keep as string
                                pass

                    pg_cursor.execute(insert_sql, row_data)
                    successful_inserts += 1
                except Exception as e:
                    print(f"⚠️  Error inserting row in {table_name}: {e}")
                    continue

        pg_conn.commit()
        print(f"✅ Migrated {successful_inserts}/{len(rows)} rows from {table_name}")
        return True

    except Exception as e:
        print(f"❌ Error migrating table {table_name}: {e}")
        return False

def update_sequences(pg_conn):
    """Update PostgreSQL sequences to match the data"""
    tables_with_sequences = [
        'users', 'feature_weights', 'stock_preferences',
        'portfolios', 'stock_analysis', 'user_bias_profiles',
        'investment_decisions', 'user_risk_profiles'
    ]

    try:
        with pg_conn.cursor() as cursor:
            for table in tables_with_sequences:
                # Get the maximum ID from the table
                cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                result = cursor.fetchone()
                max_id = result['max'] if isinstance(result, dict) else result[0]

                # Update the sequence
                if max_id > 0:
                    cursor.execute(f"SELECT setval('{table}_id_seq', %s)", (max_id,))
                    print(f"✅ Updated sequence for {table} to {max_id}")

        pg_conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating sequences: {e}")
        return False

def verify_migration(sqlite_conn, pg_conn):
    """Verify that migration was successful"""
    try:
        sqlite_cursor = sqlite_conn.cursor()

        # Get list of tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]

        print("\n📊 Migration Verification:")
        print("-" * 50)

        total_sqlite_rows = 0
        total_pg_rows = 0

        for table in sqlite_tables:
            try:
                # Count rows in SQLite
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                total_sqlite_rows += sqlite_count

                # Count rows in PostgreSQL
                with pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    result = pg_cursor.fetchone()
                    pg_count = result['count'] if isinstance(result, dict) else result[0]
                    total_pg_rows += pg_count

                status = "✅" if sqlite_count == pg_count else "⚠️"
                print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

            except Exception as e:
                print(f"❌ Error verifying {table}: {e}")

        print("-" * 50)
        print(f"📈 Total: SQLite={total_sqlite_rows}, PostgreSQL={total_pg_rows}")

        if total_sqlite_rows == total_pg_rows:
            print("🎉 Migration completed successfully!")
            return True
        else:
            print("⚠️ Migration completed with some discrepancies")
            return False

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting database migration: SQLite → PostgreSQL (psycopg v3)")
    print("=" * 60)

    # Connect to databases
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        sys.exit(1)

    pg_conn = connect_postgresql()
    if not pg_conn:
        sqlite_conn.close()
        sys.exit(1)

    try:
        # Create PostgreSQL tables
        if not create_postgresql_tables(pg_conn):
            sys.exit(1)

        # Get list of tables to migrate
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        print(f"\n📋 Found {len(tables)} tables to migrate:")
        for table in tables:
            print(f"   - {table}")

        print("\n🔄 Starting migration...")
        print("-" * 30)

        # Migrate each table
        successful_migrations = 0
        for table in tables:
            if migrate_table(sqlite_conn, pg_conn, table):
                successful_migrations += 1
            else:
                print(f"⚠️ Failed to migrate table: {table}")

        print(f"\n📊 Migration Summary: {successful_migrations}/{len(tables)} tables migrated")

        # Update sequences
        if update_sequences(pg_conn):
            print("✅ Sequences updated successfully")

        # Verify migration
        verify_migration(sqlite_conn, pg_conn)

    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        sys.exit(1)

    finally:
        # Clean up connections
        sqlite_conn.close()
        pg_conn.close()
        print("\n🔚 Database connections closed")

if __name__ == "__main__":
    # Confirm before proceeding
    print("⚠️  WARNING: This will migrate data to production PostgreSQL database!")
    print(f"Target: {POSTGRESQL_CONFIG['host']}")
    response = input("Do you want to continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        main()
    else:
        print("❌ Migration cancelled by user")
        sys.exit(0)