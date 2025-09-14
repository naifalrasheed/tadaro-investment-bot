"""
New Modular Application Entry Point
Uses the app factory pattern with blueprints
Run this to test the new architecture alongside the old app.py
"""

from app_factory import create_app
from config import get_config
import os

# Create app using factory pattern
app = create_app()

# Add index route for backward compatibility
from flask import render_template, request, redirect, url_for
from flask_login import current_user
from services.stock_service import StockService
from services.api_client import UnifiedAPIClient

# Initialize services
api_client = UnifiedAPIClient(
    alpha_vantage_key=app.config.get('ALPHA_VANTAGE_API_KEY'),
    news_api_key=app.config.get('NEWS_API_KEY')
)
stock_service = StockService(api_client)

@app.route('/')
def index():
    """Main index route with new service layer"""
    recommended_stocks = []
    
    if current_user.is_authenticated:
        try:
            # Get personalized recommendations using new service layer
            recommended_stocks = stock_service.get_user_recommendations(
                current_user.id, limit=5
            )
        except Exception as e:
            app.logger.error(f"Error getting recommendations: {e}")
            recommended_stocks = []
    
    return render_template('index.html', recommended_stocks=recommended_stocks)

@app.route('/user_profiling')
def user_profiling():
    """Redirect to auth blueprint profiling"""
    return redirect(url_for('auth.create_profile'))

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        from models import User
        user_count = User.query.count()
        
        # Test API client health
        api_health = api_client.health_check()
        
        return {
            'status': 'healthy',
            'database': {'status': 'connected', 'users': user_count},
            'apis': api_health,
            'architecture': 'modular_blueprints',
            'timestamp': app.config.get('timestamp', 'unknown')
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    print("🚀 Starting NEW modular Investment Bot with Blueprints architecture...")
    print("📊 Blueprints registered:")
    print("  - auth: /login, /register, /logout, /create-profile")
    print("  - analysis: /analysis/* (placeholder)")
    print("  - portfolio: /portfolio/* (placeholder)")
    print("  - chat: /chat/* (placeholder)")
    print("  - ml: /ml/* (placeholder)")
    print("  - api: /api/* (health check active)")
    print("\n✅ New service layer active with centralized API client")
    print("🔗 Access health check at: http://localhost:5000/api/health")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)  # Different port to avoid conflict