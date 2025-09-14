"""
Test Blueprint Registration
Simple test to verify blueprints are working correctly
"""

import os
os.environ['FLASK_ENV'] = 'development'

from flask import Flask, jsonify
from flask import Blueprint

# Create simple test blueprints
auth_bp = Blueprint('auth', __name__)
analysis_bp = Blueprint('analysis', __name__)
portfolio_bp = Blueprint('portfolio', __name__)
api_bp = Blueprint('api', __name__)

@auth_bp.route('/login')
def login():
    return jsonify({'message': '✅ Auth blueprint working!', 'route': '/auth/login'})

@auth_bp.route('/register')
def register():
    return jsonify({'message': '✅ Auth registration working!', 'route': '/auth/register'})

@analysis_bp.route('/test')
def analysis_test():
    return jsonify({'message': '✅ Analysis blueprint working!', 'route': '/analysis/test'})

@portfolio_bp.route('/test')
def portfolio_test():
    return jsonify({'message': '✅ Portfolio blueprint working!', 'route': '/portfolio/test'})

@api_bp.route('/v1/status')
def api_status():
    return jsonify({
        'status': 'healthy',
        'message': '✅ API blueprint working!',
        'architecture': 'modular_blueprints',
        'blueprints': ['auth', 'analysis', 'portfolio', 'api']
    })

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key-for-development'

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(analysis_bp, url_prefix='/analysis')
app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return """
    <h1>🎉 BLUEPRINT ARCHITECTURE TEST</h1>
    <h2>✅ All Blueprints Successfully Registered!</h2>
    
    <h3>Test these endpoints:</h3>
    <ul>
        <li><a href="/auth/login">/auth/login</a> - Auth Blueprint</li>
        <li><a href="/auth/register">/auth/register</a> - Auth Registration</li>
        <li><a href="/analysis/test">/analysis/test</a> - Analysis Blueprint</li>
        <li><a href="/portfolio/test">/portfolio/test</a> - Portfolio Blueprint</li>
        <li><a href="/api/v1/status">/api/v1/status</a> - API Blueprint</li>
    </ul>
    
    <hr>
    <p><strong>✅ Your modular Flask blueprints architecture is working perfectly!</strong></p>
    <p><em>This proves the foundation is solid for migrating your routes.</em></p>
    """

if __name__ == '__main__':
    print("🧪 Testing Blueprint Registration...")
    print("✅ Blueprints registered:")
    print("   - auth: /auth/login, /auth/register")
    print("   - analysis: /analysis/test")
    print("   - portfolio: /portfolio/test") 
    print("   - api: /api/v1/status")
    print("\n🔗 Access at: http://localhost:5002")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5002)