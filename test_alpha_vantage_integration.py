#!/usr/bin/env python
"""
Test script for Alpha Vantage integration with the investment bot.
Run this script to verify that the Alpha Vantage client is working correctly.
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
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
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from data.alpha_vantage_client import AlphaVantageClient

def test_direct_alpha_vantage():
    """Test the Alpha Vantage client directly"""
    logger.info("Testing direct Alpha Vantage client")
    client = AlphaVantageClient()
    
    # Test stocks
    symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL']
    
    for symbol in symbols:
        logger.info(f"Testing {symbol}...")
        
        # Test get_quote
        quote = client.get_quote(symbol)
        logger.info(f"{symbol} quote: ${quote['price']} ({quote['change_percent']}%)")
        
        # Test get_daily_time_series
        daily = client.get_daily_time_series(symbol)
        if daily and 'data' in daily:
            logger.info(f"{symbol} daily data: {len(daily['data'])} days")
            logger.info(f"Latest day: {daily['data'][0]['date']} - Close: {daily['data'][0]['close']}")
        
        # Test get_company_overview
        overview = client.get_company_overview(symbol)
        if overview:
            logger.info(f"{symbol} ({overview.get('Name')})")
            logger.info(f"Sector: {overview.get('Sector')}, Industry: {overview.get('Industry')}")
            logger.info(f"Market Cap: ${float(overview.get('MarketCapitalization', 0))/1000000000:.2f}B")
        
        # Test full analyze_stock
        analysis = client.analyze_stock(symbol)
        logger.info(f"{symbol} full analysis complete")
        logger.info(f"Current Price: ${analysis['current_price']}")
        logger.info(f"52-Week High: ${analysis['price_metrics']['week_52_high']}")
        logger.info(f"52-Week Low: ${analysis['price_metrics']['week_52_low']}")
        logger.info(f"Recommendation: {analysis['integrated_analysis']['recommendation']['action']}")
        
        # Save analysis to file for inspection
        os.makedirs('test_output', exist_ok=True)
        with open(f"test_output/{symbol}_alpha_vantage_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Saved {symbol} analysis to test_output/{symbol}_alpha_vantage_analysis.json")
        logger.info("-" * 50)

def test_enhanced_analyzer_integration():
    """Test the Enhanced Stock Analyzer with Alpha Vantage integration"""
    logger.info("Testing Enhanced Stock Analyzer with Alpha Vantage integration")
    analyzer = EnhancedStockAnalyzer()
    
    # Test stocks
    symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL']
    
    for symbol in symbols:
        logger.info(f"Testing {symbol} with EnhancedStockAnalyzer...")
        
        # First, clear cache to force fresh data
        analyzer.clear_cache(symbol)
        logger.info(f"Cleared cache for {symbol}")
        
        # Get analysis with force_refresh=True
        analysis = analyzer.analyze_stock(symbol, force_refresh=True)
        
        logger.info(f"{symbol} analysis complete from data source: {analysis.get('data_source', 'unknown')}")
        logger.info(f"Current Price: ${analysis['current_price']}")
        logger.info(f"52-Week High: ${analysis['price_metrics']['week_52_high']}")
        logger.info(f"52-Week Low: ${analysis['price_metrics']['week_52_low']}")
        
        if 'integrated_analysis' in analysis and 'recommendation' in analysis['integrated_analysis']:
            logger.info(f"Recommendation: {analysis['integrated_analysis']['recommendation']['action']}")
        
        # Save analysis to file for inspection
        os.makedirs('test_output', exist_ok=True)
        with open(f"test_output/{symbol}_enhanced_analyzer_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Saved {symbol} analysis to test_output/{symbol}_enhanced_analyzer_analysis.json")
        logger.info("-" * 50)

if __name__ == "__main__":
    # Create test output directory
    os.makedirs('test_output', exist_ok=True)
    
    # Test both modes
    logger.info("Starting Alpha Vantage integration tests")
    
    try:
        test_direct_alpha_vantage()
    except Exception as e:
        logger.error(f"Error in direct Alpha Vantage test: {str(e)}")
    
    try:
        test_enhanced_analyzer_integration()
    except Exception as e:
        logger.error(f"Error in Enhanced Analyzer integration test: {str(e)}")
    
    logger.info("Tests completed. Check test_output directory for results.")