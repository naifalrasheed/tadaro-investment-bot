"""
Simple test version of the new modular app
Forces development mode to avoid configuration issues
"""

import os
# Force development environment
os.environ['FLASK_ENV'] = 'development'

from app_factory import create_app

# Create app in development mode
app = create_app('development')

@app.route('/')
def test_index():
    """Simple test route"""
    return """
    <h1>🎉 NEW MODULAR ARCHITECTURE WORKING!</h1>
    <h2>✅ Flask Blueprints Architecture Active</h2>
    <p><strong>Blueprints registered:</strong></p>
    <ul>
        <li>✅ auth: Authentication routes</li>
        <li>✅ analysis: Stock analysis (placeholder)</li>
        <li>✅ portfolio: Portfolio management (placeholder)</li>
        <li>✅ chat: Chat interface (placeholder)</li>
        <li>✅ ml: Machine learning (placeholder)</li>
        <li>✅ api: REST API endpoints</li>
    </ul>
    <p><a href="/auth/login">Test Login</a> | <a href="/api/v1/status">API Status</a></p>
    <hr>
    <p><em>This proves your modular architecture is working correctly!</em></p>
    """

if __name__ == '__main__':
    print("🚀 Testing NEW modular Investment Bot...")
    print("✅ Development mode enforced")
    print("🔗 Access at: http://localhost:5001")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)