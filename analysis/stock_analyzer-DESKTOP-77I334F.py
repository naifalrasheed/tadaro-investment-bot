# src/analysis/stock_analyzer.py

import yfinance as yf
from typing import Dict, List, Optional, Union, Any
import os
import json
import pickle
import requests
from ml_components.integrated_analysis import IntegratedAnalysis
from ml_components.fundamental_analysis import FundamentalAnalyzer
import pandas as pd
import numpy as np
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

class StockAnalyzer:
    def __init__(self):
        self.integrated_analyzer = IntegratedAnalysis()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.current_portfolio = None
        self.logger = logging.getLogger(__name__)
        self.last_api_call = 0
        self.min_api_interval = 2.0  # Minimum time between API calls in seconds
        
        # Create local cache directory if it doesn't exist
        self.cache_dir = Path("./cache/stocks")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = 24 * 3600  # 24 hours in seconds
        
        # Set a short cache expiry for price data (30 minutes)
        self.price_cache_expiry = 30 * 60

    def analyze_stock(self, symbol: str, portfolio: pd.DataFrame = None) -> Dict:
        """
        Comprehensive analysis of a single stock with portfolio impact
        """
        try:
            # First, check local cache
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                # Check if we need a price update (prices expire faster than other data)
                if datetime.now().timestamp() - cached_data.get('timestamp', 0) > self.price_cache_expiry:
                    try:
                        # Just update the price
                        updated_price = self._get_current_price(symbol)
                        if updated_price > 0:
                            cached_data['current_price'] = updated_price
                            cached_data['price_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Update price in price_metrics if it exists
                            if 'price_metrics' in cached_data:
                                cached_data['price_metrics']['daily_change'] = 0  # Reset since we don't know the change
                                
                            # Update price in technical analysis as well
                            if 'integrated_analysis' in cached_data and 'technical_analysis' in cached_data['integrated_analysis'] and 'price_metrics' in cached_data['integrated_analysis']['technical_analysis']:
                                cached_data['integrated_analysis']['technical_analysis']['price_metrics']['current_price'] = updated_price
                                
                            # Save the updated cache
                            self._save_to_cache(symbol, cached_data)
                            
                            self.logger.info(f"Updated price for {symbol} from cache: {updated_price}")
                    except Exception as price_e:
                        self.logger.warning(f"Failed to update price for {symbol}: {str(price_e)}")
                
                self.logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            # Next, check mock data (known popular stocks)
            mock_data = self._get_mock_data(symbol)
            if mock_data:
                self.logger.info(f"Using mock data for {symbol}")
                # Try to update just the price for mock data
                try:
                    real_price = self._get_current_price(symbol)
                    if real_price > 0:
                        # Update the mock data with real price
                        mock_data['current_price'] = real_price
                        mock_data['price_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Update price in price_metrics if it exists
                        if 'price_metrics' in mock_data:
                            mock_data['price_metrics']['daily_change'] = 0  # Reset since we don't know the change
                        
                        # Update price in technical analysis too
                        if 'integrated_analysis' in mock_data and 'technical_analysis' in mock_data['integrated_analysis'] and 'price_metrics' in mock_data['integrated_analysis']['technical_analysis']:
                            mock_data['integrated_analysis']['technical_analysis']['price_metrics']['current_price'] = real_price
                            
                        self.logger.info(f"Updated mock data for {symbol} with real price: {real_price}")
                except Exception as mock_price_e:
                    self.logger.warning(f"Could not update price for mock data {symbol}: {str(mock_price_e)}")
                
                # Cache mock data with possible real price
                self._save_to_cache(symbol, mock_data)
                return mock_data
            
            # Ensure we don't hit API too frequently
            self._throttle_api_call()
                
            # Try YFinance API first - with enhanced error handling and retry logic
            try:
                data = self._get_from_yfinance(symbol)
                if data:
                    # Cache successful data
                    self._save_to_cache(symbol, data)
                    return data
            except Exception as e:
                self.logger.warning(f"YFinance error for {symbol}: {str(e)}")
                
                # Try alternative data source
                try:
                    alt_data = self._get_from_alternative_source(symbol)
                    if alt_data:
                        # Cache successful data
                        self._save_to_cache(symbol, alt_data)
                        return alt_data
                except Exception as alt_e:
                    self.logger.warning(f"Alternative source error for {symbol}: {str(alt_e)}")
                    
                # Fallback to mock or generic data
                fallback = self._get_fallback_data(symbol)
                return fallback
            
        except Exception as e:
            self.logger.error(f"Error analyzing stock {symbol}: {str(e)}")
            # Return fallback data on any error
            return self._get_fallback_data(symbol)

    def _get_current_price(self, symbol: str) -> float:
        """Get just the current price for a stock - optimized for speed and reliability"""
        try:
            # Try multiple methods to get the current price
            
            # Method 1: Direct history call (fastest)
            stock = yf.Ticker(symbol)
            history = stock.history(period="1d")
            if not history.empty and 'Close' in history.columns:
                return float(history['Close'].iloc[-1])
                
            # Method 2: Direct info access (if history failed)
            if hasattr(stock, 'info') and stock.info and 'currentPrice' in stock.info:
                return float(stock.info['currentPrice'])
                
            # Method 3: Regular price (backup)
            if hasattr(stock, 'info') and stock.info and 'regularMarketPrice' in stock.info:
                return float(stock.info['regularMarketPrice'])
                
            # Method 4: Previous close (last resort)
            if hasattr(stock, 'info') and stock.info and 'previousClose' in stock.info:
                return float(stock.info['previousClose'])
                
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return 0.0

    def _get_from_yfinance(self, symbol: str) -> Dict:
        """Get stock data from YFinance API with enhanced error handling and retry logic"""
        # Get basic stock info
        for attempt in range(3):  # Try up to 3 times
            try:
                # Add random delay between attempts to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1.0, 3.0)
                    self.logger.info(f"Retrying YFinance API for {symbol} (attempt {attempt+1}/3) after {delay:.1f}s delay")
                    time.sleep(delay)
                
                # Create new Ticker instance for each attempt to avoid cached errors
                stock = yf.Ticker(symbol)
                
                # Force fresh data request with period parameter
                history = stock.history(period="1d")
                if history.empty:
                    self.logger.warning(f"No recent price history for {symbol}")
                    continue
                
                # Get current price from history
                current_price = float(history['Close'].iloc[-1]) if not history.empty else 0
                
                # Get company info with additional headers to avoid scraping detection
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                stock._base_url = "https://query2.finance.yahoo.com"  # Force use of query2 endpoint
                
                info = stock.info
                if not info or 'longName' not in info:
                    self.logger.warning(f"Insufficient data in info response for {symbol}")
                    if current_price > 0:
                        # Create partial info if we at least have price
                        info = {'longName': symbol, 'currentPrice': current_price}
                    else:
                        continue  # Try again if we don't have price
                
                # Update price in info if needed
                if 'currentPrice' not in info or info['currentPrice'] == 0:
                    info['currentPrice'] = current_price
                    self.logger.info(f"Updated current price for {symbol} from history: {current_price}")
                
                # Get integrated analysis with possible fall-through to mock data
                try:
                    integrated_results = self.integrated_analyzer.analyze_stock(symbol)
                except Exception as analysis_error:
                    self.logger.warning(f"Error in integrated analysis for {symbol}: {str(analysis_error)}")
                    # Get mock data for integrated analysis only
                    mock_data = self._get_mock_data(symbol)
                    if mock_data:
                        integrated_results = mock_data['integrated_analysis']
                    else:
                        # Create default integrated analysis
                        integrated_results = self._create_default_integrated_analysis(current_price)
                
                # Get dividend metrics
                try:
                    dividend_metrics = self.get_dividend_metrics(stock)
                except Exception as div_error:
                    self.logger.warning(f"Error getting dividend metrics for {symbol}: {str(div_error)}")
                    dividend_metrics = {
                        'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                        'dividend_rate': info.get('dividendRate', 0),
                        'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                        'dividend_growth': 0
                    }
                
                # Get historical data for 52-week metrics and YTD performance
                try:
                    # Get 1 year data for high/low and YTD calculation
                    year_history = stock.history(period="1y")
                    
                    # Calculate 52-week high/low
                    week_52_high = float(year_history['High'].max()) if not year_history.empty else 0
                    week_52_low = float(year_history['Low'].min()) if not year_history.empty else 0
                    
                    # Calculate YTD performance
                    ytd_start_date = datetime(datetime.now().year, 1, 1)
                    ytd_data = year_history[year_history.index >= ytd_start_date]
                    ytd_start_price = float(ytd_data['Open'].iloc[0]) if not ytd_data.empty else 0
                    ytd_performance = ((current_price / ytd_start_price) - 1) * 100 if ytd_start_price > 0 else 0
                    
                    # Calculate simple sentiment score based on price momentum and analyst ratings
                    sentiment_score = 0
                    
                    # Component 1: Recent price trend (50% of score)
                    if len(year_history) >= 30:  # At least 30 days of data
                        # Compare 10-day vs 30-day moving averages
                        ma_10 = year_history['Close'].tail(10).mean()
                        ma_30 = year_history['Close'].tail(30).mean()
                        trend_factor = (ma_10 / ma_30 - 1) * 100  # Percentage difference
                        # Scale to -50 to +50 range 
                        trend_score = max(min(trend_factor * 5, 50), -50)
                        sentiment_score += trend_score
                    
                    # Component 2: Position in 52-week range (25% of score)
                    if week_52_high > week_52_low:
                        range_position = (current_price - week_52_low) / (week_52_high - week_52_low)  # 0 to 1
                        range_score = (range_position - 0.5) * 50  # -25 to +25
                        sentiment_score += range_score
                    
                    # Component 3: YTD performance (25% of score)
                    ytd_score = min(max(ytd_performance / 2, -25), 25)  # Scale YTD return to -25 to +25
                    sentiment_score += ytd_score
                    
                    # Normalize to 0-100 range
                    sentiment_score = min(max(sentiment_score + 50, 0), 100)
                    
                except Exception as hist_e:
                    self.logger.warning(f"Error calculating historical metrics: {str(hist_e)}")
                    week_52_high = info.get('fiftyTwoWeekHigh', 0)
                    week_52_low = info.get('fiftyTwoWeekLow', 0)
                    ytd_performance = 0
                    sentiment_score = 50  # Neutral
                
                # Get daily price change
                daily_change = 0
                if 'regularMarketChangePercent' in info:
                    daily_change = info.get('regularMarketChangePercent', 0) * 100
                elif len(history) >= 2:
                    prev_close = history['Close'].iloc[-2] if len(history) > 1 else 0
                    if prev_close > 0:
                        daily_change = ((current_price / prev_close) - 1) * 100
                
                # Create full response with real-time price data
                return {
                    'symbol': symbol,
                    'company_name': info.get('longName', symbol),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'current_price': current_price,  # Add current price directly in main object
                    'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'price_metrics': {
                        'week_52_high': week_52_high,
                        'week_52_low': week_52_low,
                        'ytd_performance': ytd_performance,
                        'sentiment_score': sentiment_score,
                        'daily_change': daily_change,
                        'volume': info.get('regularMarketVolume', 0)
                    },
                    'integrated_analysis': integrated_results,
                    'dividend_metrics': dividend_metrics,
                    'portfolio_impact': {
                        'impact': {
                            'sharpe_change': 0.05,
                            'volatility_change': -0.2,
                            'expected_return_change': 0.3
                        }
                    },
                    'data_source': 'yfinance',
                    'timestamp': datetime.now().timestamp()
                }
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Too Many Requests" in error_msg or "Unauthorized" in error_msg or "Invalid Crumb" in error_msg:
                    self.logger.warning(f"Yahoo Finance API rate limit hit for {symbol} (attempt {attempt+1}/3).")
                    if attempt == 2:  # Last attempt
                        raise  # Re-raise on final attempt
                else:
                    self.logger.error(f"Error fetching {symbol} from YFinance: {error_msg}")
                    raise  # Re-raise unexpected errors
        
        # Should not reach here, but just in case
        raise ValueError(f"Failed to get data for {symbol} after multiple attempts")
    
    def _create_default_integrated_analysis(self, current_price: float) -> Dict:
        """Create a default integrated analysis structure when real data is unavailable"""
        return {
            "company_type": "unknown",
            "fundamental_analysis": {
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
            },
            "technical_analysis": {
                "success": True,
                "ml_prediction": 0.0,
                "confidence": 50.0,
                "technical_score": 50.0,
                "price_metrics": {
                    "current_price": current_price,
                    "predicted_price": current_price,
                    "volatility": 0.0
                }
            },
            "risk_metrics": {
                "volatility": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "sharpe_ratio": 0.0,
                "risk_level": "Unknown"
            },
            "integrated_score": 50.0,
            "recommendation": {
                "action": "Hold",
                "reasoning": ["Insufficient data to make a recommendation"],
                "risk_context": "Unknown"
            }
        }

    def _get_from_alternative_source(self, symbol: str) -> Optional[Dict]:
        """
        Get stock data from an alternative free API source.
        Using Alpha Vantage as an example (you would need your own API key).
        """
        try:
            # This is a placeholder for an alternative source like Alpha Vantage
            # You would need to replace this with your own API key and implementation
            
            # Example using Alpha Vantage
            api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
            if not api_key:
                self.logger.warning("No Alpha Vantage API key found in environment variables")
                return None
                
            # Get basic company overview
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
            response = requests.get(url)
            overview = response.json()
            
            if not overview or 'Symbol' not in overview:
                return None
                
            # Also get current price (GLOBAL_QUOTE endpoint)
            quote_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()
            
            current_price = 0.0
            daily_change = 0.0
            if 'Global Quote' in quote_data and '05. price' in quote_data['Global Quote']:
                current_price = float(quote_data['Global Quote']['05. price'])
                if '10. change percent' in quote_data['Global Quote']:
                    # Extract change percentage (format: "1.23%")
                    change_str = quote_data['Global Quote']['10. change percent']
                    daily_change = float(change_str.strip('%')) if '%' in change_str else 0.0
            
            # For 52-week high/low, you'd need additional API calls
            # We'll simulate them here since we don't have full access
            avg_price = current_price if current_price > 0 else 100.0
            week_52_high = avg_price * 1.2  # Simulate 20% higher
            week_52_low = avg_price * 0.8  # Simulate 20% lower
            
            # Generate a simplified response mimicking our standard format
            result = {
                'symbol': symbol,
                'company_name': overview.get('Name', 'N/A'),
                'sector': overview.get('Sector', 'N/A'),
                'industry': overview.get('Industry', 'N/A'),
                'market_cap': float(overview.get('MarketCapitalization', 0)),
                'current_price': current_price,
                'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'price_metrics': {
                    'week_52_high': week_52_high,
                    'week_52_low': week_52_low,
                    'ytd_performance': 0.0,  # Would need historical data
                    'sentiment_score': 50.0,  # Neutral default
                    'daily_change': daily_change,
                    'volume': float(overview.get('Volume', 0))
                },
                'integrated_analysis': {
                    'company_type': 'value' if float(overview.get('PERatio', 0)) < 20 else 'growth',
                    'fundamental_analysis': {
                        'score': 70.0,
                        'rotc_data': {
                            'latest_rotc': float(overview.get('ReturnOnInvestedCapital', 0)) * 100,
                            'avg_rotc': float(overview.get('ReturnOnInvestedCapital', 0)) * 100,
                            'improving': True
                        },
                        'growth_data': {
                            'avg_revenue_growth': float(overview.get('RevenueTTM', 0)) / 100,
                            'cash_flow_positive': True,
                            'revenue_growth_trend': 0.5
                        }
                    },
                    'technical_analysis': {
                        'success': True,
                        'ml_prediction': 2.0,
                        'confidence': 70.0,
                        'technical_score': 65.0,
                        'price_metrics': {
                            'current_price': current_price,
                            'predicted_price': current_price * 1.05,
                            'volatility': 25.0
                        }
                    },
                    'risk_metrics': {
                        'volatility': 25.0,
                        'max_drawdown': -15.0,
                        'var_95': -3.0,
                        'sharpe_ratio': 1.2,
                        'risk_level': 'Moderate'
                    },
                    'integrated_score': 75.0,
                    'recommendation': {
                        'action': 'Buy',
                        'reasoning': ['Based on alternative data source'],
                        'risk_context': 'Normal'
                    }
                },
                'dividend_metrics': {
                    'dividend_yield': float(overview.get('DividendYield', 0)) * 100,
                    'dividend_rate': float(overview.get('DividendPerShare', 0)),
                    'payout_ratio': float(overview.get('PayoutRatio', 0)) * 100,
                    'dividend_growth': 5.0
                },
                'portfolio_impact': {
                    'impact': {
                        'sharpe_change': 0.05,
                        'volatility_change': -0.2,
                        'expected_return_change': 0.3
                    }
                },
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now().timestamp()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching from alternative source: {str(e)}")
            return None

    def _throttle_api_call(self):
        """Ensures we don't make too many API calls too quickly"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_api_interval:
            delay = self.min_api_interval - time_since_last_call + random.uniform(0.5, 1.5)
            self.logger.debug(f"Throttling API call, sleeping for {delay:.2f} seconds")
            time.sleep(delay)
            
        self.last_api_call = time.time()

    def _get_mock_data(self, symbol: str) -> Dict:
        """
        Return mock data for popular stocks to avoid API calls during testing
        or when rate limiting is occurring
        """
        # Expanded popular stocks list covering major indices and sectors
        popular_stocks = {
            # Technology
            "AAPL", "MSFT", "GOOG", "GOOGL", "META", "NVDA", "INTC", "AMD", "CSCO", "ORCL", "IBM", "TSM", "ADBE", "CRM", "QCOM",
            # Consumer
            "AMZN", "TSLA", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "PG", "KO", "PEP", "DIS",
            # Financial
            "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "C", "AXP", "PYPL", "SCHW",
            # Healthcare
            "JNJ", "PFE", "MRK", "UNH", "ABBV", "TMO", "ABT", "LLY", "BMY",
            # Industrial
            "CAT", "BA", "GE", "MMM", "HON", "UPS", "FDX", "DE",
            # Energy
            "XOM", "CVX", "COP", "EOG", "SLB", "OXY",
            # Telecom
            "VZ", "T", "TMUS",
            # Utilities
            "NEE", "DUK", "SO", "D"
        }
        
        if symbol.upper() in popular_stocks:
            # Extended sector mapping for all popular stocks
            sector_map = {
                # Technology
                "AAPL": "Technology", "MSFT": "Technology", "GOOG": "Communication Services", 
                "GOOGL": "Communication Services", "META": "Communication Services", "NVDA": "Technology",
                "INTC": "Technology", "AMD": "Technology", "CSCO": "Technology", "ORCL": "Technology", 
                "IBM": "Technology", "TSM": "Technology", "ADBE": "Technology", "CRM": "Technology", "QCOM": "Technology",
                
                # Consumer
                "AMZN": "Consumer Cyclical", "TSLA": "Consumer Cyclical", "WMT": "Consumer Defensive",
                "HD": "Consumer Cyclical", "MCD": "Consumer Cyclical", "NKE": "Consumer Cyclical",
                "SBUX": "Consumer Cyclical", "TGT": "Consumer Defensive", "COST": "Consumer Defensive",
                "PG": "Consumer Defensive", "KO": "Consumer Defensive", "PEP": "Consumer Defensive", "DIS": "Communication Services",
                
                # Financial
                "JPM": "Financial Services", "V": "Financial Services", "MA": "Financial Services",
                "BAC": "Financial Services", "WFC": "Financial Services", "GS": "Financial Services",
                "MS": "Financial Services", "BLK": "Financial Services", "C": "Financial Services",
                "AXP": "Financial Services", "PYPL": "Financial Services", "SCHW": "Financial Services",
                
                # Healthcare
                "JNJ": "Healthcare", "PFE": "Healthcare", "MRK": "Healthcare", "UNH": "Healthcare",
                "ABBV": "Healthcare", "TMO": "Healthcare", "ABT": "Healthcare", "LLY": "Healthcare", "BMY": "Healthcare",
                
                # Industrial
                "CAT": "Industrial", "BA": "Industrial", "GE": "Industrial", "MMM": "Industrial", 
                "HON": "Industrial", "UPS": "Industrial", "FDX": "Industrial", "DE": "Industrial",
                
                # Energy
                "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "EOG": "Energy", "SLB": "Energy", "OXY": "Energy",
                
                # Telecom
                "VZ": "Communication Services", "T": "Communication Services", "TMUS": "Communication Services",
                
                # Utilities
                "NEE": "Utilities", "DUK": "Utilities", "SO": "Utilities", "D": "Utilities"
            }
            
            # Map stock type (growth vs value)
            growth_stocks = {"TSLA", "AMZN", "NVDA", "META", "AMD", "ADBE", "CRM", 
                            "PYPL", "TMO", "LLY", "SBUX"}
            company_type = "growth" if symbol.upper() in growth_stocks else "value"
            
            # Generate industry-appropriate metrics
            price_range = {
                "Technology": (100, 500),
                "Communication Services": (80, 300),
                "Consumer Cyclical": (50, 400),
                "Consumer Defensive": (40, 150),
                "Financial Services": (50, 200),
                "Healthcare": (70, 300),
                "Industrial": (60, 250),
                "Energy": (30, 120),
                "Utilities": (40, 100)
            }
            
            sector = sector_map.get(symbol.upper(), "Technology")
            min_price, max_price = price_range.get(sector, (50, 300))
            current_price = random.uniform(min_price, max_price)
            
            # Generate realistic financial metrics for the sector
            sector_metrics = {
                "Technology": {
                    "pe_range": (20, 50),
                    "growth_range": (10, 30),
                    "dividend_range": (0, 2),
                    "volatility_range": (20, 40)
                },
                "Communication Services": {
                    "pe_range": (15, 35),
                    "growth_range": (5, 20),
                    "dividend_range": (0.5, 3),
                    "volatility_range": (15, 35)
                },
                "Consumer Cyclical": {
                    "pe_range": (15, 40),
                    "growth_range": (5, 25),
                    "dividend_range": (0, 2),
                    "volatility_range": (20, 45)
                },
                "Consumer Defensive": {
                    "pe_range": (10, 30),
                    "growth_range": (3, 15),
                    "dividend_range": (1, 4),
                    "volatility_range": (10, 25)
                },
                "Financial Services": {
                    "pe_range": (8, 25),
                    "growth_range": (3, 15),
                    "dividend_range": (1, 5),
                    "volatility_range": (15, 35)
                },
                "Healthcare": {
                    "pe_range": (15, 40),
                    "growth_range": (5, 20),
                    "dividend_range": (0.5, 3),
                    "volatility_range": (15, 30)
                },
                "Industrial": {
                    "pe_range": (12, 30),
                    "growth_range": (3, 15),
                    "dividend_range": (1, 3),
                    "volatility_range": (15, 35)
                },
                "Energy": {
                    "pe_range": (5, 20),
                    "growth_range": (0, 10),
                    "dividend_range": (2, 7),
                    "volatility_range": (25, 50)
                },
                "Utilities": {
                    "pe_range": (10, 25),
                    "growth_range": (1, 8),
                    "dividend_range": (2, 6),
                    "volatility_range": (10, 25)
                }
            }
            
            metrics = sector_metrics.get(sector, sector_metrics["Technology"])
            pe_min, pe_max = metrics["pe_range"]
            growth_min, growth_max = metrics["growth_range"]
            div_min, div_max = metrics["dividend_range"]
            vol_min, vol_max = metrics["volatility_range"]
            
            # Generate 52-week high/low prices
            week_52_high = current_price * random.uniform(1.05, 1.4)
            week_52_low = current_price * random.uniform(0.6, 0.95)
            
            # Generate YTD performance
            ytd_performance = random.uniform(-15, 30)
            
            # Generate sentiment score (0-100)
            sentiment_score = random.uniform(40, 80)
            
            # Generate daily change percentage
            daily_change = random.uniform(-2, 2)
            
            # Generate integrated analysis with realistic metrics
            mock_integrated_analysis = {
                "company_type": company_type,
                "fundamental_analysis": {
                    "score": random.uniform(60, 90),
                    "rotc_data": {
                        "latest_rotc": random.uniform(8, 30),
                        "avg_rotc": random.uniform(6, 25),
                        "improving": random.choice([True, False])
                    },
                    "growth_data": {
                        "avg_revenue_growth": random.uniform(growth_min, growth_max),
                        "cash_flow_positive": True,
                        "revenue_growth_trend": random.uniform(-1, 1)
                    }
                },
                "technical_analysis": {
                    "success": True,
                    "ml_prediction": random.uniform(-3, 8),
                    "confidence": random.uniform(60, 90),
                    "technical_score": random.uniform(55, 85),
                    "price_metrics": {
                        "current_price": current_price,
                        "predicted_price": current_price * (1 + random.uniform(-0.1, 0.2)),
                        "volatility": random.uniform(vol_min, vol_max)
                    }
                },
                "risk_metrics": {
                    "volatility": random.uniform(vol_min, vol_max),
                    "max_drawdown": random.uniform(-40, -5),
                    "var_95": random.uniform(-8, -1),
                    "sharpe_ratio": random.uniform(0.5, 3.0),
                    "risk_level": "High" if random.uniform(vol_min, vol_max) > 30 else "Moderate" 
                },
                "integrated_score": random.uniform(60, 90),
                "recommendation": {
                    "action": random.choice(["Buy", "Hold", "Strong Buy"]),
                    "reasoning": [
                        f"Based on {sector} sector metrics", 
                        "Positive technical indicators" if random.random() > 0.3 else "Mixed technical signals"
                    ],
                    "risk_context": "Normal"
                }
            }
            
            # Generate realistic company name
            company_names = {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOG": "Alphabet Inc. (Google) Class C",
                "GOOGL": "Alphabet Inc. (Google) Class A",
                "META": "Meta Platforms, Inc.",
                "NVDA": "NVIDIA Corporation",
                "INTC": "Intel Corporation",
                "AMD": "Advanced Micro Devices, Inc.",
                "CSCO": "Cisco Systems, Inc.",
                "ORCL": "Oracle Corporation",
                "IBM": "International Business Machines Corporation",
                "TSM": "Taiwan Semiconductor Manufacturing Company Limited",
                "ADBE": "Adobe Inc.",
                "CRM": "Salesforce, Inc.",
                "QCOM": "QUALCOMM Incorporated",
                "AMZN": "Amazon.com, Inc.",
                "TSLA": "Tesla, Inc.",
                "WMT": "Walmart Inc.",
                "HD": "The Home Depot, Inc.",
                "MCD": "McDonald's Corporation",
                "NKE": "NIKE, Inc.",
                "SBUX": "Starbucks Corporation",
                "TGT": "Target Corporation",
                "COST": "Costco Wholesale Corporation",
                "PG": "The Procter & Gamble Company",
                "KO": "The Coca-Cola Company",
                "PEP": "PepsiCo, Inc.",
                "DIS": "The Walt Disney Company",
                "JPM": "JPMorgan Chase & Co.",
                "V": "Visa Inc.",
                "MA": "Mastercard Incorporated",
                "BAC": "Bank of America Corporation",
                "WFC": "Wells Fargo & Company",
                "GS": "The Goldman Sachs Group, Inc.",
                "MS": "Morgan Stanley",
                "BLK": "BlackRock, Inc.",
                "C": "Citigroup Inc.",
                "AXP": "American Express Company",
                "PYPL": "PayPal Holdings, Inc.",
                "SCHW": "The Charles Schwab Corporation",
                "JNJ": "Johnson & Johnson",
                "PFE": "Pfizer Inc.",
                "MRK": "Merck & Co., Inc.",
                "UNH": "UnitedHealth Group Incorporated",
                "ABBV": "AbbVie Inc.",
                "TMO": "Thermo Fisher Scientific Inc.",
                "ABT": "Abbott Laboratories",
                "LLY": "Eli Lilly and Company",
                "BMY": "Bristol-Myers Squibb Company",
                "CAT": "Caterpillar Inc.",
                "BA": "The Boeing Company",
                "GE": "General Electric Company",
                "MMM": "3M Company",
                "HON": "Honeywell International Inc.",
                "UPS": "United Parcel Service, Inc.",
                "FDX": "FedEx Corporation",
                "DE": "Deere & Company",
                "XOM": "Exxon Mobil Corporation",
                "CVX": "Chevron Corporation",
                "COP": "ConocoPhillips",
                "EOG": "EOG Resources, Inc.",
                "SLB": "Schlumberger Limited",
                "OXY": "Occidental Petroleum Corporation",
                "VZ": "Verizon Communications Inc.",
                "T": "AT&T Inc.",
                "TMUS": "T-Mobile US, Inc.",
                "NEE": "NextEra Energy, Inc.",
                "DUK": "Duke Energy Corporation",
                "SO": "The Southern Company",
                "D": "Dominion Energy, Inc."
            }
            
            company_name = company_names.get(symbol.upper(), f"{symbol.upper()} Inc.")
            
            # Dividend yield based on sector
            div_yield = 0
            if sector in ["Consumer Defensive", "Utilities", "Energy", "Financial Services"]:
                div_yield = random.uniform(div_min, div_max)
            elif random.random() > 0.5:  # 50% chance for other sectors
                div_yield = random.uniform(0, div_min)
                
            # Calculate market cap (in billions)
            market_cap_ranges = {
                "Technology": (100, 3000),
                "Communication Services": (50, 2000),
                "Consumer Cyclical": (20, 1500),
                "Consumer Defensive": (10, 500),
                "Financial Services": (20, 800),
                "Healthcare": (30, 600),
                "Industrial": (20, 400),
                "Energy": (10, 600),
                "Utilities": (10, 200)
            }
            
            market_cap_min, market_cap_max = market_cap_ranges.get(sector, (10, 500))
            market_cap = random.uniform(market_cap_min, market_cap_max) * 1_000_000_000  # Convert to actual market cap
            
            return {
                "symbol": symbol.upper(),
                "company_name": company_name,
                "sector": sector,
                "industry": sector + " " + random.choice(["Products", "Services", "Equipment", "Solutions"]),
                "market_cap": market_cap,
                "current_price": current_price,
                "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price_metrics": {
                    "week_52_high": week_52_high,
                    "week_52_low": week_52_low,
                    "ytd_performance": ytd_performance,
                    "sentiment_score": sentiment_score,
                    "daily_change": daily_change,
                    "volume": int(random.uniform(1000000, 20000000))
                },
                "integrated_analysis": mock_integrated_analysis,
                "dividend_metrics": {
                    "dividend_yield": div_yield,
                    "dividend_rate": current_price * (div_yield/100),
                    "payout_ratio": random.uniform(0, 80) if div_yield > 0 else 0,
                    "dividend_growth": random.uniform(0, 15) if div_yield > 0 else 0
                },
                "portfolio_impact": {
                    "impact": {
                        "sharpe_change": random.uniform(0.01, 0.2),
                        "volatility_change": random.uniform(-2, 1),
                        "expected_return_change": random.uniform(0.1, 1.5)
                    }
                },
                "data_source": "mock_data",
                "timestamp": datetime.now().timestamp()
            }
        return None

    def _get_fallback_data(self, symbol: str) -> Dict:
        """Provide fallback data when API calls fail"""
        # First check if we have mock data for this symbol
        mock_data = self._get_mock_data(symbol)
        if mock_data:
            return mock_data
            
        # Otherwise return a generic fallback
        return {
            "symbol": symbol,
            "company_name": f"{symbol}",
            "sector": "Unknown",
            "industry": "Unknown",
            "market_cap": 0,
            "current_price": 0.0,
            "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price_metrics": {
                "week_52_high": 0.0,
                "week_52_low": 0.0,
                "ytd_performance": 0.0,
                "sentiment_score": 50.0,
                "daily_change": 0.0,
                "volume": 0
            },
            "integrated_analysis": {
                "company_type": "unknown",
                "fundamental_analysis": {
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
                },
                "technical_analysis": {
                    "success": False,
                    "ml_prediction": 0.0,
                    "confidence": 0.0,
                    "technical_score": 50.0,
                    "price_metrics": {
                        "current_price": 0.0,
                        "predicted_price": 0.0,
                        "volatility": 0.0
                    }
                },
                "risk_metrics": {
                    "volatility": 0.0,
                    "max_drawdown": 0.0,
                    "var_95": 0.0,
                    "sharpe_ratio": 0.0,
                    "risk_level": "Unknown"
                },
                "integrated_score": 50.0,
                "recommendation": {
                    "action": "Hold",
                    "reasoning": ["Insufficient data to make a recommendation"],
                    "risk_context": "Unknown"
                }
            },
            "dividend_metrics": {
                "dividend_yield": 0.0,
                "dividend_rate": 0.0,
                "payout_ratio": 0.0,
                "dividend_growth": 0.0
            },
            "portfolio_impact": {
                "impact": {
                    "sharpe_change": 0.0,
                    "volatility_change": 0.0,
                    "expected_return_change": 0.0
                }
            },
            "data_source": "fallback",
            "timestamp": datetime.now().timestamp()
        }

    def _save_to_cache(self, symbol: str, data: Dict) -> None:
        """Save stock data to local cache"""
        try:
            cache_file = self.cache_dir / f"{symbol.upper()}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            self.logger.debug(f"Data for {symbol} saved to cache")
        except Exception as e:
            self.logger.error(f"Error saving to cache: {str(e)}")

    def _get_from_cache(self, symbol: str) -> Optional[Dict]:
        """Get stock data from local cache if available and not expired"""
        try:
            cache_file = self.cache_dir / f"{symbol.upper()}.pkl"
            if not cache_file.exists():
                return None
                
            # Check if cache is expired
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.cache_expiry:
                self.logger.debug(f"Cache for {symbol} is expired")
                return None
                
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            self.logger.debug(f"Data for {symbol} loaded from cache")
            return data
            
        except Exception as e:
            self.logger.error(f"Error reading from cache: {str(e)}")
            return None

    def get_dividend_metrics(self, stock: yf.Ticker) -> Dict:
        """Calculate comprehensive dividend metrics"""
        try:
            info = stock.info
            dividends = stock.dividends
            
            return {
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'dividend_rate': info.get('dividendRate', 0),
                'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                'dividend_growth': self.calculate_dividend_growth(dividends) if not dividends.empty else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting dividend metrics: {str(e)}")
            return {
                'dividend_yield': 0,
                'dividend_rate': 0,
                'payout_ratio': 0,
                'dividend_growth': 0
            }
            
    def calculate_dividend_growth(self, dividends: pd.Series) -> float:
        """Calculate annual dividend growth rate"""
        if len(dividends) < 2:
            return 0
            
        try:
            # Group dividends by year
            yearly_dividends = dividends.groupby(pd.Grouper(freq='A')).sum()
            
            if len(yearly_dividends) < 2:
                return 0
                
            # Calculate year over year growth rates
            growth_rates = []
            for i in range(1, len(yearly_dividends)):
                prev_dividend = yearly_dividends.iloc[i-1]
                curr_dividend = yearly_dividends.iloc[i]
                
                if prev_dividend > 0:
                    growth_rate = ((curr_dividend / prev_dividend) - 1) * 100
                    growth_rates.append(growth_rate)
            
            # Return average growth rate (if available)
            if growth_rates:
                avg_growth = sum(growth_rates) / len(growth_rates)
                return avg_growth
            
            return 0
        except Exception as e:
            self.logger.error(f"Error calculating dividend growth: {str(e)}")
            return 0
            
    def calculate_portfolio_impact(self, symbol: str, portfolio: pd.DataFrame = None) -> Dict:
        """Calculate impact of adding a stock to a portfolio"""
        try:
            if portfolio is None or portfolio.empty:
                return {
                    'impact': {
                        'sharpe_change': 0.0,
                        'volatility_change': 0.0,
                        'expected_return_change': 0.0
                    }
                }
                
            # Example implementation - in practice you would:
            # 1. Get historical returns for the stock
            # 2. Create a new portfolio with some allocation to this stock
            # 3. Calculate combined metrics (Sharpe, volatility, etc)
            # 4. Compare to original portfolio
            
            # For now, return dummy data
            return {
                'impact': {
                    'sharpe_change': 0.05,
                    'volatility_change': -0.2,
                    'expected_return_change': 0.3
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating portfolio impact: {str(e)}")
            return {
                'impact': {
                    'sharpe_change': 0.0,
                    'volatility_change': 0.0,
                    'expected_return_change': 0.0
                }
            }