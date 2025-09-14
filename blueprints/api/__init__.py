"""
REST API Blueprint
Handles RESTful API endpoints for frontend consumption
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import routes