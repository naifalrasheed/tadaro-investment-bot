#!/usr/bin/env python

"""
Script to run the sentiment analysis and update the stock analyzer code.

This script:
1. Demonstrates how to use the sentiment calculator with real stock data
2. Shows how to add the sentiment calculation to the stock_analyzer.py file
"""

import os
import sys
import logging
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime
import random
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create necessary directories
Path("./cache/news_sentiment").mkdir(parents=True, exist_ok=True)

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import sentiment calculator
try:
    from analysis.sentiment_calculator import SentimentCalculator
    HAS_SENTIMENT_CALCULATOR = True
except ImportError:
    HAS_SENTIMENT_CALCULATOR = False
    logger.warning("Sentiment calculator not available")

def analyze_stock_sentiment(symbol: str, verbose: bool = False):
    """Analyze sentiment for a stock symbol using the new weighted model."""
    if not HAS_SENTIMENT_CALCULATOR:
        print("Error: Sentiment calculator not available")
        return None
        
    try:
        print(f"Analyzing sentiment for {symbol}...")
        
        # Get stock data from Yahoo Finance
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Check if we got valid data
        if not info or len(info) < 5:
            print(f"Error: Could not get data for {symbol}")
            return None
            
        current_price = info.get('regularMarketPrice', 0)
        if not current_price:
            current_price = info.get('currentPrice', 0)
        if not current_price:
            print(f"Error: Could not get current price for {symbol}")
            return None
            
        company_name = info.get('longName', symbol)
        print(f"Company: {company_name}")
        print(f"Current Price: ${current_price:.2f}")
        
        # Get historical data for calculations
        year_history = stock.history(period="1y")
        if year_history.empty:
            print(f"Error: No historical data for {symbol}")
            return None
            
        # Calculate required inputs for sentiment analysis
        week_52_high = year_history['High'].max()
        week_52_low = year_history['Low'].min()
        
        # Calculate YTD performance
        ytd_start_date = datetime(datetime.now().year, 1, 1)
        ytd_data = year_history[year_history.index >= ytd_start_date]
        ytd_start_price = float(ytd_data['Open'].iloc[0]) if not ytd_data.empty else 0
        ytd_performance = ((current_price / ytd_start_price) - 1) * 100 if ytd_start_price > 0 else 0
        
        # Get daily change
        daily_change = 0
        if 'regularMarketChangePercent' in info:
            daily_change = info.get('regularMarketChangePercent', 0)
        elif len(year_history) >= 2:
            prev_close = year_history['Close'].iloc[-2]
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
            
        # Print additional info if verbose
        if verbose:
            print(f"52-Week Range: ${week_52_low:.2f} - ${week_52_high:.2f}")
            print(f"Current in Range: {((current_price - week_52_low) / (week_52_high - week_52_low) * 100):.1f}%")
            print(f"YTD Performance: {ytd_performance:.2f}%")
            print(f"Daily Change: {daily_change:.2f}%")
            if rotc is not None:
                print(f"Return on Capital: {rotc:.2f}%")
        
        # Calculate sentiment score
        sentiment_calc = SentimentCalculator()
        sentiment_result = sentiment_calc.calculate_sentiment(
            symbol=symbol,
            price_history=year_history,
            current_price=current_price,
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            ytd_performance=ytd_performance,
            rotc=rotc,
            daily_change=daily_change
        )
        
        # Create data structure that can be added to stock_analyzer response
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'current_price': current_price,
            'price_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'price_metrics': {
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'ytd_performance': ytd_performance,
                'sentiment_score': sentiment_result['sentiment_score'],
                'daily_change': daily_change,
                'volume': info.get('regularMarketVolume', 0)
            },
            'sentiment_data': sentiment_result
        }
        
        # Print sentiment results
        print("\nSentiment Analysis Results:")
        print(f"Overall Sentiment Score: {sentiment_result['sentiment_score']:.1f}/100 - {sentiment_result['sentiment_label']}")
        
        # Print component contributions
        print("\nComponent Contributions:")
        components = sentiment_result['components']
        for component, data in components.items():
            print(f"- {component}: {data['score']:.1f}/100 × {data['weight']:.1f} = {data['contribution']:.1f} points")
            
        return result
    
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        return None

def main():
    """Main function to parse arguments and run analysis."""
    parser = argparse.ArgumentParser(description='Analyze stock sentiment using the new weighted model')
    parser.add_argument('symbols', nargs='*', help='Stock symbols to analyze')
    parser.add_argument('-a', '--all', action='store_true', help='Analyze a preset list of diverse stocks')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show additional details')
    args = parser.parse_args()
    
    # Get symbols to analyze
    symbols = args.symbols
    if args.all or not symbols:
        # Default set of diverse stocks
        symbols = [
            "AAPL",   # Large tech
            "MSFT",   # Large tech
            "TSLA",   # Volatile tech
            "JPM",    # Financial
            "WMT",    # Retail
            "XOM",    # Energy
            "JNJ"     # Healthcare
        ]
    
    print("\n===== Comprehensive Sentiment Analysis =====")
    print("Using the new weighted sentiment model:")
    print(" - 40% Recent price momentum")
    print(" - 20% Position in 52-week range")
    print(" - 20% YTD performance")
    print(" - 10% News/social media mentions")
    print(" - 10% Return on Total Capital (ROTC)")
    print("=" * 50)
    
    # Analyze each symbol
    results = {}
    for symbol in symbols:
        print(f"\n----- Analyzing {symbol} -----")
        result = analyze_stock_sentiment(symbol, args.verbose)
        if result:
            results[symbol] = result
        print("-" * 40)
    
    # Integration instructions
    print("\nINTEGRATION INSTRUCTIONS:")
    print("To integrate this sentiment analysis with your stock_analyzer.py:")
    print("1. Import SentimentCalculator at the top of your file:")
    print("   from analysis.sentiment_calculator import SentimentCalculator")
    print("\n2. Add sentiment calculation in _get_from_yfinance method before returning results:")
    print("""
    # Calculate sentiment
    try:
        sentiment_calculator = SentimentCalculator()
        sentiment_data = sentiment_calculator.calculate_sentiment(
            symbol=symbol,
            price_history=year_history,
            current_price=current_price,
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            ytd_performance=ytd_performance,
            rotc=rotc,
            daily_change=daily_change
        )
        
        # Add to price_metrics
        price_metrics = {
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
            'ytd_performance': ytd_performance,
            'sentiment_score': sentiment_data['sentiment_score'],
            'daily_change': daily_change,
            'volume': info.get('regularMarketVolume', 0)
        }
    except Exception as e:
        self.logger.error(f"Error calculating sentiment: {str(e)}")
        sentiment_data = {"sentiment_score": 50, "sentiment_label": "Neutral"}
        price_metrics = {}
    """)
    
    print("\n3. Add the new data to the returned result:")
    print("""
    return {
        ...
        'price_metrics': price_metrics,
        'sentiment_data': sentiment_data,
        ...
    }
    """)
    
    print("\nYour template is already updated to display this information.")

if __name__ == "__main__":
    main()