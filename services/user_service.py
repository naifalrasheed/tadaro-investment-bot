"""
User Service
Business logic for user management, authentication, and profiles  
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from models import db, User, FeatureWeight
from flask_login import login_user

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user-related business logic"""
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user with proper initialization"""
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                raise ValueError("Username already exists")
            
            if User.query.filter_by(email=email).first():
                raise ValueError("Email already exists")
            
            # Create user
            user = User(username=username, email=email)
            user.set_password(password)
            user.has_completed_profiling = False
            
            db.session.add(user)
            db.session.commit()
            
            # Initialize feature weights
            feature_weights = FeatureWeight(user_id=user.id)
            db.session.add(feature_weights)
            db.session.commit()
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created': True
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.session.rollback()
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            return user
        
        return None
    
    # Additional user methods will be added here