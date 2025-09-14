"""
Application Factory
Creates Flask app with modular blueprint architecture
"""

from flask import Flask
from flask_login import LoginManager
from models import db, User
from blueprints import register_blueprints
from config import get_config
from security import SecurityMiddleware, APIKeyRotation
import os
import logging


def create_app(config_name=None):
    """
    Application factory function
    Creates and configures Flask app with all blueprints
    """
    # Determine configuration - default to development for testing
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Force development mode for testing
    if config_name not in ['development', 'testing', 'production']:
        config_name = 'development'
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Validate production configuration
    if config_name == 'production':
        try:
            config.validate_config()
        except ValueError as e:
            logging.error(f"Production configuration error: {e}")
            raise
    
    # Setup logging
    setup_logging(app)
    
    # Initialize security middleware
    security_middleware = SecurityMiddleware(app)
    api_key_rotation = APIKeyRotation(app)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register all blueprints
    register_blueprints(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def setup_logging(app):
    """Setup application logging"""
    if app.config.get('LOG_FILE'):
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup file handler
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        
        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        
        app.logger.info('Application logging started')


def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found', 'status': 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error', 'status': 500}, 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return {'error': 'Forbidden', 'status': 403}, 403


# For backward compatibility and development
if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)