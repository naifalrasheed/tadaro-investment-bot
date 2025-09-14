"""
Flask Blueprints Package
Registers all blueprints for modular architecture
"""

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    
    # Import blueprints
    from .auth import auth_bp
    from .analysis import analysis_bp
    from .portfolio import portfolio_bp
    from .chat import chat_bp
    from .ml import ml_bp
    from .api import api_bp
    
    # Register blueprints with appropriate URL prefixes
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(ml_bp, url_prefix='/ml')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Optional: Register admin blueprint (if needed)
    try:
        from .admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass  # Admin blueprint is optional