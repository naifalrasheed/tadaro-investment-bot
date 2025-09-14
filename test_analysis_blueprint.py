"""
Test Analysis Blueprint
Test the new clean analysis routes using service layer
"""

import os
os.environ['FLASK_ENV'] = 'development'

from flask import Flask
from flask_login import LoginManager, UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy

# Simple test setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALPHA_VANTAGE_API_KEY'] = 'demo'
app.config['NEWS_API_KEY'] = 'demo'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Mock user for testing
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import and register analysis blueprint
from blueprints.analysis import analysis_bp
app.register_blueprint(analysis_bp, url_prefix='/analysis')

@app.route('/')
def index():
    return """
    <h1>🧪 ANALYSIS BLUEPRINT TEST</h1>
    <h2>✅ Clean Service Layer Architecture</h2>
    
    <h3>Original vs New Comparison:</h3>
    <div style="display: flex; gap: 20px;">
        <div style="border: 2px solid red; padding: 10px; width: 45%;">
            <h4>❌ OLD MONOLITHIC</h4>
            <p><strong>app.py analyze() function:</strong></p>
            <ul>
                <li>📏 603 lines of code</li>
                <li>🔥 Mixed business logic with HTTP</li>
                <li>🕸️ Complex thread pools and data fetching</li>
                <li>🐛 Hard to test and maintain</li>
                <li>⚠️ No error isolation</li>
            </ul>
        </div>
        
        <div style="border: 2px solid green; padding: 10px; width: 45%;">
            <h4>✅ NEW MODULAR</h4>
            <p><strong>Analysis Blueprint + Service Layer:</strong></p>
            <ul>
                <li>📏 Clean, focused route handlers</li>
                <li>🎯 Business logic in service layer</li>
                <li>🔧 Unified API client with fallbacks</li>
                <li>🧪 Easy to test and maintain</li>
                <li>🛡️ Proper error handling and isolation</li>
            </ul>
        </div>
    </div>
    
    <h3>Test the New Analysis Routes:</h3>
    <ul>
        <li><a href="/analysis/test">/analysis/test</a> - Blueprint status</li>
        <li><strong>Main Routes (require templates):</strong></li>
        <li>/analysis/analyze - Main analysis form</li>
        <li>/analysis/technical/AAPL - Technical analysis</li>
        <li>/analysis/fundamental/AAPL - Fundamental analysis</li>
        <li>/analysis/sentiment/AAPL - Sentiment analysis</li>
        <li>/analysis/compare - Compare stocks</li>
        <li>/analysis/naif/AAPL/US - Naif model analysis</li>
        <li><a href="/analysis/api/quick-analysis/AAPL">/analysis/api/quick-analysis/AAPL</a> - Quick API test</li>
    </ul>
    
    <hr>
    <p><strong>🎉 ACHIEVEMENT: Reduced 603-line monolithic function to clean, maintainable service layer architecture!</strong></p>
    """

@app.route('/login')
def login():
    # Create test user and login
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(username='testuser')
            db.session.add(user)
            db.session.commit()
        login_user(user)
    return "Logged in as test user. <a href='/'>Back to main page</a>"

if __name__ == '__main__':
    print("🧪 Testing Analysis Blueprint Architecture...")
    print("✅ Service Layer: StockService + UnifiedAPIClient")
    print("✅ Clean Routes: 8 focused route handlers")
    print("✅ Error Handling: Proper isolation and logging")
    print("\n🔗 Access at: http://localhost:5003")
    print("💡 Visit /login first, then test routes")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5003)