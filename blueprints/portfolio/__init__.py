"""
Portfolio Management Blueprint
Handles portfolio creation, management, and optimization
"""

from flask import Blueprint

portfolio_bp = Blueprint('portfolio', __name__, template_folder='templates')

from . import routes