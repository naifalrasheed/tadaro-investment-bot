"""
Alpha Vantage API Client for Investment Bot
This module provides a client for Alpha Vantage API integration with proper rate limiting,
caching, and data transformation.
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

# Import config for API key
sys.path.append('..')
from config import DevelopmentConfig as Config


class AlphaVantageClient:
    """
    Client for Alpha Vantage API with rate limiting and caching.
    
    Features:
    - Rate limiting to respect Alpha Vantage's 5 calls/minute limit (free tier)
    - Multi-level caching (memory + disk)
    - Data transformation to investment bot's format
    - Error handling and retry logic
    """
    
    # API endpoints
    ENDPOINTS = {
        'GLOBAL_QUOTE': 'GLOBAL_QUOTE',
        'TIME_SERIES_DAILY': 'TIME_SERIES_DAILY',
        'TIME_SERIES_WEEKLY': 'TIME_SERIES_WEEKLY',
        'TIME_SERIES_INTRADAY': 'TIME_SERIES_INTRADAY',
        'OVERVIEW': 'OVERVIEW',
        'INCOME_STATEMENT': 'INCOME_STATEMENT',
        'BALANCE_SHEET': 'BALANCE_SHEET',
        'CASH_FLOW': 'CASH_FLOW',
        'NEWS_SENTIMENT': 'NEWS_SENTIMENT',
    }
    
    # Cache TTL settings in seconds
    CACHE_TTL = {
        'GLOBAL_QUOTE': 60,              # 1 minute for real-time quotes
        'TIME_SERIES_INTRADAY': 300,     # 5 minutes for intraday data
        'TIME_SERIES_DAILY': 3600 * 6,   # 6 hours for daily data
        'TIME_SERIES_WEEKLY': 3600 * 24, # 24 hours for weekly data
        'OVERVIEW': 3600 * 24 * 7,       # 1 week for company fundamentals
        'INCOME_STATEMENT': 3600 * 24 * 7,  # 1 week for financial statements
        'BALANCE_SHEET': 3600 * 24 * 7,     # 1 week for financial statements
        'CASH_FLOW': 3600 * 24 * 7,         # 1 week for financial statements
        'NEWS_SENTIMENT': 3600 * 4,       # 4 hours for news sentiment
    }
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key. If not provided, it will be retrieved from Config.
            cache_dir: Directory to store cache files. If not provided, defaults to './cache/alpha_vantage/'.
        """
        self.api_key = api_key or Config.ALPHA_VANTAGE_API_KEY
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting settings (5 calls per minute on free tier)
        self.rate_limit = 5
        self.rate_limit_period = 60  # seconds
        self.last_call_times = []
        self.rate_limit_lock = Lock()
        
        # Set up caching
        self.cache_dir = Path(cache_dir) if cache_dir else Path('./cache/alpha_vantage/')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.memory_cache = {}
        
        # Executor for concurrent requests
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        
        # Tracking for circuit breaker
        self.consecutive_errors = 0
        self.circuit_breaker_triggered = False
        self.circuit_breaker_reset_time = None
        
        self.logger.info("Alpha Vantage client initialized")
    
    def _get_base_url(self) -> str:
        """Get the base URL for Alpha Vantage API"""
        return "https://www.alphavantage.co/query"
    
    def _enforce_rate_limit(self) -> None:
        """
        Enforce the rate limit by waiting if necessary.
        Uses a sliding window approach for rate limiting.
        """
        with self.rate_limit_lock:
            current_time = time.time()
            
            # Remove call times outside the current window
            self.last_call_times = [t for t in self.last_call_times 
                                   if current_time - t <= self.rate_limit_period]
            
            # If we've exceeded our rate limit, wait until we can make another call
            if len(self.last_call_times) >= self.rate_limit:
                oldest_call = min(self.last_call_times)
                sleep_time = self.rate_limit_period - (current_time - oldest_call) + 0.1
                if sleep_time > 0:
                    self.logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            # Record this call
            self.last_call_times.append(time.time())
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker is triggered.
        Returns True if requests should be allowed, False otherwise.
        """
        # If circuit breaker is triggered, check if it's time to reset
        if self.circuit_breaker_triggered:
            if time.time() >= self.circuit_breaker_reset_time:
                self.logger.info("Resetting circuit breaker")
                self.circuit_breaker_triggered = False
                self.consecutive_errors = 0
                return True
            return False
        return True
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, str]) -> str:
        """
        Generate a cache key from endpoint and parameters.
        
        Args:
            endpoint: The API endpoint
            params: The API parameters
            
        Returns:
            A string cache key
        """
        # Sort params to ensure consistent key
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}_{param_str}"
    
    def _get_from_memory_cache(self, cache_key: str) -> Optional[Dict]:
        """
        Get data from memory cache if available and not expired.
        
        Args:
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
            endpoint: API endpoint (used to determine TTL)
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
            ttl = self.CACHE_TTL.get(endpoint, 3600)  # Default 1 hour TTL
            
            if file_age > ttl:
                self.logger.debug(f"Disk cache expired for {cache_key} (age: {file_age:.0f}s, ttl: {ttl}s)")
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
            # If there's an error reading the cache, treat it as a cache miss
            return None
    
    def _save_to_cache(self, endpoint: str, cache_key: str, data: Dict) -> None:
        """
        Save data to both memory and disk cache.
        
        Args:
            endpoint: API endpoint (used to determine TTL)
            cache_key: Cache key to store under
            data: Data to cache
        """
        ttl = self.CACHE_TTL.get(endpoint, 3600)  # Default 1 hour TTL
        
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
    
    def _make_api_request(self, endpoint: str, params: Dict[str, str], 
                         retry_count: int = 3) -> Optional[Dict]:
        """
        Make an API request with rate limiting and retries.
        
        Args:
            endpoint: API endpoint function
            params: API parameters
            retry_count: Number of retries on failure
            
        Returns:
            API response as dict or None on failure
        """
        if not self._check_circuit_breaker():
            self.logger.warning("Circuit breaker active, skipping API request")
            return None
        
        url = self._get_base_url()
        params = {**params, 'function': endpoint, 'apikey': self.api_key}
        
        for attempt in range(retry_count):
            try:
                # Only enforce rate limit on the first attempt
                if attempt == 0:
                    self._enforce_rate_limit()
                elif attempt > 0:
                    # Add increasing delays for retries
                    delay = 2 ** attempt  # Exponential backoff: 2, 4, 8...
                    self.logger.info(f"Retry attempt {attempt+1}/{retry_count} after {delay}s delay")
                    time.sleep(delay)
                
                # Add random User-Agent to avoid potential blocking
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                # Check for rate limit error
                if "Thank you for using Alpha Vantage" in response.text and "call frequency" in response.text:
                    self.logger.warning("Alpha Vantage rate limit exceeded")
                    # Wait longer on rate limit error
                    time.sleep(5)
                    continue
                
                # Check for other error responses
                if response.status_code != 200:
                    self.logger.error(f"API request failed with status code {response.status_code}")
                    continue
                
                data = response.json()
                
                # Check for empty or error responses
                if "Error Message" in data:
                    self.logger.error(f"API error: {data['Error Message']}")
                    continue
                    
                if "Note" in data and "call frequency" in data["Note"]:
                    self.logger.warning(f"Rate limit warning: {data['Note']}")
                    # Wait longer on rate limit warning
                    time.sleep(5)
                    continue
                
                # Check for empty response
                if not data or data == {}:
                    self.logger.warning("Empty response from API")
                    continue
                
                # Successful response
                self.consecutive_errors = 0
                return data
                
            except Exception as e:
                self.logger.error(f"API request error: {str(e)}")
                
                if attempt == retry_count - 1:
                    # This was the last attempt
                    self.consecutive_errors += 1
                    
                    # Trigger circuit breaker after 5 consecutive errors
                    if self.consecutive_errors >= 5:
                        self.logger.warning("Circuit breaker triggered due to consecutive errors")
                        self.circuit_breaker_triggered = True
                        self.circuit_breaker_reset_time = time.time() + 60  # Try again after 1 minute
                
        return None
    
    def _call_api(self, endpoint: str, params: Dict[str, str], 
                 force_refresh: bool = False) -> Optional[Dict]:
        """
        Call the Alpha Vantage API with caching.
        
        Args:
            endpoint: API endpoint function
            params: API parameters
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            API response or None on failure
        """
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache if not forcing refresh
        if not force_refresh:
            # Check memory cache first
            memory_data = self._get_from_memory_cache(cache_key)
            if memory_data:
                return memory_data
            
            # Then check disk cache
            disk_data = self._get_from_disk_cache(endpoint, cache_key)
            if disk_data:
                return disk_data
        
        # Make API request
        data = self._make_api_request(endpoint, params)
        
        # Save to cache if we got data
        if data:
            self._save_to_cache(endpoint, cache_key, data)
        
        return data
    
    def get_quote(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Quote data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['GLOBAL_QUOTE'], params, force_refresh)
        
        if data and 'Global Quote' in data:
            quote_data = data['Global Quote']
            return {
                'symbol': quote_data.get('01. symbol', symbol),
                'price': float(quote_data.get('05. price', 0)),
                'change': float(quote_data.get('09. change', 0)),
                'change_percent': quote_data.get('10. change percent', '0%').strip('%'),
                'volume': int(quote_data.get('06. volume', 0)),
                'latest_trading_day': quote_data.get('07. latest trading day', ''),
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
        
        return None
    
    def get_daily_time_series(self, symbol: str, outputsize: str = 'compact', 
                            force_refresh: bool = False) -> Optional[Dict]:
        """
        Get daily time series data.
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (last 100 data points) or 'full' (up to 20 years)
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Daily time series data or None on failure
        """
        params = {'symbol': symbol, 'outputsize': outputsize}
        data = self._call_api(self.ENDPOINTS['TIME_SERIES_DAILY'], params, force_refresh)
        
        if data and 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            
            # Convert to a more usable format
            formatted_data = []
            for date, values in time_series.items():
                formatted_data.append({
                    'date': date,
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': int(values.get('5. volume', 0))
                })
            
            # Sort by date descending
            formatted_data.sort(key=lambda x: x['date'], reverse=True)
            
            return {
                'symbol': symbol,
                'data': formatted_data,
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
        
        return None
    
    def get_intraday_time_series(self, symbol: str, interval: str = '5min', 
                               outputsize: str = 'compact',
                               force_refresh: bool = False) -> Optional[Dict]:
        """
        Get intraday time series data.
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            outputsize: 'compact' or 'full'
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Intraday time series data or None on failure
        """
        params = {'symbol': symbol, 'interval': interval, 'outputsize': outputsize}
        data = self._call_api(self.ENDPOINTS['TIME_SERIES_INTRADAY'], params, force_refresh)
        
        if data and f'Time Series ({interval})' in data:
            time_series = data[f'Time Series ({interval})']
            
            # Convert to a more usable format
            formatted_data = []
            for datetime_str, values in time_series.items():
                formatted_data.append({
                    'datetime': datetime_str,
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': int(values.get('5. volume', 0))
                })
            
            # Sort by datetime descending
            formatted_data.sort(key=lambda x: x['datetime'], reverse=True)
            
            return {
                'symbol': symbol,
                'interval': interval,
                'data': formatted_data,
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
        
        return None
    
    def get_company_overview(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get company overview data.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Company overview data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['OVERVIEW'], params, force_refresh)
        
        if data and 'Symbol' in data:
            # Return as is since it's already well-formatted
            data['data_source'] = 'alpha_vantage'
            data['timestamp'] = datetime.now().timestamp()
            return data
        
        return None
    
    def get_weekly_time_series(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get weekly time series data.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Weekly time series data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['TIME_SERIES_WEEKLY'], params, force_refresh)
        
        if data and 'Weekly Time Series' in data:
            time_series = data['Weekly Time Series']
            
            # Convert to a more usable format
            formatted_data = []
            for date, values in time_series.items():
                formatted_data.append({
                    'date': date,
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': int(values.get('5. volume', 0))
                })
            
            # Sort by date descending
            formatted_data.sort(key=lambda x: x['date'], reverse=True)
            
            return {
                'symbol': symbol,
                'data': formatted_data,
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
        
        return None
    
    def get_news_sentiment(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get news sentiment data for a symbol.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            News sentiment data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['NEWS_SENTIMENT'], params, force_refresh)
        
        if data and 'feed' in data:
            # Return structured news data
            return {
                'symbol': symbol,
                'sentiment_score': data.get('sentiment_score_definition', ''),
                'relevance_score': data.get('relevance_score_definition', ''),
                'news_count': len(data['feed']),
                'news': data['feed'],
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
        
        return None
    
    def get_income_statement(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get income statement data.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Income statement data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['INCOME_STATEMENT'], params, force_refresh)
        
        if data and 'annualReports' in data:
            # Add metadata
            data['data_source'] = 'alpha_vantage'
            data['timestamp'] = datetime.now().timestamp()
            return data
        
        return None
    
    def get_balance_sheet(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get balance sheet data and process it into a standardized format.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Processed balance sheet data or None on failure
        """
        try:
            # Fetch raw balance sheet data
            params = {'symbol': symbol}
            raw_data = self._call_api(self.ENDPOINTS['BALANCE_SHEET'], params, force_refresh)
            
            self.logger.info(f"Balance sheet data received for {symbol}: {str(raw_data is not None)}")
            
            if not raw_data:
                self.logger.warning(f"No balance sheet API response for {symbol}")
                return None
                
            if 'Information' in raw_data:
                self.logger.warning(f"API limit message: {raw_data.get('Information')}")
                
            if 'annualReports' not in raw_data or not raw_data['annualReports']:
                self.logger.warning(f"No annual reports in balance sheet data for {symbol}")
                return None
            
            # Extract the most recent annual balance sheet
            annual_reports = raw_data['annualReports']
            if not annual_reports:
                self.logger.warning(f"Empty annual reports for {symbol}")
                return None
            
            latest_report = annual_reports[0]
            self.logger.info(f"Latest balance sheet report for {symbol} is from {latest_report.get('fiscalDateEnding')}")
            
            # Process the data into a standardized format
            processed_data = {
                'symbol': symbol,
                'fiscal_date_ending': latest_report.get('fiscalDateEnding'),
                'total_assets': self._safe_parse_float(latest_report.get('totalAssets')),
                'total_current_assets': self._safe_parse_float(latest_report.get('totalCurrentAssets')),
                'cash_and_equivalents': self._safe_parse_float(latest_report.get('cashAndCashEquivalentsAtCarryingValue')),
                'total_liabilities': self._safe_parse_float(latest_report.get('totalLiabilities')),
                'total_current_liabilities': self._safe_parse_float(latest_report.get('totalCurrentLiabilities')),
                'total_shareholder_equity': self._safe_parse_float(latest_report.get('totalShareholderEquity')),
                'retained_earnings': self._safe_parse_float(latest_report.get('retainedEarnings')),
                'common_stock': self._safe_parse_float(latest_report.get('commonStock')),
                'common_stock_shares_outstanding': self._safe_parse_float(latest_report.get('commonStockSharesOutstanding')),
                'short_term_investments': self._safe_parse_float(latest_report.get('shortTermInvestments')),
                'long_term_investments': self._safe_parse_float(latest_report.get('longTermInvestments')),
                'short_term_debt': self._safe_parse_float(latest_report.get('shortTermDebt')),
                'long_term_debt': self._safe_parse_float(latest_report.get('longTermDebt')),
                'inventory': self._safe_parse_float(latest_report.get('inventory')),
                'annual_report_raw': latest_report,  # Include raw data for reference
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
            
            # Calculate financial ratios
            if processed_data['total_current_liabilities'] > 0:
                processed_data['current_ratio'] = processed_data['total_current_assets'] / processed_data['total_current_liabilities']
            else:
                processed_data['current_ratio'] = 0
                
            if processed_data['total_shareholder_equity'] > 0:
                processed_data['debt_to_equity'] = processed_data['total_liabilities'] / processed_data['total_shareholder_equity']
            else:
                processed_data['debt_to_equity'] = 0
            
            # Log some key metrics to confirm data extraction
            self.logger.info(f"Extracted balance sheet metrics for {symbol}: " +
                            f"Total Assets: {processed_data['total_assets']}, " +
                            f"Total Liabilities: {processed_data['total_liabilities']}, " +
                            f"Total Equity: {processed_data['total_shareholder_equity']}")
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing balance sheet for {symbol}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
    def _safe_parse_float(self, value: Any) -> float:
        """
        Safely parse a value to float, handling None, 'None', and other non-numeric values.
        
        Args:
            value: The value to parse
            
        Returns:
            Parsed float value or 0.0 if parsing fails
        """
        if value is None or value == 'None':
            return 0.0
            
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def get_cash_flow(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get cash flow data.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            
        Returns:
            Cash flow data or None on failure
        """
        params = {'symbol': symbol}
        data = self._call_api(self.ENDPOINTS['CASH_FLOW'], params, force_refresh)
        
        if data and 'annualReports' in data:
            # Add metadata
            data['data_source'] = 'alpha_vantage'
            data['timestamp'] = datetime.now().timestamp()
            return data
        
        return None
    
    def analyze_stock(self, symbol: str, force_refresh: bool = False, include_financials: bool = True, custom_weights: Dict = None) -> Dict:
        """
        Comprehensive analysis of a stock using Alpha Vantage data.
        Integrates multiple API endpoints to build a complete profile.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, ignore cache and force fresh API call
            include_financials: If True, include detailed financial statements
            custom_weights: Optional custom weights for sentiment calculation
            
        Returns:
            Comprehensive stock analysis data
        """
        # Use concurrent requests to speed up data collection
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit API requests concurrently
            quote_future = executor.submit(self.get_quote, symbol, force_refresh)
            overview_future = executor.submit(self.get_company_overview, symbol, force_refresh)
            daily_future = executor.submit(self.get_daily_time_series, symbol, force_refresh)
            balance_sheet_future = executor.submit(self.get_balance_sheet, symbol, force_refresh) if include_financials else None
            
            # Get results
            quote_data = quote_future.result()
            overview_data = overview_future.result()
            daily_data = daily_future.result()
            balance_sheet_data = balance_sheet_future.result() if balance_sheet_future else None
        
        # Fallback values
        current_price = 0.0
        company_name = symbol
        sector = "Unknown"
        industry = "Unknown"
        market_cap = 0
        daily_change = 0.0
        daily_change_percent = "0.0%"
        volume = 0
        
        # Extract quote data
        if quote_data:
            current_price = quote_data.get('price', 0.0)
            daily_change = quote_data.get('change', 0.0)
            daily_change_percent = quote_data.get('change_percent', '0.0')
            volume = quote_data.get('volume', 0)
        
        # Extract overview data
        if overview_data:
            company_name = overview_data.get('Name', symbol)
            sector = overview_data.get('Sector', "Unknown")
            industry = overview_data.get('Industry', "Unknown")
            market_cap = float(overview_data.get('MarketCapitalization', 0))
        
        # Calculate 52-week high/low and YTD performance from daily data
        week_52_high = 0.0
        week_52_low = float('inf')
        ytd_performance = 0.0
        price_history = []
        
        if daily_data and 'data' in daily_data:
            price_data = daily_data['data']
            
            # Find 52-week high/low
            one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            ytd_start = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
            ytd_start_price = None
            
            for day in price_data:
                # Add to price history for technical analysis
                price_history.append({
                    'date': day['date'],
                    'price': day['close']
                })
                
                # Skip if before 1 year ago
                if day['date'] < one_year_ago:
                    continue
                
                # Update 52-week high/low
                week_52_high = max(week_52_high, day['high'])
                week_52_low = min(week_52_low, day['low'])
                
                # Find YTD start price
                if ytd_start_price is None and day['date'] <= ytd_start:
                    ytd_start_price = day['close']
            
            # Calculate YTD performance
            if ytd_start_price and ytd_start_price > 0:
                ytd_performance = ((current_price / ytd_start_price) - 1) * 100
        
        # Ensure week_52_low is valid
        if week_52_low == float('inf'):
            week_52_low = current_price * 0.8  # Fallback to 80% of current price
        
        # Format output in the format expected by the investment bot
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'industry': industry,
            'market_cap': market_cap,
            'current_price': current_price,
            'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'price_metrics': {
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'ytd_performance': ytd_performance,
                'daily_change': float(daily_change_percent.replace('%', '')),
                'volume': volume
            },
            'integrated_analysis': {
                'company_type': self._determine_company_type(overview_data),
                'fundamental_analysis': self._extract_fundamental_analysis(overview_data),
                'technical_analysis': {
                    'success': True,
                    'price_metrics': {
                        'current_price': current_price,
                        'predicted_price': current_price,  # Placeholder for ML prediction
                        'volatility': self._calculate_volatility(price_history)
                    }
                },
                'risk_metrics': self._calculate_risk_metrics(price_history),
                'recommendation': self._generate_recommendation(overview_data, price_history)
            },
            'dividend_metrics': self._extract_dividend_metrics(overview_data),
            'data_source': 'alpha_vantage',
            'timestamp': datetime.now().timestamp()
        }
        
        # Add balance sheet data if available
        if balance_sheet_data and include_financials:
            try:
                # The balance sheet data is already processed in our improved get_balance_sheet method
                # Just add it directly to the result
                result['balance_sheet'] = balance_sheet_data
                
                # Remove raw data to save memory
                if 'annual_report_raw' in result['balance_sheet']:
                    del result['balance_sheet']['annual_report_raw']
                    
                self.logger.info(f"Added balance sheet data for {symbol} from {balance_sheet_data.get('fiscal_date_ending', 'unknown date')}")
            except Exception as e:
                self.logger.error(f"Error adding balance sheet data: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                
                result['balance_sheet'] = {
                    'total_assets': 0,
                    'total_liabilities': 0,
                    'total_shareholder_equity': 0,
                    'debt_to_equity': 0,
                    'current_ratio': 0,
                    'fiscal_date_ending': 'N/A'
                }
        
        # Memory optimization: Clear large objects that are no longer needed
        if 'price_history' in locals():
            del price_history
            
        return result
        
    def _safe_float(self, value):
        """Safely convert value to float"""
        if value is None:
            return 0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
            
    def _calculate_debt_to_equity(self, balance_sheet_data):
        """Calculate debt to equity ratio"""
        try:
            total_liabilities = self._safe_float(balance_sheet_data.get('total_liabilities'))
            total_equity = self._safe_float(balance_sheet_data.get('total_shareholder_equity'))
            
            if total_equity > 0:
                return total_liabilities / total_equity
            return 0
        except:
            return 0
            
    def _calculate_current_ratio(self, balance_sheet_data):
        """Calculate current ratio"""
        try:
            current_assets = self._safe_float(balance_sheet_data.get('total_current_assets'))
            current_liabilities = self._safe_float(balance_sheet_data.get('total_current_liabilities'))
            
            if current_liabilities > 0:
                return current_assets / current_liabilities
            return 0
        except:
            return 0
    
    def _determine_company_type(self, overview_data: Optional[Dict]) -> str:
        """Determine if a company is growth or value based on fundamentals"""
        if not overview_data:
            return "unknown"
        
        # Get PE ratio
        try:
            pe_ratio = float(overview_data.get('PERatio', 0))
            pb_ratio = float(overview_data.get('PriceToBookRatio', 0))
            revenue_growth = float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)) * 100
            
            # Simple heuristic for growth vs value
            if (pe_ratio > 25 or pb_ratio > 5) and revenue_growth > 15:
                return "growth"
            elif pe_ratio > 0 and pe_ratio < 15 and pb_ratio < 3:
                return "value"
            else:
                return "blend"
        except:
            return "unknown"
    
    def _extract_fundamental_analysis(self, overview_data: Optional[Dict]) -> Dict:
        """Extract fundamental analysis metrics from overview data"""
        if not overview_data:
            return {
                "score": 50.0,
                "rotc_data": {
                    "latest_rotc": 0.0,
                    "avg_rotc": 0.0,
                    "improving": False
                },
                "growth_data": {
                    "avg_revenue_growth": 0.0,
                    "cash_flow_positive": False,
                    "revenue_growth_trend": 0.0
                }
            }
        
        try:
            # Calculate return on total capital
            rotc = 0.0
            if 'ReturnOnAssetsTTM' in overview_data:
                rotc = float(overview_data.get('ReturnOnAssetsTTM', 0)) * 100
            
            # Get revenue growth
            rev_growth = float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)) * 100
            
            # Get profit margin to determine if cash flow positive
            profit_margin = float(overview_data.get('ProfitMargin', 0)) * 100
            
            # Calculate fundamental score (0-100) based on metrics
            score = 50.0  # Default score
            
            # Adjust score based on ROTC (0-30 points)
            if rotc > 25:
                score += 30
            elif rotc > 15:
                score += 20
            elif rotc > 10:
                score += 15
            elif rotc > 5:
                score += 10
            elif rotc > 0:
                score += 5
            
            # Adjust score based on revenue growth (0-30 points)
            if rev_growth > 30:
                score += 30
            elif rev_growth > 20:
                score += 25
            elif rev_growth > 10:
                score += 20
            elif rev_growth > 5:
                score += 15
            elif rev_growth > 0:
                score += 10
            
            # Adjust score based on profit margin (0-20 points)
            if profit_margin > 20:
                score += 20
            elif profit_margin > 15:
                score += 15
            elif profit_margin > 10:
                score += 10
            elif profit_margin > 5:
                score += 5
            elif profit_margin > 0:
                score += 2
            
            # Ensure score is within 0-100 range
            score = max(0, min(100, score))
            
            return {
                "score": score,
                "rotc_data": {
                    "latest_rotc": rotc,
                    "avg_rotc": rotc,  # We only have current data
                    "improving": rev_growth > 0  # Assume improving if growth is positive
                },
                "growth_data": {
                    "avg_revenue_growth": rev_growth,
                    "cash_flow_positive": profit_margin > 0,
                    "revenue_growth_trend": 0.5 if rev_growth > 0 else -0.5  # Placeholder
                }
            }
        except Exception as e:
            self.logger.error(f"Error extracting fundamental analysis: {str(e)}")
            return {
                "score": 50.0,
                "rotc_data": {
                    "latest_rotc": 0.0,
                    "avg_rotc": 0.0,
                    "improving": False
                },
                "growth_data": {
                    "avg_revenue_growth": 0.0,
                    "cash_flow_positive": False,
                    "revenue_growth_trend": 0.0
                }
            }
    
    def _calculate_volatility(self, price_history: List[Dict]) -> float:
        """Calculate price volatility from price history"""
        if not price_history or len(price_history) < 2:
            return 0.0
        
        try:
            # Calculate daily returns
            prices = [day['price'] for day in price_history]
            returns = []
            
            for i in range(1, len(prices)):
                daily_return = (prices[i-1] / prices[i]) - 1 if prices[i] > 0 else 0
                returns.append(daily_return)
            
            # Calculate volatility (standard deviation of returns * sqrt(252) * 100)
            import numpy as np
            volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 0
            return volatility
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0
    
    def _calculate_risk_metrics(self, price_history: List[Dict]) -> Dict:
        """Calculate risk metrics from price history"""
        if not price_history or len(price_history) < 30:
            return {
                "volatility": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "sharpe_ratio": 0.0,
                "risk_level": "Unknown"
            }
        
        try:
            import numpy as np
            
            # Calculate volatility
            prices = [day['price'] for day in price_history]
            returns = []
            
            for i in range(1, len(prices)):
                daily_return = (prices[i-1] / prices[i]) - 1 if prices[i] > 0 else 0
                returns.append(daily_return)
            
            volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 0
            
            # Calculate max drawdown
            max_drawdown = 0
            peak = prices[0]
            
            for price in prices:
                if price > peak:
                    peak = price
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            max_drawdown *= 100  # Convert to percentage
            
            # Calculate Value at Risk (95% confidence)
            returns_arr = np.array(returns)
            var_95 = np.percentile(returns_arr, 5) * 100 if len(returns_arr) > 0 else 0
            
            # Calculate Sharpe Ratio (assume risk-free rate of 3%)
            risk_free_rate = 0.03
            avg_return = np.mean(returns_arr) * 252 if len(returns_arr) > 0 else 0
            sharpe_ratio = (avg_return - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
            
            # Determine risk level
            risk_level = "Unknown"
            if volatility > 35:
                risk_level = "High"
            elif volatility > 20:
                risk_level = "Moderate"
            elif volatility > 0:
                risk_level = "Low"
            
            return {
                "volatility": volatility,
                "max_drawdown": -max_drawdown,  # Negative since it's a loss
                "var_95": var_95,
                "sharpe_ratio": sharpe_ratio,
                "risk_level": risk_level
            }
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {
                "volatility": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "sharpe_ratio": 0.0,
                "risk_level": "Unknown"
            }
    
    def _generate_recommendation(self, overview_data: Optional[Dict], 
                               price_history: List[Dict]) -> Dict:
        """Generate investment recommendation based on available data"""
        # Default recommendation
        default_recommendation = {
            "action": "Hold",
            "reasoning": ["Insufficient data to make a recommendation"],
            "risk_context": "Unknown"
        }
        
        if not overview_data or not price_history or len(price_history) < 30:
            return default_recommendation
        
        try:
            # Extract key metrics
            pe_ratio = float(overview_data.get('PERatio', 0))
            profit_margin = float(overview_data.get('ProfitMargin', 0)) * 100
            rev_growth = float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)) * 100
            dividend_yield = float(overview_data.get('DividendYield', 0)) * 100
            
            # Get risk metrics
            risk_metrics = self._calculate_risk_metrics(price_history)
            volatility = risk_metrics.get('volatility', 0)
            sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
            
            # Determine action
            action = "Hold"  # Default action
            reasoning = []
            
            # Positive factors
            positive_count = 0
            
            if pe_ratio > 0 and pe_ratio < 20:
                reasoning.append("Attractive valuation (P/E ratio)")
                positive_count += 1
            
            if profit_margin > 15:
                reasoning.append("Strong profit margins")
                positive_count += 1
            
            if rev_growth > 10:
                reasoning.append("Solid revenue growth")
                positive_count += 1
            
            if dividend_yield > 2:
                reasoning.append("Attractive dividend yield")
                positive_count += 1
            
            if sharpe_ratio > 1:
                reasoning.append("Favorable risk-adjusted returns")
                positive_count += 1
            
            # Negative factors
            negative_count = 0
            
            if pe_ratio <= 0:
                reasoning.append("Negative earnings")
                negative_count += 1
            elif pe_ratio > 40:
                reasoning.append("Elevated valuation")
                negative_count += 1
            
            if profit_margin <= 0:
                reasoning.append("Unprofitable operations")
                negative_count += 1
            
            if rev_growth < 0:
                reasoning.append("Declining revenue")
                negative_count += 1
            
            if volatility > 35:
                reasoning.append("High price volatility")
                negative_count += 1
            
            # Determine action based on factors
            if positive_count >= 4 and negative_count <= 1:
                action = "Strong Buy"
            elif positive_count >= 3 and negative_count <= 1:
                action = "Buy"
            elif negative_count >= 3:
                action = "Sell"
            elif negative_count >= 2:
                action = "Reduce"
            else:
                action = "Hold"
            
            # Risk context
            risk_context = risk_metrics.get('risk_level', 'Unknown')
            
            return {
                "action": action,
                "reasoning": reasoning[:3],  # Limit to top 3 reasons
                "risk_context": risk_context
            }
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {str(e)}")
            return default_recommendation
    
    def _extract_dividend_metrics(self, overview_data: Optional[Dict]) -> Dict:
        """Extract dividend metrics from overview data"""
        if not overview_data:
            return {
                'dividend_yield': 0,
                'dividend_rate': 0,
                'payout_ratio': 0,
                'dividend_growth': 0
            }
        
        try:
            dividend_yield = float(overview_data.get('DividendYield', 0)) * 100
            dividend_rate = float(overview_data.get('DividendPerShare', 0))
            payout_ratio = float(overview_data.get('PayoutRatio', 0)) * 100
            
            # Dividend growth is not provided directly, use a default value
            dividend_growth = 0
            
            return {
                'dividend_yield': dividend_yield,
                'dividend_rate': dividend_rate,
                'payout_ratio': payout_ratio,
                'dividend_growth': dividend_growth
            }
        except Exception as e:
            self.logger.error(f"Error extracting dividend metrics: {str(e)}")
            return {
                'dividend_yield': 0,
                'dividend_rate': 0,
                'payout_ratio': 0,
                'dividend_growth': 0
            }
    
    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """
        Clear cache for a specific symbol or all symbols.
        
        Args:
            symbol: If provided, clear cache only for this symbol
            
        Returns:
            True if cache was cleared successfully
        """
        try:
            if symbol:
                # Clear cache for specific symbol
                # First clear memory cache
                keys_to_remove = []
                for cache_key in self.memory_cache:
                    if f"symbol={symbol}" in cache_key:
                        keys_to_remove.append(cache_key)
                
                for key in keys_to_remove:
                    del self.memory_cache[key]
                
                # Then clear disk cache
                count = 0
                for cache_file in self.cache_dir.glob(f"*symbol={symbol}*.pkl"):
                    cache_file.unlink()
                    count += 1
                
                self.logger.info(f"Cleared {count} cache files for {symbol}")
            else:
                # Clear all cache
                self.memory_cache = {}
                count = 0
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                    count += 1
                
                self.logger.info(f"Cleared all cache ({count} files)")
            
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False
            
    def analyze_stock_with_custom_weights(self, symbol: str, custom_weights: Dict = None) -> Dict:
        """
        Analyze stock with custom sentiment weights
        
        Args:
            symbol: Stock symbol
            custom_weights: Dictionary of custom weights for sentiment calculation
            
        Returns:
            Stock analysis with custom sentiment weights
        """
        # First get the stock data (use cached data whenever possible)
        data = self.analyze_stock(symbol, force_refresh=False)
        
        # If we have data and sentiment calculator is available
        if data:
            try:
                # Import sentiment calculator
                from analysis.sentiment_calculator import SentimentCalculator
                sentiment_calculator = SentimentCalculator()
                
                # Extract data needed for sentiment calculation
                week_52_high = data['price_metrics']['week_52_high']
                week_52_low = data['price_metrics']['week_52_low']
                current_price = data['current_price']
                ytd_performance = data['price_metrics']['ytd_performance']
                daily_change = data['price_metrics']['daily_change']
                
                # Extract ROTC if available
                rotc = None
                if 'integrated_analysis' in data and 'fundamental_analysis' in data['integrated_analysis']:
                    rotc_data = data['integrated_analysis']['fundamental_analysis'].get('rotc_data', {})
                    rotc = rotc_data.get('latest_rotc', None)
                
                # Get daily price history
                daily_data = self.get_daily_time_series(symbol)
                
                if daily_data and 'data' in daily_data:
                    # Create DataFrame from time series data
                    dates = []
                    prices_open = []
                    prices_high = []
                    prices_low = []
                    prices_close = []
                    
                    for day in daily_data['data']:
                        dates.append(day['date'])
                        prices_open.append(day['open'])
                        prices_high.append(day['high'])
                        prices_low.append(day['low'])
                        prices_close.append(day['close'])
                    
                    # Create DataFrame
                    import pandas as pd
                    price_history = pd.DataFrame({
                        'Open': prices_open,
                        'High': prices_high,
                        'Low': prices_low,
                        'Close': prices_close
                    }, index=pd.DatetimeIndex(dates))
                    
                    # Calculate sentiment with custom weights
                    print(f"AlphaVantageClient: Calculating sentiment with custom weights: {custom_weights}")
                    sentiment_data = sentiment_calculator.calculate_sentiment(
                        symbol=symbol,
                        price_history=price_history,
                        current_price=current_price,
                        week_52_high=week_52_high,
                        week_52_low=week_52_low,
                        ytd_performance=ytd_performance,
                        rotc=rotc,
                        daily_change=daily_change,
                        custom_weights=custom_weights
                    )
                    print(f"AlphaVantageClient: Sentiment result: {sentiment_data}")
                    
                    # Update sentiment data and scores
                    data['sentiment_data'] = sentiment_data
                    data['price_metrics']['sentiment_score'] = sentiment_data.get('sentiment_score', 50)
                    
                    # Log info about custom weights
                    self.logger.info(f"Applied custom sentiment weights to {symbol}: {custom_weights}")
            except Exception as e:
                self.logger.error(f"Error applying custom sentiment weights: {str(e)}")
        
        return data


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = AlphaVantageClient()
    
    # Test quote endpoint
    quote = client.get_quote('AAPL')
    print(f"AAPL Quote: {quote}")
    
    # Test company overview
    overview = client.get_company_overview('MSFT')
    if overview:
        print(f"MSFT Name: {overview.get('Name')}")
        print(f"MSFT Sector: {overview.get('Sector')}")
    
    # Test full analysis
    analysis = client.analyze_stock('NVDA')
    print(f"NVDA Analysis Results:")
    print(f"Current Price: ${analysis['current_price']}")
    print(f"52-Week High: ${analysis['price_metrics']['week_52_high']}")
    print(f"52-Week Low: ${analysis['price_metrics']['week_52_low']}")
    print(f"Recommendation: {analysis['integrated_analysis']['recommendation']['action']}")