"""
TwelveData API Stock Analyzer - SECURE VERSION
Primary data source for all stock analysis with proper security and API integration

SECURITY FIXES:
- No hardcoded API keys anywhere
- Proper environment variable handling
- No API key logging
- Clean error handling without fallbacks to mock data

API FIXES:
- Removed interval parameter from quote endpoint (doesn't support it)
- Proper authentication via query parameter
- Correct endpoint usage per TwelveData documentation
"""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List, Union
import os
import time
import json
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class TwelveDataAnalyzer:
    """Secure TwelveData API analyzer with proper authentication and error handling"""

    # Valid intervals for time_series endpoint (NOT used for quote endpoint)
    VALID_INTERVALS = {
        '1min', '5min', '15min', '30min', '45min',
        '1h', '2h', '4h', '5h', '1day', '1week', '1month'
    }

    # API limits
    MAX_OUTPUTSIZE = 5000
    MAX_BATCH_SYMBOLS = 100

    # Saudi market configuration
    SAUDI_EXCHANGE_CODE = 'XSAU'
    SAUDI_CURRENCY = 'SAR'
    SAUDI_TIMEZONE = 'Asia/Riyadh'

    def __init__(self, api_key: str = None):
        """Initialize with secure API key management - NO HARDCODED KEYS"""
        # SECURITY: Only use environment variable or explicit parameter
        self.api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')

        if not self.api_key:
            raise ValueError(
                "TWELVEDATA_API_KEY environment variable is required. "
                "Set this variable in AWS App Runner environment configuration. "
                "No fallback or default keys are provided for security."
            )

        # SECURITY: Never log full API key - only show it's configured
        logger.info(f"TwelveData API Key configured (ending in ****{self.api_key[-4:]})")
        self.base_url = "https://api.twelvedata.com"

        # Initialize connection pooling and circuit breaker
        self._init_connection_pooling()
        self._init_rate_limiting()
        self._init_circuit_breaker()

    def _init_connection_pooling(self):
        """Initialize HTTP session with connection pooling"""
        self.session = requests.Session()

        # HTTP adapter with connection pooling
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=50,
            max_retries=retry_strategy,
            pool_block=False
        )

        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Tadaro Investment Bot 1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=30, max=100'
        })

    def _init_rate_limiting(self):
        """Initialize Pro 610 rate limiting"""
        self.last_request = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Pro 610 Plan Rate Limits
        self.max_requests_per_minute = 610
        self.min_request_interval = 0.098  # ~98ms between requests
        self.burst_limit = 50
        self.burst_window = 10
        self.burst_count = 0
        self.last_burst_reset = time.time()

    def _init_circuit_breaker(self):
        """Initialize circuit breaker for API failure resilience"""
        self.circuit_failure_threshold = 5
        self.circuit_failure_window = 60
        self.circuit_open_duration = 300
        self.circuit_half_open_max_requests = 3

        self.circuit_state = CircuitState.CLOSED
        self.circuit_failure_count = 0
        self.circuit_success_count = 0
        self.circuit_total_requests = 0
        self.circuit_failures = []
        self.circuit_last_state_change = time.time()
        self.circuit_half_open_requests = 0
        self.circuit_lock = threading.Lock()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get current quote data - FIXED VERSION without interval parameter

        The quote endpoint does NOT accept interval parameter according to TwelveData docs
        """
        try:
            validated_symbol = self._validate_symbol(symbol)

            # Quote endpoint parameters (NO INTERVAL PARAMETER)
            params = {
                'symbol': validated_symbol
            }

            # Add timezone for Saudi market symbols
            if ':Tadawul' in validated_symbol:
                params['timezone'] = self.SAUDI_TIMEZONE

            logger.info(f"Getting quote for {symbol} -> {validated_symbol}")
            data = self._make_request('quote', params)

            if isinstance(data, dict) and 'symbol' in data:
                is_saudi = ':Tadawul' in validated_symbol

                return {
                    'symbol': data.get('symbol', validated_symbol),
                    'original_symbol': symbol,
                    'name': data.get('name', symbol),
                    'exchange': data.get('exchange', self.SAUDI_EXCHANGE_CODE if is_saudi else ''),
                    'currency': data.get('currency', self.SAUDI_CURRENCY if is_saudi else 'USD'),
                    'datetime': data.get('datetime', ''),
                    'timestamp': int(data.get('timestamp', 0)),
                    'open': float(data.get('open', 0)) if data.get('open') else 0,
                    'high': float(data.get('high', 0)) if data.get('high') else 0,
                    'low': float(data.get('low', 0)) if data.get('low') else 0,
                    'close': float(data.get('close', 0)) if data.get('close') else 0,
                    'volume': int(data.get('volume', 0)) if data.get('volume') else 0,
                    'previous_close': float(data.get('previous_close', 0)) if data.get('previous_close') else 0,
                    'change': float(data.get('change', 0)) if data.get('change') else 0,
                    'percent_change': float(data.get('percent_change', 0)) if data.get('percent_change') else 0,
                    'data_source': 'twelvedata',
                    'data_timestamp': datetime.now().isoformat(),
                    'success': True,
                    'is_saudi_market': is_saudi
                }
            else:
                logger.error(f"Invalid quote response format for {symbol}: {data}")
                raise Exception(f"Invalid quote data format from TwelveData")

        except Exception as e:
            logger.error(f"TwelveData quote failed for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price - simplified endpoint"""
        try:
            validated_symbol = self._validate_symbol(symbol)
            params = {'symbol': validated_symbol}

            data = self._make_request('price', params)

            if isinstance(data, dict) and 'price' in data:
                return {
                    'symbol': validated_symbol,
                    'original_symbol': symbol,
                    'price': float(data['price']),
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'twelvedata',
                    'success': True,
                    'is_saudi_market': ':Tadawul' in validated_symbol
                }
            else:
                raise Exception(f"Invalid price data format: {data}")

        except Exception as e:
            logger.error(f"TwelveData price failed for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def analyze_stock(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Comprehensive stock analysis using TwelveData"""
        try:
            logger.info(f"Analyzing {symbol} using TwelveData API as primary source")

            # Get quote data (main method)
            quote_data = self.get_quote(symbol)

            if not quote_data.get('success'):
                raise Exception(f"Failed to get quote data: {quote_data.get('error', 'Unknown error')}")

            # Extract key metrics
            current_price = quote_data.get('close', 0)
            if current_price <= 0:
                raise Exception("Invalid or zero price from TwelveData")

            return {
                'symbol': quote_data['symbol'],
                'original_symbol': symbol,
                'current_price': current_price,
                'open': quote_data.get('open', 0),
                'high': quote_data.get('high', 0),
                'low': quote_data.get('low', 0),
                'volume': quote_data.get('volume', 0),
                'change': quote_data.get('change', 0),
                'percent_change': quote_data.get('percent_change', 0),
                'currency': quote_data.get('currency', 'USD'),
                'exchange': quote_data.get('exchange', ''),
                'data_source': 'twelvedata',
                'data_timestamp': datetime.now().isoformat(),
                'success': True,
                'is_saudi_market': quote_data.get('is_saudi_market', False)
            }

        except Exception as e:
            logger.error(f"TwelveData analysis failed for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make secure API request with proper authentication"""
        current_time = time.time()

        # Circuit breaker check
        if not self._check_circuit_breaker():
            raise Exception("TwelveData API temporarily unavailable - Circuit breaker open")

        # Rate limiting
        self._apply_rate_limiting(current_time)

        # SECURITY: Add API key as query parameter (TwelveData standard)
        params['apikey'] = self.api_key
        params['format'] = 'json'

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=(10, 30)
            )

            if response.status_code == 401:
                self._record_circuit_failure()
                raise ValueError(f"TwelveData authentication failed - check API key configuration in AWS App Runner environment")

            elif response.status_code == 403:
                self._record_circuit_failure()
                raise ValueError("Insufficient TwelveData subscription privileges")

            elif response.status_code == 429:
                self._record_circuit_failure()
                raise ValueError("TwelveData rate limit exceeded")

            elif response.status_code >= 400:
                self._record_circuit_failure()
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', response.text)
                except:
                    error_msg = response.text
                raise requests.HTTPError(f"TwelveData API Error {response.status_code}: {error_msg}")

            response.raise_for_status()
            data = response.json()

            # Check for API-level errors
            if isinstance(data, dict) and data.get('status') == 'error':
                self._record_circuit_failure()
                raise Exception(f"TwelveData API Error: {data.get('message', 'Unknown error')}")

            # Record success
            self._record_circuit_success()
            return data

        except requests.exceptions.RequestException as e:
            self._record_circuit_failure()
            logger.error(f"Network error for TwelveData API: {str(e)}")
            raise
        except Exception as e:
            if "TwelveData API Error" not in str(e):
                self._record_circuit_failure()
            raise

    def _validate_symbol(self, symbol: str) -> str:
        """Validate and format symbol with Saudi market support"""
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

        symbol = symbol.upper().strip()

        # Already formatted Tadawul symbols
        if ':TADAWUL' in symbol:
            return symbol

        # Handle .SAU format
        if symbol.endswith('.SAU'):
            base_symbol = symbol[:-4]
            return f"{base_symbol}:Tadawul"

        # Saudi symbol detection
        if self._is_saudi_symbol(symbol):
            return f"{symbol}:Tadawul"

        return symbol

    def _is_saudi_symbol(self, symbol: str) -> bool:
        """Detect Saudi market symbols"""
        # 4-digit numbers (most common Saudi stocks)
        if symbol.isdigit() and len(symbol) == 4:
            return True

        # 5-digit numbers
        if symbol.isdigit() and len(symbol) == 5:
            return True

        # Alphanumeric starting with 4+ digits
        if len(symbol) >= 4 and symbol[:4].isdigit():
            remaining = symbol[4:]
            if remaining == "" or remaining.isalpha():
                return True

        return False

    def _apply_rate_limiting(self, current_time: float):
        """Apply Pro 610 rate limiting"""
        # Reset window if needed
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time

        # Reset burst counter
        if current_time - self.last_burst_reset >= self.burst_window:
            self.burst_count = 0
            self.last_burst_reset = current_time

        # Check rate limits
        if self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()

        # Check burst limit
        if self.burst_count >= self.burst_limit:
            time.sleep(self.burst_window)
            self.burst_count = 0

        # Apply minimum interval
        time_since_last = current_time - self.last_request
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.request_count += 1
        self.burst_count += 1
        self.last_request = time.time()

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows requests"""
        current_time = time.time()

        with self.circuit_lock:
            if self.circuit_state == CircuitState.CLOSED:
                return True

            elif self.circuit_state == CircuitState.OPEN:
                if current_time - self.circuit_last_state_change >= self.circuit_open_duration:
                    self._transition_to_half_open()
                    return True
                return False

            elif self.circuit_state == CircuitState.HALF_OPEN:
                if self.circuit_half_open_requests < self.circuit_half_open_max_requests:
                    self.circuit_half_open_requests += 1
                    return True
                return False

        return False

    def _record_circuit_success(self):
        """Record successful request for circuit breaker"""
        current_time = time.time()

        with self.circuit_lock:
            self.circuit_success_count += 1
            self.circuit_total_requests += 1

            if self.circuit_state == CircuitState.HALF_OPEN:
                if self.circuit_half_open_requests >= self.circuit_half_open_max_requests:
                    self.circuit_state = CircuitState.CLOSED
                    self.circuit_last_state_change = current_time
                    self.circuit_half_open_requests = 0
                    logger.info("TwelveData Circuit Breaker: API recovered - CLOSED state")

    def _record_circuit_failure(self):
        """Record failed request for circuit breaker"""
        current_time = time.time()

        with self.circuit_lock:
            self.circuit_total_requests += 1
            self.circuit_failures.append(current_time)

            # Remove old failures outside window
            self.circuit_failures = [
                f for f in self.circuit_failures
                if current_time - f <= self.circuit_failure_window
            ]

            self.circuit_failure_count = len(self.circuit_failures)

            # Check if should open circuit
            if (self.circuit_state == CircuitState.CLOSED and
                self.circuit_failure_count >= self.circuit_failure_threshold):
                self.circuit_state = CircuitState.OPEN
                self.circuit_last_state_change = current_time
                logger.warning(f"TwelveData Circuit Breaker: OPENED due to {self.circuit_failure_count} failures")

    def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state"""
        self.circuit_state = CircuitState.HALF_OPEN
        self.circuit_last_state_change = time.time()
        self.circuit_half_open_requests = 0

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        with self.circuit_lock:
            success_rate = (self.circuit_success_count / self.circuit_total_requests * 100) if self.circuit_total_requests > 0 else 100.0

            return {
                'state': self.circuit_state.value,
                'failure_count': self.circuit_failure_count,
                'success_rate_percentage': round(success_rate, 2),
                'total_requests': self.circuit_total_requests
            }