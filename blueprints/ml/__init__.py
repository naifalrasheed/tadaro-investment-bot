"""
Machine Learning Blueprint
Handles ML features, adaptive learning, and Naif model
"""

from flask import Blueprint

ml_bp = Blueprint('ml', __name__, template_folder='templates')

from . import routes