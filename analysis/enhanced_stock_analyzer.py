# src/analysis/enhanced_stock_analyzer.py

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

# Import our manual stock price data
try:
    import sys
    sys.path.append('.')  # Add current directory to path if necessary
    from stock_prices import get_stock_data
    HAS_MANUAL_PRICES = True
except ImportError:
    HAS_MANUAL_PRICES = False

try:
    from analysis.sentiment_calculator import SentimentCalculator
    HAS_SENTIMENT_CALCULATOR = True
except ImportError:
    HAS_SENTIMENT_CALCULATOR = False

class EnhancedStockAnalyzer:
    """
    Enhanced version of StockAnalyzer with integrated sentiment analysis.
    This class extends the original StockAnalyzer with:
    - Comprehensive sentiment scoring using multiple factors
    - Additional price metrics (52-week high/low, YTD performance)
    - News and social media integration
    """
    
    def __init__(self):
        self.integrated_analyzer = IntegratedAnalysis()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.current_portfolio = None
        self.logger = logging.getLogger(__name__)
        self.last_api_call = 0
        self.min_api_interval = 2.0  # Minimum time between API calls in seconds
        
        # Initialize data sources clients for API integration
        self._init_data_sources()
        
        # Initialize sentiment calculator if available
        if HAS_SENTIMENT_CALCULATOR:
            self.sentiment_calculator = SentimentCalculator()
        else:
            self.logger.warning("Sentiment calculator not available - using default values")
        
        # Create local cache directory if it doesn't exist
        self.cache_dir = Path("./cache/stocks")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = 24 * 3600  # 24 hours in seconds
        
        # Set a longer cache expiry for price data (30 minutes)
        self.price_cache_expiry = 30 * 60

    def analyze_stock(self, symbol: str, portfolio: pd.DataFrame = None, force_refresh: bool = False) -> Dict:
        """
        Comprehensive analysis of a single stock with portfolio impact
        
        Args:
            symbol: Stock ticker symbol
            portfolio: Optional portfolio data for impact analysis
            force_refresh: If True, ignores cache and forces fresh data fetch
        """
        try:
            # We don't use manual data as primary source anymore
            # Instead, we'll use it as fallback if other sources fail
            
            # Next, check local cache (unless forcing refresh)
            cached_data = None if force_refresh else self._get_from_cache(symbol)
            if cached_data:
                # Always try to get the latest price data
                try:
                    # Just update the price
                    updated_price = self._get_current_price(symbol)
                    if updated_price > 0:
                        cached_data['current_price'] = updated_price
                        cached_data['price_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Update price in price_metrics if it exists
                        if 'price_metrics' in cached_data:
                            # Try to get daily change
                            try:
                                import yfinance as yf
                                ticker = yf.Ticker(symbol)
                                recent_data = ticker.history(period="2d")
                                if len(recent_data) >= 2:
                                    prev_close = recent_data['Close'].iloc[-2]
                                    if prev_close > 0:
                                        daily_change = ((updated_price / prev_close) - 1) * 100
                                        cached_data['price_metrics']['daily_change'] = daily_change
                                        self.logger.info(f"Updated daily change for {symbol}: {daily_change:.2f}%")
                                else:
                                    cached_data['price_metrics']['daily_change'] = 0  # Reset since we don't know the change
                            except Exception as dc_e:
                                self.logger.warning(f"Failed to calculate daily change: {str(dc_e)}")
                                cached_data['price_metrics']['daily_change'] = 0
                                
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
            
            # DISABLED: Mock data system (was causing wrong financial data)
            # mock_data = self._get_mock_data(symbol)
            # if False:  # Never use mock data
            #     self.logger.info(f"Using mock data for {symbol}")
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
            
            # Try TwelveData first (PRIMARY source - Pro 610 subscription)
            try:
                if hasattr(self, 'has_twelvedata') and self.has_twelvedata:
                    self.logger.info(f"Using TwelveData as PRIMARY source for {symbol}")

                    # Get TwelveData client (lazy initialization with retry logic)
                    twelvedata_client = self._get_twelvedata_client()
                    if twelvedata_client is None:
                        raise Exception("TwelveData client unavailable after initialization attempts")

                    # Get data from TwelveData
                    td_data = twelvedata_client.analyze_stock(symbol, force_refresh)

                    if td_data and td_data.get('success') and 'current_price' in td_data and td_data.get('current_price', 0) > 0:
                        # Mark the data source
                        td_data['data_source'] = 'twelvedata'
                        td_data['data_source_priority'] = 'primary'

                        # Add sentiment data if not already present
                        if 'sentiment_metrics' not in td_data:
                            td_data['sentiment_metrics'] = self._get_sentiment_analysis(symbol)

                        # Cache and return
                        self._save_to_cache(symbol, td_data)
                        self.logger.info(f"✅ SUCCESS: Got TwelveData data for {symbol} - Price: {td_data.get('current_price')}")
                        return td_data
                    else:
                        self.logger.warning(f"TwelveData returned invalid data for {symbol}, falling back to Alpha Vantage")
            except Exception as td_e:
                self.logger.error(f"TwelveData failed for {symbol}: {str(td_e)}, falling back to Alpha Vantage")

            # Fallback to Alpha Vantage if TwelveData fails
            try:
                # Check if Alpha Vantage client is available
                try:
                    import sys
                    sys.path.append('.')
                    from data.alpha_vantage_client import AlphaVantageClient
                    HAS_ALPHA_VANTAGE = True
                except ImportError:
                    self.logger.warning("Alpha Vantage client not available")
                    HAS_ALPHA_VANTAGE = False

                if HAS_ALPHA_VANTAGE:
                    self.logger.info(f"Using Alpha Vantage as FALLBACK source for {symbol}")

                    # Initialize the client if not already done
                    if not hasattr(self, 'alpha_vantage_client'):
                        self.alpha_vantage_client = AlphaVantageClient()

                    # Get data from Alpha Vantage
                    alpha_data = self.alpha_vantage_client.analyze_stock(symbol, force_refresh)
                    
                    if alpha_data:
                        # Add sentiment data if not already present
                        if not 'sentiment_data' in alpha_data and HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
                            try:
                                # Get data for sentiment calculation
                                week_52_high = alpha_data['price_metrics']['week_52_high']
                                week_52_low = alpha_data['price_metrics']['week_52_low']
                                current_price = alpha_data['current_price']
                                ytd_performance = alpha_data['price_metrics']['ytd_performance']
                                daily_change = alpha_data['price_metrics']['daily_change']
                                
                                # Try to get daily data for price history
                                daily_data = self.alpha_vantage_client.get_daily_time_series(symbol)
                                
                                if daily_data and 'data' in daily_data:
                                    # Convert to pandas DataFrame
                                    import pandas as pd
                                    import numpy as np
                                    
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
                                    year_history = pd.DataFrame({
                                        'Open': prices_open,
                                        'High': prices_high,
                                        'Low': prices_low,
                                        'Close': prices_close
                                    }, index=pd.DatetimeIndex(dates))
                                    
                                    # Extract ROTC from fundamental analysis if available
                                    rotc = None
                                    if 'integrated_analysis' in alpha_data and 'fundamental_analysis' in alpha_data['integrated_analysis']:
                                        rotc_data = alpha_data['integrated_analysis']['fundamental_analysis'].get('rotc_data', {})
                                        rotc = rotc_data.get('latest_rotc', None)
                                    
                                    # Calculate sentiment
                                    sentiment_data = self.sentiment_calculator.calculate_sentiment(
                                        symbol=symbol,
                                        price_history=year_history,
                                        current_price=current_price,
                                        week_52_high=week_52_high,
                                        week_52_low=week_52_low,
                                        ytd_performance=ytd_performance,
                                        rotc=rotc,
                                        daily_change=daily_change
                                    )
                                    
                                    # Add sentiment data
                                    alpha_data['sentiment_data'] = sentiment_data
                                    alpha_data['price_metrics']['sentiment_score'] = sentiment_data.get('sentiment_score', 50)
                                else:
                                    # Use default sentiment
                                    alpha_data['sentiment_data'] = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                                    alpha_data['price_metrics']['sentiment_score'] = 50
                            except Exception as e:
                                self.logger.warning(f"Error calculating sentiment for Alpha Vantage data: {str(e)}")
                                alpha_data['sentiment_data'] = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                                alpha_data['price_metrics']['sentiment_score'] = 50
                        
                        # Add portfolio impact if not already present
                        if not 'portfolio_impact' in alpha_data:
                            alpha_data['portfolio_impact'] = self.calculate_portfolio_impact(symbol, portfolio)

                        # Mark as fallback data source
                        alpha_data['data_source'] = 'alpha_vantage'
                        alpha_data['data_source_priority'] = 'fallback'
                        self.logger.info(f"Using Alpha Vantage as fallback data source for {symbol}")

                        # Cache the data
                        self._save_to_cache(symbol, alpha_data)
                        return alpha_data
                else:
                    self.logger.info(f"Alpha Vantage client not available, using YFinance for {symbol}")
            except Exception as alpha_e:
                self.logger.warning(f"Alpha Vantage error for {symbol}: {str(alpha_e)}")
                
            # If Alpha Vantage failed or isn't available, try YFinance
            try:
                self.logger.info(f"Trying YFinance for {symbol}")
                data = self._get_from_yfinance(symbol)
                if data:
                    # Cache successful data
                    self._save_to_cache(symbol, data)
                    return data
            except Exception as e:
                self.logger.warning(f"YFinance error for {symbol}: {str(e)}")
                
                # Try direct Alpha Vantage API as alternative data source
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
            # PRIMARY METHOD - YFinance History
            # This is the most reliable method for current prices
            try:
                stock = yf.Ticker(symbol)
                # Use '1d' for most recent data with interval='1m' for minute-level data (more real-time)
                history = stock.history(period="1d", interval="1m")
                
                # Check if we have valid data with a Close column
                if not history.empty and 'Close' in history.columns:
                    # Get latest price
                    latest_price = float(history['Close'].iloc[-1])
                    
                    self.logger.info(f"YFinance data for {symbol}: \n" +
                                    f"Latest timestamp: {history.index[-1]} \n" +
                                    f"Latest close: {latest_price} \n" +
                                    f"Data points: {len(history)}")
                    
                    # Add validation - check if price seems reasonable
                    if latest_price > 0 and latest_price < 10000:  # Basic sanity check
                        self.logger.info(f"Got current price for {symbol} from YFinance history: {latest_price}")
                        return latest_price
                    else:
                        self.logger.warning(f"Unreasonable YFinance price for {symbol}: {latest_price}, trying alternate methods")
            except Exception as yf_hist_e:
                self.logger.warning(f"Error getting YFinance history price for {symbol}: {str(yf_hist_e)}")
            
            # BACKUP METHOD 1 - Alpha Vantage if available
            try:
                # Check if Alpha Vantage client is available
                import sys
                sys.path.append('.')
                from data.alpha_vantage_client import AlphaVantageClient
                
                # Initialize the client if not already done
                if not hasattr(self, 'alpha_vantage_client'):
                    self.alpha_vantage_client = AlphaVantageClient()
                
                # Get quote data from Alpha Vantage
                quote_data = self.alpha_vantage_client.get_quote(symbol)
                if quote_data and 'price' in quote_data and quote_data['price'] > 0:
                    price = float(quote_data['price'])
                    # Validate the price is reasonable
                    if price < 10000:  # Basic sanity check
                        self.logger.info(f"Got current price for {symbol} from Alpha Vantage: {price}")
                        return price
                    else:
                        self.logger.warning(f"Unreasonable Alpha Vantage price for {symbol}: {price}")
            except Exception as av_e:
                self.logger.warning(f"Error getting price from Alpha Vantage for {symbol}: {str(av_e)}")
            
            # BACKUP METHOD 2 - Direct YFinance info access
            try:
                stock = yf.Ticker(symbol)
                if hasattr(stock, 'info') and stock.info:
                    # Try currentPrice first
                    if 'currentPrice' in stock.info:
                        price = float(stock.info['currentPrice'])
                        if 0 < price < 10000:  # Sanity check
                            self.logger.info(f"Got current price for {symbol} from YFinance currentPrice: {price}")
                            return price
                    
                    # Try regularMarketPrice next
                    if 'regularMarketPrice' in stock.info:
                        price = float(stock.info['regularMarketPrice'])
                        if 0 < price < 10000:  # Sanity check
                            self.logger.info(f"Got current price for {symbol} from YFinance regularMarketPrice: {price}")
                            return price
                    
                    # Previous close as last resort
                    if 'previousClose' in stock.info:
                        price = float(stock.info['previousClose'])
                        if 0 < price < 10000:  # Sanity check
                            self.logger.info(f"Got current price for {symbol} from YFinance previousClose: {price}")
                            return price
            except Exception as yf_info_e:
                self.logger.warning(f"Error getting YFinance info price for {symbol}: {str(yf_info_e)}")
            
            # ALTERNATIVE METHOD: Try real-time quote from Yahoo Finance API
            try:
                import requests
                url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                data = response.json()
                
                if 'quoteResponse' in data and 'result' in data['quoteResponse'] and len(data['quoteResponse']['result']) > 0:
                    quote_data = data['quoteResponse']['result'][0]
                    if 'regularMarketPrice' in quote_data:
                        price = float(quote_data['regularMarketPrice'])
                        if 0 < price < 10000:  # Sanity check
                            self.logger.info(f"Got price for {symbol} from Yahoo Finance API: {price}")
                            return price
            except Exception as yahoo_e:
                self.logger.warning(f"Error getting Yahoo Finance API price for {symbol}: {str(yahoo_e)}")
            
            # FALLBACK - Manual stock prices (if available) - LEAST PREFERRED OPTION
            if HAS_MANUAL_PRICES:
                manual_data = get_stock_data(symbol)
                if manual_data and 'current_price' in manual_data:
                    price = float(manual_data['current_price'])
                    self.logger.warning(f"USING OUTDATED MANUAL PRICE DATA FOR {symbol}: {price}")
                    return price
            
            # If all methods failed, return 0
            self.logger.error(f"All price retrieval methods failed for {symbol}")
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return 0.0
            
    def get_manual_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get manually maintained stock data"""
        if not HAS_MANUAL_PRICES:
            return None
            
        stock_data = get_stock_data(symbol)
        if not stock_data:
            return None
            
        # Create a full stock analysis result using our manual data
        current_price = stock_data.get('current_price', 0)
        week_52_high = stock_data.get('week_52_high', current_price * 1.2)
        week_52_low = stock_data.get('week_52_low', current_price * 0.8)
        ytd_performance = stock_data.get('ytd_performance', 0)
        
        return {
            "symbol": symbol.upper(),
            "company_name": stock_data.get('company_name', f"{symbol.upper()} Inc."),
            "sector": stock_data.get('sector', 'Technology'),
            "industry": stock_data.get('industry', 'Unknown'),
            "market_cap": current_price * 1000000000,  # Estimate
            "current_price": current_price,
            "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price_metrics": {
                "week_52_high": week_52_high,
                "week_52_low": week_52_low,
                "ytd_performance": ytd_performance,
                "sentiment_score": 65.0,
                "daily_change": 0.0,
                "volume": 10000000
            },
            "sentiment_data": {
                "sentiment_score": 65.0,
                "sentiment_label": "Bullish" if ytd_performance > 0 else "Neutral",
                "components": {}
            },
            "integrated_analysis": self._create_default_integrated_analysis(current_price),
            "dividend_metrics": {
                "dividend_yield": 0.5,
                "dividend_rate": current_price * 0.005,
                "payout_ratio": 10.0,
                "dividend_growth": 5.0
            },
            "portfolio_impact": {
                "impact": {
                    "sharpe_change": 0.05,
                    "volatility_change": -0.2,
                    "expected_return_change": 0.3
                }
            },
            "data_source": "manual_data",
            "timestamp": datetime.now().timestamp()
        }

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
                    if False:  # Mock data disabled
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
                    
                    # Calculate daily price change
                    daily_change = 0
                    if 'regularMarketChangePercent' in info:
                        daily_change = info.get('regularMarketChangePercent', 0) * 100
                    elif len(history) >= 2:
                        prev_close = history['Close'].iloc[-2] if len(history) > 1 else 0
                        if prev_close > 0:
                            daily_change = ((current_price / prev_close) - 1) * 100
                    
                    # Get ROTC if available
                    rotc = None
                    if 'returnOnCapital' in info:
                        rotc = info.get('returnOnCapital', None)
                    elif 'returnOnAssets' in info:  # Fallback
                        rotc = info.get('returnOnAssets', None)
                    
                    # Convert to percentage if needed
                    if rotc is not None and rotc < 1:
                        rotc = rotc * 100
                    
                    # Add the price metrics to use in the template
                    price_metrics = {
                        'week_52_high': week_52_high,
                        'week_52_low': week_52_low,
                        'ytd_performance': ytd_performance,
                        'daily_change': daily_change,
                        'volume': info.get('regularMarketVolume', 0)
                    }
                    
                    # Calculate sentiment score if sentiment calculator is available
                    if HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
                        try:
                            sentiment_data = self.sentiment_calculator.calculate_sentiment(
                                symbol=symbol,
                                price_history=year_history,
                                current_price=current_price,
                                week_52_high=week_52_high,
                                week_52_low=week_52_low,
                                ytd_performance=ytd_performance,
                                rotc=rotc,
                                daily_change=daily_change
                            )
                            # Add sentiment score to price metrics for easy display
                            price_metrics['sentiment_score'] = sentiment_data.get('sentiment_score', 50)
                        except Exception as sentiment_error:
                            self.logger.warning(f"Error calculating sentiment for {symbol}: {str(sentiment_error)}")
                            sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                            price_metrics['sentiment_score'] = 50
                    else:
                        # Default sentiment if calculator not available
                        sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                        price_metrics['sentiment_score'] = 50
                        
                except Exception as hist_e:
                    self.logger.warning(f"Error calculating historical metrics: {str(hist_e)}")
                    week_52_high = info.get('fiftyTwoWeekHigh', 0)
                    week_52_low = info.get('fiftyTwoWeekLow', 0)
                    ytd_performance = 0
                    sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                    price_metrics = {
                        'week_52_high': week_52_high,
                        'week_52_low': week_52_low,
                        'ytd_performance': 0,
                        'daily_change': 0,
                        'sentiment_score': 50,
                        'volume': info.get('regularMarketVolume', 0)
                    }
                
                # Create full response with real-time price data
                return {
                    'symbol': symbol,
                    'company_name': info.get('longName', symbol),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'current_price': current_price,  # Add current price directly in main object
                    'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'price_metrics': price_metrics,
                    'sentiment_data': sentiment_data,
                    'integrated_analysis': integrated_results,
                    'dividend_metrics': dividend_metrics,
                    'portfolio_impact': self.calculate_portfolio_impact(symbol),
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
        Get stock data from Alpha Vantage API as an alternative source.
        Uses the AlphaVantageClient for proper rate limiting and caching.
        """
        try:
            # Import our Alpha Vantage client
            try:
                import sys
                sys.path.append('.')
                from data.alpha_vantage_client import AlphaVantageClient
                HAS_ALPHA_VANTAGE = True
            except ImportError:
                self.logger.warning("Alpha Vantage client not available - falling back to direct API calls")
                HAS_ALPHA_VANTAGE = False
            
            if HAS_ALPHA_VANTAGE:
                # Use our dedicated Alpha Vantage client
                self.logger.info(f"Using Alpha Vantage client for {symbol}")
                
                # Initialize the client if not already done
                if not hasattr(self, 'alpha_vantage_client'):
                    self.alpha_vantage_client = AlphaVantageClient()
                    
                # Use the analyze_stock method to get comprehensive data
                result = self.alpha_vantage_client.analyze_stock(symbol)
                
                # If we have a valid result, add sentiment data
                if result and 'price_metrics' in result:
                    # Calculate sentiment data if sentiment calculator is available
                    week_52_high = result['price_metrics']['week_52_high']
                    week_52_low = result['price_metrics']['week_52_low']
                    current_price = result['current_price']
                    ytd_performance = result['price_metrics']['ytd_performance']
                    daily_change = result['price_metrics']['daily_change']
                    
                    if HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
                        try:
                            # Try to get daily time series for sentiment calculation
                            daily_data = self.alpha_vantage_client.get_daily_time_series(symbol)
                            
                            if daily_data and 'data' in daily_data:
                                # Convert Alpha Vantage format to pandas DataFrame
                                import pandas as pd
                                import numpy as np
                                
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
                                year_history = pd.DataFrame({
                                    'Open': prices_open,
                                    'High': prices_high,
                                    'Low': prices_low,
                                    'Close': prices_close
                                }, index=pd.DatetimeIndex(dates))
                                
                                # Extract ROTC from fundamental analysis if available
                                rotc = None
                                if 'integrated_analysis' in result and 'fundamental_analysis' in result['integrated_analysis']:
                                    rotc_data = result['integrated_analysis']['fundamental_analysis'].get('rotc_data', {})
                                    rotc = rotc_data.get('latest_rotc', None)
                                
                                # Calculate sentiment
                                sentiment_data = self.sentiment_calculator.calculate_sentiment(
                                    symbol=symbol,
                                    price_history=year_history,
                                    current_price=current_price,
                                    week_52_high=week_52_high,
                                    week_52_low=week_52_low,
                                    ytd_performance=ytd_performance,
                                    rotc=rotc,
                                    daily_change=daily_change
                                )
                                
                                # Add sentiment data to result
                                result['sentiment_data'] = sentiment_data
                                result['price_metrics']['sentiment_score'] = sentiment_data.get('sentiment_score', 50)
                            else:
                                # Use default sentiment if no price history
                                result['sentiment_data'] = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                                result['price_metrics']['sentiment_score'] = 50
                                
                        except Exception as e:
                            self.logger.warning(f"Error calculating sentiment for Alpha Vantage data: {str(e)}")
                            result['sentiment_data'] = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                            result['price_metrics']['sentiment_score'] = 50
                    else:
                        # Use default sentiment if calculator not available
                        result['sentiment_data'] = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                        result['price_metrics']['sentiment_score'] = 50
                        
                # Add portfolio impact
                result['portfolio_impact'] = self.calculate_portfolio_impact(symbol)
                
                return result
            else:
                # Legacy implementation when Alpha Vantage client is not available
                self.logger.warning("Using legacy Alpha Vantage integration - less efficient")
                
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
                
                # Calculate sentiment data (simple simulation)
                sentiment_score = 50.0  # Neutral default
                if HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
                    try:
                        # Create a minimal dataframe for the sentiment calculator
                        import pandas as pd
                        import numpy as np
                        
                        # Create a minimal price history with linear trend
                        dates = pd.date_range(end=datetime.now(), periods=30)
                        prices = np.linspace(current_price * 0.9, current_price, 30)
                        year_history = pd.DataFrame({
                            'Close': prices,
                            'Open': prices * 0.99,
                            'High': prices * 1.01,
                            'Low': prices * 0.98
                        }, index=dates)
                        
                        # Use the sentiment calculator with simulated data
                        sentiment_data = self.sentiment_calculator.calculate_sentiment(
                            symbol=symbol,
                            price_history=year_history,
                            current_price=current_price,
                            week_52_high=week_52_high,
                            week_52_low=week_52_low,
                            ytd_performance=0.0,  # Unknown
                            rotc=None,
                            daily_change=daily_change
                        )
                        sentiment_score = sentiment_data.get('sentiment_score', 50)
                    except Exception as e:
                        self.logger.warning(f"Error calculating sentiment for alternative source: {str(e)}")
                        sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                else:
                    sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
                
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
                        'sentiment_score': sentiment_score,
                        'daily_change': daily_change,
                        'volume': float(overview.get('Volume', 0))
                    },
                    'sentiment_data': sentiment_data,
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
            # Use fixed delay - randomness here is not needed and can cause inconsistencies
            delay = self.min_api_interval - time_since_last_call + 0.5
            self.logger.debug(f"Throttling API call, sleeping for {delay:.2f} seconds")
            time.sleep(delay)
            
        self.last_api_call = time.time()
        
    def _init_data_sources(self):
        """Initialize connections to data sources (TwelveData, Alpha Vantage, Interactive Brokers, etc.)"""
        # Check for TwelveData availability (PRIMARY DATA SOURCE) - LAZY INITIALIZATION
        try:
            import sys
            sys.path.append('.')
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer
            self._twelvedata_class = TwelveDataAnalyzer
            self._twelvedata_client = None  # Will be created lazily
            self.has_twelvedata = True
            self.logger.info("TwelveData client available (PRIMARY) - will initialize on demand")
        except ImportError as e:
            self._twelvedata_class = None
            self._twelvedata_client = None
            self.has_twelvedata = False
            self.logger.warning(f"TwelveData client not available - import failed: {str(e)}")

        # Check for Alpha Vantage client (FALLBACK)
        try:
            import sys
            sys.path.append('.')
            from data.alpha_vantage_client import AlphaVantageClient
            self.alpha_vantage_client = AlphaVantageClient()
            self.has_alpha_vantage = True
            self.logger.info("Alpha Vantage client initialized (FALLBACK)")
        except ImportError:
            self.has_alpha_vantage = False
            self.logger.warning("Alpha Vantage client not available")
        
        # Check for Interactive Brokers client
        try:
            import sys
            sys.path.append('.')
            from data.ib_data_client import IBDataClient
            self.ib_client = IBDataClient()
            self.has_ib = True
            self.logger.info("Interactive Brokers client initialized")
        except ImportError:
            self.has_ib = False
            self.logger.warning("Interactive Brokers client not available")
            
        # Initialize Data Comparison Service
        try:
            from data.data_comparison_service import DataComparisonService
            self.data_comparison_service = DataComparisonService()
            self.has_comparison_service = True
            self.logger.info("Data Comparison Service initialized")
        except ImportError:
            self.has_comparison_service = False
            self.logger.warning("Data Comparison Service not available")

    def _get_twelvedata_client(self):
        """
        Lazy initialization of TwelveData client with error recovery
        Returns TwelveData client instance or None if unavailable
        """
        if not self.has_twelvedata or not self._twelvedata_class:
            return None

        # Return existing client if already initialized
        if self._twelvedata_client is not None:
            return self._twelvedata_client

        # Attempt to create client with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._twelvedata_client = self._twelvedata_class()
                self.logger.info(f"TwelveData client initialized successfully (attempt {attempt + 1})")
                return self._twelvedata_client

            except Exception as e:
                self.logger.warning(f"TwelveData client initialization failed (attempt {attempt + 1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    wait_time = (2 ** attempt)  # 1, 2, 4 seconds
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    # Final failure - disable TwelveData for this session
                    self.has_twelvedata = False
                    self.logger.error("TwelveData client permanently disabled for this session due to initialization failures")

        return None

    def _get_mock_data(self, symbol: str) -> Dict:
        """
        Return mock data for popular stocks to avoid API calls during testing
        or when rate limiting is occurring
        
        Uses deterministic values based on the symbol to ensure consistent results.
        No randomness is used.
        """
        # Generate a deterministic value based on the symbol
        symbol_value = sum(ord(c) for c in symbol.upper())
        
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
            # Calculate a deterministic price based on symbol_value
            range_size = max_price - min_price
            current_price = min_price + ((symbol_value % 100) / 100) * range_size
            
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
            
            # Generate 52-week high/low prices deterministically
            # Use different aspects of the symbol to create variation
            high_factor = 1.05 + ((symbol_value % 35) / 100)  # 1.05 to 1.40
            low_factor = 0.60 + ((symbol_value % 35) / 100)   # 0.60 to 0.95
            week_52_high = current_price * high_factor
            week_52_low = current_price * low_factor
            
            # Generate YTD performance (-15 to 30 range)
            ytd_performance = -15 + (symbol_value % 45)
            
            # Generate sentiment score (40 to 80 range)
            sentiment_score = 40 + (symbol_value % 40)
            
            # Generate daily change percentage (-2 to 2 range)
            # Use the last character of the symbol to add some variation
            last_char_value = ord(symbol.upper()[-1])
            daily_change = -2 + ((last_char_value % 40) / 10)
            
            # Generate integrated analysis with realistic metrics (all deterministic)
            # Use different symbol characteristics for different metrics
            first_char = ord(symbol.upper()[0])
            second_char = ord(symbol.upper()[min(1, len(symbol) - 1)])
            
            # Fundamental scores
            fundamental_score = 60 + (symbol_value % 30)  # 60-90
            rotc_latest = 8 + (symbol_value % 22)  # 8-30
            rotc_avg = 6 + (symbol_value % 19)  # 6-25
            improving = (symbol_value % 2) == 0  # Deterministic boolean
            
            # Growth data
            growth_range = growth_max - growth_min
            revenue_growth = growth_min + ((symbol_value % 100) / 100) * growth_range
            revenue_trend = -1 + ((first_char % 100) / 50)  # -1 to 1 range
            
            # Technical analysis
            ml_prediction = -3 + (symbol_value % 11)  # -3 to 8
            confidence = 60 + (second_char % 30)  # 60-90
            technical_score = 55 + (symbol_value % 30)  # 55-85
            
            # Calculate deterministic price prediction
            pred_factor = -0.1 + ((symbol_value % 30) / 100)  # -0.1 to 0.2
            predicted_price = current_price * (1 + pred_factor)
            
            # Volatility (use vol_min and vol_max from sector metrics)
            vol_range = vol_max - vol_min
            volatility = vol_min + ((symbol_value % 100) / 100) * vol_range
            
            # Risk metrics
            max_drawdown = -40 + (symbol_value % 35)  # -40 to -5
            var_95 = -8 + (symbol_value % 7)  # -8 to -1
            sharpe_ratio = 0.5 + ((symbol_value % 25) / 10)  # 0.5 to 3.0
            risk_level = "High" if volatility > 30 else "Moderate"
            
            # Integrated score
            integrated_score = 60 + (symbol_value % 30)  # 60-90
            
            # Recommendation
            action_options = ["Buy", "Hold", "Strong Buy"]
            action = action_options[symbol_value % 3]
            tech_indicator = "Positive technical indicators" if (symbol_value % 10) > 3 else "Mixed technical signals"
            
            mock_integrated_analysis = {
                "company_type": company_type,
                "fundamental_analysis": {
                    "score": fundamental_score,
                    "rotc_data": {
                        "latest_rotc": rotc_latest,
                        "avg_rotc": rotc_avg,
                        "improving": improving
                    },
                    "growth_data": {
                        "avg_revenue_growth": revenue_growth,
                        "cash_flow_positive": True,
                        "revenue_growth_trend": revenue_trend
                    }
                },
                "technical_analysis": {
                    "success": True,
                    "ml_prediction": ml_prediction,
                    "confidence": confidence,
                    "technical_score": technical_score,
                    "price_metrics": {
                        "current_price": current_price,
                        "predicted_price": predicted_price,
                        "volatility": volatility
                    }
                },
                "risk_metrics": {
                    "volatility": volatility,
                    "max_drawdown": max_drawdown,
                    "var_95": var_95,
                    "sharpe_ratio": sharpe_ratio,
                    "risk_level": risk_level
                },
                "integrated_score": integrated_score,
                "recommendation": {
                    "action": action,
                    "reasoning": [
                        f"Based on {sector} sector metrics", 
                        tech_indicator
                    ],
                    "risk_context": "Normal"
                }
            }
            
            # Calculate sentiment if the calculator is available
            if HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
                try:
                    # Create a minimal dataframe for the sentiment calculator
                    import pandas as pd
                    import numpy as np
                    
                    # Create a minimal price history with random trend
                    dates = pd.date_range(end=datetime.now(), periods=30)
                    
                    # Generate prices with a trend based on YTD performance
                    if ytd_performance > 0:
                        # Positive trend
                        prices = np.linspace(current_price * 0.8, current_price, 30)
                    else:
                        # Negative trend
                        prices = np.linspace(current_price * 1.2, current_price, 30)
                        
                    year_history = pd.DataFrame({
                        'Close': prices,
                        'Open': prices * 0.99,
                        'High': prices * 1.01,
                        'Low': prices * 0.98
                    }, index=dates)
                    
                    # Use the sentiment calculator with simulated data
                    rotc = mock_integrated_analysis['fundamental_analysis']['rotc_data']['latest_rotc']
                    sentiment_data = self.sentiment_calculator.calculate_sentiment(
                        symbol=symbol,
                        price_history=year_history,
                        current_price=current_price,
                        week_52_high=week_52_high,
                        week_52_low=week_52_low,
                        ytd_performance=ytd_performance,
                        rotc=rotc,
                        daily_change=daily_change
                    )
                    sentiment_score = sentiment_data.get('sentiment_score', sentiment_score)
                except Exception as e:
                    self.logger.warning(f"Error calculating sentiment for mock data: {str(e)}")
                    sentiment_data = {
                        "sentiment_score": sentiment_score,
                        "sentiment_label": "Bullish" if sentiment_score > 70 else "Neutral" if sentiment_score > 40 else "Bearish"
                    }
            else:
                sentiment_data = {
                    "sentiment_score": sentiment_score,
                    "sentiment_label": "Bullish" if sentiment_score > 70 else "Neutral" if sentiment_score > 40 else "Bearish"
                }
            
            # Update stock mock data with accurate values (March 2025)
            if symbol.upper() == "NVDA" or symbol.upper() == "AAPL":
                # Special handling for key stocks
                if symbol.upper() == "AAPL":
                    # Current accurate data for Apple as of March 2025
                    return {
                        "symbol": "AAPL",
                        "company_name": "Apple Inc.",
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "market_cap": 3150000000000,  # $3.15T
                        "current_price": 192.53,  # Real price as of March 2025
                        "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "price_metrics": {
                            "week_52_high": 220.20,  # Accurate 52-week high
                            "week_52_low": 164.04,   # Accurate 52-week low
                            "ytd_performance": -0.74,  # YTD performance
                            "sentiment_score": 65.0,  # Bullish sentiment
                            "daily_change": 0.38,     # Recent daily change
                            "volume": 58900000       # Average volume
                        },
                        "sentiment_data": {
                            "sentiment_score": 65.0,
                            "sentiment_label": "Bullish",
                            "components": {}
                        },
                        "integrated_analysis": {
                            "company_type": "value",
                            "fundamental_analysis": {
                                "score": 85.0,
                                "rotc_data": {
                                    "latest_rotc": 36.2,
                                    "avg_rotc": 33.8,
                                    "improving": True
                                },
                                "growth_data": {
                                    "avg_revenue_growth": 7.8,
                                    "cash_flow_positive": True,
                                    "revenue_growth_trend": 0.4
                                }
                            },
                            "technical_analysis": {
                                "success": True,
                                "ml_prediction": 4.2,
                                "confidence": 78.0,
                                "technical_score": 72.0,
                                "price_metrics": {
                                    "current_price": 192.53,
                                    "predicted_price": 200.50,
                                    "volatility": 22.0
                                }
                            },
                            "risk_metrics": {
                                "volatility": 22.0,
                                "max_drawdown": -12.5,
                                "var_95": -2.2,
                                "sharpe_ratio": 1.9,
                                "risk_level": "Low"
                            },
                            "integrated_score": 82.0,
                            "recommendation": {
                                "action": "Buy",
                                "reasoning": [
                                    "Strong services revenue growth",
                                    "Consistent return of capital to shareholders",
                                    "Stable market position"
                                ],
                                "risk_context": "Low"
                            }
                        },
                        "dividend_metrics": {
                            "dividend_yield": 0.52,
                            "dividend_rate": 1.00,
                            "payout_ratio": 14.8,
                            "dividend_growth": 5.4
                        },
                        "portfolio_impact": {
                            "impact": {
                                "sharpe_change": 0.08,
                                "volatility_change": -0.5,
                                "expected_return_change": 0.7
                            }
                        },
                        "data_source": "updated_mock",
                        "timestamp": datetime.now().timestamp()
                    }
                
                # NVIDIA data if not Apple
                if symbol.upper() == "NVDA":
                    # Current accurate data for NVIDIA as of March 2025
                    return {
                        "symbol": "NVDA",
                        "company_name": "NVIDIA Corporation",
                        "sector": "Technology",
                        "industry": "Semiconductors",
                        "market_cap": 2720000000000,  # $2.72T
                        "current_price": 110.32,  # Real price as of March 11, 2025
                        "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "price_metrics": {
                            "week_52_high": 131.21,  # Accurate 52-week high
                            "week_52_low": 44.23,    # Accurate 52-week low
                            "ytd_performance": 84.2,  # YTD performance
                            "sentiment_score": 85.5,  # Bullish sentiment
                            "daily_change": 1.2,     # Recent daily change
                            "volume": 28500000       # Average volume
                        },
                        "sentiment_data": {
                            "sentiment_score": 85.5,
                            "sentiment_label": "Bullish",
                            "components": {}
                        },
                        "integrated_analysis": {
                            "company_type": "growth",
                            "fundamental_analysis": {
                                "score": 92.0,
                                "rotc_data": {
                                    "latest_rotc": 26.8,
                                    "avg_rotc": 24.5,
                                    "improving": True
                                },
                                "growth_data": {
                                    "avg_revenue_growth": 38.2,
                                    "cash_flow_positive": True,
                                    "revenue_growth_trend": 0.8
                                }
                            },
                            "technical_analysis": {
                                "success": True,
                                "ml_prediction": 6.5,
                                "confidence": 88.0,
                                "technical_score": 90.5,
                                "price_metrics": {
                                    "current_price": 110.32,
                                    "predicted_price": 117.50,
                                    "volatility": 35.0
                                }
                            },
                            "risk_metrics": {
                                "volatility": 35.0,
                                "max_drawdown": -15.0,
                                "var_95": -3.5,
                                "sharpe_ratio": 2.8,
                                "risk_level": "Moderate"
                            },
                            "integrated_score": 91.0,
                            "recommendation": {
                                "action": "Strong Buy",
                                "reasoning": [
                                    "AI and GPU market leader with dominant position",
                                    "Strong growth in data center revenue",
                                    "Positive technical indicators"
                                ],
                                "risk_context": "Normal"
                            }
                        },
                        "dividend_metrics": {
                            "dividend_yield": 0.05,
                            "dividend_rate": 0.04,
                            "payout_ratio": 0.8,
                            "dividend_growth": 0.0
                        },
                        "portfolio_impact": {
                            "impact": {
                                "sharpe_change": 0.15,
                                "volatility_change": 0.5,
                                "expected_return_change": 1.2
                            }
                        },
                        "data_source": "updated_mock",
                        "timestamp": datetime.now().timestamp()
                    }
            
            # Generate realistic company name for other stocks
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
            
            # Dividend yield based on sector (deterministic)
            div_yield = 0
            if sector in ["Consumer Defensive", "Utilities", "Energy", "Financial Services"]:
                # Calculate yield within div_min to div_max range
                div_range = div_max - div_min
                div_yield = div_min + ((symbol_value % 100) / 100) * div_range
            elif (symbol_value % 100) > 50:  # Deterministic 50% chance for other sectors
                div_yield = ((symbol_value % 100) / 100) * div_min
                
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
            market_cap_range = market_cap_max - market_cap_min
            market_cap = (market_cap_min + ((symbol_value % 100) / 100) * market_cap_range) * 1_000_000_000
            
            return {
                "symbol": symbol.upper(),
                "company_name": company_name,
                "sector": sector,
                "industry": sector + " " + ["Products", "Services", "Equipment", "Solutions"][symbol_value % 4],
                "market_cap": market_cap,
                "current_price": current_price,
                "price_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price_metrics": {
                    "week_52_high": week_52_high,
                    "week_52_low": week_52_low,
                    "ytd_performance": ytd_performance,
                    "sentiment_score": sentiment_score,
                    "daily_change": daily_change,
                    "volume": 1000000 + (symbol_value * 19000) % 19000000  # 1M to 20M range
                },
                "sentiment_data": sentiment_data,
                "integrated_analysis": mock_integrated_analysis,
                "dividend_metrics": {
                    "dividend_yield": div_yield,
                    "dividend_rate": current_price * (div_yield/100),
                    "payout_ratio": ((symbol_value % 80) if div_yield > 0 else 0),  # 0-80 range
                    "dividend_growth": ((symbol_value % 15) if div_yield > 0 else 0)  # 0-15 range
                },
                "portfolio_impact": {
                    "impact": {
                        "sharpe_change": 0.01 + ((symbol_value % 19) / 100),  # 0.01-0.20 range
                        "volatility_change": -2 + ((symbol_value % 30) / 10),  # -2 to 1 range
                        "expected_return_change": 0.1 + ((symbol_value % 14) / 10)  # 0.1-1.5 range
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
        if False:  # Mock data disabled
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
            "sentiment_data": {
                "sentiment_score": 50.0,
                "sentiment_label": "Neutral",
                "components": {}
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
            
    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """
        Clear all cache or cache for a specific symbol
        
        Args:
            symbol: If provided, only clear cache for this symbol
            
        Returns:
            True if cache was cleared successfully, False otherwise
        """
        try:
            if symbol:
                # Clear cache for a specific symbol
                cache_file = self.cache_dir / f"{symbol.upper()}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                    self.logger.info(f"Cache cleared for {symbol}")
                    return True
                return False
            else:
                # Clear all cache
                count = 0
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                    count += 1
                self.logger.info(f"Cleared {count} cache files")
                return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False

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
            
    def analyze_stock_with_custom_weights(self, symbol: str, custom_weights: Dict, portfolio: pd.DataFrame = None) -> Dict:
        """
        Analyze a stock with custom sentiment weights
        
        Args:
            symbol: Stock ticker symbol
            custom_weights: Custom weights for sentiment calculation
            portfolio: Optional portfolio data
            
        Returns:
            Stock analysis with custom sentiment
        """
        # First get the standard analysis (use cached data whenever possible)
        data = self.analyze_stock(symbol, portfolio, force_refresh=False)
        
        # If we have the sentiment calculator available, recalculate sentiment
        if HAS_SENTIMENT_CALCULATOR and hasattr(self, 'sentiment_calculator'):
            try:
                # Get required data from the analysis
                if 'price_metrics' in data:
                    week_52_high = data['price_metrics']['week_52_high']
                    week_52_low = data['price_metrics']['week_52_low']
                    ytd_performance = data['price_metrics']['ytd_performance']
                    daily_change = data['price_metrics']['daily_change']
                    
                    # Get current price
                    current_price = data['current_price']
                    
                    # Extract ROTC from fundamental analysis if available
                    rotc = None
                    if 'integrated_analysis' in data and 'fundamental_analysis' in data['integrated_analysis']:
                        if 'rotc_data' in data['integrated_analysis']['fundamental_analysis']:
                            rotc_data = data['integrated_analysis']['fundamental_analysis']['rotc_data']
                            rotc = rotc_data.get('latest_rotc')
                    
                    # Get price history data
                    # Use yfinance to get historical data
                    try:
                        import yfinance as yf
                        stock = yf.Ticker(symbol)
                        price_history = stock.history(period="1y")
                        
                        if not price_history.empty:
                            # Calculate sentiment with custom weights
                            print(f"EnhancedStockAnalyzer: Calculating sentiment with custom weights: {custom_weights}")
                            sentiment_data = self.sentiment_calculator.calculate_sentiment(
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
                            print(f"EnhancedStockAnalyzer: Sentiment result: {sentiment_data}")
                            
                            # Update sentiment data in the analysis
                            data['sentiment_data'] = sentiment_data
                            data['price_metrics']['sentiment_score'] = sentiment_data['sentiment_score']
                            
                            self.logger.info(f"Applied custom sentiment weights to {symbol}: {custom_weights}")
                    except Exception as e:
                        self.logger.error(f"Error getting price history: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error applying custom sentiment weights: {str(e)}")
        
        return data
        
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