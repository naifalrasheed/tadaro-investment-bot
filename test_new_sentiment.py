#!/usr/bin/env python

"""
Test script for the new sentiment analysis system that combines news/social mentions 
with technical indicators to generate a comprehensive sentiment score.

The score is composed of:
- Price momentum (40%)
- 52-week range position (20%)
- YTD performance (20%)
- News/social media mentions (10%)
- ROTC (Return on Total Capital) (10%)
"""

import os
import logging
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

# Import our sentiment calculator
from analysis.sentiment_calculator import SentimentCalculator

def demo_sentiment_analysis(symbols):
    """Run sentiment analysis on a list of stock symbols."""
    print("\n===== Comprehensive Sentiment Analysis Demo =====")
    print("Using the new weighted sentiment model:")
    print(" - 40% Recent price momentum")
    print(" - 20% Position in 52-week range")
    print(" - 20% YTD performance")
    print(" - 10% News/social media mentions")
    print(" - 10% Return on Total Capital (ROTC)")
    print("=" * 50)
    
    # Initialize sentiment calculator
    sentiment_calc = SentimentCalculator()
    
    for symbol in symbols:
        print(f"\n----- Analyzing {symbol} -----")
        
        try:
            # Get stock data from Yahoo Finance
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Check if we got valid data
            if not info or len(info) < 5:
                print(f"Error: Could not get data for {symbol}")
                continue
                
            current_price = info.get('regularMarketPrice', 0)
            if not current_price:
                current_price = info.get('currentPrice', 0)
            if not current_price:
                print(f"Error: Could not get current price for {symbol}")
                continue
                
            print(f"Company: {info.get('longName', symbol)}")
            print(f"Current Price: ${current_price:.2f}")
            
            # Get historical data for calculations
            year_history = stock.history(period="1y")
            if year_history.empty:
                print(f"Error: No historical data for {symbol}")
                continue
                
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
                
            # Print some of the components
            print(f"52-Week Range: ${week_52_low:.2f} - ${week_52_high:.2f}")
            print(f"Current in Range: {((current_price - week_52_low) / (week_52_high - week_52_low) * 100):.1f}%")
            print(f"YTD Performance: {ytd_performance:.2f}%")
            print(f"Daily Change: {daily_change:.2f}%")
            if rotc is not None:
                print(f"Return on Capital: {rotc:.2f}%")
            
            # Calculate sentiment score
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
            
            # Print sentiment results
            print("\nSentiment Analysis Results:")
            print(f"Overall Sentiment Score: {sentiment_result['sentiment_score']:.1f}/100 - {sentiment_result['sentiment_label']}")
            
            # Print component contributions
            print("\nComponent Contributions:")
            components = sentiment_result['components']
            for component, data in components.items():
                print(f"- {component}: {data['score']:.1f}/100 × {data['weight']:.1f} = {data['contribution']:.1f} points")
                
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
            
        print("-" * 40)

if __name__ == "__main__":
    # Test with a variety of stocks
    test_symbols = [
        "AAPL",   # Large tech
        "MSFT",   # Large tech
        "TSLA",   # Volatile tech
        "JPM",    # Financial
        "WMT",    # Retail
        "XOM",    # Energy
        "JNJ"     # Healthcare
    ]
    
    # Run demo
    demo_sentiment_analysis(test_symbols)