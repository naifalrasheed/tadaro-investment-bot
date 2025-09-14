#!/usr/bin/env python

"""
Test script for the news sentiment analyzer.
This demonstrates how to use the API integration with fallback to simulated data.
"""

import os
import json
import logging
from data.news_sentiment_analyzer import NewsSentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sentiment_analyzer():
    """Test the sentiment analyzer with a few sample stocks."""
    # Create the analyzer
    analyzer = NewsSentimentAnalyzer()
    
    # Test stocks
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "XOM", "JPM", "UNKNOWN"]
    
    print("\n===== News and Social Media Sentiment Analysis =====\n")
    
    # Check if API keys are set
    if not analyzer.alpha_vantage_key:
        print("No Alpha Vantage API key found in environment variables.")
        print("Set ALPHA_VANTAGE_API_KEY to enable live data.")
        print("Using simulated data for demonstration.\n")
    
    if not analyzer.twitter_bearer_token:
        print("No Twitter API credentials found in environment variables.")
        print("Set TWITTER_BEARER_TOKEN to enable social media data.")
        print("Using simulated data for demonstration.\n")
    
    # Test with each symbol
    for symbol in test_symbols:
        print(f"\n----- Testing sentiment for {symbol} -----")
        
        # Get sentiment data
        sentiment_data = analyzer.get_sentiment_data(symbol)
        
        # Display results
        sources = ", ".join(sentiment_data.get("sentiment_sources", ["unknown"]))
        print(f"Data sources: {sources}")
        print(f"Overall sentiment score: {sentiment_data['sentiment_score']:.1f}/100")
        
        if sentiment_data["sentiment_score"] > 70:
            sentiment_label = "Bullish 📈"
        elif sentiment_data["sentiment_score"] > 40:
            sentiment_label = "Neutral ↔️"
        else:
            sentiment_label = "Bearish 📉"
        
        print(f"Sentiment classification: {sentiment_label}")
        print(f"Mention volume: {sentiment_data['mention_volume']:.1f}/100")
        print(f"News mentions: {sentiment_data['news_count']}")
        print(f"Social media mentions: {sentiment_data['social_count']}")
        
        # Show sample articles if available
        if sentiment_data.get("sentiment_articles"):
            print("\nRecent news headlines:")
            for i, article in enumerate(sentiment_data["sentiment_articles"][:3], 1):
                print(f"{i}. {article['title']}")
                if 'sentiment' in article:
                    sentiment_val = article['sentiment']
                    sentiment_emoji = "🟢" if sentiment_val > 0.2 else "🟡" if sentiment_val > -0.2 else "🔴"
                    print(f"   Sentiment: {sentiment_emoji} ({sentiment_val:.2f})")
        
        print("\n")

if __name__ == "__main__":
    try:
        test_sentiment_analyzer()
    except Exception as e:
        logger.error(f"Error running sentiment test: {str(e)}")
        raise