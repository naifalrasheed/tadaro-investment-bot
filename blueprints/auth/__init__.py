"""
Authentication Blueprint
Handles user registration, login, logout, and profile management
"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Import routes after blueprint creation to avoid circular imports
try:
    from . import routes
except ImportError as e:
    print(f"Warning: Could not import auth routes: {e}")