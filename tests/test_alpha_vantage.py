"""
Test suite for the Alpha Vantage API client
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import time
import logging

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.alpha_vantage_client import AlphaVantageClient

class TestAlphaVantageClient(unittest.TestCase):
    """Test cases for the Alpha Vantage client"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Use a test API key
        self.test_api_key = "test_api_key"
        
        # Create a test cache directory
        self.test_cache_dir = Path("./test_cache")
        self.test_cache_dir.mkdir(exist_ok=True)
        
        # Initialize the client with test configurations
        self.client = AlphaVantageClient(
            api_key=self.test_api_key,
            cache_dir=str(self.test_cache_dir)
        )
        
        # Sample response data for mocking
        self.sample_quote_response = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "190.0000",
                "03. high": "193.0000",
                "04. low": "189.5000",
                "05. price": "192.5300",
                "06. volume": "58900000",
                "07. latest trading day": "2025-03-12",
                "08. previous close": "191.8000",
                "09. change": "0.7300",
                "10. change percent": "0.3800%"
            }
        }
        
        self.sample_daily_response = {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2025-03-12",
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                "2025-03-12": {
                    "1. open": "190.0000",
                    "2. high": "193.0000",
                    "3. low": "189.5000",
                    "4. close": "192.5300",
                    "5. volume": "58900000"
                },
                "2025-03-11": {
                    "1. open": "189.0000",
                    "2. high": "192.0000",
                    "3. low": "188.0000",
                    "4. close": "191.8000",
                    "5. volume": "59000000"
                }
            }
        }
        
        self.sample_overview_response = {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "PERatio": "32.15",
            "MarketCapitalization": "3150000000000",
            "DividendYield": "0.0052",
            "DividendPerShare": "1.00",
            "PayoutRatio": "0.148",
            "ProfitMargin": "0.2850",
            "ReturnOnAssetsTTM": "0.3620",
            "QuarterlyRevenueGrowthYOY": "0.0780"
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove test cache directory
        import shutil
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)
    
    @patch('requests.get')
    def test_get_quote(self, mock_get):
        """Test getting a quote from Alpha Vantage"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_quote_response
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.get_quote('AAPL')
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['price'], 192.53)
        self.assertEqual(result['change'], 0.73)
        self.assertEqual(result['change_percent'], '0.3800')
        self.assertEqual(result['volume'], 58900000)
        
        # Check that the API was called with the correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]['params']
        self.assertEqual(call_args['function'], 'GLOBAL_QUOTE')
        self.assertEqual(call_args['symbol'], 'AAPL')
        self.assertEqual(call_args['apikey'], self.test_api_key)
    
    @patch('requests.get')
    def test_get_daily_time_series(self, mock_get):
        """Test getting daily time series from Alpha Vantage"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_daily_response
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.get_daily_time_series('AAPL')
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['date'], '2025-03-12')
        self.assertEqual(result['data'][0]['close'], 192.53)
        self.assertEqual(result['data'][1]['date'], '2025-03-11')
        self.assertEqual(result['data'][1]['close'], 191.8)
        
        # Check that the API was called with the correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]['params']
        self.assertEqual(call_args['function'], 'TIME_SERIES_DAILY')
        self.assertEqual(call_args['symbol'], 'AAPL')
        self.assertEqual(call_args['outputsize'], 'compact')
    
    @patch('requests.get')
    def test_get_company_overview(self, mock_get):
        """Test getting company overview from Alpha Vantage"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_overview_response
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.get_company_overview('AAPL')
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['Symbol'], 'AAPL')
        self.assertEqual(result['Name'], 'Apple Inc')
        self.assertEqual(result['Sector'], 'Technology')
        self.assertEqual(result['Industry'], 'Consumer Electronics')
        self.assertEqual(result['PERatio'], '32.15')
        self.assertEqual(result['MarketCapitalization'], '3150000000000')
        
        # Check that the API was called with the correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]['params']
        self.assertEqual(call_args['function'], 'OVERVIEW')
        self.assertEqual(call_args['symbol'], 'AAPL')
    
    @patch('requests.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_quote_response
        mock_get.return_value = mock_response
        
        # Make the rate limit very small for testing
        original_rate_limit = self.client.rate_limit
        original_period = self.client.rate_limit_period
        self.client.rate_limit = 2
        self.client.rate_limit_period = 5
        
        # Make multiple requests and measure time
        start_time = time.time()
        
        self.client.get_quote('AAPL')  # First request
        self.client.get_quote('MSFT')  # Second request
        
        # Third request should trigger rate limiting
        self.client.get_quote('NVDA')
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Restore original settings
        self.client.rate_limit = original_rate_limit
        self.client.rate_limit_period = original_period
        
        # Verify that rate limiting caused a delay
        # The delay should be at least the rate limit period
        self.assertGreaterEqual(elapsed, 1)
        
        # Check that the API was called 3 times
        self.assertEqual(mock_get.call_count, 3)
    
    @patch('requests.get')
    def test_caching(self, mock_get):
        """Test caching functionality"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_quote_response
        mock_get.return_value = mock_response
        
        # First request should hit the API
        self.client.get_quote('AAPL')
        
        # Second request should use the cache
        self.client.get_quote('AAPL')
        
        # Verify the API was only called once
        self.assertEqual(mock_get.call_count, 1)
        
        # Force refresh should hit the API again
        self.client.get_quote('AAPL', force_refresh=True)
        
        # Verify the API was called again
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('requests.get')
    def test_analyze_stock(self, mock_get):
        """Test the comprehensive stock analysis method"""
        # This method uses multiple endpoints, so we need to set up multiple responses
        def mock_api_response(*args, **kwargs):
            # Get the function parameter from the API call
            function = kwargs['params']['function']
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if function == 'GLOBAL_QUOTE':
                mock_response.json.return_value = self.sample_quote_response
            elif function == 'TIME_SERIES_DAILY':
                mock_response.json.return_value = self.sample_daily_response
            elif function == 'OVERVIEW':
                mock_response.json.return_value = self.sample_overview_response
            
            return mock_response
        
        mock_get.side_effect = mock_api_response
        
        # Call the analyze_stock method
        result = self.client.analyze_stock('AAPL')
        
        # Verify the result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['company_name'], 'Apple Inc')
        self.assertEqual(result['sector'], 'Technology')
        self.assertEqual(result['industry'], 'Consumer Electronics')
        self.assertEqual(result['current_price'], 192.53)
        
        # Check price metrics
        self.assertIn('price_metrics', result)
        self.assertIn('week_52_high', result['price_metrics'])
        self.assertIn('week_52_low', result['price_metrics'])
        self.assertIn('ytd_performance', result['price_metrics'])
        
        # Check integrated analysis
        self.assertIn('integrated_analysis', result)
        self.assertIn('fundamental_analysis', result['integrated_analysis'])
        self.assertIn('technical_analysis', result['integrated_analysis'])
        self.assertIn('risk_metrics', result['integrated_analysis'])
        self.assertIn('recommendation', result['integrated_analysis'])
        
        # Check dividend metrics
        self.assertIn('dividend_metrics', result)
        self.assertAlmostEqual(result['dividend_metrics']['dividend_yield'], 0.52)
        self.assertEqual(result['dividend_metrics']['dividend_rate'], 1.0)
        
        # Verify that multiple API calls were made
        self.assertGreaterEqual(mock_get.call_count, 3)
    
    def test_clear_cache(self):
        """Test clearing the cache"""
        # Create some test cache files
        test_data = {"test": "data"}
        
        # Create memory cache entries
        self.client.memory_cache = {
            "GLOBAL_QUOTE_symbol=AAPL": {"data": test_data, "expires_at": time.time() + 3600},
            "GLOBAL_QUOTE_symbol=MSFT": {"data": test_data, "expires_at": time.time() + 3600}
        }
        
        # Create disk cache files
        (self.test_cache_dir / "GLOBAL_QUOTE_symbol=AAPL.pkl").write_bytes(b"test")
        (self.test_cache_dir / "GLOBAL_QUOTE_symbol=MSFT.pkl").write_bytes(b"test")
        
        # Clear cache for AAPL
        result = self.client.clear_cache('AAPL')
        
        # Verify cache was cleared for AAPL but not MSFT
        self.assertTrue(result)
        self.assertNotIn("GLOBAL_QUOTE_symbol=AAPL", self.client.memory_cache)
        self.assertIn("GLOBAL_QUOTE_symbol=MSFT", self.client.memory_cache)
        self.assertFalse((self.test_cache_dir / "GLOBAL_QUOTE_symbol=AAPL.pkl").exists())
        self.assertTrue((self.test_cache_dir / "GLOBAL_QUOTE_symbol=MSFT.pkl").exists())
        
        # Clear all cache
        result = self.client.clear_cache()
        
        # Verify all cache was cleared
        self.assertTrue(result)
        self.assertEqual(self.client.memory_cache, {})
        self.assertFalse((self.test_cache_dir / "GLOBAL_QUOTE_symbol=MSFT.pkl").exists())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()