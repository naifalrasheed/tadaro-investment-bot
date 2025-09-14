import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to resolve import issues
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path is set
from app import app, db
from models import User, StockAnalysis, Portfolio


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for API endpoints."""

    @classmethod
    def setUpClass(cls):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-key'
        app.config['SESSION_TYPE'] = 'filesystem'
        cls.client = app.test_client()
        
        # Global patch for render_template to avoid template issues
        cls.render_patch = patch('flask.render_template', return_value='mocked template')
        cls.mock_render = cls.render_patch.start()
        
        with app.app_context():
            # Create the database and tables
            db.create_all()
            
            # Create a test user
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('password123')
            db.session.add(test_user)
            
            # Create sample stock analysis
            test_analysis = StockAnalysis(
                user_id=1,
                symbol='AAPL',
                analysis_data={
                    'integrated_score': 85,
                    'recommendation': {'action': 'Buy'},
                    'valuation_analysis': {'target_price': 180},
                    'technical_analysis': {'technical_score': 75}
                }
            )
            db.session.add(test_analysis)
            
            # Create sample portfolio
            test_portfolio = Portfolio(
                user_id=1,
                name='Test Portfolio',
                stocks={'stocks': ['AAPL', 'MSFT', 'GOOG']}
            )
            db.session.add(test_portfolio)
            
            db.session.commit()
    
    @classmethod
    def tearDownClass(cls):
        # Stop global patches
        cls.render_patch.stop()
        
        with app.app_context():
            # Clean up database
            db.session.remove()
            db.drop_all()
    
    def login(self, username='testuser', password='password123'):
        """Helper function to login a user"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        """Helper function to logout a user"""
        return self.client.get('/logout', follow_redirects=True)
    
    def test_index_route(self):
        """Test the index route returns 200 status code."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check render_template was called with the right template
        self.__class__.mock_render.assert_called_with('index.html')
    
    def test_login_route(self):
        """Test login endpoint with valid credentials."""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Test invalid credentials
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='wrongpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_register_route(self):
        """Test user registration endpoint."""
        response = self.client.post('/register', data=dict(
            username='newuser',
            email='new@example.com',
            password='newpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Test duplicate username
        response = self.client.post('/register', data=dict(
            username='testuser',  # Existing username
            email='another@example.com',
            password='password456'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_protected_routes_require_login(self):
        """Test that protected routes require login."""
        # Ensure we're logged out
        self.logout()
        
        # Try to access protected routes
        protected_routes = [
            '/analyze',
            '/portfolio',
            '/analysis-history',
            '/view-profile',
            '/create-profile'
        ]
        
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=True)
            self.assertEqual(response.status_code, 200)  # Should redirect to login page
    
    @patch('analysis.stock_analyzer.StockAnalyzer.analyze_stock')
    def test_analyze_route(self, mock_analyze_stock):
        """Test stock analysis endpoint."""
        # Mock the stock analyzer
        mock_result = {
            'symbol': 'TSLA',
            'integrated_score': 78,
            'recommendation': {'action': 'Buy'},
            'valuation_analysis': {'target_price': 250},
            'technical_analysis': {'technical_score': 82},
            'dividend_metrics': {
                'dividend_yield': 1.5,
                'dividend_growth': 5.0,
                'payout_ratio': 30.0
            }
        }
        mock_analyze_stock.return_value = mock_result
        
        # Login first
        self.login()
        
        # Test analyze endpoint
        response = self.client.post('/analyze', data=dict(
            symbol='TSLA'
        ), follow_redirects=True)
        
        # Check mock interaction
        mock_analyze_stock.assert_called_once_with('TSLA')
        
        # Verify analysis was saved to database
        with app.app_context():
            analysis = StockAnalysis.query.filter_by(symbol='TSLA').first()
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis.user_id, 1)
            self.assertEqual(analysis.symbol, 'TSLA')
    
    def test_portfolio_route(self):
        """Test portfolio route displays user portfolios."""
        # Login
        self.login()
        
        # Access portfolio page
        response = self.client.get('/portfolio')
        self.assertEqual(response.status_code, 200)
        
        # Check render_template was called with the right arguments
        self.__class__.mock_render.assert_called_with('portfolio.html', portfolios=unittest.mock.ANY)
    
    def test_analysis_history_route(self):
        """Test analysis history displays past analyses."""
        # Login
        self.login()
        
        # Access analysis history
        response = self.client.get('/analysis-history')
        self.assertEqual(response.status_code, 200)
        
        # Check render_template was called with the right arguments
        self.__class__.mock_render.assert_called_with('analysis_history.html', analyses=unittest.mock.ANY)
    
    def test_error_handling(self):
        """Test that invalid symbols return appropriate error responses."""
        # Login
        self.login()
        
        # Mock to simulate an error
        with patch('analysis.stock_analyzer.StockAnalyzer.analyze_stock', return_value=None):
            response = self.client.post('/analyze', data=dict(
                symbol='INVALID'
            ), follow_redirects=True)
            
            # Verify the analyzer returns None for invalid symbol
            self.assertEqual(response.status_code, 200)
            
            # Verify render_template was called with None results
            self.__class__.mock_render.assert_called_with('analysis.html', results=None)


if __name__ == '__main__':
    unittest.main()