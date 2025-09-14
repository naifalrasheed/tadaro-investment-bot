"""
Interactive Brokers Web API Client for Investment Bot
This module provides a client for accessing financial data from Interactive Brokers' 
Client Portal Web API for both real-time and historical market data.
"""

import os
import json
import time
import logging
import requests
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
from threading import Lock
import concurrent.futures
import sys
import urllib3

# Disable insecure warnings when connecting to local IB gateway
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IBDataClient:
    """
    Client for Interactive Brokers Client Portal Web API.
    
    Features:
    - Session management and authentication
    - Data fetching for market data and portfolio information
    - Caching of responses to reduce API calls
    - Rate limiting to respect IB's API limits
    - Error handling and automatic reconnection
    
    Prerequisites:
    - Client Portal Gateway must be running locally
    - User must be authenticated to the gateway
    """
    
    def __init__(self, base_url: str = "https://localhost:5000", cache_dir: Optional[str] = None):
        """
        Initialize the Interactive Brokers API client.
        
        Args:
            base_url: Base URL for the IB Client Portal Gateway (default: https://localhost:5000)
            cache_dir: Directory to store cache files (default: ./cache/interactive_brokers/)
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Allow connections to local Gateway with self-signed certificates
        self.session.verify = False
        
        # Authentication status
        self.authenticated = False
        self.last_authenticated = 0
        self.session_timeout = 60 * 60  # Session timeout in seconds (1 hour)
        
        # Rate limiting settings
        self.rate_limit_lock = Lock()
        self.last_call_times = []
        self.min_api_interval = 0.5  # Minimum time between API calls in seconds

        # Set up caching
        self.cache_dir = Path(cache_dir) if cache_dir else Path('./cache/interactive_brokers/')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache TTL settings in seconds
        self.cache_ttl = {
            'market_data': 60,             # 1 minute for real-time market data
            'historical_data': 3600 * 6,   # 6 hours for historical data
            'contract_details': 3600 * 24, # 24 hours for contract details
            'fundamentals': 3600 * 24 * 7, # 1 week for fundamentals
        }
        
        # In-memory cache
        self.memory_cache = {}
        
        self.logger.info("Interactive Brokers client initialized")
    
    def check_gateway_status(self) -> bool:
        """
        Check if the Client Portal Gateway is running and accessible.
        
        Returns:
            True if the gateway is reachable, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/tickle", timeout=5)
            if response.status_code == 200:
                self.logger.info("IB Gateway is running and reachable")
                return True
            else:
                self.logger.warning(f"IB Gateway returned unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect to IB Gateway: {str(e)}")
            return False
    
    def check_authentication(self) -> bool:
        """
        Check if the user is authenticated to the Gateway.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            response = self.session.post(f"{self.base_url}/sso/validate")
            data = response.json()
            
            if data.get('authenticated', False):
                self.authenticated = True
                self.last_authenticated = time.time()
                self.logger.info("User is authenticated to IB Gateway")
                return True
            else:
                self.authenticated = False
                self.logger.warning("User is not authenticated to IB Gateway")
                return False
        except Exception as e:
            self.authenticated = False
            self.logger.error(f"Failed to check authentication status: {str(e)}")
            return False
    
    def login(self) -> bool:
        """
        Initialize a login sequence. 
        
        NOTE: This doesn't actually log in the user, but redirects to the IB login page.
        The user must manually login through the browser. This method is for completeness.
        
        Returns:
            True if login URL is successfully generated, False otherwise
        """
        try:
            # This would open a browser window for the user to login
            login_url = f"{self.base_url}/oauth/login"
            self.logger.info(f"To login, open this URL in your browser: {login_url}")
            self.logger.info("After logging in through the browser, call check_authentication() to verify")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize login: {str(e)}")
            return False
    
    def logout(self) -> bool:
        """
        Log out from the current session.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(f"{self.base_url}/logout")
            if response.status_code == 200:
                self.authenticated = False
                self.logger.info("Successfully logged out from IB Gateway")
                return True
            else:
                self.logger.warning(f"Logout returned unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to log out: {str(e)}")
            return False
    
    def keep_session_alive(self) -> bool:
        """
        Keep the session alive by sending a tickle request to the server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(f"{self.base_url}/tickle")
            if response.status_code == 200:
                self.logger.debug("Kept session alive with tickle")
                return True
            else:
                self.logger.warning(f"Tickle returned unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to keep session alive: {str(e)}")
            return False
    
    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limits to avoid overloading the IB Gateway.
        """
        with self.rate_limit_lock:
            current_time = time.time()
            
            # Remove call times outside the current window (5 seconds)
            self.last_call_times = [t for t in self.last_call_times 
                                  if current_time - t <= 5]
            
            # If we've made too many calls in the window, wait
            if len(self.last_call_times) >= 10:  # Max 10 calls in 5 seconds
                oldest_call = min(self.last_call_times)
                sleep_time = self.min_api_interval - (current_time - oldest_call) + 0.1
                if sleep_time > 0:
                    self.logger.debug(f"Rate limiting, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            # Ensure minimum time between consecutive calls
            if self.last_call_times and current_time - max(self.last_call_times) < self.min_api_interval:
                sleep_time = self.min_api_interval - (current_time - max(self.last_call_times))
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record this call
            self.last_call_times.append(time.time())
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """
        Generate a cache key from endpoint and parameters.
        
        Args:
            endpoint: API endpoint
            params: API parameters
            
        Returns:
            A string cache key
        """
        # Convert params to a sorted parameter string
        param_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}_{param_str}"
    
    def _get_from_memory_cache(self, endpoint: str, cache_key: str) -> Optional[Dict]:
        """
        Get data from memory cache if available and not expired.
        
        Args:
            endpoint: API endpoint category (for TTL lookup)
            cache_key: Cache key to look up
            
        Returns:
            Cached data or None if not found or expired
        """
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() < entry['expires_at']:
                self.logger.debug(f"Memory cache hit for {cache_key}")
                return entry['data']
            
            # Remove expired cache
            del self.memory_cache[cache_key]
        
        return None
    
    def _get_from_disk_cache(self, endpoint: str, cache_key: str) -> Optional[Dict]:
        """
        Get data from disk cache if available and not expired.
        
        Args:
            endpoint: API endpoint category (for TTL lookup)
            cache_key: Cache key to look up
            
        Returns:
            Cached data or None if not found or expired
        """
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            file_age = time.time() - cache_file.stat().st_mtime
            ttl = self.cache_ttl.get(endpoint, 3600)  # Default 1 hour TTL
            
            if file_age > ttl:
                self.logger.debug(f"Disk cache expired for {cache_key}")
                return None
            
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
                
                # Add to memory cache
                self.memory_cache[cache_key] = {
                    'data': data,
                    'expires_at': time.time() + ttl
                }
                
                self.logger.debug(f"Disk cache hit for {cache_key}")
                return data
                
        except Exception as e:
            self.logger.error(f"Error reading from disk cache: {str(e)}")
            return None
    
    def _save_to_cache(self, endpoint: str, cache_key: str, data: Dict) -> None:
        """
        Save data to both memory and disk cache.
        
        Args:
            endpoint: API endpoint category (for TTL lookup)
            cache_key: Cache key to store under
            data: Data to cache
        """
        ttl = self.cache_ttl.get(endpoint, 3600)  # Default 1 hour TTL
        
        # Save to memory cache
        self.memory_cache[cache_key] = {
            'data': data,
            'expires_at': time.time() + ttl
        }
        
        # Save to disk cache
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
            self.logger.debug(f"Saved to cache: {cache_key}")
        except Exception as e:
            self.logger.error(f"Error saving to disk cache: {str(e)}")
    
    def _make_api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                         data: Optional[Dict] = None, force_refresh: bool = False) -> Optional[Dict]:
        """
        Make an API request to the IB Gateway with authentication checks.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            params: URL parameters
            data: JSON body data
            force_refresh: If True, bypass cache
            
        Returns:
            Response data or None on failure
        """
        # Check if session is still valid, refresh if needed
        current_time = time.time()
        if self.authenticated and (current_time - self.last_authenticated) > (self.session_timeout - 300):
            self.logger.info("Session is about to expire, refreshing...")
            self.keep_session_alive()
            if self.check_authentication():
                self.logger.info("Session successfully refreshed")
            else:
                self.logger.warning("Failed to refresh session, needs re-authentication")
                return None
        
        # Check if authenticated
        if not self.authenticated:
            if not self.check_authentication():
                self.logger.warning("Not authenticated, cannot make API request")
                return None
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Generate cache key and check cache if not forcing refresh
        cache_key = None
        if method.upper() == 'GET' and not force_refresh:
            cache_category = endpoint.split('/')[0] if '/' in endpoint else 'default'
            cache_key = self._get_cache_key(endpoint, params or {})
            
            # Check memory cache
            memory_data = self._get_from_memory_cache(cache_category, cache_key)
            if memory_data:
                return memory_data
            
            # Check disk cache
            disk_data = self._get_from_disk_cache(cache_category, cache_key)
            if disk_data:
                return disk_data
        
        # Make the API request
        try:
            url = f"{self.base_url}/v1/portal/{endpoint}"
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check for authentication errors
            if response.status_code == 401:
                self.authenticated = False
                self.logger.warning("Authentication expired, need to re-authenticate")
                return None
            
            # Check for other errors
            if response.status_code != 200:
                self.logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
            
            # Parse response
            try:
                result = response.json()
            except:
                # Some endpoints might return text or empty
                result = {'text': response.text} if response.text else {}
            
            # Cache successful GET responses
            if method.upper() == 'GET' and cache_key:
                cache_category = endpoint.split('/')[0] if '/' in endpoint else 'default'
                self._save_to_cache(cache_category, cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"API request error: {str(e)}")
            return None
    
    def get_account_summary(self) -> Optional[Dict]:
        """
        Get account summary information.
        
        Returns:
            Account summary data or None on failure
        """
        return self._make_api_request('GET', 'portfolio/accounts')
    
    def get_portfolio_positions(self, account_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get portfolio positions for an account.
        
        Args:
            account_id: Account ID (if None, gets positions for all accounts)
            
        Returns:
            Portfolio positions data or None on failure
        """
        if account_id:
            return self._make_api_request('GET', f'portfolio/{account_id}/positions')
        else:
            # Get all accounts first
            accounts = self.get_account_summary()
            if not accounts:
                return None
            
            # Use the first account if available
            if len(accounts) > 0:
                account_id = accounts[0].get('accountId')
                return self._make_api_request('GET', f'portfolio/{account_id}/positions')
        
        return None
    
    def get_market_data(self, conids: List[str]) -> Optional[Dict]:
        """
        Get real-time market data for a list of contract IDs.
        
        Args:
            conids: List of contract IDs
            
        Returns:
            Market data or None on failure
        """
        # Convert conids to comma-separated string
        conid_str = ','.join(conids)
        return self._make_api_request('GET', 'iserver/marketdata/snapshot', params={'conids': conid_str})
    
    def search_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Search for a symbol to get contract details.
        
        Args:
            symbol: Symbol to search for
            
        Returns:
            Search results or None on failure
        """
        return self._make_api_request('POST', 'iserver/secdef/search', data={'symbol': symbol})
    
    def get_contract_details(self, conid: str) -> Optional[Dict]:
        """
        Get contract details for a specific contract ID.
        
        Args:
            conid: Contract ID
            
        Returns:
            Contract details or None on failure
        """
        return self._make_api_request('GET', f'iserver/contract/{conid}/info')
    
    def get_historical_data(self, conid: str, period: str = '1d', bar: str = '5min') -> Optional[Dict]:
        """
        Get historical market data.
        
        Args:
            conid: Contract ID
            period: Time period ('1d', '1w', '1m', '1y', etc.)
            bar: Bar size ('1min', '5min', '1h', '1d', etc.)
            
        Returns:
            Historical data or None on failure
        """
        params = {'conid': conid, 'period': period, 'bar': bar}
        return self._make_api_request('GET', 'iserver/marketdata/history', params=params)
    
    def get_stock_fundamentals(self, conid: str) -> Optional[Dict]:
        """
        Get fundamental data for a stock.
        
        Args:
            conid: Contract ID
            
        Returns:
            Fundamental data or None on failure
        """
        return self._make_api_request('GET', f'fundamentals/snapshot/{conid}')
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        High-level function to get stock information by symbol.
        Searches for the symbol, gets contract details, and fetches market data.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Combined stock data or None on failure
        """
        # Search for the symbol
        search_results = self.search_symbol(symbol)
        if not search_results or not search_results.get('sections'):
            self.logger.warning(f"No search results found for symbol: {symbol}")
            return None
        
        # Find the stock contract (looking for STK asset type)
        stock_contract = None
        for section in search_results.get('sections', []):
            for item in section.get('items', []):
                if item.get('assetClass') == 'STK':
                    stock_contract = item
                    break
            if stock_contract:
                break
        
        if not stock_contract:
            self.logger.warning(f"No stock contract found for symbol: {symbol}")
            return None
        
        conid = stock_contract.get('conid')
        if not conid:
            self.logger.warning(f"No contract ID found for symbol: {symbol}")
            return None
        
        # Get contract details
        contract_details = self.get_contract_details(conid)
        
        # Get market data
        market_data = self.get_market_data([conid])
        
        # Get fundamentals
        fundamentals = self.get_stock_fundamentals(conid)
        
        # Combine all data
        result = {
            'symbol': symbol,
            'contract': stock_contract,
            'details': contract_details,
            'market_data': market_data,
            'fundamentals': fundamentals,
            'timestamp': datetime.now().timestamp(),
            'data_source': 'interactive_brokers'
        }
        
        return result
    
    def analyze_stock(self, symbol: str, force_refresh: bool = False) -> Dict:
        """
        Comprehensive analysis of a stock using Interactive Brokers data.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache
            
        Returns:
            Comprehensive stock analysis in a standard format
        """
        # Get stock data
        stock_data = self.get_stock_by_symbol(symbol)
        
        # If we couldn't get the data, return a minimal result
        if not stock_data:
            self.logger.warning(f"Could not get stock data for {symbol}")
            return {
                'symbol': symbol,
                'company_name': symbol,
                'current_price': 0.0,
                'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data_source': 'interactive_brokers',
                'timestamp': datetime.now().timestamp()
            }
        
        # Extract market data
        market_data = stock_data.get('market_data', [])
        current_price = 0.0
        daily_change_percent = 0.0
        
        if market_data:
            for item in market_data:
                if str(item.get('conid')) == str(stock_data['contract']['conid']):
                    current_price = item.get('31', 0.0)  # Last price
                    prev_close = item.get('7295', 0.0)  # Previous close
                    if prev_close > 0:
                        daily_change_percent = ((current_price / prev_close) - 1) * 100
                    break
        
        # Extract fundamentals
        fundamentals = stock_data.get('fundamentals', {})
        
        # Try to get historical data for 52-week high/low
        conid = stock_data['contract']['conid']
        historical_data = self.get_historical_data(conid, period='1y', bar='1d')
        
        week_52_high = 0.0
        week_52_low = current_price * 0.8  # Default if we can't get history
        ytd_performance = 0.0
        
        if historical_data and 'data' in historical_data:
            prices = [item.get('c', 0) for item in historical_data['data']]
            if prices:
                week_52_high = max(prices)
                week_52_low = min(prices)
                
                # Calculate YTD performance
                ytd_start = datetime(datetime.now().year, 1, 1)
                start_price = None
                
                for i, point in enumerate(historical_data['data']):
                    if 't' in point:
                        point_time = datetime.fromtimestamp(point['t'] / 1000)
                        if point_time.year == ytd_start.year and point_time.month == ytd_start.month:
                            start_price = point.get('c', 0)
                            break
                
                if start_price and start_price > 0:
                    ytd_performance = ((current_price / start_price) - 1) * 100
        
        # Extract company information
        company_name = stock_data['contract'].get('name', symbol)
        
        # Build the standardized result
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'sector': fundamentals.get('Sector', 'Unknown'),
            'industry': fundamentals.get('Industry', 'Unknown'),
            'market_cap': fundamentals.get('MarketCap', 0),
            'current_price': current_price,
            'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'price_metrics': {
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'ytd_performance': ytd_performance,
                'daily_change': daily_change_percent,
                'volume': market_data[0].get('7762', 0) if market_data else 0  # Volume
            },
            'integrated_analysis': {
                'company_type': 'unknown',  # Need more data to determine
                'fundamental_analysis': {
                    'score': 50.0,  # Placeholder
                    'rotc_data': {
                        'latest_rotc': fundamentals.get('ROTC', 0.0),
                        'avg_rotc': fundamentals.get('ROTC', 0.0),
                        'improving': False
                    },
                    'growth_data': {
                        'avg_revenue_growth': fundamentals.get('RevenueGrowth', 0.0),
                        'cash_flow_positive': fundamentals.get('CashFlow', 0) > 0,
                        'revenue_growth_trend': 0.0
                    }
                },
                'technical_analysis': {
                    'success': True,
                    'ml_prediction': 0.0,  # Placeholder
                    'confidence': 50.0,    # Placeholder
                    'technical_score': 50.0, # Placeholder
                    'price_metrics': {
                        'current_price': current_price,
                        'predicted_price': current_price,  # Placeholder
                        'volatility': 0.0  # Placeholder
                    }
                },
                'risk_metrics': {
                    'volatility': 0.0,  # Placeholder
                    'max_drawdown': 0.0, # Placeholder
                    'var_95': 0.0,       # Placeholder
                    'sharpe_ratio': 0.0, # Placeholder
                    'risk_level': 'Unknown'
                },
                'recommendation': {
                    'action': 'Hold',  # Placeholder
                    'reasoning': ['Insufficient data for analysis'],
                    'risk_context': 'Unknown'
                }
            },
            'dividend_metrics': {
                'dividend_yield': fundamentals.get('DividendYield', 0.0),
                'dividend_rate': fundamentals.get('DividendRate', 0.0),
                'payout_ratio': fundamentals.get('PayoutRatio', 0.0),
                'dividend_growth': 0.0  # Placeholder
            },
            'data_source': 'interactive_brokers',
            'timestamp': datetime.now().timestamp()
        }
        
        return result
    
    def clear_cache(self, pattern: Optional[str] = None) -> bool:
        """
        Clear the cache, optionally matching a pattern.
        
        Args:
            pattern: If provided, only clear cache entries matching this pattern
            
        Returns:
            True if successful
        """
        # Clear memory cache
        if pattern:
            keys_to_remove = [k for k in self.memory_cache if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
        else:
            self.memory_cache = {}
        
        # Clear disk cache
        try:
            count = 0
            if pattern:
                for cache_file in self.cache_dir.glob(f"*{pattern}*.pkl"):
                    cache_file.unlink()
                    count += 1
            else:
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                    count += 1
            
            self.logger.info(f"Cleared {count} cache files")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = IBDataClient()
    
    # Check if gateway is running
    if not client.check_gateway_status():
        print("IB Gateway is not running. Please start it first.")
        sys.exit(1)
    
    # Check authentication
    if not client.check_authentication():
        print("Not authenticated. Please login through the browser first.")
        client.login()
        sys.exit(1)
    
    # Try to get some data
    print("Getting account summary...")
    accounts = client.get_account_summary()
    if accounts:
        print(f"Found {len(accounts)} accounts:")
        for account in accounts:
            print(f"  Account: {account.get('accountId')}, Type: {account.get('accountType')}")
    
    # Test stock lookup
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    for symbol in symbols:
        print(f"\nGetting data for {symbol}...")
        data = client.get_stock_by_symbol(symbol)
        if data:
            print(f"  Contract ID: {data['contract']['conid']}")
            print(f"  Name: {data['contract']['name']}")
            
            # Get market data
            if 'market_data' in data and data['market_data']:
                for item in data['market_data']:
                    if str(item.get('conid')) == str(data['contract']['conid']):
                        print(f"  Last Price: {item.get('31', 'N/A')}")
                        print(f"  Change: {item.get('7695', 'N/A')}")
                        break
        else:
            print(f"  Failed to get data for {symbol}")