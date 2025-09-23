"""
TwelveData API Stock Analyzer - FIXED VERSION
Primary data source for all stock analysis with security and functionality fixes

CRITICAL FIXES APPLIED:
1. Header-based authentication (instead of query parameter)
2. Environment variable API key management (security)
3. Improved error handling for all HTTP status codes
4. Input validation for intervals and parameters
5. Saudi market support with proper symbol formatting
6. Timezone support for consistent timestamps
7. Batch request capabilities
8. Proper rate limiting logic
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

logger = logging.getLogger(__name__)

class TwelveDataAnalyzer:
    """Fixed TwelveData API analyzer with security and functionality improvements"""

    # Valid intervals as per TwelveData documentation
    VALID_INTERVALS = {
        '1min', '5min', '15min', '30min', '45min',
        '1h', '2h', '4h', '5h', '1day', '1week', '1month'
    }

    # Maximum values as per TwelveData limits
    MAX_OUTPUTSIZE = 5000
    MAX_BATCH_SYMBOLS = 100

    # Saudi market configuration
    SAUDI_EXCHANGE_CODE = 'XSAU'
    SAUDI_CURRENCY = 'SAR'
    SAUDI_TIMEZONE = 'Asia/Riyadh'

    def __init__(self, api_key: str = None):
        """Initialize with secure API key management"""
        # SECURITY FIX: Use environment variable - NO HARDCODED KEYS
        self.api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError(
                "TWELVEDATA_API_KEY environment variable is required. "
                "Set this variable with your Pro 610 subscription key from https://twelvedata.com/. "
                "Example: export TWELVEDATA_API_KEY='your_api_key_here'"
            )

        if not self._validate_api_key():
            raise ValueError("Invalid TwelveData API key format")

        logger.info(f"TwelveData API Key configured: {self.api_key[:8]}...{self.api_key[-4:]}")
        self.base_url = "https://api.twelvedata.com"

        # CONNECTION POOLING: Advanced HTTP session with connection pooling
        self.session = self._create_optimized_session()
        self.session.headers.update({
            'Authorization': f'apikey {self.api_key}',
            'User-Agent': 'Tadaro Investment Bot 1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        # Optimized rate limiting - Pro 610 plan: FULL 610 requests/minute utilization
        self.last_request = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Pro 610 Plan Rate Limits (OPTIMIZED)
        self.max_requests_per_minute = 610  # Full Pro 610 capacity
        self.min_request_interval = 0.098  # ~98ms between requests (10.2 req/sec)
        self.burst_limit = 50  # Allow bursts up to 50 requests
        self.burst_window = 10  # Reset burst counter every 10 seconds
        self.burst_count = 0
        self.last_burst_reset = time.time()

        logger.info(f"TwelveData Pro 610 rate limiting: {self.max_requests_per_minute} req/min, burst: {self.burst_limit}/{self.burst_window}s")

        # CIRCUIT BREAKER: API failure resilience pattern
        self._init_circuit_breaker()

    def _validate_api_key(self) -> bool:
        """Validate API key format"""
        if not self.api_key or len(self.api_key) < 20:
            return False
        return True

    def _create_optimized_session(self) -> requests.Session:
        """Create optimized HTTP session with advanced connection pooling"""
        session = requests.Session()

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=50,
            max_retries=self._create_retry_strategy(),
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.trust_env = False

        session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=30, max=100'
        })

        logger.info(f"TwelveData connection pool: 10 pools × 50 connections, keep-alive: 30s")
        return session

    def _create_retry_strategy(self) -> Retry:
        """Create intelligent retry strategy for API resilience"""
        return Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_redirect=False,
            raise_on_status=False
        )

    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status for monitoring"""
        try:
            adapter = self.session.get_adapter("https://api.twelvedata.com")
            if hasattr(adapter, 'poolmanager') and adapter.poolmanager:
                return {
                    'pool_manager_active': True,
                    'optimization_status': 'Connection pooling active and optimized'
                }
            else:
                return {
                    'pool_manager_active': False,
                    'optimization_status': 'Ready to initialize on first request'
                }
        except Exception as e:
            return {
                'pool_manager_active': False,
                'error': str(e),
                'optimization_status': 'Connection pool status unavailable'
            }

    def _validate_symbol(self, symbol: str) -> str:
        """
        Validate and format symbol, including comprehensive Saudi market symbol support

        Supported Saudi formats:
        - 4-digit: "4261" -> "4261:Tadawul"
        - 5-digit: "12345" -> "12345:Tadawul"
        - Alphanumeric: "2222A" -> "2222A:Tadawul"
        - Already formatted: "4261:Tadawul" -> "4261:Tadawul"
        - Saudi with exchange: "4261.SAU" -> "4261:Tadawul"
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

        original_symbol = symbol
        symbol = symbol.upper().strip()

        # Already formatted Tadawul symbols
        if ':TADAWUL' in symbol:
            return symbol

        # Handle .SAU format (convert to Tadawul)
        if symbol.endswith('.SAU'):
            base_symbol = symbol[:-4]  # Remove .SAU
            return f"{base_symbol}:Tadawul"

        # Enhanced Saudi market symbol detection
        if self._is_saudi_symbol(symbol):
            return f"{symbol}:Tadawul"

        return symbol

    def _is_saudi_symbol(self, symbol: str) -> bool:
        """
        Comprehensive Saudi symbol detection

        Saudi market patterns:
        - 4-digit numbers: 1234, 4261, 7040
        - 5-digit numbers: 12345, 98765
        - Alphanumeric with numbers: 2222A, 1180B, 4260C
        - Mixed patterns: A1B2C, but starting with numbers preferred
        """
        # Pattern 1: Pure 4-digit numbers (most common)
        if symbol.isdigit() and len(symbol) == 4:
            return True

        # Pattern 2: Pure 5-digit numbers (emerging)
        if symbol.isdigit() and len(symbol) == 5:
            return True

        # Pattern 3: Alphanumeric starting with 4+ digits
        if len(symbol) >= 4 and symbol[:4].isdigit():
            # Remaining characters can be letters
            remaining = symbol[4:]
            if remaining == "" or remaining.isalpha():
                return True

        # Pattern 4: Special known Saudi patterns
        saudi_patterns = [
            # Rights issues and warrants
            r'^[0-9]{4}[A-Z]$',  # 4 digits + 1 letter (e.g., 2222A)
            r'^[0-9]{4}[A-Z][0-9]$',  # 4 digits + letter + digit
        ]

        import re
        for pattern in saudi_patterns:
            if re.match(pattern, symbol):
                return True

        return False

    def _apply_rate_limiting(self, current_time: float) -> None:
        """
        Apply optimized Pro 610 rate limiting with intelligent burst handling

        Strategy:
        1. Track requests per minute (610 max)
        2. Allow bursts for better performance
        3. Smooth distribution to avoid API limits
        4. Reset counters appropriately
        """
        # Reset burst counter every burst_window seconds
        if current_time - self.last_burst_reset >= self.burst_window:
            self.burst_count = 0
            self.last_burst_reset = current_time

        # Reset minute counter if 60+ seconds have passed
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time

        # Check if we're approaching minute limit
        if self.request_count >= self.max_requests_per_minute:
            # Calculate time to wait until next minute window
            time_to_wait = 60 - (current_time - self.request_window_start)
            if time_to_wait > 0:
                logger.info(f"TwelveData rate limit approached: waiting {time_to_wait:.2f}s for next minute window")
                time.sleep(time_to_wait)
                # Reset counters after waiting
                self.request_count = 0
                self.request_window_start = time.time()

        # Handle burst limiting for API stability
        if self.burst_count >= self.burst_limit:
            # Small pause to prevent overwhelming the API
            time.sleep(0.2)  # 200ms pause after burst
            logger.debug(f"TwelveData burst limit reached: brief pause for API stability")

        # Standard inter-request delay
        time_since_last = current_time - self.last_request
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        # Update counters
        self.request_count += 1
        self.burst_count += 1
        self.last_request = time.time()

        # Log rate limiting stats every 50 requests
        if self.request_count % 50 == 0:
            requests_per_minute = self.request_count / ((current_time - self.request_window_start) / 60)
            logger.info(f"TwelveData Pro 610 stats: {self.request_count}/610 requests this minute, rate: {requests_per_minute:.1f}/min")

    def get_rate_limiting_status(self) -> Dict[str, Any]:
        """Get current rate limiting status for monitoring and debugging"""
        current_time = time.time()
        window_elapsed = current_time - self.request_window_start
        burst_elapsed = current_time - self.last_burst_reset

        # Calculate current rates
        if window_elapsed > 0:
            current_rate_per_minute = (self.request_count / window_elapsed) * 60
        else:
            current_rate_per_minute = 0

        return {
            'subscription_plan': 'Pro 610',
            'max_requests_per_minute': self.max_requests_per_minute,
            'requests_this_minute': self.request_count,
            'requests_remaining': max(0, self.max_requests_per_minute - self.request_count),
            'current_rate_per_minute': round(current_rate_per_minute, 1),
            'utilization_percentage': round((self.request_count / self.max_requests_per_minute) * 100, 1),
            'burst_count': self.burst_count,
            'burst_remaining': max(0, self.burst_limit - self.burst_count),
            'window_elapsed_seconds': round(window_elapsed, 2),
            'time_to_reset_minutes': max(0, round((60 - window_elapsed) / 60, 2)),
            'time_to_burst_reset': max(0, round(self.burst_window - burst_elapsed, 2)),
            'optimization_status': 'Fully optimized for Pro 610 capacity'
        }

    def _init_circuit_breaker(self) -> None:
        """
        Initialize circuit breaker for API failure resilience

        Circuit Breaker States:
        1. CLOSED: Normal operation (requests allowed)
        2. OPEN: API failures detected (requests blocked)
        3. HALF_OPEN: Testing if API recovered (limited requests)

        Configuration optimized for TwelveData Pro 610:
        - Failure threshold: 5 failures in 60 seconds
        - Open circuit duration: 300 seconds (5 minutes)
        - Half-open test requests: 3 requests
        """
        from enum import Enum
        import threading

        # Circuit breaker states
        class CircuitState(Enum):
            CLOSED = "closed"      # Normal operation
            OPEN = "open"          # Blocking requests due to failures
            HALF_OPEN = "half_open"  # Testing recovery

        self.CircuitState = CircuitState

        # Circuit breaker configuration
        self.circuit_failure_threshold = 5        # Failures to trigger open state
        self.circuit_failure_window = 60          # Time window for failure counting (seconds)
        self.circuit_open_duration = 300          # How long to keep circuit open (seconds)
        self.circuit_half_open_max_requests = 3   # Test requests in half-open state

        # Circuit breaker state
        self.circuit_state = CircuitState.CLOSED
        self.circuit_failure_count = 0
        self.circuit_last_failure_time = 0
        self.circuit_last_state_change = time.time()
        self.circuit_half_open_requests = 0

        # Thread safety for circuit breaker
        self.circuit_lock = threading.Lock()

        # Success/failure tracking
        self.circuit_success_count = 0
        self.circuit_total_requests = 0

        logger.info(f"TwelveData Circuit Breaker: threshold={self.circuit_failure_threshold}, window={self.circuit_failure_window}s, timeout={self.circuit_open_duration}s")

    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker allows the request

        Returns:
            True if request is allowed
            False if request is blocked (circuit is open)
        """
        current_time = time.time()

        with self.circuit_lock:
            if self.circuit_state == self.CircuitState.CLOSED:
                # Normal operation - allow all requests
                return True

            elif self.circuit_state == self.CircuitState.OPEN:
                # Check if enough time has passed to try half-open
                if current_time - self.circuit_last_state_change >= self.circuit_open_duration:
                    self._transition_to_half_open()
                    logger.info("TwelveData Circuit Breaker: Transitioning to HALF_OPEN for recovery testing")
                    return True
                else:
                    # Circuit is still open - block request
                    return False

            elif self.circuit_state == self.CircuitState.HALF_OPEN:
                # Allow limited requests to test recovery
                if self.circuit_half_open_requests < self.circuit_half_open_max_requests:
                    self.circuit_half_open_requests += 1
                    return True
                else:
                    # Already sent max test requests
                    return False

        return False

    def _record_circuit_success(self) -> None:
        """Record a successful API request for circuit breaker"""
        current_time = time.time()

        with self.circuit_lock:
            self.circuit_success_count += 1
            self.circuit_total_requests += 1

            if self.circuit_state == self.CircuitState.HALF_OPEN:
                # If we're in half-open and got success, consider closing circuit
                if self.circuit_half_open_requests >= self.circuit_half_open_max_requests:
                    self._transition_to_closed()
                    logger.info("TwelveData Circuit Breaker: API recovered - Transitioning to CLOSED")

            # Clean up old failures (outside the failure window)
            if current_time - self.circuit_last_failure_time > self.circuit_failure_window:
                self.circuit_failure_count = 0

    def _record_circuit_failure(self) -> None:
        """Record a failed API request for circuit breaker"""
        current_time = time.time()

        with self.circuit_lock:
            self.circuit_failure_count += 1
            self.circuit_last_failure_time = current_time
            self.circuit_total_requests += 1

            # Check if we should open the circuit
            if self.circuit_state == self.CircuitState.CLOSED:
                if self.circuit_failure_count >= self.circuit_failure_threshold:
                    self._transition_to_open()
                    logger.warning(f"TwelveData Circuit Breaker: OPENED due to {self.circuit_failure_count} failures")

            elif self.circuit_state == self.CircuitState.HALF_OPEN:
                # Failure during half-open means API is still failing
                self._transition_to_open()
                logger.warning("TwelveData Circuit Breaker: Recovery test failed - Transitioning back to OPEN")

    def _transition_to_closed(self) -> None:
        """Transition circuit breaker to CLOSED state"""
        self.circuit_state = self.CircuitState.CLOSED
        self.circuit_last_state_change = time.time()
        self.circuit_failure_count = 0
        self.circuit_half_open_requests = 0

    def _transition_to_open(self) -> None:
        """Transition circuit breaker to OPEN state"""
        self.circuit_state = self.CircuitState.OPEN
        self.circuit_last_state_change = time.time()
        self.circuit_half_open_requests = 0

    def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to HALF_OPEN state"""
        self.circuit_state = self.CircuitState.HALF_OPEN
        self.circuit_last_state_change = time.time()
        self.circuit_half_open_requests = 0

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status for monitoring"""
        current_time = time.time()

        with self.circuit_lock:
            # Calculate success rate
            if self.circuit_total_requests > 0:
                success_rate = (self.circuit_success_count / self.circuit_total_requests) * 100
            else:
                success_rate = 100.0

            # Time until circuit attempts recovery
            if self.circuit_state == self.CircuitState.OPEN:
                time_to_half_open = max(0, self.circuit_open_duration - (current_time - self.circuit_last_state_change))
            else:
                time_to_half_open = 0

            return {
                'state': self.circuit_state.value,
                'failure_count': self.circuit_failure_count,
                'success_count': self.circuit_success_count,
                'total_requests': self.circuit_total_requests,
                'success_rate_percentage': round(success_rate, 2),
                'failure_threshold': self.circuit_failure_threshold,
                'time_to_recovery_test': round(time_to_half_open, 1),
                'half_open_requests_sent': self.circuit_half_open_requests,
                'half_open_requests_max': self.circuit_half_open_max_requests,
                'configuration': {
                    'failure_threshold': self.circuit_failure_threshold,
                    'failure_window_seconds': self.circuit_failure_window,
                    'open_duration_seconds': self.circuit_open_duration,
                    'recovery_test_requests': self.circuit_half_open_max_requests
                },
                'resilience_status': f'Circuit breaker provides API failure resilience - {self.circuit_state.value.upper()} state'
            }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make optimized request with connection pooling, Pro 610 rate limiting, and circuit breaker protection

        Connection Pooling Benefits:
        1. Reuses existing connections (faster requests)
        2. Handles connection failures with retry logic
        3. Optimizes for TwelveData Pro 610 throughput
        4. Monitors connection performance

        Circuit Breaker Protection:
        1. Prevents API overload during failures
        2. Automatic failure detection and recovery
        3. Fast-fail behavior when API is down
        4. Graceful degradation for reliability
        """
        current_time = time.time()
        request_start_time = time.time()

        # CIRCUIT BREAKER: Check if we should block the request
        if not self._check_circuit_breaker():
            circuit_status = self.get_circuit_breaker_status()
            logger.warning(f"TwelveData Circuit Breaker: Request blocked - State: {circuit_status['state']}, "
                         f"Failures: {circuit_status['failure_count']}/{circuit_status['failure_threshold']}")
            raise Exception(f"TwelveData API temporarily unavailable - Circuit Breaker {circuit_status['state']}")

        # Optimized Pro 610 rate limiting with burst handling
        self._apply_rate_limiting(current_time)

        # Always request JSON format
        params['format'] = 'json'

        try:
            # Connection pooling optimized request with enhanced timeout
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=(10, 30),  # (connect_timeout, read_timeout)
                allow_redirects=True,
                stream=False  # Don't stream for JSON responses
            )

            request_duration = time.time() - request_start_time
            self.last_request = time.time()

            # Log connection performance every 25 requests
            if self.request_count % 25 == 0:
                logger.debug(f"TwelveData connection performance: {request_duration:.3f}s for {endpoint}")

            # Enhanced error handling with connection context and circuit breaker integration
            if response.status_code == 401:
                raise ValueError("Invalid TwelveData API key - check TWELVEDATA_API_KEY environment variable")
            elif response.status_code == 403:
                raise ValueError("Insufficient TwelveData plan access for requested data")
            elif response.status_code == 429:
                # Rate limit hit - connection pooling + retry should handle this
                # CIRCUIT BREAKER: Record rate limit as failure
                self._record_circuit_failure()
                logger.warning(f"TwelveData rate limit hit - retry logic should handle this")
                raise ValueError("TwelveData rate limit exceeded despite optimization")
            elif response.status_code == 404:
                raise ValueError(f"Symbol not found or endpoint not available: {params.get('symbol', endpoint)}")
            elif response.status_code in [500, 502, 503, 504]:
                # Server errors - retry logic should have handled these
                # CIRCUIT BREAKER: Record server errors as failures
                self._record_circuit_failure()
                logger.warning(f"TwelveData server error {response.status_code} - retries exhausted")
                raise requests.HTTPError(f"TwelveData server error {response.status_code} after retries")
            elif response.status_code >= 400:
                # CIRCUIT BREAKER: Record client/server errors as failures
                self._record_circuit_failure()
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', response.text)
                except:
                    error_msg = response.text
                raise requests.HTTPError(f"HTTP {response.status_code}: {error_msg}")

            response.raise_for_status()
            data = response.json()

            # Enhanced success logging with performance metrics
            if request_duration > 2.0:  # Log slow requests
                logger.info(f"TwelveData slow request: {endpoint} took {request_duration:.2f}s")
            else:
                logger.debug(f"TwelveData API success: {endpoint} ({request_duration:.3f}s)")

            # IMPROVED API ERROR DETECTION
            if isinstance(data, dict):
                if data.get('status') == 'error':
                    error_code = data.get('code', 'unknown')
                    error_message = data.get('message', 'Unknown error')
                    # CIRCUIT BREAKER: Record API-level failure
                    self._record_circuit_failure()
                    raise Exception(f"TwelveData API Error {error_code}: {error_message}")

                # Check for empty response
                if not data or (isinstance(data, dict) and not any(data.values())):
                    # CIRCUIT BREAKER: Record failure for empty responses
                    self._record_circuit_failure()
                    raise Exception("Empty response from TwelveData API")

            # CIRCUIT BREAKER: Record successful request
            self._record_circuit_success()

            return data

        except requests.exceptions.RequestException as e:
            # CIRCUIT BREAKER: Record network failure
            self._record_circuit_failure()
            logger.error(f"Network error for TwelveData API: {str(e)}")
            raise
        except Exception as e:
            # CIRCUIT BREAKER: Record general failure (only if not already recorded)
            # Note: API errors and empty responses already recorded above
            if "TwelveData API Error" not in str(e) and "Empty response" not in str(e):
                self._record_circuit_failure()
            logger.error(f"TwelveData API request failed: {str(e)}")
            raise

    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """Get real-time price data with symbol validation"""
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
            logger.error(f"Error getting real-time price for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def get_quote(self, symbol: str, interval: str = '1min') -> Dict[str, Any]:
        """Get comprehensive quote data with Saudi market support"""
        try:
            validated_symbol = self._validate_symbol(symbol)

            # Validate interval
            if interval not in self.VALID_INTERVALS:
                logger.warning(f"Invalid interval '{interval}', using '1min'")
                interval = '1min'

            params = {
                'symbol': validated_symbol,
                'interval': interval
            }

            # Add timezone for Saudi market
            if ':Tadawul' in validated_symbol:
                params['timezone'] = self.SAUDI_TIMEZONE

            data = self._make_request('quote', params)

            if isinstance(data, dict) and 'symbol' in data:
                is_saudi = ':Tadawul' in validated_symbol

                return {
                    'symbol': data.get('symbol', validated_symbol),
                    'original_symbol': symbol,
                    'name': data.get('name', symbol),
                    'exchange': data.get('exchange', 'XSAU' if is_saudi else ''),
                    'currency': data.get('currency', 'SAR' if is_saudi else 'USD'),
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
                    'average_volume': int(data.get('average_volume', 0)) if data.get('average_volume') else 0,
                    'is_market_open': data.get('is_market_open', False),
                    'fifty_two_week': data.get('fifty_two_week', {}),
                    'data_source': 'twelvedata',
                    'is_saudi_market': is_saudi,
                    'success': True
                }
            else:
                raise Exception(f"Invalid quote data format: {data}")

        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def get_time_series(self, symbol: str, interval: str = '1day', outputsize: int = 365,
                       timezone: str = 'UTC', start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get historical time series data with full input validation and Saudi market support"""
        try:
            # INPUT VALIDATION
            validated_symbol = self._validate_symbol(symbol)

            if interval not in self.VALID_INTERVALS:
                raise ValueError(f"Invalid interval '{interval}'. Must be one of: {sorted(self.VALID_INTERVALS)}")

            if outputsize > self.MAX_OUTPUTSIZE:
                logger.warning(f"OutputSize {outputsize} exceeds limit of {self.MAX_OUTPUTSIZE}, capping")
                outputsize = self.MAX_OUTPUTSIZE
            elif outputsize < 1:
                outputsize = 1

            params = {
                'symbol': validated_symbol,
                'interval': interval,
                'outputsize': outputsize,
                'timezone': timezone
            }

            # Add date range if specified
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date

            # Use Saudi timezone for Saudi stocks
            if ':Tadawul' in validated_symbol:
                params['timezone'] = self.SAUDI_TIMEZONE

            data = self._make_request('time_series', params)

            if isinstance(data, dict) and 'values' in data:
                return {
                    'symbol': data.get('meta', {}).get('symbol', validated_symbol),
                    'original_symbol': symbol,
                    'interval': data.get('meta', {}).get('interval', interval),
                    'currency': data.get('meta', {}).get('currency', 'SAR' if ':Tadawul' in validated_symbol else 'USD'),
                    'exchange': data.get('meta', {}).get('exchange', ''),
                    'type': data.get('meta', {}).get('type', ''),
                    'timezone': data.get('meta', {}).get('timezone', timezone),
                    'values': data['values'],
                    'data_source': 'twelvedata',
                    'is_saudi_market': ':Tadawul' in validated_symbol,
                    'success': True
                }
            else:
                raise Exception(f"Invalid time series data format: {data}")

        except Exception as e:
            logger.error(f"Error getting time series for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def get_batch_quotes(self, symbols: List[str], interval: str = '1min') -> Dict[str, Any]:
        """Get multiple quotes in a single API call using batch endpoint"""
        try:
            if not symbols or len(symbols) == 0:
                raise ValueError("Symbols list cannot be empty")

            if len(symbols) > self.MAX_BATCH_SYMBOLS:
                logger.warning(f"Too many symbols ({len(symbols)}), limiting to {self.MAX_BATCH_SYMBOLS}")
                symbols = symbols[:self.MAX_BATCH_SYMBOLS]

            # Validate all symbols
            validated_symbols = [self._validate_symbol(s) for s in symbols]
            symbols_str = ','.join(validated_symbols)

            params = {
                'symbol': symbols_str,
                'interval': interval
            }

            data = self._make_request('quote', params)

            # Handle both single dict and list responses
            if isinstance(data, dict) and 'symbol' in data:
                # Single symbol response
                data = [data]
            elif isinstance(data, list):
                # Multiple symbols response
                pass
            else:
                raise Exception(f"Unexpected batch response format: {type(data)}")

            return {
                'symbols': symbols,
                'data': data,
                'count': len(data),
                'data_source': 'twelvedata',
                'success': True
            }

        except Exception as e:
            logger.error(f"Error getting batch quotes for {symbols}: {str(e)}")
            return {
                'symbols': symbols,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def analyze_stock(self, symbol: str, force_refresh: bool = True) -> Dict[str, Any]:
        """
        Comprehensive stock analysis using TwelveData API with Saudi market support
        This is the main method called by app.py for stock analysis
        """
        try:
            validated_symbol = self._validate_symbol(symbol)
            is_saudi_market = ':Tadawul' in validated_symbol

            logger.info(f"Analyzing {validated_symbol} using TwelveData API (Saudi: {is_saudi_market})")

            # Get quote data (includes current price and basic metrics)
            quote_data = self.get_quote(symbol)
            if not quote_data.get('success'):
                raise Exception(f"Failed to get quote data: {quote_data.get('error')}")

            # Get historical data for technical analysis
            historical_data = self.get_time_series(symbol, interval='1day', outputsize=252)

            # Process the data into the expected format
            result = {
                'symbol': validated_symbol,
                'original_symbol': symbol,
                'current_price': quote_data.get('close', 0),
                'open': quote_data.get('open', 0),
                'high': quote_data.get('high', 0),
                'low': quote_data.get('low', 0),
                'volume': quote_data.get('volume', 0),
                'previous_close': quote_data.get('previous_close', 0),
                'change': quote_data.get('change', 0),
                'percent_change': quote_data.get('percent_change', 0),
                'company_name': quote_data.get('name', symbol),
                'currency': quote_data.get('currency', 'SAR' if is_saudi_market else 'USD'),
                'exchange': quote_data.get('exchange', 'XSAU' if is_saudi_market else ''),
                'data_source': 'twelvedata',
                'is_saudi_market': is_saudi_market,
                'timestamp': datetime.now().isoformat(),
                'is_market_open': quote_data.get('is_market_open', False)
            }

            # Add 52-week range if available
            fifty_two_week = quote_data.get('fifty_two_week', {})
            if fifty_two_week:
                result['52_week_high'] = float(fifty_two_week.get('high', 0)) if fifty_two_week.get('high') else 0
                result['52_week_low'] = float(fifty_two_week.get('low', 0)) if fifty_two_week.get('low') else 0

            # Process historical data for technical indicators
            if historical_data.get('success') and historical_data.get('values'):
                values = historical_data['values']
                if values and len(values) > 0:
                    # Convert to pandas DataFrame for easier analysis
                    df = pd.DataFrame(values)

                    # Ensure numeric types
                    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    # Calculate basic technical indicators
                    if 'close' in df.columns and len(df) >= 20:
                        # Simple moving averages
                        df['sma_20'] = df['close'].rolling(window=20).mean()
                        df['sma_50'] = df['close'].rolling(window=50).mean() if len(df) >= 50 else None

                        # Current price vs moving averages
                        latest_close = df['close'].iloc[0] if len(df) > 0 else result['current_price']
                        latest_sma_20 = df['sma_20'].iloc[0] if len(df) > 0 and not pd.isna(df['sma_20'].iloc[0]) else None

                        result['sma_20'] = float(latest_sma_20) if latest_sma_20 is not None else None

                        if latest_sma_20:
                            result['price_vs_sma_20'] = ((latest_close - latest_sma_20) / latest_sma_20) * 100

                        # Calculate price momentum
                        if len(df) >= 5:
                            price_5d_ago = df['close'].iloc[min(4, len(df)-1)]
                            result['momentum_5d'] = ((latest_close - price_5d_ago) / price_5d_ago) * 100

                        if len(df) >= 22:
                            price_1m_ago = df['close'].iloc[min(21, len(df)-1)]
                            result['momentum_1m'] = ((latest_close - price_1m_ago) / price_1m_ago) * 100

                        # Volume analysis
                        if 'volume' in df.columns:
                            avg_volume = df['volume'].rolling(window=20).mean()
                            latest_avg_volume = avg_volume.iloc[0] if len(avg_volume) > 0 and not pd.isna(avg_volume.iloc[0]) else None
                            if latest_avg_volume and result['volume']:
                                result['volume_vs_avg'] = (result['volume'] / latest_avg_volume - 1) * 100

            # Set success flag
            result['success'] = True

            logger.info(f"Successfully analyzed {validated_symbol} using TwelveData - Price: {result['current_price']} {result['currency']}")
            return result

        except Exception as e:
            logger.error(f"TwelveData analysis failed for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False,
                'data_source': 'twelvedata'
            }

    def health_check(self) -> Dict[str, Any]:
        """Check if TwelveData API is accessible with both US and Saudi market tests"""
        try:
            # Test US market
            us_test = self.get_real_time_price('AAPL')

            # Test Saudi market
            saudi_test = self.get_real_time_price('4261')  # Theeb Rent A Car (trial symbol)

            if us_test.get('success') or saudi_test.get('success'):
                return {
                    'status': 'healthy',
                    'message': 'TwelveData API is accessible',
                    'us_market_test': us_test.get('success', False),
                    'saudi_market_test': saudi_test.get('success', False),
                    'test_us_price': us_test.get('price') if us_test.get('success') else None,
                    'test_saudi_price': saudi_test.get('price') if saudi_test.get('success') else None,
                    'api_key_configured': bool(self.api_key),
                    'auth_method': 'header'
                }
            else:
                return {
                    'status': 'error',
                    'message': f"Both tests failed - US: {us_test.get('error')}, Saudi: {saudi_test.get('error')}",
                    'api_key_configured': bool(self.api_key),
                    'auth_method': 'header'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'api_key_configured': bool(self.api_key),
                'auth_method': 'header'
            }

    def get_saudi_market_symbols(self, limit: int = 100) -> Dict[str, Any]:
        """Get available Saudi market symbols from TwelveData"""
        try:
            # This would use the /stocks endpoint with exchange filter
            params = {
                'exchange': 'XSAU',
                'country': 'Saudi Arabia',
                'outputsize': min(limit, 1000)
            }

            data = self._make_request('stocks', params)

            if isinstance(data, dict) and 'data' in data:
                symbols = data['data']
                return {
                    'symbols': symbols,
                    'count': len(symbols),
                    'exchange': 'XSAU',
                    'success': True
                }
            elif isinstance(data, list):
                return {
                    'symbols': data,
                    'count': len(data),
                    'exchange': 'XSAU',
                    'success': True
                }
            else:
                raise Exception(f"Unexpected response format: {type(data)}")

        except Exception as e:
            logger.error(f"Error getting Saudi market symbols: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }