#!/usr/bin/env python
"""
Example of parallel data fetching from multiple sources using the DataComparisonService
"""

import sys
import logging
import time
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the data comparison service
sys.path.append('..')
from data.data_comparison_service import DataComparisonService

def create_alpha_vantage_client():
    """Factory function to create an Alpha Vantage client"""
    try:
        from data.alpha_vantage_client import AlphaVantageClient
        return AlphaVantageClient()
    except ImportError:
        logger.error("Alpha Vantage client not available")
        return None

def create_ib_client():
    """Factory function to create an Interactive Brokers client"""
    try:
        from data.ib_data_client import IBDataClient
        client = IBDataClient()
        # Check if the gateway is running and authenticated
        if client.check_gateway_status() and client.check_authentication():
            return client
        logger.warning("IB Gateway not running or not authenticated")
        return None
    except ImportError:
        logger.error("Interactive Brokers client not available")
        return None

def create_yfinance_analyzer():
    """Factory function to create a YFinance analyzer wrapper"""
    try:
        # This is a wrapper around stock_analyzer.analyze_stock that follows the client pattern
        from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
        analyzer = EnhancedStockAnalyzer()
        
        class YFinanceWrapper:
            def analyze_stock(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
                """Wrapper to make the EnhancedStockAnalyzer conform to the client interface"""
                result = analyzer.analyze_stock(symbol, force_refresh=force_refresh)
                if result:
                    # Add the data source explicitly
                    result['data_source'] = 'yfinance'
                return result
        
        return YFinanceWrapper()
    except ImportError:
        logger.error("YFinance analyzer not available")
        return None

def analyze_stock_parallel(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a stock by fetching data from multiple sources in parallel
    
    Args:
        symbol: Stock ticker symbol to analyze
        
    Returns:
        Dictionary with reconciled stock analysis data or None if all sources fail
    """
    logger.info(f"Starting parallel analysis for {symbol}")
    start_time = time.time()
    
    # Initialize the data comparison service
    data_comparison = DataComparisonService()
    
    # Create factory functions dictionary
    client_factories = {
        'alpha_vantage': create_alpha_vantage_client,
        'interactive_brokers': create_ib_client,
        'yfinance': create_yfinance_analyzer
    }
    
    # Perform parallel fetching and data reconciliation
    result = data_comparison.fetch_multi_source_data(symbol, client_factories)
    
    # Calculate and log the total time taken
    elapsed = time.time() - start_time
    logger.info(f"Total analysis time for {symbol}: {elapsed:.2f} seconds")
    
    return result

def main():
    """Example usage"""
    # List of stocks to analyze
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        # Analyze the stock using parallel fetching
        result = analyze_stock_parallel(symbol)
        
        if result:
            print(f"\nResults for {symbol}:")
            print(f"Selected data source: {result.get('data_source', 'unknown')}")
            print(f"Current price: ${result.get('current_price', 0):.2f}")
            
            # Check if we have reconciliation metadata
            if 'data_reconciliation' in result:
                recon = result['data_reconciliation']
                print("\nData Reconciliation:")
                print(f"Sources used: {', '.join(recon.get('sources', []))}")
                print(f"Primary source: {recon.get('primary_source', 'unknown')}")
                if 'conflict_fields' in recon and recon['conflict_fields']:
                    print(f"Conflicts resolved: {', '.join(recon['conflict_fields'])}")
                else:
                    print("No conflicts detected between sources")
        else:
            print(f"\nNo data available for {symbol}")

if __name__ == "__main__":
    main()