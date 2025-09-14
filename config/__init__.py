"""
Configuration Management
Environment-specific configuration classes
"""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration class with common settings"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-a1b2c3d4e5f6g7h8i9j0')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # API Keys from environment
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'FRFZAADBV18NJXSB')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '15f001975f4746228da3259e64012a69')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///investment_bot.db')
    
    # MongoDB (optional)
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'investment_bot')
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True
    
    # Use environment variables if available, otherwise fallback to base config
    SECRET_KEY = os.environ.get('SECRET_KEY', BaseConfig.SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', BaseConfig.SQLALCHEMY_DATABASE_URI)


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


def get_config(config_name='development'):
    """Get configuration class by name"""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configs.get(config_name, DevelopmentConfig)