#!/usr/bin/env python
"""
Simple test script for Interactive Brokers integration
"""

import os
import sys
import logging
import json
from datetime import datetime
from pprint import pprint

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append('.')

# Import our modules
try:
    from data.ib_data_client import IBDataClient
    from data.data_comparison_service import DataComparisonService
    from data.alpha_vantage_client import AlphaVantageClient
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
    sys.exit(1)

def test_data_sources_integration():
    """Test the integration of multiple data sources"""
    logger.info("Testing data sources integration")
    
    # Initialize all clients
    ib_client = IBDataClient()
    av_client = AlphaVantageClient()
    data_comparison = DataComparisonService()
    
    # Check if IB gateway is running
    if not ib_client.check_gateway_status():
        logger.warning("IB Gateway is not running, will skip IB data")
    
    # Check if authentication is valid
    if not ib_client.check_authentication():
        logger.warning("Not authenticated to IB Gateway, will skip IB data")
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        logger.info(f"Testing {symbol}")
        data_sources = []
        
        # Get data from Alpha Vantage
        try:
            av_data = av_client.analyze_stock(symbol)
            if av_data:
                data_sources.append(av_data)
                logger.info(f"Got Alpha Vantage data for {symbol}")
        except Exception as e:
            logger.error(f"Error getting Alpha Vantage data: {str(e)}")
        
        # Get data from Interactive Brokers (if available)
        if ib_client.check_gateway_status() and ib_client.check_authentication():
            try:
                ib_data = ib_client.analyze_stock(symbol)
                if ib_data:
                    data_sources.append(ib_data)
                    logger.info(f"Got Interactive Brokers data for {symbol}")
            except Exception as e:
                logger.error(f"Error getting Interactive Brokers data: {str(e)}")
        
        # Compare data sources if we have multiple
        if len(data_sources) > 1:
            try:
                result = data_comparison.compare_and_select(data_sources)
                logger.info(f"Reconciled data from {len(data_sources)} sources for {symbol}")
                
                # Check if we have reconciliation data
                if 'data_reconciliation' in result:
                    logger.info(f"Reconciliation data: {result['data_reconciliation']}")
                    
                # Print the selected data source
                logger.info(f"Selected data source: {result.get('data_source')}")
                logger.info(f"Current price: {result.get('current_price')}")
                
                # Save the result to a test file
                os.makedirs('test_output', exist_ok=True)
                with open(f"test_output/{symbol}_comparison.json", 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Saved reconciled data to test_output/{symbol}_comparison.json")
            except Exception as e:
                logger.error(f"Error comparing data sources: {str(e)}")
        else:
            logger.warning(f"Only got {len(data_sources)} data source(s) for {symbol}, skipping comparison")

if __name__ == "__main__":
    test_data_sources_integration()