#!/usr/bin/env python

"""
Integration script for the EnhancedStockAnalyzer.

This script shows how to:
1. Use the enhanced analyzer in place of the original StockAnalyzer
2. Access the new price metrics and sentiment data
3. Display the information in the UI

Usage:
  python use_enhanced_analyzer.py
"""

import logging
import sys
import os
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Demonstrate how to integrate the EnhancedStockAnalyzer.
    """
    print("=== Enhanced Stock Analyzer Integration Guide ===")
    print("\nThis script explains how to integrate the new sentiment analysis:")
    
    print("\n1. Replace StockAnalyzer with EnhancedStockAnalyzer")
    print("   In your main application (app.py or server.py), update the import:")
    print("   from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer")
    
    print("\n2. Replace instances of StockAnalyzer with EnhancedStockAnalyzer:")
    print("   # Old code")
    print("   analyzer = StockAnalyzer()")
    print("   # New code")
    print("   analyzer = EnhancedStockAnalyzer()")
    
    print("\n3. Access new price metrics in your routes/views:")
    print("   # The data structure already contains the new fields:")
    print("   result = analyzer.analyze_stock(symbol)")
    print("   # Access new metrics:")
    print("   price_metrics = result.get('price_metrics', {})")
    print("   week_52_high = price_metrics.get('week_52_high', 0)")
    print("   week_52_low = price_metrics.get('week_52_low', 0)")
    print("   ytd_performance = price_metrics.get('ytd_performance', 0)")
    print("   sentiment_score = price_metrics.get('sentiment_score', 50)")
    
    print("\n4. Integration with the app:")
    print("   # The template is already updated to show these fields")
    print("   # Just ensure you pass the full result to the template:")
    print("   return render_template('analysis.html', results=result)")
    
    print("\nTesting the Enhanced Analyzer with a sample stock:")
    try:
        # Create the enhanced analyzer
        analyzer = EnhancedStockAnalyzer()
        
        # Analyze a test stock
        symbol = "AAPL" if len(sys.argv) <= 1 else sys.argv[1]
        result = analyzer.analyze_stock(symbol)
        
        # Display key information
        print(f"\nCompany: {result['company_name']}")
        print(f"Current Price: ${result['current_price']:.2f}")
        
        # Show price metrics
        if 'price_metrics' in result:
            print("\nNew Price Metrics:")
            price_metrics = result['price_metrics']
            print(f"  52-Week High: ${price_metrics.get('week_52_high', 0):.2f}")
            print(f"  52-Week Low: ${price_metrics.get('week_52_low', 0):.2f}")
            print(f"  YTD Performance: {price_metrics.get('ytd_performance', 0):.2f}%")
            print(f"  Sentiment Score: {price_metrics.get('sentiment_score', 50):.1f}/100")
        
        # Show sentiment component contribution
        if 'sentiment_data' in result and 'components' in result['sentiment_data']:
            print("\nSentiment Components:")
            components = result['sentiment_data']['components']
            for component, data in components.items():
                print(f"  {component}: {data['contribution']:.1f} points")
        
        print("\nIntegration complete! The enhanced analyzer is working properly.")
        
    except Exception as e:
        logger.error(f"Error testing enhanced analyzer: {str(e)}")
        print(f"\nError testing enhanced analyzer: {str(e)}")
        print("Please check your implementation and try again.")

if __name__ == "__main__":
    main()