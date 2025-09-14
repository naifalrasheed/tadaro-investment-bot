#!/usr/bin/env python3
"""
Universal Database Adapter - Works with both psycopg2 and psycopg v3
Automatically detects and uses the available PostgreSQL driver
"""

import sys
import os

# Try to import available PostgreSQL drivers
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DRIVER_TYPE = 'psycopg2'
    print("✅ Using psycopg2 driver")
except ImportError:
    try:
        import psycopg
        from psycopg.rows import dict_row
        DRIVER_TYPE = 'psycopg3'
        print("✅ Using psycopg v3 driver")
    except ImportError:
        print("❌ No PostgreSQL driver found. Install either psycopg2-binary or psycopg[binary]")
        sys.exit(1)

# Database configuration - CORRECTED HOSTNAME
DB_CONFIG = {
    'host': 'db-tradaro-ai.cmp4g2awon0q.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'naif_alrasheed',
    'password': 'CodeNaif123'
}

def get_connection():
    """Get database connection using available driver"""
    if DRIVER_TYPE == 'psycopg2':
        return psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
    elif DRIVER_TYPE == 'psycopg3':
        conn_string = (
            f"host={DB_CONFIG['host']} "
            f"port={DB_CONFIG['port']} "
            f"dbname={DB_CONFIG['database']} "
            f"user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']}"
        )
        return psycopg.connect(conn_string, row_factory=dict_row)

def get_cursor(conn):
    """Get cursor with dict-like results"""
    if DRIVER_TYPE == 'psycopg2':
        return conn.cursor(cursor_factory=RealDictCursor)
    elif DRIVER_TYPE == 'psycopg3':
        return conn.cursor()

def test_connection():
    """Test database connection"""
    try:
        conn = get_connection()
        cursor = get_cursor(conn)
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"📊 PostgreSQL Version: {version['version'] if DRIVER_TYPE == 'psycopg2' else version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def setup_database():
    """Set up database tables"""
    try:
        conn = get_connection()
        cursor = get_cursor(conn)

        # Read SQL setup file
        sql_file = os.path.join(os.path.dirname(__file__), 'quick_db_setup.sql')
        with open(sql_file, 'r') as f:
            sql_content = f.read()

        # Execute SQL commands
        cursor.execute(sql_content)
        conn.commit()

        print("✅ Database schema created successfully!")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main function to test and setup database"""
    print("🚀 Universal Database Adapter - Testing Connection")
    print("=" * 50)

    # Test connection
    if test_connection():
        print("\n🔧 Setting up database schema...")
        if setup_database():
            print("🎉 Database setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Your PostgreSQL database is ready for production")
            print("2. Update your application configuration")
            print("3. Deploy to AWS App Runner")
        else:
            print("⚠️ Database setup encountered issues")
    else:
        print("⚠️ Cannot proceed without database connection")

if __name__ == "__main__":
    main()