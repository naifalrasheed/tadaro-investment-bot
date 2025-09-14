"""
Production Configuration with Enhanced Security
Secure configuration for production deployment
"""

import os
import secrets
from datetime import timedelta

class ProductionConfig:
    """Production configuration with security best practices"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///production_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # API Security
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # API Keys (with validation)
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY')  # Saudi market data
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/production.log')
    
    # Cache Configuration
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # SSL Configuration
    SSL_DISABLE = False
    PREFERRED_URL_SCHEME = 'https'
    
    @staticmethod
    def validate_config():
        """Validate that all required configuration is present"""
        required_keys = [
            'SECRET_KEY',
            'ALPHA_VANTAGE_API_KEY',
            'CLAUDE_API_KEY'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not os.environ.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        return True

class DevelopmentSecureConfig(ProductionConfig):
    """Development config with security features for testing"""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///secure_development.db'
    
    # Security (relaxed for development)
    SESSION_COOKIE_SECURE = False  # HTTP allowed in development
    SSL_DISABLE = True
    PREFERRED_URL_SCHEME = 'http'
    
    # Rate limiting (more permissive)
    RATELIMIT_DEFAULT = "1000 per hour"
    
    @staticmethod
    def validate_config():
        """Relaxed validation for development"""
        required_keys = ['SECRET_KEY']  # Minimal requirements
        
        missing_keys = []
        for key in required_keys:
            if not os.environ.get(key) and key == 'SECRET_KEY':
                # Auto-generate for development
                os.environ['SECRET_KEY'] = secrets.token_hex(32)
        
        return True