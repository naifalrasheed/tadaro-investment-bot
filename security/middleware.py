"""
Security Middleware for Production
Comprehensive security features including rate limiting, CORS, and security headers
"""

import time
import logging
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import request, jsonify, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Comprehensive security middleware for production"""
    
    def __init__(self, app=None):
        self.app = app
        self.rate_limiter = None
        self.request_counts = defaultdict(lambda: deque())
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        # Initialize rate limiting
        self.setup_rate_limiting()
        
        # Setup CORS
        self.setup_cors()
        
        # Setup security headers
        self.setup_security_headers()
        
        # Setup request logging
        self.setup_request_logging()
    
    def setup_rate_limiting(self):
        """Setup rate limiting for API endpoints"""
        def rate_limit_key():
            # Use IP address and user ID if authenticated
            key = get_remote_address()
            if hasattr(g, 'current_user') and g.current_user.is_authenticated:
                key += f":{g.current_user.id}"
            return key
        
        self.rate_limiter = Limiter(
            app=self.app,
            key_func=rate_limit_key,
            default_limits=[self.app.config.get('RATELIMIT_DEFAULT', '100 per hour')],
            storage_uri=self.app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
        )
        
        # Custom rate limits for different endpoints
        self.setup_endpoint_limits()
    
    def setup_endpoint_limits(self):
        """Setup specific rate limits for different endpoint types"""
        
        @self.rate_limiter.limit("10 per minute", exempt_when=lambda: current_app.config.get('TESTING', False))
        def limit_analysis_endpoints():
            """Rate limit for analysis endpoints"""
            return request.endpoint and 'analysis' in request.endpoint
        
        @self.rate_limiter.limit("50 per hour", exempt_when=lambda: current_app.config.get('TESTING', False))
        def limit_chat_endpoints():
            """Rate limit for chat endpoints (Claude API calls)"""
            return request.endpoint and 'chat' in request.endpoint
        
        @self.rate_limiter.limit("20 per minute", exempt_when=lambda: current_app.config.get('TESTING', False))
        def limit_portfolio_endpoints():
            """Rate limit for portfolio endpoints"""
            return request.endpoint and 'portfolio' in request.endpoint
    
    def setup_cors(self):
        """Setup Cross-Origin Resource Sharing"""
        cors_origins = self.app.config.get('CORS_ORIGINS', [])
        
        if cors_origins and cors_origins != ['']:
            CORS(self.app, 
                 origins=cors_origins,
                 methods=['GET', 'POST', 'PUT', 'DELETE'],
                 allow_headers=['Content-Type', 'Authorization'],
                 supports_credentials=True)
        else:
            # Development mode - allow all origins
            CORS(self.app, supports_credentials=True)
    
    def setup_security_headers(self):
        """Setup security headers for all responses"""
        
        @self.app.after_request
        def add_security_headers(response):
            """Add security headers to all responses"""
            
            # Content Security Policy
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: wss:;"
            )
            
            # Other security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # HTTPS enforcement in production
            if not self.app.config.get('SSL_DISABLE', False):
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # API-specific headers
            if request.endpoint and 'api' in request.endpoint:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            
            return response
    
    def setup_request_logging(self):
        """Setup comprehensive request logging"""
        
        @self.app.before_request
        def log_request_info():
            """Log request information for security monitoring"""
            
            # Skip logging for static files
            if request.endpoint == 'static':
                return
            
            # Log request details
            logger.info(f"Request: {request.method} {request.path} from {get_remote_address()}")
            
            # Log suspicious activity
            if self.is_suspicious_request(request):
                logger.warning(f"Suspicious request: {request.method} {request.path} from {get_remote_address()}")
            
            # Track request timing
            g.request_start_time = time.time()
        
        @self.app.after_request
        def log_response_info(response):
            """Log response information"""
            
            if hasattr(g, 'request_start_time'):
                duration = time.time() - g.request_start_time
                
                # Log slow requests
                if duration > 5.0:  # 5 seconds
                    logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
                
                # Log errors
                if response.status_code >= 400:
                    logger.warning(f"Error response: {response.status_code} for {request.method} {request.path}")
            
            return response
    
    def is_suspicious_request(self, request):
        """Check if a request looks suspicious"""
        suspicious_patterns = [
            'script', 'alert', 'javascript:', 'vbscript:',
            '../', '..\\', '/etc/', '/var/', '/usr/',
            'union', 'select', 'drop', 'delete', 'insert',
            'onload', 'onerror', 'onclick'
        ]
        
        # Check URL and parameters
        full_url = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in full_url:
                return True
        
        # Check for unusual user agents
        user_agent = request.headers.get('User-Agent', '').lower()
        if not user_agent or any(bot in user_agent for bot in ['bot', 'crawler', 'spider']) and 'googlebot' not in user_agent:
            # Allow legitimate bots but flag others
            pass
        
        return False

class APIKeyRotation:
    """Manage API key rotation for enhanced security"""
    
    def __init__(self, app=None):
        self.app = app
        self.key_usage = defaultdict(int)
        self.key_rotation_threshold = 10000  # Rotate after 10k calls
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def track_api_usage(self, api_name, key):
        """Track API key usage"""
        key_id = f"{api_name}:{key[:8]}..."  # Log partial key for tracking
        self.key_usage[key_id] += 1
        
        if self.key_usage[key_id] > self.key_rotation_threshold:
            logger.warning(f"API key {key_id} has exceeded usage threshold")
            # In production, you'd implement actual key rotation here
    
    def get_api_key(self, api_name):
        """Get API key with usage tracking"""
        key_env_var = f"{api_name.upper()}_API_KEY"
        key = self.app.config.get(key_env_var)
        
        if key:
            self.track_api_usage(api_name, key)
        
        return key

# Rate limiting decorators for specific use cases
def limit_api_calls(limit_string):
    """Decorator for custom rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Custom rate limiting logic here
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(api_name):
    """Decorator to require valid API key"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = current_app.config.get(f"{api_name.upper()}_API_KEY")
            if not api_key:
                logger.error(f"Missing API key for {api_name}")
                return jsonify({'error': 'Service temporarily unavailable'}), 503
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize security components
security_middleware = SecurityMiddleware()
api_key_rotation = APIKeyRotation()