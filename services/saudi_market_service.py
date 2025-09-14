"""
Saudi Market Service
TwelveData API integration for Saudi Arabian stock market (Tadawul)
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from flask import current_app
from .api_client import UnifiedAPIClient
from monitoring.performance import monitor_api_call, metrics_collector

logger = logging.getLogger(__name__)

class SaudiMarketService:
    """Service for accessing Saudi Arabian stock market data via TwelveData API"""
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None):
        self.api_client = api_client or UnifiedAPIClient()
        self.base_url = "https://api.twelvedata.com"
        self.market_code = "TADAWUL"
        self.currency = "SAR"
        
        # Saudi market trading hours (Riyadh timezone)
        self.market_hours = {
            'open': '10:00',
            'close': '15:00',
            'timezone': 'Asia/Riyadh'
        }
        
        # Common Saudi stock sectors
        self.sectors = {
            'banks': 'Banking',
            'petrochemical': 'Petrochemical Industries',
            'cement': 'Cement',
            'retail': 'Retail',
            'telecom': 'Telecommunication Services',
            'insurance': 'Insurance',
            'energy': 'Energy & Utilities',
            'real_estate': 'Real Estate Development',
            'transport': 'Transport',
            'media': 'Media and Entertainment',
            'pharma': 'Pharmaceuticals',
            'agriculture': 'Agriculture & Food Industries'
        }
    
    @monitor_api_call('twelvedata')
    def get_api_key(self) -> str:
        """Get TwelveData API key"""
        # Production API key for Saudi market data
        return "71cdbb03b46645628e8416eeb4836c99"
    
    @monitor_api_call('twelvedata')
    def get_stock_data(self, symbol: str, period: str = "1day", 
                      outputsize: int = 30) -> Dict[str, Any]:
        """
        Get Saudi stock data from TwelveData API
        
        Args:
            symbol: Saudi stock symbol (e.g., "1180" for Al Rajhi Bank)
            period: Data period (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
            outputsize: Number of data points to retrieve (max 5000)
        """
        try:
            api_key = self.get_api_key()
            
            # Format symbol for Saudi market
            formatted_symbol = self._format_saudi_symbol(symbol)
            
            params = {
                'symbol': formatted_symbol,
                'interval': period,
                'outputsize': outputsize,
                'apikey': api_key,
                'format': 'JSON',
                'country': 'Saudi Arabia',
                'exchange': 'TADAWUL'
            }
            
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'values' not in data:
                logger.warning(f"No time series data for Saudi symbol {symbol}: {data}")
                return self._get_fallback_data(symbol)
            
            # Process and format data
            processed_data = self._process_time_series_data(data, symbol)
            
            # Add Saudi market specific information
            processed_data['market'] = 'Saudi Arabia'
            processed_data['currency'] = self.currency
            processed_data['exchange'] = self.market_code
            processed_data['trading_hours'] = self.market_hours
            
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TwelveData API request failed for {symbol}: {str(e)}")
            return self._get_fallback_data(symbol)
        except Exception as e:
            logger.error(f"Error getting Saudi stock data for {symbol}: {str(e)}")
            return self._get_fallback_data(symbol)
    
    @monitor_api_call('twelvedata')
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """Get real-time price for Saudi stock"""
        try:
            api_key = self.get_api_key()
            formatted_symbol = self._format_saudi_symbol(symbol)
            
            params = {
                'symbol': formatted_symbol,
                'apikey': api_key,
                'country': 'Saudi Arabia'
            }
            
            response = requests.get(f"{self.base_url}/price", params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'price' not in data:
                logger.warning(f"No price data for Saudi symbol {symbol}: {data}")
                return {'error': 'No price data available'}
            
            return {
                'symbol': symbol,
                'price': float(data['price']),
                'currency': self.currency,
                'timestamp': datetime.now().isoformat(),
                'market': 'Saudi Arabia',
                'source': 'TwelveData'
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time price for Saudi symbol {symbol}: {str(e)}")
            return {'error': str(e)}
    
    @monitor_api_call('twelvedata')
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile for Saudi stock"""
        try:
            api_key = self.get_api_key()
            formatted_symbol = self._format_saudi_symbol(symbol)
            
            params = {
                'symbol': formatted_symbol,
                'apikey': api_key,
                'country': 'Saudi Arabia'
            }
            
            response = requests.get(f"{self.base_url}/profile", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Add Saudi market context
            if isinstance(data, dict):
                data['market'] = 'Saudi Arabia'
                data['currency'] = self.currency
                data['exchange'] = self.market_code
                
                # Map sector if available
                if 'sector' in data:
                    data['saudi_sector'] = self._map_sector(data['sector'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting company profile for Saudi symbol {symbol}: {str(e)}")
            return {'error': str(e), 'symbol': symbol}
    
    @monitor_api_call('twelvedata')
    def get_market_movers(self, direction: str = 'gainers') -> Dict[str, Any]:
        """
        Get Saudi market movers (gainers/losers)
        
        Args:
            direction: 'gainers' or 'losers'
        """
        try:
            api_key = self.get_api_key()
            
            params = {
                'country': 'Saudi Arabia',
                'apikey': api_key,
                'dp': 2  # Decimal places
            }
            
            endpoint = 'gainers' if direction == 'gainers' else 'losers'
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Add market context
            result = {
                'market': 'Saudi Arabia',
                'currency': self.currency,
                'direction': direction,
                'timestamp': datetime.now().isoformat(),
                'data': data if isinstance(data, list) else data.get('values', [])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Saudi market {direction}: {str(e)}")
            return {'error': str(e), 'market': 'Saudi Arabia', 'direction': direction}
    
    def get_saudi_indices(self) -> Dict[str, Any]:
        """Get major Saudi stock indices"""
        indices = {
            'TASI': 'Tadawul All Share Index',
            'NOMU': 'Nomu Parallel Market Index'
        }
        
        results = {}
        
        for index_code, index_name in indices.items():
            try:
                data = self.get_stock_data(index_code, period="1day", outputsize=1)
                results[index_code] = {
                    'name': index_name,
                    'data': data,
                    'market': 'Saudi Arabia'
                }
            except Exception as e:
                logger.error(f"Error getting Saudi index {index_code}: {str(e)}")
                results[index_code] = {
                    'name': index_name,
                    'error': str(e)
                }
        
        return {
            'indices': results,
            'market': 'Saudi Arabia',
            'timestamp': datetime.now().isoformat()
        }
    
    def convert_sar_to_usd(self, sar_amount: float) -> Dict[str, Any]:
        """Convert Saudi Riyal to USD using current exchange rate"""
        try:
            api_key = self.get_api_key()
            
            params = {
                'symbol': 'SAR/USD',
                'apikey': api_key
            }
            
            response = requests.get(f"{self.base_url}/exchange_rate", params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'rate' in data:
                exchange_rate = float(data['rate'])
                usd_amount = sar_amount * exchange_rate
                
                return {
                    'sar_amount': sar_amount,
                    'usd_amount': round(usd_amount, 2),
                    'exchange_rate': exchange_rate,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'TwelveData'
                }
            else:
                # Fallback to approximate rate
                approximate_rate = 0.27  # Approximate SAR to USD
                return {
                    'sar_amount': sar_amount,
                    'usd_amount': round(sar_amount * approximate_rate, 2),
                    'exchange_rate': approximate_rate,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Approximate',
                    'note': 'Using approximate exchange rate'
                }
                
        except Exception as e:
            logger.error(f"Error converting SAR to USD: {str(e)}")
            # Fallback conversion
            approximate_rate = 0.27
            return {
                'sar_amount': sar_amount,
                'usd_amount': round(sar_amount * approximate_rate, 2),
                'exchange_rate': approximate_rate,
                'error': str(e),
                'source': 'Fallback'
            }
    
    def _format_saudi_symbol(self, symbol: str) -> str:
        """Format symbol for Saudi market (TwelveData format)"""
        # Remove any existing suffixes
        clean_symbol = symbol.replace('.SR', '').replace('.SA', '')
        
        # TwelveData uses symbol.SR format for Saudi stocks
        return f"{clean_symbol}.SR"
    
    def _process_time_series_data(self, raw_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Process time series data from TwelveData"""
        try:
            values = raw_data.get('values', [])
            meta = raw_data.get('meta', {})
            
            if not values:
                return {'error': 'No time series data available'}
            
            # Get latest data point
            latest = values[0] if values else {}
            
            processed = {
                'symbol': symbol,
                'current_price': float(latest.get('close', 0)),
                'open': float(latest.get('open', 0)),
                'high': float(latest.get('high', 0)),
                'low': float(latest.get('low', 0)),
                'volume': int(latest.get('volume', 0)),
                'timestamp': latest.get('datetime', datetime.now().isoformat()),
                'currency': self.currency,
                'data_points': len(values),
                'meta': meta
            }
            
            # Calculate basic metrics if we have multiple data points
            if len(values) > 1:
                prev_close = float(values[1].get('close', 0))
                if prev_close > 0:
                    change = processed['current_price'] - prev_close
                    change_percent = (change / prev_close) * 100
                    
                    processed['change'] = round(change, 2)
                    processed['change_percent'] = round(change_percent, 2)
            
            # Store historical data
            processed['historical_data'] = values[:30]  # Last 30 data points
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing time series data for {symbol}: {str(e)}")
            return {'error': f'Data processing failed: {str(e)}'}
    
    def _map_sector(self, sector: str) -> str:
        """Map international sector to Saudi market sector"""
        sector_lower = sector.lower()
        
        for key, saudi_sector in self.sectors.items():
            if key in sector_lower or saudi_sector.lower() in sector_lower:
                return saudi_sector
        
        return sector  # Return original if no mapping found
    
    def _get_fallback_data(self, symbol: str) -> Dict[str, Any]:
        """Get fallback data when TwelveData fails"""
        return {
            'symbol': symbol,
            'error': 'TwelveData API unavailable',
            'market': 'Saudi Arabia',
            'currency': self.currency,
            'fallback': True,
            'timestamp': datetime.now().isoformat(),
            'message': 'Using fallback data source or cached data'
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get Saudi market status (open/closed)"""
        try:
            # Simple market status based on time
            # In production, you'd get this from the API
            now = datetime.now()
            
            # Simplified logic - Saudi market is typically closed on Friday and Saturday
            is_weekend = now.weekday() in [4, 5]  # Friday, Saturday
            
            # Trading hours: 10:00 - 15:00 Riyadh time
            is_trading_hours = 10 <= now.hour < 15 and not is_weekend
            
            return {
                'market': 'Saudi Arabia',
                'exchange': self.market_code,
                'is_open': is_trading_hours,
                'is_weekend': is_weekend,
                'current_time': now.isoformat(),
                'trading_hours': self.market_hours,
                'timezone': 'UTC'  # Should be converted to Riyadh time in production
            }
            
        except Exception as e:
            logger.error(f"Error getting Saudi market status: {str(e)}")
            return {
                'market': 'Saudi Arabia',
                'error': str(e),
                'is_open': False
            }
    
    def search_saudi_stocks(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for Saudi stocks by name or symbol"""
        try:
            api_key = self.get_api_key()
            
            params = {
                'symbol': query,
                'country': 'Saudi Arabia',
                'apikey': api_key
            }
            
            response = requests.get(f"{self.base_url}/symbol_search", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process search results
            results = data.get('data', [])[:limit] if isinstance(data, dict) else data[:limit]
            
            return {
                'query': query,
                'market': 'Saudi Arabia',
                'results': results,
                'count': len(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching Saudi stocks for '{query}': {str(e)}")
            return {
                'query': query,
                'market': 'Saudi Arabia',
                'error': str(e),
                'results': []
            }