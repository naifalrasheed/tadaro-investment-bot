"""
Test suite for the Interactive Brokers API client
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import time
import logging

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.ib_data_client import IBDataClient

class TestIBDataClient(unittest.TestCase):
    """Test cases for the Interactive Brokers client"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a test cache directory
        self.test_cache_dir = Path("./test_cache")
        self.test_cache_dir.mkdir(exist_ok=True)
        
        # Initialize the client with test configurations
        self.client = IBDataClient(
            base_url="https://localhost:5000",
            cache_dir=str(self.test_cache_dir)
        )
        
        # Sample response data for mocking
        self.sample_account_response = [
            {
                "accountId": "DU12345",
                "accountType": "INDIVIDUAL",
                "accountTitle": "Test Account"
            }
        ]
        
        self.sample_search_response = {
            "sections": [
                {
                    "sectionType": "STK",
                    "items": [
                        {
                            "conid": "265598",
                            "name": "AAPL",
                            "description": "APPLE INC",
                            "assetClass": "STK",
                            "exchangeId": "NASDAQ"
                        }
                    ]
                }
            ]
        }
        
        self.sample_contract_details = {
            "conid": "265598",
            "companyName": "APPLE INC",
            "symbol": "AAPL",
            "currency": "USD",
            "assetClass": "STK",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Consumer Electronics"
        }
        
        self.sample_market_data = [
            {
                "conid": "265598",
                "31": 192.53,  # Last price
                "7295": 191.80,  # Previous close
                "7762": 58900000  # Volume
            }
        ]
        
        self.sample_historical_data = {
            "data": [
                {"t": 1615308000000, "o": 190.0, "h": 193.0, "l": 189.5, "c": 192.53, "v": 58900000},
                {"t": 1614703600000, "o": 189.0, "h": 192.0, "l": 188.0, "c": 191.80, "v": 59000000}
            ]
        }
        
        self.sample_fundamentals = {
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "MarketCap": 3150000000000,
            "DividendYield": 0.52,
            "DividendRate": 1.00,
            "PayoutRatio": 14.8,
            "ROTC": 36.2,
            "RevenueGrowth": 7.8,
            "CashFlow": 100000000000
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove test cache directory
        import shutil
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)
    
    @patch('requests.Session.get')
    def test_check_gateway_status(self, mock_get):
        """Test checking gateway status"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.check_gateway_status()
        
        # Verify the result
        self.assertTrue(result)
        
        # Check that the API was called with the correct URL
        mock_get.assert_called_once_with(f"{self.client.base_url}/tickle", timeout=5)
    
    @patch('requests.Session.post')
    def test_check_authentication(self, mock_post):
        """Test checking authentication status"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"authenticated": True}
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.client.check_authentication()
        
        # Verify the result
        self.assertTrue(result)
        self.assertTrue(self.client.authenticated)
        
        # Check that the API was called with the correct URL
        mock_post.assert_called_once_with(f"{self.client.base_url}/sso/validate")
    
    @patch('requests.Session.get')
    def test_get_account_summary(self, mock_get):
        """Test getting account summary"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_account_response
        mock_get.return_value = mock_response
        
        # Setup authenticated state
        self.client.authenticated = True
        self.client.last_authenticated = time.time()
        
        # Call the method
        result = self.client._make_api_request('GET', 'portfolio/accounts')
        
        # Verify the result
        self.assertEqual(result, self.sample_account_response)
        
        # Check that the API was called with the correct URL
        mock_get.assert_called_once_with(f"{self.client.base_url}/v1/portal/portfolio/accounts", params=None)
    
    @patch('requests.Session.post')
    def test_search_symbol(self, mock_post):
        """Test searching for a symbol"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_search_response
        mock_post.return_value = mock_response
        
        # Setup authenticated state
        self.client.authenticated = True
        self.client.last_authenticated = time.time()
        
        # Call the method
        result = self.client._make_api_request('POST', 'iserver/secdef/search', data={'symbol': 'AAPL'})
        
        # Verify the result
        self.assertEqual(result, self.sample_search_response)
        
        # Check that the API was called with the correct URL and data
        mock_post.assert_called_once_with(
            f"{self.client.base_url}/v1/portal/iserver/secdef/search", 
            json={'symbol': 'AAPL'}, 
            params=None
        )
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_get_stock_by_symbol(self, mock_post, mock_get):
        """Test getting stock information by symbol"""
        # We need to mock multiple API calls
        def mock_api_response(*args, **kwargs):
            url = args[0]
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if '/iserver/secdef/search' in url:
                mock_response.json.return_value = self.sample_search_response
            elif '/iserver/contract/' in url:
                mock_response.json.return_value = self.sample_contract_details
            elif '/iserver/marketdata/snapshot' in url:
                mock_response.json.return_value = self.sample_market_data
            elif '/fundamentals/snapshot/' in url:
                mock_response.json.return_value = self.sample_fundamentals
            else:
                mock_response.json.return_value = {}
            
            return mock_response
        
        mock_post.side_effect = mock_api_response
        mock_get.side_effect = mock_api_response
        
        # Setup authenticated state
        self.client.authenticated = True
        self.client.last_authenticated = time.time()
        
        # Mock the component methods
        self.client.search_symbol = lambda symbol: self.sample_search_response
        self.client.get_contract_details = lambda conid: self.sample_contract_details
        self.client.get_market_data = lambda conids: self.sample_market_data
        self.client.get_stock_fundamentals = lambda conid: self.sample_fundamentals
        
        # Call the method
        result = self.client.get_stock_by_symbol('AAPL')
        
        # Verify the result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['contract'], self.sample_search_response['sections'][0]['items'][0])
        self.assertEqual(result['details'], self.sample_contract_details)
        self.assertEqual(result['market_data'], self.sample_market_data)
        self.assertEqual(result['fundamentals'], self.sample_fundamentals)
        self.assertIn('timestamp', result)
        self.assertEqual(result['data_source'], 'interactive_brokers')
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_analyze_stock(self, mock_post, mock_get):
        """Test analyzing a stock"""
        # Mock all the required method calls
        # First mock get_stock_by_symbol
        self.client.get_stock_by_symbol = lambda symbol, force_refresh=False: {
            'symbol': symbol,
            'contract': self.sample_search_response['sections'][0]['items'][0],
            'details': self.sample_contract_details,
            'market_data': self.sample_market_data,
            'fundamentals': self.sample_fundamentals,
            'timestamp': time.time(),
            'data_source': 'interactive_brokers'
        }
        
        # Mock get_historical_data
        self.client.get_historical_data = lambda conid, period, bar: self.sample_historical_data
        
        # Call the method
        result = self.client.analyze_stock('AAPL')
        
        # Verify the result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['data_source'], 'interactive_brokers')
        
        # Check the main categories
        self.assertIn('price_metrics', result)
        self.assertIn('week_52_high', result['price_metrics'])
        self.assertIn('week_52_low', result['price_metrics'])
        self.assertIn('ytd_performance', result['price_metrics'])
        
        self.assertIn('integrated_analysis', result)
        self.assertIn('fundamental_analysis', result['integrated_analysis'])
        self.assertIn('technical_analysis', result['integrated_analysis'])
        self.assertIn('risk_metrics', result['integrated_analysis'])
        self.assertIn('recommendation', result['integrated_analysis'])
        
        self.assertIn('dividend_metrics', result)
        self.assertEqual(result['dividend_metrics']['dividend_yield'], self.sample_fundamentals['DividendYield'])
        self.assertEqual(result['dividend_metrics']['dividend_rate'], self.sample_fundamentals['DividendRate'])
        
    def test_caching(self):
        """Test caching functionality"""
        # Mock a successful API response
        test_data = {"test": "data"}
        
        # Save to cache
        self.client._save_to_cache('market_data', 'test_key', test_data)
        
        # Verify memory cache
        self.assertIn('test_key', self.client.memory_cache)
        self.assertEqual(self.client.memory_cache['test_key']['data'], test_data)
        
        # Verify disk cache
        cache_file = self.test_cache_dir / "test_key.pkl"
        self.assertTrue(cache_file.exists())
        
        # Test cache retrieval
        memory_data = self.client._get_from_memory_cache('market_data', 'test_key')
        self.assertEqual(memory_data, test_data)
        
        # Clear memory cache and test disk retrieval
        self.client.memory_cache = {}
        disk_data = self.client._get_from_disk_cache('market_data', 'test_key')
        self.assertEqual(disk_data, test_data)
        
        # Test cache clearing
        result = self.client.clear_cache()
        self.assertTrue(result)
        self.assertEqual(self.client.memory_cache, {})
        self.assertFalse(cache_file.exists())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()