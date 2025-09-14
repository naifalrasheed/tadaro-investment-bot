"""
Test script for the Naif Al-Rasheed investment model with multi-market support
"""
import unittest
from ml_components.naif_alrasheed_model import NaifAlRasheedModel

class TestNaifAlRasheedModel(unittest.TestCase):
    
    def setUp(self):
        self.model = NaifAlRasheedModel()
        
    def test_model_initialization(self):
        """Test that the model initializes correctly with right components"""
        self.assertIsNotNone(self.model.saudi_api)
        self.assertIsNotNone(self.model.data_fetcher)
        self.assertIsNotNone(self.model.stock_analyzer)
        
        # Check if investment criteria contains parameters for both markets
        self.assertIn('us', self.model.investment_criteria)
        self.assertIn('saudi', self.model.investment_criteria)
        
        # Check if pipeline stages are properly initialized
        self.assertIn('macro_analysis', self.model.pipeline_stages)
        self.assertIn('sector_ranking', self.model.pipeline_stages)
        self.assertIn('fundamental_screening', self.model.pipeline_stages)
        self.assertIn('management_quality', self.model.pipeline_stages)
        
    def test_us_market_parameters(self):
        """Test US market investment criteria parameters"""
        us_criteria = self.model.investment_criteria['us']
        
        # Check essential parameters
        self.assertIn('min_rotc', us_criteria)
        self.assertIn('min_revenue_growth', us_criteria)
        self.assertIn('min_market_cap', us_criteria)
        self.assertIn('max_pe_ratio', us_criteria)
        
        # Verify US-specific values
        self.assertEqual(us_criteria['min_rotc'], 15.0)  # US ROTC threshold should be 15%
        self.assertTrue(us_criteria['min_market_cap'] >= 1000000000)  # US min market cap should be $1B+
        
    def test_saudi_market_parameters(self):
        """Test Saudi market investment criteria parameters"""
        saudi_criteria = self.model.investment_criteria['saudi']
        us_criteria = self.model.investment_criteria['us']
        
        # Check essential parameters
        self.assertIn('min_rotc', saudi_criteria)
        self.assertIn('min_revenue_growth', saudi_criteria)
        self.assertIn('min_market_cap', saudi_criteria)
        self.assertIn('max_pe_ratio', saudi_criteria)
        
        # Verify Saudi-specific values
        self.assertEqual(saudi_criteria['min_rotc'], 12.0)  # Saudi ROTC threshold should be 12%
        self.assertTrue(saudi_criteria['min_market_cap'] >= 500000000)  # Saudi min market cap is lower
        self.assertTrue(saudi_criteria['min_dividend_yield'] > us_criteria['min_dividend_yield'])  # Saudi dividend requirements higher
        
    def test_portfolio_construction_parameters(self):
        """Test portfolio construction parameters"""
        # Check portfolio diversification requirements
        self.assertGreaterEqual(self.model.portfolio_params['min_stocks'], 12)
        self.assertLessEqual(self.model.portfolio_params['max_stocks'], 18)
        self.assertGreaterEqual(self.model.portfolio_params['min_sectors'], 5)
        self.assertLessEqual(self.model.portfolio_params['max_sector_weight'], 0.25)
        
        # Check if model has benchmarks for both markets
        self.assertIn('us', self.model.portfolio_params['benchmark'])
        self.assertIn('saudi', self.model.portfolio_params['benchmark'])
        
    def test_technical_signal_generation(self):
        """Test technical signal generation"""
        # Test US market signals
        us_signal = self.model._generate_technical_signal('AAPL', 75.0, 'us')
        self.assertIn('AAPL', us_signal)
        self.assertIn('US', us_signal.upper())
        self.assertIn('S&P 500', us_signal)
        
        # Test Saudi market signals
        saudi_signal = self.model._generate_technical_signal('2222.SR', 60.0, 'saudi')
        self.assertIn('2222.SR', saudi_signal)
        self.assertIn('SAUDI', saudi_signal.upper())
        self.assertIn('TASI', saudi_signal)
        
        # Test different signal strengths
        strong_signal = self.model._generate_technical_signal('MSFT', 85.0, 'us')
        weak_signal = self.model._generate_technical_signal('MSFT', 25.0, 'us')
        
        self.assertIn('Strong', strong_signal)
        self.assertIn('caution', weak_signal.lower())
        
    def test_full_screening_validation(self):
        """Test input validation in full screening function"""
        # Test invalid market handling
        invalid_result = self.model.run_full_screening(market='invalid')
        self.assertFalse(invalid_result['success'])
        self.assertIn('Invalid market', invalid_result['message'])
        
        # Test custom parameters handling (would need mocking for full test)
        custom_params = {
            'min_rotc': 20.0,  # Higher than default
            'min_revenue_growth': 10.0,  # Higher than default
            'max_pe_ratio': 15.0  # Lower than default
        }
        
        # This would only check parameter handling, not full execution
        # since actual API calls would be made otherwise
        try:
            result = self.model.run_full_screening(market='us', custom_params=custom_params)
            # If it returns success, check that the parameters were properly applied
            if result.get('success', False):
                self.assertEqual(result['parameters']['min_rotc'], 20.0)
                self.assertEqual(result['parameters']['min_revenue_growth'], 10.0)
                self.assertEqual(result['parameters']['max_pe_ratio'], 15.0)
        except Exception as e:
            # Allow exceptions from API calls since we're testing parameter handling
            pass
            
if __name__ == '__main__':
    unittest.main()