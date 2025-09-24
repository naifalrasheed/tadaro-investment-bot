#!/usr/bin/env python3
"""
API Integration Tests for Investment Bot
Tests environment variable handling and API authentication
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append('/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src')

class TestAPIIntegration(unittest.TestCase):
    """Test API integration and security"""

    def test_environment_variable_reading(self):
        """Test that environment variables are properly read"""
        with patch.dict(os.environ, {'TWELVEDATA_API_KEY': 'test-key-123'}):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            # Should not raise exception
            analyzer = TwelveDataAnalyzer()
            self.assertTrue(analyzer.api_key.endswith('123'))

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises proper error"""
        with patch.dict(os.environ, {}, clear=True):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            with self.assertRaises(ValueError) as context:
                TwelveDataAnalyzer()

            self.assertIn('TWELVEDATA_API_KEY environment variable is required', str(context.exception))

    def test_no_hardcoded_keys_in_analyzer(self):
        """Test that no hardcoded API keys exist in the analyzer"""
        analyzer_file = '/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py'

        with open(analyzer_file, 'r') as f:
            content = f.read()

        # Check for common hardcoded key patterns
        suspicious_patterns = [
            '4420a6f49fbf468c843c102571ec7329',  # Old key
            'api_key = "',
            'api_key = \'',
            'apikey = "',
            'apikey = \'',
        ]

        for pattern in suspicious_patterns:
            self.assertNotIn(pattern, content, f"Found suspicious pattern: {pattern}")

    def test_data_comparison_service_priority(self):
        """Test that data comparison service uses priority-based selection"""
        from data.data_comparison_service import DataComparisonService

        service = DataComparisonService()

        # Test with mock sources
        sources = [
            {'symbol': 'MSFT', 'current_price': 100.0, 'data_source': 'yfinance', 'success': True},
            {'symbol': 'MSFT', 'current_price': 101.0, 'data_source': 'twelvedata', 'success': True},
            {'symbol': 'MSFT', 'current_price': 99.0, 'data_source': 'alpha_vantage', 'success': True}
        ]

        result = service.select_best_source(sources)

        # Should select TwelveData (highest priority)
        self.assertEqual(result['data_source'], 'twelvedata')
        self.assertEqual(result['current_price'], 101.0)

        # Should not have averaged prices
        self.assertNotEqual(result['current_price'], 100.0)  # Not an average

    def test_fallback_behavior(self):
        """Test fallback behavior when TwelveData fails"""
        from data.data_comparison_service import DataComparisonService

        service = DataComparisonService()

        # Test with TwelveData failed, Alpha Vantage working
        sources = [
            {'symbol': 'MSFT', 'error': 'API failed', 'data_source': 'twelvedata', 'success': False},
            {'symbol': 'MSFT', 'current_price': 99.0, 'data_source': 'alpha_vantage', 'success': True}
        ]

        result = service.select_best_source(sources)

        # Should fall back to Alpha Vantage
        self.assertEqual(result['data_source'], 'alpha_vantage')
        self.assertEqual(result['current_price'], 99.0)

    def test_no_api_key_logging(self):
        """Test that API keys are not logged in full"""
        with patch.dict(os.environ, {'TWELVEDATA_API_KEY': 'test-key-12345678'}):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            with patch('analysis.twelvedata_analyzer.logger') as mock_logger:
                analyzer = TwelveDataAnalyzer()

                # Check that full key is never logged
                for call in mock_logger.info.call_args_list:
                    call_str = str(call)
                    self.assertNotIn('test-key-12345678', call_str)

                    # Should only show last 4 digits
                    if 'API Key configured' in call_str:
                        self.assertIn('5678', call_str)


if __name__ == '__main__':
    unittest.main()