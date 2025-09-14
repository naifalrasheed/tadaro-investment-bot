"""
Centralized API Client
Manages all external API calls with proper error handling and caching
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Any, Optional
from functools import wraps
import time

# Set up logging
logger = logging.getLogger(__name__)

class APIClientError(Exception):
    """Custom exception for API client errors"""
    pass

class RateLimitError(APIClientError):
    """Exception for rate limit exceeded"""
    pass

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

class CacheManager:
    """Simple in-memory cache for API responses"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, max_age_minutes: int = 30) -> Optional[Any]:
        """Get cached value if it exists and is not expired"""
        if key not in self._cache:
            return None
        
        timestamp = self._timestamps.get(key)
        if not timestamp:
            return None
        
        age = datetime.now() - timestamp
        if age > timedelta(minutes=max_age_minutes):
            # Cache expired
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        """Cache a value with current timestamp"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self):
        """Clear all cached data"""
        self._cache.clear()
        self._timestamps.clear()

class UnifiedAPIClient:
    """
    Centralized API client for all external data sources
    Handles Yahoo Finance, Alpha Vantage, and other APIs with unified interface
    """
    
    def __init__(self, alpha_vantage_key: str = None, news_api_key: str = None, 
                 twelvedata_api_key: str = None):
        self.alpha_vantage_key = alpha_vantage_key
        self.news_api_key = news_api_key
        self.twelvedata_api_key = twelvedata_api_key
        self.cache = CacheManager()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Investment Bot 1.0'})
        
        # Initialize Saudi market service if TwelveData key is available
        self.saudi_service = None
        if twelvedata_api_key:
            try:
                from .saudi_market_service import SaudiMarketService
                self.saudi_service = SaudiMarketService(self)
            except ImportError:
                logger.warning("Saudi market service not available")
    
    @retry_on_failure(max_retries=3, delay=1)
    def get_stock_data(self, symbol: str, period: str = '1y') -> Dict[str, Any]:
        """
        Get comprehensive stock data with fallback strategy
        Primary: Yahoo Finance, Fallback: Alpha Vantage
        """
        cache_key = f"stock_data_{symbol}_{period}"
        cached_data = self.cache.get(cache_key, max_age_minutes=15)
        if cached_data:
            return cached_data
        
        try:
            # Primary source: Yahoo Finance
            data = self._get_yahoo_data(symbol, period)
            if data:
                self.cache.set(cache_key, data)
                return data
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {e}")
        
        try:
            # Fallback: Alpha Vantage
            if self.alpha_vantage_key:
                data = self._get_alpha_vantage_data(symbol)
                if data:
                    self.cache.set(cache_key, data)
                    return data
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        
        raise APIClientError(f"Failed to fetch data for {symbol} from all sources")
    
    def _get_yahoo_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Get data from Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            info = stock.info
            
            if hist.empty:
                raise APIClientError(f"No historical data found for {symbol}")
            
            latest = hist.iloc[-1]
            
            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'history': hist.to_dict('records'),
                'company_name': info.get('longName', symbol),
                'data_source': 'yahoo_finance',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            raise APIClientError(f"Yahoo Finance error: {e}")
    
    def _get_alpha_vantage_data(self, symbol: str) -> Dict[str, Any]:
        """Get data from Alpha Vantage as fallback"""
        if not self.alpha_vantage_key:
            raise APIClientError("Alpha Vantage API key not configured")
        
        # Get daily data
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'Error Message' in data:
            raise APIClientError(f"Alpha Vantage error: {data['Error Message']}")
        
        if 'Note' in data:
            raise RateLimitError("Alpha Vantage rate limit exceeded")
        
        quote = data.get('Global Quote', {})
        if not quote:
            raise APIClientError(f"No data returned for {symbol}")
        
        return {
            'symbol': symbol,
            'price': float(quote.get('05. price', 0)),
            'open': float(quote.get('02. open', 0)),
            'high': float(quote.get('03. high', 0)),
            'low': float(quote.get('04. low', 0)),
            'volume': int(quote.get('06. volume', 0)),
            'change_percent': quote.get('10. change percent', '').replace('%', ''),
            'data_source': 'alpha_vantage',
            'timestamp': datetime.now().isoformat()
        }
    
    @retry_on_failure(max_retries=2, delay=1)
    def get_news_sentiment(self, symbol: str, company_name: str = None) -> Dict[str, Any]:
        """Get news sentiment data"""
        if not self.news_api_key:
            return {'sentiment_score': 0.0, 'articles': [], 'source': 'fallback'}
        
        cache_key = f"news_{symbol}"
        cached_data = self.cache.get(cache_key, max_age_minutes=60)
        if cached_data:
            return cached_data
        
        try:
            # Search for recent news
            query = company_name or symbol
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{query}" AND (stock OR shares OR earnings OR financial)',
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'apiKey': self.news_api_key,
                'pageSize': 10
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Simple sentiment calculation based on keywords
            sentiment_score = self._calculate_sentiment(articles)
            
            result = {
                'sentiment_score': sentiment_score,
                'articles': articles[:5],  # Return top 5 articles
                'total_articles': len(articles),
                'source': 'news_api',
                'timestamp': datetime.now().isoformat()
            }
            
            self.cache.set(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"News API failed for {symbol}: {e}")
            return {
                'sentiment_score': 0.0,
                'articles': [],
                'source': 'fallback_neutral',
                'error': str(e)
            }
    
    def _calculate_sentiment(self, articles) -> float:
        """Simple sentiment analysis based on keywords"""
        if not articles:
            return 0.0
        
        positive_words = ['growth', 'profit', 'gain', 'rise', 'up', 'increase', 'beat', 'strong', 'positive', 'bull']
        negative_words = ['loss', 'fall', 'drop', 'decline', 'down', 'decrease', 'miss', 'weak', 'negative', 'bear']
        
        total_score = 0
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            # Simple scoring: +1 for positive words, -1 for negative words
            article_score = positive_count - negative_count
            total_score += article_score
        
        # Normalize to -1.0 to +1.0 range
        if len(articles) > 0:
            return max(-1.0, min(1.0, total_score / (len(articles) * 3)))
        
        return 0.0
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all configured APIs"""
        results = {
            'yahoo_finance': {'status': 'unknown', 'message': ''},
            'alpha_vantage': {'status': 'unknown', 'message': ''},
            'news_api': {'status': 'unknown', 'message': ''}
        }
        
        # Test Yahoo Finance
        try:
            test_stock = yf.Ticker('AAPL')
            info = test_stock.info
            if info:
                results['yahoo_finance'] = {'status': 'healthy', 'message': 'OK'}
        except Exception as e:
            results['yahoo_finance'] = {'status': 'error', 'message': str(e)}
        
        # Test Alpha Vantage
        if self.alpha_vantage_key:
            try:
                response = self.session.get(
                    f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.alpha_vantage_key}",
                    timeout=10
                )
                if response.status_code == 200:
                    results['alpha_vantage'] = {'status': 'healthy', 'message': 'OK'}
                else:
                    results['alpha_vantage'] = {'status': 'error', 'message': f'HTTP {response.status_code}'}
            except Exception as e:
                results['alpha_vantage'] = {'status': 'error', 'message': str(e)}
        else:
            results['alpha_vantage'] = {'status': 'not_configured', 'message': 'API key not provided'}
        
        # Test News API
        if self.news_api_key:
            try:
                response = self.session.get(
                    f"https://newsapi.org/v2/top-headlines?country=us&apiKey={self.news_api_key}&pageSize=1",
                    timeout=10
                )
                if response.status_code == 200:
                    results['news_api'] = {'status': 'healthy', 'message': 'OK'}
                else:
                    results['news_api'] = {'status': 'error', 'message': f'HTTP {response.status_code}'}
            except Exception as e:
                results['news_api'] = {'status': 'error', 'message': str(e)}
        else:
            results['news_api'] = {'status': 'not_configured', 'message': 'API key not provided'}
        
        # Test TwelveData (Saudi market)
        if self.twelvedata_api_key and self.saudi_service:
            try:
                # Test with a simple API call
                test_result = self.saudi_service.get_real_time_price('1180')  # Al Rajhi Bank
                if 'error' not in test_result:
                    results['twelvedata'] = {'status': 'healthy', 'message': 'OK'}
                else:
                    results['twelvedata'] = {'status': 'error', 'message': test_result.get('error', 'Unknown error')}
            except Exception as e:
                results['twelvedata'] = {'status': 'error', 'message': str(e)}
        else:
            results['twelvedata'] = {'status': 'not_configured', 'message': 'API key not provided'}
        
        return results
    
    # ============================================
    # SAUDI MARKET INTEGRATION METHODS
    # ============================================
    
    def is_saudi_symbol(self, symbol: str) -> bool:
        """Check if symbol is for Saudi Arabian stock market"""
        # Saudi symbols are typically 4-digit numbers or have .SR/.SA suffix
        symbol_clean = symbol.replace('.SR', '').replace('.SA', '')
        return (
            symbol_clean.isdigit() and len(symbol_clean) == 4 or  # 4-digit Saudi stock codes
            '.SR' in symbol.upper() or 
            '.SA' in symbol.upper() or
            symbol.upper() in ['TASI', 'NOMU']  # Saudi indices
        )
    
    def get_saudi_stock_data(self, symbol: str, period: str = '1day') -> Dict[str, Any]:
        """Get Saudi stock data via TwelveData API"""
        if not self.saudi_service:
            return {
                'error': 'Saudi market service not available - TwelveData API key required',
                'symbol': symbol,
                'market': 'Saudi Arabia'
            }
        
        try:
            return self.saudi_service.get_stock_data(symbol, period)
        except Exception as e:
            logger.error(f"Error getting Saudi stock data for {symbol}: {str(e)}")
            return {
                'error': str(e),
                'symbol': symbol,
                'market': 'Saudi Arabia'
            }
    
    def get_enhanced_stock_data(self, symbol: str, period: str = '1y') -> Dict[str, Any]:
        """
        Enhanced stock data that automatically detects and handles Saudi market symbols
        """
        # Check if this is a Saudi market symbol
        if self.is_saudi_symbol(symbol):
            logger.info(f"Detected Saudi market symbol: {symbol}")
            saudi_data = self.get_saudi_stock_data(symbol, period='1day')  # TwelveData uses different period format
            
            # Add market identifier
            saudi_data['detected_market'] = 'Saudi Arabia'
            saudi_data['api_source'] = 'TwelveData'
            
            return saudi_data
        
        # Use regular stock data for non-Saudi symbols
        regular_data = self.get_stock_data(symbol, period)
        regular_data['detected_market'] = 'International'
        regular_data['api_source'] = 'Yahoo Finance / Alpha Vantage'
        
        return regular_data
    
    def get_saudi_market_summary(self) -> Dict[str, Any]:
        """Get Saudi market summary including indices and top movers"""
        if not self.saudi_service:
            return {
                'error': 'Saudi market service not available',
                'market': 'Saudi Arabia'
            }
        
        try:
            summary = {
                'market': 'Saudi Arabia',
                'timestamp': datetime.now().isoformat(),
            }
            
            # Get indices
            indices = self.saudi_service.get_saudi_indices()
            summary['indices'] = indices
            
            # Get market movers
            try:
                gainers = self.saudi_service.get_market_movers('gainers')
                losers = self.saudi_service.get_market_movers('losers')
                
                summary['market_movers'] = {
                    'gainers': gainers,
                    'losers': losers
                }
            except Exception as e:
                logger.warning(f"Could not get Saudi market movers: {str(e)}")
                summary['market_movers'] = {'error': str(e)}
            
            # Get market status
            try:
                status = self.saudi_service.get_market_status()
                summary['market_status'] = status
            except Exception as e:
                logger.warning(f"Could not get Saudi market status: {str(e)}")
                summary['market_status'] = {'error': str(e)}
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting Saudi market summary: {str(e)}")
            return {
                'error': str(e),
                'market': 'Saudi Arabia'
            }
    
    def search_stocks(self, query: str, market: str = 'auto') -> Dict[str, Any]:
        """
        Search for stocks with market detection
        
        Args:
            query: Search query (symbol or company name)
            market: 'auto', 'saudi', 'international'
        """
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results': []
        }
        
        # If Saudi market specified or auto-detected
        if market in ['auto', 'saudi'] and self.saudi_service:
            try:
                saudi_results = self.saudi_service.search_saudi_stocks(query)
                if saudi_results.get('results'):
                    results['saudi_results'] = saudi_results
                    results['results'].extend(saudi_results['results'])
            except Exception as e:
                logger.warning(f"Saudi stock search failed: {str(e)}")
        
        # Add international search here in the future
        # For now, return Saudi results or empty
        
        return results