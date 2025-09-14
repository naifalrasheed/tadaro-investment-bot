
import unittest
import logging
import os
import sys

# Get the path to the 'src' directory
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add to Python path if not already there
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
from datetime import datetime

# Rest of your test file remains the same...

# Rest of your test file remains the same...

class TestIntegratedAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before all tests"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
        # Initialize analyzer
        cls.analyzer = IntegratedAnalysis()
        
        # Test stocks representing different scenarios
        cls.test_stocks = {
            'value': 'JNJ',      # Value stock
            'growth': 'SHOP',    # Growth stock
            'blend': 'AAPL',     # Blend of value and growth
            'high_vol': 'TSLA'   # High volatility stock
        }

    def test_basic_initialization(self):
        """Test if the analyzer can be initialized"""
        self.assertIsInstance(self.analyzer, IntegratedAnalysis)
        self.logger.info("Basic initialization test passed")

    def test_single_stock_analysis(self):
        """Test analysis with a single stock first"""
        symbol = 'AAPL'
        self.logger.info(f"\nTesting analysis for {symbol}")

        try:
            result = self.analyzer.analyze_stock(symbol)
            self.assertIsInstance(result, dict)
            
            if result:
                self.logger.info(f"Analysis completed for {symbol}")
                self.logger.info(f"Result keys: {list(result.keys())}")
                self.logger.info(f"Intermediate Results for {symbol}: {result}")
            else:
                self.logger.warning("Empty result returned")
                
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            raise

if __name__ == '__main__':
    unittest.main(verbosity=2)

    def test_valuation_integration(self):
        """Test valuation component integration"""
        for stock_type, symbol in self.test_stocks.items():
            self.logger.info(f"\nTesting valuation for {symbol}")
            
            result = self.analyzer.analyze_stock(symbol)
            valuation = result.get('valuation_analysis', {})
            
            if valuation.get('success', False):
                self.assertIn('target_price', valuation)
                self.assertIn('primary_method', valuation)
                self.assertGreater(valuation.get('confidence', 0), 0)
                
                self.logger.info(f"Target Price: ${valuation.get('target_price', 0):.2f}")
                self.logger.info(f"Method: {valuation.get('primary_method', 'Unknown')}")
                self.logger.info(f"Confidence: {valuation.get('confidence', 0):.2%}")

    def test_risk_metrics(self):
        """Test risk metrics calculation"""
        for stock_type, symbol in self.test_stocks.items():
            self.logger.info(f"\nTesting risk metrics for {symbol}")
            
            try:
                result = self.analyzer.analyze_stock(symbol)
                risk_metrics = result.get('risk_metrics', {})
                
                if risk_metrics:
                    self._verify_risk_metrics(risk_metrics)
                    self._log_risk_metrics(risk_metrics, symbol)
                else:
                    self.logger.warning(f"No risk metrics available for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Error testing risk metrics for {symbol}: {str(e)}")
                continue

    def _verify_risk_metrics(self, risk_metrics):
        """Verify risk metrics are within expected ranges"""
        try:
            if risk_metrics.get('volatility') is not None:
                self.assertGreaterEqual(risk_metrics['volatility'], 0)
            if risk_metrics.get('max_drawdown') is not None:
                self.assertLessEqual(risk_metrics['max_drawdown'], 0)
            if risk_metrics.get('risk_level') is not None:
                self.assertIn(risk_metrics['risk_level'], ['Low', 'Moderate', 'High'])
        except AssertionError as e:
            self.logger.error(f"Risk metrics verification failed: {str(e)}")
            raise

    def _verify_risk_metrics(self, risk_metrics):
        """Verify risk metrics are within expected ranges"""
        self.assertGreaterEqual(risk_metrics.get('volatility', 0), 0)
        self.assertLessEqual(risk_metrics.get('max_drawdown', 0), 0)
        self.assertIn('risk_level', risk_metrics)
        self.assertIn(risk_metrics['risk_level'], ['Low', 'Moderate', 'High'])

    def _log_analysis_results(self, result, symbol, stock_type):
        """Log detailed analysis results"""
        self.logger.info(f"\nAnalysis Results for {symbol} ({stock_type})")
        self.logger.info(f"Company Type: {result.get('company_type', 'Unknown')}")
        self.logger.info(f"Integrated Score: {result['integrated_score']:.2f}")
        
        recommendation = result.get('recommendation', {})
        self.logger.info("\nRecommendation:")
        self.logger.info(f"Action: {recommendation.get('action', 'Unknown')}")
        
        if 'reasoning' in recommendation:
            self.logger.info("Reasoning:")
            for reason in recommendation['reasoning']:
                self.logger.info(f"- {reason}")

    def _log_risk_metrics(self, risk_metrics, symbol):
        """Log risk metrics"""
        self.logger.info(f"\nRisk Metrics for {symbol}")
        self.logger.info(f"Volatility: {risk_metrics.get('volatility', 0):.1f}%")
        self.logger.info(f"Max Drawdown: {risk_metrics.get('max_drawdown', 0):.1f}%")
        self.logger.info(f"Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.2f}")
        self.logger.info(f"Risk Level: {risk_metrics.get('risk_level', 'Unknown')}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
    def _verify_analysis_components(self, result):
        """Verify all analysis components are present and valid"""
        # Fundamental analysis checks
        fundamental = result.get('fundamental_analysis', {})
        self.assertIsInstance(fundamental.get('score', 0), (int, float))
        self.assertTrue(0 <= fundamental.get('score', 0) <= 100)
        
        # Technical analysis checks
        technical = result.get('technical_analysis', {})
        self.assertIsInstance(technical.get('technical_score', 0), (int, float))
        self.assertTrue(0 <= technical.get('technical_score', 0) <= 100)
        
        # Valuation analysis checks
        valuation = result.get('valuation_analysis', {})
        if valuation.get('success', False):
            self.assertIn('target_price', valuation)
            self.assertIn('primary_method', valuation)
            self.assertGreater(valuation.get('confidence', 0), 0)
        
        # Integrated score checks
        self.assertIsInstance(result['integrated_score'], (int, float))
        self.assertTrue(0 <= result['integrated_score'] <= 100)

    def test_valuation_score_calculation(self):
        """Test the calculation of valuation scores"""
        test_cases = [
            {
                'name': 'Positive upside',
                'valuation': {
                    'success': True,
                    'target_price': 200,
                    'current_price': 180,
                    'confidence': 0.8,
                    'upside_potential': 11.11
                },
                'expected_min': 50,
                'expected_max': 100
            },
            {
                'name': 'Negative upside',
                'valuation': {
                    'success': True,
                    'target_price': 160,
                    'current_price': 180,
                    'confidence': 0.8,
                    'upside_potential': -11.11
                },
                'expected_min': 0,
                'expected_max': 50
            },
            {
                'name': 'Failed valuation',
                'valuation': {
                    'success': False
                },
                'expected_min': 45,
                'expected_max': 55
            }
        ]
        
        for case in test_cases:
            self.logger.info(f"\nTesting valuation score - {case['name']}")
            score = self.analyzer.calculate_valuation_score(case['valuation'])
            
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, case['expected_min'])
            self.assertLessEqual(score, case['expected_max'])
            self.logger.info(f"Score: {score:.2f}")

    def test_integrated_score_with_valuation(self):
        """Test integrated score calculation including valuation component"""
        symbol = 'AAPL'  # Use a stable stock for testing
        self.logger.info(f"\nTesting integrated score calculation with valuation for {symbol}")
        
        result = self.analyzer.analyze_stock(symbol)
        if not result:
            self.logger.warning("Could not get analysis results")
            return
            
        integrated_score = result.get('integrated_score', 0)
        valuation = result.get('valuation_analysis', {})
        
        # Verify score components
        self.assertIsInstance(integrated_score, float)
        self.assertGreaterEqual(integrated_score, 0)
        self.assertLessEqual(integrated_score, 100)
        
        # Log detailed results
        self.logger.info(f"Integrated Score: {integrated_score:.2f}")
        if valuation.get('success', False):
            self.logger.info(f"Valuation Method: {valuation.get('primary_method', 'Unknown')}")
            self.logger.info(f"Target Price: ${valuation.get('target_price', 0):.2f}")
            self.logger.info(f"Upside Potential: {valuation.get('upside_potential', 0):.1f}%")

    def test_recommendation_with_valuation(self):
        """Test recommendation generation with valuation insights"""
        for stock_type, symbol in self.test_stocks.items():
            self.logger.info(f"\nTesting recommendation with valuation for {symbol} ({stock_type})")
            
            result = self.analyzer.analyze_stock(symbol)
            if not result:
                continue
                
            recommendation = result.get('recommendation', {})
            valuation = result.get('valuation_analysis', {})
            
            # Verify recommendation structure
            self.assertIn('action', recommendation)
            self.assertIn('reasoning', recommendation)
            self.assertIn('valuation_confidence', recommendation)
            
            # Log recommendation details
            self.logger.info(f"Action: {recommendation.get('action', 'Unknown')}")
            self.logger.info("Reasoning:")
            for reason in recommendation.get('reasoning', []):
                self.logger.info(f"- {reason}")
                
            # Verify valuation integration
            if valuation.get('success', False):
                self.assertTrue(
                    any('valuation' in reason.lower() for reason in recommendation.get('reasoning', []))
                )

    def test_edge_cases(self):
        """Test handling of edge cases"""
        edge_cases = [
            {
                'name': 'High volatility stock',
                'symbol': 'TSLA',
                'check': lambda r: r.get('recommendation', {}).get('risk_context') == 'High'
            },
            {
                'name': 'Value stock with analyst coverage',
                'symbol': 'JNJ',
                'check': lambda r: r.get('valuation_analysis', {}).get('primary_method') in ['DCF', 'Analyst Consensus']
            }
        ]
        
        for case in edge_cases:
            self.logger.info(f"\nTesting edge case: {case['name']}")
            result = self.analyzer.analyze_stock(case['symbol'])
            
            if result:
                self.assertTrue(
                    case['check'](result),
                    f"Edge case check failed for {case['name']}"
                )
            self._log_analysis_results(result, case['symbol'], case['name'])

    def _verify_analysis_components(self, result):
        """Verify all analysis components are present and valid"""
        # Fundamental analysis checks
        fundamental = result.get('fundamental_analysis', {})
        self.assertIsInstance(fundamental.get('score', 0), (int, float))
        self.assertTrue(0 <= fundamental.get('score', 0) <= 100)
        
        # Technical analysis checks
        technical = result.get('technical_analysis', {})
        self.assertIsInstance(technical.get('technical_score', 0), (int, float))
        self.assertTrue(0 <= technical.get('technical_score', 0) <= 100)
        
        # Valuation analysis checks
        valuation = result.get('valuation_analysis', {})
        if valuation.get('success', False):
            self.assertIn('target_price', valuation)
            self.assertIn('primary_method', valuation)
            self.assertGreater(valuation.get('confidence', 0), 0)
        
        # Integrated score checks
        self.assertIsInstance(result['integrated_score'], (int, float))
        self.assertTrue(0 <= result['integrated_score'] <= 100)