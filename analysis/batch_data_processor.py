"""
Batch Data Processor for TwelveData Pro 610 Plan
Maximizes API usage by processing multiple stocks efficiently
"""

import asyncio
import aiohttp
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import os

logger = logging.getLogger(__name__)

class BatchTwelveDataProcessor:
    """
    Optimized batch processor for TwelveData Pro 610 plan
    - 610 requests/minute = ~10 requests/second
    - Batch processing for multiple symbols
    - WebSocket connections for real-time data
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
        self.base_url = "https://api.twelvedata.com"

        # Rate limiting optimized for Pro 610
        self.max_requests_per_minute = 600  # Leave 10 buffer
        self.max_requests_per_second = 10
        self.request_timestamps = []

        # Batch processing configuration
        self.max_batch_size = 50  # Process 50 stocks at once
        self.concurrent_batches = 3  # Run 3 batches concurrently

        # Session configuration
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Tadaro Investment Bot Pro',
                'Accept': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        current_time = time.time()

        # Clean old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 60
        ]

        # Check minute-based limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            oldest_request = min(self.request_timestamps)
            wait_time = 60 - (current_time - oldest_request) + 0.1
            return wait_time

        return 0

    async def _make_batch_request(self, symbols: List[str], endpoint: str,
                                extra_params: Dict = None) -> Dict[str, Any]:
        """
        Make batch request for multiple symbols
        TwelveData supports comma-separated symbols for batch requests
        """
        wait_time = self._check_rate_limit()
        if wait_time > 0:
            logger.info(f"Rate limit protection: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        # Prepare batch request
        symbols_str = ','.join(symbols[:8])  # TwelveData batch limit is 8 symbols
        params = {
            'symbol': symbols_str,
            'apikey': self.api_key,
            'format': 'json'
        }

        if extra_params:
            params.update(extra_params)

        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.get(url, params=params) as response:
                self.request_timestamps.append(time.time())

                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Batch request success: {len(symbols)} symbols")
                    return data
                else:
                    logger.error(f"Batch request failed: HTTP {response.status}")
                    return {'error': f'HTTP {response.status}'}

        except Exception as e:
            logger.error(f"Batch request error: {str(e)}")
            return {'error': str(e)}

    async def get_real_time_quotes_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time quotes for multiple symbols"""
        results = {}

        # Process in batches of 8 (TwelveData's batch limit)
        for i in range(0, len(symbols), 8):
            batch_symbols = symbols[i:i+8]
            batch_data = await self._make_batch_request(
                batch_symbols, 'quote'
            )

            if isinstance(batch_data, dict) and 'error' not in batch_data:
                # Handle single symbol response
                if 'symbol' in batch_data:
                    results[batch_data['symbol']] = batch_data
                # Handle multiple symbol response
                elif isinstance(batch_data, dict):
                    for symbol, data in batch_data.items():
                        if isinstance(data, dict) and 'symbol' in data:
                            results[symbol] = data

            # Small delay between batches
            await asyncio.sleep(0.1)

        return results

    async def get_time_series_batch(self, symbols: List[str],
                                  interval: str = '1day',
                                  outputsize: int = 30) -> Dict[str, Any]:
        """Get historical time series for multiple symbols"""
        results = {}
        extra_params = {
            'interval': interval,
            'outputsize': outputsize
        }

        # Process in smaller batches for time series (more data intensive)
        for i in range(0, len(symbols), 5):
            batch_symbols = symbols[i:i+5]
            batch_data = await self._make_batch_request(
                batch_symbols, 'time_series', extra_params
            )

            if isinstance(batch_data, dict) and 'error' not in batch_data:
                # Handle batch response structure
                if 'meta' in batch_data and 'values' in batch_data:
                    symbol = batch_data['meta'].get('symbol')
                    if symbol:
                        results[symbol] = batch_data
                else:
                    # Multiple symbols response
                    for symbol, data in batch_data.items():
                        if isinstance(data, dict) and ('meta' in data or 'values' in data):
                            results[symbol] = data

            # Longer delay for time series requests
            await asyncio.sleep(0.2)

        return results

    async def process_portfolio_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Process a complete portfolio analysis in batches
        Maximizes Pro 610 subscription efficiency
        """
        logger.info(f"Processing portfolio batch: {len(symbols)} symbols")
        start_time = time.time()

        # Concurrent processing of different data types
        tasks = []

        # Real-time quotes (highest priority)
        tasks.append(asyncio.create_task(
            self.get_real_time_quotes_batch(symbols)
        ))

        # Historical data (1 month)
        tasks.append(asyncio.create_task(
            self.get_time_series_batch(symbols, '1day', 30)
        ))

        # Wait for all tasks to complete
        quote_results, timeseries_results = await asyncio.gather(*tasks)

        # Combine results
        portfolio_data = {
            'quotes': quote_results,
            'historical': timeseries_results,
            'processed_symbols': len(symbols),
            'processing_time': time.time() - start_time,
            'api_requests_used': len(self.request_timestamps[-100:])  # Last 100 requests
        }

        logger.info(f"Portfolio batch completed: {len(symbols)} symbols in {portfolio_data['processing_time']:.2f} seconds")
        return portfolio_data

    async def get_market_overview_batch(self) -> Dict[str, Any]:
        """
        Get comprehensive market overview using batch processing
        Covers major indices, sectors, and top stocks
        """

        # Define major market symbols
        major_indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
        sector_etfs = ['XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP', 'XLB', 'XLU', 'XLRE']
        top_stocks = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'JNJ', 'V']

        all_symbols = major_indices + sector_etfs + top_stocks

        return await self.process_portfolio_batch(all_symbols)

    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        current_time = time.time()

        # Clean old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 60
        ]

        return {
            'requests_last_minute': len(self.request_timestamps),
            'requests_remaining_this_minute': self.max_requests_per_minute - len(self.request_timestamps),
            'utilization_percentage': (len(self.request_timestamps) / self.max_requests_per_minute) * 100,
            'plan_limit': '610 requests/minute',
            'plan_type': 'Pro 610',
            'timestamp': datetime.now().isoformat()
        }

# Example usage function
async def example_usage():
    """Example of how to use the batch processor"""

    # Portfolio symbols
    portfolio_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM',
        'JNJ', 'V', 'WMT', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE',
        'CRM', 'NFLX', 'XOM', 'CVX', 'PFE', 'ABT', 'TMO', 'COST', 'AVGO',
        'LLY', 'ORCL', 'ACN', 'MCD', 'DHR', 'VZ', 'BMY', 'NEE', 'PM'
    ]

    async with BatchTwelveDataProcessor() as processor:
        # Get comprehensive portfolio data
        results = await processor.process_portfolio_batch(portfolio_symbols)

        # Print usage stats
        usage_stats = processor.get_api_usage_stats()
        print(f"API Usage: {usage_stats['requests_last_minute']}/610 requests used")
        print(f"Utilization: {usage_stats['utilization_percentage']:.1f}%")

        return results

if __name__ == "__main__":
    # Run example
    results = asyncio.run(example_usage())
    print(f"Processed {results['processed_symbols']} symbols in {results['processing_time']:.2f} seconds")