"""
Database schema update script.

This script adds the new columns and tables needed for CFA integration.
"""

from app import app, db
from models import User, UserBiasProfile, InvestmentDecision, UserRiskProfile
import sqlalchemy as sa

def update_schema():
    """Update the database schema to add CFA-related tables and columns."""
    print("Starting database schema update...")
    
    # Use app context
    with app.app_context():
        # Check if has_completed_profiling column exists, add if it doesn't
        inspector = sa.inspect(db.engine)
        has_profile_col = False
        
        for column in inspector.get_columns('user'):
            if column['name'] == 'has_completed_profiling':
                has_profile_col = True
                break
        
        if not has_profile_col:
            print("Adding has_completed_profiling column to user table...")
            with db.engine.connect() as conn:
                conn.execute(sa.text('ALTER TABLE user ADD COLUMN has_completed_profiling BOOLEAN DEFAULT FALSE'))
                conn.commit()
            
        # Create the new tables
        print("Creating new tables...")
        db.create_all()
        
        print("Database schema update completed successfully!")

if __name__ == '__main__':
    update_schema()