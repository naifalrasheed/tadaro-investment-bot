import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
import requests
from bs4 import BeautifulSoup
import time
import random
from functools import lru_cache, wraps
from datetime import datetime, timedelta

# Custom retry decorator with exponential backoff
def retry_with_backoff(retries=5, backoff_in_seconds=1):
    """
    Retry decorator with exponential backoff for Yahoo Finance API calls
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    sleep_time = backoff_in_seconds * (2 ** x) + random.uniform(0, 1)
                    logging.warning(f"Retrying {func.__name__} in {sleep_time:.2f} seconds due to: {str(e)}")
                    time.sleep(sleep_time)
                    x += 1
        return wrapper
    return decorator

class DataFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Cache dictionaries with expiration timestamps
        self._sector_cache = {}
        self._stock_info_cache = {}
        self._rotc_cache = {}
        self._growth_metrics_cache = {}
        self._sp500_cache = None
        self._sp500_cache_expiry = None
        # Cache expiration times (in seconds)
        self.SECTOR_CACHE_EXPIRY = 24 * 60 * 60  # 24 hours
        self.STOCK_INFO_CACHE_EXPIRY = 4 * 60 * 60  # 4 hours
        self.ROTC_CACHE_EXPIRY = 24 * 60 * 60  # 24 hours
        self.GROWTH_CACHE_EXPIRY = 24 * 60 * 60  # 24 hours
        self.SP500_CACHE_EXPIRY = 7 * 24 * 60 * 60  # 7 days
        # Settings for API access
        self.request_delay = 1.0  # Delay between Yahoo Finance API calls
        self.last_request_time = 0

    def _throttle_api_call(self):
        """Ensures we don't make too many requests too quickly"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def get_macro_data(self, metric: str) -> float:
        """Fetch macroeconomic indicators like inflation or interest rates."""
        try:
            # Dummy logic; replace with actual API integration
            macro_data = {
                'inflation': 0.03,  # Example: Annualized inflation rate (3%)
                'interest_rate': 0.04  # Example: Annualized interest rate (4%)
            }
            return macro_data.get(metric, 0.0)
        except Exception as e:
            self.logger.error(f"Error fetching macro data for {metric}: {str(e)}")
            return 0.0

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def get_sp500_sector_stocks(self) -> Dict[str, List[str]]:
        """Get S&P 500 stocks grouped by sector with caching."""
        try:
            current_time = time.time()
            
            # Check if we have a valid cached response
            if self._sp500_cache and self._sp500_cache_expiry and current_time < self._sp500_cache_expiry:
                self.logger.debug("Using cached S&P 500 data")
                return self._sp500_cache
            
            self.logger.info("Fetching S&P 500 stocks from Wikipedia...")
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'wikitable'})
            
            sector_stocks = {}
            for row in table.find_all('tr')[1:]:  # Skip header row
                columns = row.find_all('td')
                if len(columns) >= 4:
                    symbol = columns[0].text.strip()
                    sector = columns[3].text.strip()
                    
                    if sector not in sector_stocks:
                        sector_stocks[sector] = []
                    sector_stocks[sector].append(symbol)
            
            # Store in cache with expiry time
            self._sp500_cache = sector_stocks
            self._sp500_cache_expiry = current_time + self.SP500_CACHE_EXPIRY
            
            self.logger.info(f"Found stocks in {len(sector_stocks)} sectors")
            return sector_stocks
            
        except Exception as e:
            self.logger.error(f"Error fetching S&P 500 stocks: {str(e)}")
            # Return cached data if available, even if expired
            if self._sp500_cache:
                self.logger.warning("Using expired S&P 500 data due to fetch error")
                return self._sp500_cache
            return {}

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock information with caching."""
        try:
            # Handle the case where symbol is a dictionary
            if isinstance(symbol, dict):
                self.logger.warning(f"Symbol parameter is a dictionary, extracting symbol from dict")
                if 'symbol' in symbol:
                    symbol = symbol['symbol']
                else:
                    self.logger.error(f"Dictionary does not contain 'symbol' key: {symbol}")
                    return None
            current_time = time.time()
            
            # Check for cached data
            if symbol in self._stock_info_cache:
                cache_time, cache_data = self._stock_info_cache[symbol]
                if current_time < cache_time + self.STOCK_INFO_CACHE_EXPIRY:
                    self.logger.debug(f"Using cached info for {symbol}")
                    return cache_data
            
            self.logger.info(f"Fetching info for {symbol}...")
            # Throttle API calls
            self._throttle_api_call()
            
            stock = yf.Ticker(symbol)
            info = stock.info
            
            result = {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', 0),
                'volume': info.get('volume', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0)
            }
            
            # Cache the result
            self._stock_info_cache[symbol] = (current_time, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching info for {symbol}: {str(e)}")
            # Return cached data if available, even if expired
            if symbol in self._stock_info_cache:
                self.logger.warning(f"Using expired cache for {symbol} due to fetch error")
                return self._stock_info_cache[symbol][1]
            return None

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def calculate_rotc(self, symbol) -> Dict:
        """Calculate return on tangible capital with caching."""
        try:
            current_time = time.time()
            
            # Handle the case where symbol is a dictionary (e.g., mock data)
            if isinstance(symbol, dict):
                self.logger.warning(f"Symbol parameter is a dictionary, extracting symbol from dict")
                if 'symbol' in symbol:
                    symbol = symbol['symbol']
                else:
                    self.logger.error(f"Dictionary does not contain 'symbol' key: {symbol}")
                    return {'rotc': None, 'quarters': []}
            
            # Check for cached data
            if symbol in self._rotc_cache:
                cache_time, cache_data = self._rotc_cache[symbol]
                if current_time < cache_time + self.ROTC_CACHE_EXPIRY:
                    self.logger.debug(f"Using cached ROTC for {symbol}")
                    return cache_data
            
            self.logger.info(f"Calculating ROTC for {symbol}...")
            # Throttle API calls
            self._throttle_api_call()
            
            stock = yf.Ticker(symbol)
            income_stmt = stock.quarterly_income_stmt
            balance_sheet = stock.quarterly_balance_sheet
        
            if income_stmt.empty or balance_sheet.empty:
                self.logger.warning(f"No financial data available for {symbol}")
                result = {'rotc': None, 'quarters': []}
                self._rotc_cache[symbol] = (current_time, result)
                return result

            results = []
            for quarter_end in income_stmt.columns[:4]:  # Last 4 quarters
                try:
                    if 'Operating Income' not in income_stmt.index:
                        self.logger.warning(f"Skipping {symbol} due to missing Operating Income in {quarter_end}")
                        continue  # Skip to the next quarter if data is missing

                    operating_income = income_stmt.loc['Operating Income', quarter_end]
                    nopat = operating_income * (1 - 0.21)  # Assumed tax rate
                    
                    if 'Total Assets' not in balance_sheet.index or 'Total Liabilities Net Minority Interest' not in balance_sheet.index:
                        self.logger.warning(f"Missing balance sheet data for {symbol} in {quarter_end}")
                        continue

                    total_assets = balance_sheet.loc['Total Assets', quarter_end]
                    intangible_assets = balance_sheet.loc['Intangible Assets', quarter_end] if 'Intangible Assets' in balance_sheet.index else 0
                    total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest', quarter_end]

                    tangible_capital = total_assets - intangible_assets - total_liabilities
                    
                    if tangible_capital > 0:
                        rotc = (nopat / tangible_capital) * 100
                    else:
                        rotc = None

                    # Calculate quarter number based on the month
                    quarter_number = (quarter_end.month - 1) // 3 + 1

                    results.append({
                        'quarter': f"{quarter_end.year}-Q{quarter_number}",
                        'rotc': rotc,
                        'nopat': nopat,
                        'tangible_capital': tangible_capital
                    })

                except Exception as e:
                    self.logger.error(f"Error calculating ROTC for {symbol} in quarter {quarter_end}: {e}")
                    continue

            valid_rotcs = [r['rotc'] for r in results if r['rotc'] is not None]
            avg_rotc = sum(valid_rotcs) / len(valid_rotcs) if valid_rotcs else None

            result = {
                'rotc': avg_rotc,
                'quarters': results
            }
            
            # Cache the result
            self._rotc_cache[symbol] = (current_time, result)
            return result

        except Exception as e:
            self.logger.error(f"Error calculating ROTC for {symbol}: {e}")
            # Return cached data if available, even if expired
            if symbol in self._rotc_cache:
                self.logger.warning(f"Using expired ROTC cache for {symbol} due to error")
                return self._rotc_cache[symbol][1]
            return {'rotc': None, 'quarters': []}

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def get_growth_metrics(self, symbol: str) -> Dict:
        """Get growth metrics with caching."""
        try:
            # Handle the case where symbol is a dictionary
            if isinstance(symbol, dict):
                self.logger.warning(f"Symbol parameter is a dictionary, extracting symbol from dict")
                if 'symbol' in symbol:
                    symbol = symbol['symbol']
                else:
                    self.logger.error(f"Dictionary does not contain 'symbol' key: {symbol}")
                    return {'revenue_growth': None, 'operating_cash_flow': None}
            current_time = time.time()
            
            # Check for cached data
            if symbol in self._growth_metrics_cache:
                cache_time, cache_data = self._growth_metrics_cache[symbol]
                if current_time < cache_time + self.GROWTH_CACHE_EXPIRY:
                    self.logger.debug(f"Using cached growth metrics for {symbol}")
                    return cache_data
            
            self.logger.info(f"Calculating growth metrics for {symbol}...")
            # Throttle API calls
            self._throttle_api_call()
            
            stock = yf.Ticker(symbol)
            income_stmt = stock.quarterly_income_stmt
            cash_flow = stock.quarterly_cash_flow
            
            if income_stmt.empty or cash_flow.empty:
                result = {'revenue_growth': None, 'operating_cash_flow': None}
                self._growth_metrics_cache[symbol] = (current_time, result)
                return result

            revenues = income_stmt.loc['Total Revenue']
            revenue_growth = []
            
            for i in range(1, len(revenues)):
                prev_rev = revenues.iloc[i-1]
                curr_rev = revenues.iloc[i]
                if prev_rev > 0:
                    growth = ((curr_rev - prev_rev) / prev_rev) * 100
                    revenue_growth.append(growth)

            operating_cash = cash_flow.loc['Operating Cash Flow']
            avg_operating_cash = operating_cash.mean()

            result = {
                'revenue_growth': np.mean(revenue_growth) if revenue_growth else None,
                'operating_cash_flow': avg_operating_cash
            }
            
            # Cache the result
            self._growth_metrics_cache[symbol] = (current_time, result)
            return result

        except Exception as e:
            self.logger.error(f"Error calculating growth metrics for {symbol}: {str(e)}")
            # Return cached data if available, even if expired
            if symbol in self._growth_metrics_cache:
                self.logger.warning(f"Using expired growth metrics cache for {symbol} due to error")
                return self._growth_metrics_cache[symbol][1]
            return {'revenue_growth': None, 'operating_cash_flow': None}

    def get_sector_stocks(self, sector: str) -> List[Dict]:
        """Get stocks in a specific sector with caching."""
        try:
            current_time = time.time()
            
            # Check if we have valid cached sector data
            if sector in self._sector_cache:
                cache_time, cache_data = self._sector_cache[sector]
                if current_time < cache_time + self.SECTOR_CACHE_EXPIRY:
                    self.logger.debug(f"Using cached data for {sector} sector")
                    return cache_data

            self.logger.info(f"Fetching stocks for {sector} sector...")
            sector_data = self.get_sp500_sector_stocks()
            
            if sector not in sector_data:
                self.logger.warning(f"Sector {sector} not found in S&P 500")
                return []
            
            stocks_info = []
            for symbol in sector_data[sector]:
                # Add a random delay between API calls to prevent rate limiting
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
                
                info = self.get_stock_info(symbol)
                if info:
                    stocks_info.append(info)
            
            stocks_info.sort(key=lambda x: x['market_cap'], reverse=True)
            
            # Cache the result
            self._sector_cache[sector] = (current_time, stocks_info)
            
            self.logger.info(f"Found {len(stocks_info)} stocks in {sector} sector")
            return stocks_info
            
        except Exception as e:
            self.logger.error(f"Error getting sector stocks: {str(e)}")
            # Return cached data if available, even if expired
            if sector in self._sector_cache:
                self.logger.warning(f"Using expired sector cache for {sector} due to error")
                return self._sector_cache[sector][1]
            return []
        
    # Helper method to clear all caches
    def clear_caches(self):
        """Clear all caches for testing or when fresh data is required."""
        self._sector_cache = {}
        self._stock_info_cache = {}
        self._rotc_cache = {}
        self._growth_metrics_cache = {}
        self._sp500_cache = None
        self._sp500_cache_expiry = None
        self.logger.info("All caches cleared")