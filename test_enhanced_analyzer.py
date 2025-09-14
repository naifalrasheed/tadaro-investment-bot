#!/usr/bin/env python

"""
Test script for the enhanced stock analyzer with new sentiment analysis features.
This demonstrates the new price metrics and sentiment score calculation.
"""

import logging
import sys
import os
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from pprint import pprint

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_stock_analyzer(symbol):
    """Test the enhanced stock analyzer with a specific stock symbol."""
    print(f"\n=== Analyzing {symbol} with Enhanced Stock Analyzer ===")
    
    # Create the enhanced analyzer
    analyzer = EnhancedStockAnalyzer()
    
    # Analyze the stock
    result = analyzer.analyze_stock(symbol)
    
    # Display basic info
    print(f"Company: {result['company_name']}")
    print(f"Sector: {result['sector']}")
    print(f"Industry: {result['industry']}")
    print(f"Current Price: ${result['current_price']:.2f}")
    print(f"Price Time: {result['price_time']}")
    print(f"Data Source: {result['data_source']}")
    
    # Display price metrics
    if 'price_metrics' in result:
        print("\n-- Price Metrics --")
        price_metrics = result['price_metrics']
        
        if 'week_52_high' in price_metrics:
            print(f"52-Week High: ${price_metrics['week_52_high']:.2f}")
            
        if 'week_52_low' in price_metrics:
            print(f"52-Week Low: ${price_metrics['week_52_low']:.2f}")
            
        if 'ytd_performance' in price_metrics:
            ytd = price_metrics['ytd_performance']
            print(f"YTD Performance: {ytd:.2f}% {'▲' if ytd >= 0 else '▼'}")
            
        if 'daily_change' in price_metrics:
            daily = price_metrics['daily_change']
            print(f"Daily Change: {daily:.2f}% {'▲' if daily >= 0 else '▼'}")
            
        if 'sentiment_score' in price_metrics:
            score = price_metrics['sentiment_score']
            sentiment_label = "Bullish" if score > 70 else "Neutral" if score > 40 else "Bearish"
            print(f"Sentiment Score: {score:.1f}/100 ({sentiment_label})")
    
    # Display sentiment details if available
    if 'sentiment_data' in result and 'components' in result['sentiment_data']:
        print("\n-- Sentiment Components --")
        components = result['sentiment_data']['components']
        
        for component, data in components.items():
            print(f"{component}: {data['score']:.1f}/100 × {data['weight']} = {data['contribution']:.1f} points")
    
    # Display recommendation
    if 'integrated_analysis' in result and 'recommendation' in result['integrated_analysis']:
        print("\n-- Recommendation --")
        recommendation = result['integrated_analysis']['recommendation']
        print(f"Action: {recommendation['action']}")
        
        if 'reasoning' in recommendation:
            print("Reasoning:")
            for reason in recommendation['reasoning']:
                print(f"  • {reason}")
        
        if 'integrated_score' in result['integrated_analysis']:
            print(f"Integrated Score: {result['integrated_analysis']['integrated_score']:.1f}/100")
    
    print("\n" + "=" * 60)
    
    return result

if __name__ == "__main__":
    # Get symbols to analyze
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
    else:
        # Default symbols to test
        symbols = ["AAPL", "MSFT", "TSLA", "JPM", "XOM"]
    
    # Test each symbol
    for symbol in symbols:
        test_stock_analyzer(symbol)