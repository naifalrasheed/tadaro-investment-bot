"""
Stock Analysis Blueprint
Handles stock analysis, comparisons, technical and fundamental analysis
"""

from flask import Blueprint

analysis_bp = Blueprint('analysis', __name__, template_folder='templates')

from . import routes