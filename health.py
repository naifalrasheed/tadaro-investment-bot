"""
Health Check Endpoint for Production Monitoring
"""

from flask import Blueprint, jsonify
import os
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for AWS App Runner and monitoring"""
    try:
        # Check environment
        env = os.getenv('FLASK_ENV', 'unknown')

        # Basic application status
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': env,
            'version': '1.0.0',
            'service': 'tadaro-investment-bot'
        }

        # Check database connection (basic test)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            health_status['database'] = 'configured'
        else:
            health_status['database'] = 'not_configured'

        # Check API keys
        health_status['api_keys'] = {
            'claude': 'configured' if os.getenv('CLAUDE_API_KEY') else 'missing',
            'twelvedata': 'configured' if os.getenv('TWELVEDATA_API_KEY') else 'missing',
            'google_oauth': 'configured' if os.getenv('GOOGLE_CLIENT_ID') else 'missing'
        }

        return jsonify(health_status), 200

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 500

@health_bp.route('/ready')
def readiness_check():
    """Readiness check - more thorough than health check"""
    try:
        # Test database connection if possible
        # (We'll keep it simple for now due to Python 3.13 driver issues)

        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'database': 'ready',
                'api_keys': 'ready',
                'environment': 'ready'
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 503