#!/usr/bin/env python3
"""
Database migration script to fix password_hash column size
This script will update the password_hash column from 128 to 255 characters
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Set up Flask app for database connection
app = Flask(__name__)

# Database configuration - use environment variable or fallback to SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production: Use PostgreSQL from environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development: Use SQLite as fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment_bot.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

def fix_password_column():
    """Fix password_hash column size from 128 to 255 characters"""
    try:
        with app.app_context():
            # Check if we're using PostgreSQL or SQLite
            if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                # PostgreSQL syntax
                sql = "ALTER TABLE \"user\" ALTER COLUMN password_hash TYPE VARCHAR(255);"
            else:
                # SQLite doesn't support ALTER COLUMN TYPE, need to recreate table
                print("SQLite detected - this fix is only needed for PostgreSQL")
                return True

            # Execute the SQL
            db.engine.execute(sql)
            print("✅ Successfully updated password_hash column to 255 characters")
            return True

    except Exception as e:
        print(f"❌ Error updating password_hash column: {str(e)}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing password_hash column size...")

    if fix_password_column():
        print("✅ Database migration completed successfully!")
        print("📝 Users can now register with proper password hashing")
    else:
        print("❌ Database migration failed!")
        sys.exit(1)