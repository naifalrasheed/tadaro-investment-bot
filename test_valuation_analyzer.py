# test_valuation_analyzer.py

from ml_components.integrated_analysis import IntegratedAnalysis
import unittest
from ml_components.valuation_analyzer import ValuationAnalyzer
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import logging

class TestValuationAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before all tests"""
        cls.analyzer = ValuationAnalyzer()
        cls.test_symbols = ['AAPL', 'MSFT']  # Test with well-known stocks
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)

    def test_company_valuation(self):
        """Test full company valuation functionality"""
        for symbol in self.test_symbols:
            self.logger.info(f"\nTesting valuation for {symbol}")
            result = self.analyzer.calculate_company_valuation(symbol)
            
            # Check basic structure
            self.assertTrue('success' in result)
            self.assertTrue('target_price' in result)
            
            if result['success']:
                self.logger.info(f"Target Price: ${result['target_price']:.2f}")
                self.logger.info(f"Method Used: {result['primary_method']}")
                self.logger.info(f"Confidence: {result['confidence']:.2%}")
                
                # Verify reasonable target price (non-zero, positive)
                self.assertGreater(result['target_price'], 0)
                
                # Verify confidence score is between 0 and 1
                self.assertGreaterEqual(result['confidence'], 0)
                self.assertLessEqual(result['confidence'], 1)

    def test_dcf_valuation(self):
        """Test DCF valuation components"""
        for symbol in self.test_symbols:
            stock = yf.Ticker(symbol)
            result = self.analyzer.calculate_dcf_valuation(stock)
            
            if result['success']:
                self.logger.info(f"\nDCF Valuation for {symbol}")
                self.logger.info(f"DCF Target Price: ${result['target_price']:.2f}")
                
                # Check detailed components
                details = result['details']
                self.assertTrue(0.05 <= details['wacc'] <= 0.20)  # Reasonable WACC range
                self.assertTrue(isinstance(details['projected_fcf'], list))
                self.assertGreater(details['terminal_value'], 0)

    def test_analyst_targets(self):
        """Test analyst target processing"""
        for symbol in self.test_symbols:
            stock = yf.Ticker(symbol)
            result = self.analyzer.get_analyst_targets(stock)
            
            self.logger.info(f"\nAnalyst Targets for {symbol}")
            if result['success']:
                self.logger.info(f"Mean Target: ${result['mean_target']:.2f}")
                self.logger.info(f"Number of Analysts: {result['num_analysts']}")
                
                # Verify analyst target data
                self.assertGreater(result['num_analysts'], 0)
                self.assertGreater(result['mean_target'], 0)
                self.assertGreaterEqual(result['high_target'], result['mean_target'])
                self.assertLessEqual(result['low_target'], result['mean_target'])

    def test_growth_rates(self):
        """Test growth rate calculations"""
        for symbol in self.test_symbols:
            stock = yf.Ticker(symbol)
            cashflows = stock.cashflow
            
            if not cashflows.empty:
                fcf_data = self.analyzer.calculate_historical_fcf(cashflows)
                if fcf_data['success']:
                    growth_rates = self.analyzer.estimate_growth_rates(fcf_data['historical_fcf'])
                    
                    self.logger.info(f"\nGrowth Rates for {symbol}")
                    if growth_rates['success']:
                        self.logger.info(f"CAGR: {growth_rates['cagr']:.2%}")
                        self.logger.info(f"Growth Stability: {growth_rates['growth_stability']:.2%}")
                        
                        # Verify growth rates are reasonable
                        self.assertGreaterEqual(growth_rates['cagr'], -0.15)
                        self.assertLessEqual(growth_rates['cagr'], 0.30)
                        self.assertGreaterEqual(growth_rates['growth_stability'], 0)
                        self.assertLessEqual(growth_rates['growth_stability'], 1)

    def test_industry_wacc(self):
        """Test industry WACC functionality"""
        for symbol in self.test_symbols:
            result = self.analyzer.get_industry_wacc(symbol)
            
            self.logger.info(f"\nIndustry WACC for {symbol}")
            self.logger.info(f"Industry: {result['industry']}")
            self.logger.info(f"WACC: {result['industry_wacc']:.2%}")
            
            # Verify WACC ranges
            self.assertGreater(result['industry_wacc'], 0)
            self.assertLess(result['industry_wacc'], 0.20)
            self.assertLess(result['wacc_range']['low'], result['wacc_range']['high'])

    # Add the new methods here
    def test_integrated_valuation(self):
        """Test valuation integration with main analysis"""
        for symbol in self.test_symbols:
            self.logger.info(f"\nTesting integrated analysis with valuation for {symbol}")
            
            integrated = IntegratedAnalysis()
            result = integrated.analyze_stock(symbol)
            self.assertIn('valuation_analysis', result)
            
            valuation = result['valuation_analysis']
            if valuation['success']:
                self.logger.info(f"Method: {valuation['primary_method']}")
                self.logger.info(f"Target: ${valuation['target_price']:.2f}")
                self.logger.info(f"Upside: {valuation['upside_potential']:.1f}%")

    def test_wacc_user_input(self):
        """Test WACC user input functionality"""
        symbol = 'AAPL'  # Use a stable stock for testing
        stock = yf.Ticker(symbol)
        
        # Test automated WACC calculation first
        result = self.analyzer.calculate_dcf_valuation(stock)
        if result['success']:
            self.logger.info(f"\nTesting WACC calculation and user input for {symbol}")
            self.logger.info(f"Initial WACC: {result['details']['initial_wacc']:.2%}")
            self.logger.info(f"Final WACC: {result['details']['wacc']:.2%}")

if __name__ == '__main__':
    unittest.main(verbosity=2)