# src/data/news_sentiment_analyzer.py

import os
import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

class NewsSentimentAnalyzer:
    """
    Class to fetch and analyze news and social media sentiment for stocks.
    Integrates with multiple data sources:
    1. Alpha Vantage News Sentiment API (primary financial news source)
    2. NewsAPI.org (broader news coverage)
    3. Twitter API (social media mentions)
    4. Fallback to simulated data when APIs are unavailable
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Import Config for API keys
        try:
            from config import DevelopmentConfig as Config
            self.alpha_vantage_key = Config.ALPHA_VANTAGE_API_KEY
            self.news_api_key = Config.NEWS_API_KEY
            self.twitter_api_key = os.environ.get('TWITTER_API_KEY', '')
            self.twitter_api_secret = os.environ.get('TWITTER_API_SECRET', '')
            self.twitter_bearer_token = os.environ.get('TWITTER_BEARER_TOKEN', '')
        except ImportError:
            # Fallback to environment variables
            self.alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
            self.news_api_key = os.environ.get('NEWS_API_KEY', '')
            self.twitter_api_key = os.environ.get('TWITTER_API_KEY', '')
            self.twitter_api_secret = os.environ.get('TWITTER_API_SECRET', '')
            self.twitter_bearer_token = os.environ.get('TWITTER_BEARER_TOKEN', '')
        
        # Setup cache directory
        self.cache_dir = Path("./cache/news_sentiment")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = 4 * 3600  # 4 hours in seconds (news data becomes stale quickly)
        
        # Track API call times to respect rate limits
        self.last_alpha_vantage_call = 0
        self.last_twitter_call = 0
        self.last_news_api_call = 0
        
        # Define minimum intervals between API calls
        self.min_alpha_vantage_interval = 12.0  # seconds (5 calls per minute) - increased with premium
        self.min_twitter_interval = 3.0  # seconds (20 calls per minute)
        self.min_news_api_interval = 0.5  # seconds (NewsAPI limits vary by plan)

    def get_sentiment_data(self, symbol: str) -> Dict:
        """
        Main method to get comprehensive sentiment data for a stock.
        Returns a standardized sentiment object combining all sources.
        """
        result = {
            'sentiment_score': 50,  # Default neutral score
            'news_sentiment': 0,    # -100 to 100 scale
            'social_sentiment': 0,  # -100 to 100 scale
            'mention_volume': 0,    # Relative scale 0-100
            'news_count': 0,
            'social_count': 0,
            'sentiment_articles': [],
            'sentiment_sources': [],
            'timestamp': datetime.now().timestamp()
        }
        
        try:
            # First check cache
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                self.logger.info(f"Using cached sentiment data for {symbol}")
                return cached_data
            
            # Get news sentiment from Alpha Vantage
            alpha_data = self._get_alpha_vantage_sentiment(symbol)
            
            # Get news from NewsAPI.org
            news_api_data = self._get_news_api_sentiment(symbol)
            
            # Get social sentiment from Twitter
            twitter_data = self._get_twitter_sentiment(symbol)
            
            # Combine data sources
            if alpha_data:
                result['news_sentiment'] = alpha_data['news_sentiment']
                result['news_count'] = alpha_data['news_count']
                result['sentiment_articles'] = alpha_data.get('articles', [])
                result['sentiment_sources'].append('alpha_vantage')
                
            # Add NewsAPI data if available
            if news_api_data:
                # If we already have Alpha Vantage data, combine the sentiment (60% Alpha, 40% NewsAPI)
                if alpha_data:
                    result['news_sentiment'] = (result['news_sentiment'] * 0.6) + (news_api_data['news_sentiment'] * 0.4)
                    result['news_count'] += news_api_data['news_count']
                    # Add additional articles (up to 5 total)
                    current_articles = result['sentiment_articles']
                    additional_articles = news_api_data.get('articles', [])
                    result['sentiment_articles'] = current_articles + additional_articles[:max(0, 5-len(current_articles))]
                else:
                    # Use NewsAPI as primary source
                    result['news_sentiment'] = news_api_data['news_sentiment']
                    result['news_count'] = news_api_data['news_count']
                    result['sentiment_articles'] = news_api_data.get('articles', [])
                
                # Add to sources
                result['sentiment_sources'].append('news_api')
            
            if twitter_data:
                result['social_sentiment'] = twitter_data['social_sentiment']
                result['social_count'] = twitter_data['social_count']
                result['sentiment_sources'].append('twitter')
            
            # Calculate overall mention volume (normalized to 0-100 scale)
            total_mentions = result['news_count'] + result['social_count']
            # Normalize based on typical mention volumes
            # High mention stocks like AAPL might get 100+ mentions daily
            result['mention_volume'] = min(100, (total_mentions / 50) * 100)
            
            # Calculate combined sentiment score (0-100 scale) with configurable weights
            try:
                from config import DevelopmentConfig as Config
                # Get weights for each source
                source_weights = Config.SENTIMENT_SOURCE_WEIGHTS
            except (ImportError, AttributeError):
                # Default weights if config not available
                source_weights = {
                    'alpha_vantage': 0.5,
                    'news_api': 0.3,
                    'twitter': 0.2
                }
                
            # Calculate weighted average based on available sources
            available_sources = result['sentiment_sources']
            if not available_sources:
                combined_sentiment = 0
            else:
                # Normalize weights for available sources
                total_weight = sum(source_weights.get(source, 0) for source in available_sources)
                if total_weight <= 0:
                    total_weight = 1  # Avoid division by zero
                
                weighted_sum = 0
                
                # Add alpha_vantage sentiment if available
                if 'alpha_vantage' in available_sources:
                    weighted_sum += result['news_sentiment'] * (source_weights['alpha_vantage'] / total_weight)
                    
                # Add news_api sentiment if available
                if 'news_api' in available_sources:
                    weighted_sum += result['news_sentiment'] * (source_weights['news_api'] / total_weight)
                    
                # Add twitter sentiment if available
                if 'twitter' in available_sources:
                    weighted_sum += result['social_sentiment'] * (source_weights['twitter'] / total_weight)
                    
                combined_sentiment = weighted_sum
                
            # Convert from -100,100 scale to 0,100 scale
            result['sentiment_score'] = (combined_sentiment + 100) / 2
            
            # Cache the result
            self._save_to_cache(symbol, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment data for {symbol}: {str(e)}")
            # Generate fallback data
            return self._get_fallback_sentiment(symbol)
    
    def _get_alpha_vantage_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get news sentiment data from Alpha Vantage API.
        """
        if not self.alpha_vantage_key:
            self.logger.warning("No Alpha Vantage API key provided")
            return None
            
        try:
            # Respect rate limits
            current_time = time.time()
            time_since_last_call = current_time - self.last_alpha_vantage_call
            
            if time_since_last_call < self.min_alpha_vantage_interval:
                sleep_time = self.min_alpha_vantage_interval - time_since_last_call
                self.logger.debug(f"Sleeping for {sleep_time:.2f}s to respect Alpha Vantage rate limits")
                time.sleep(sleep_time)
            
            # Mark call time
            self.last_alpha_vantage_call = time.time()
            
            # Make API request
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url)
            
            if response.status_code != 200:
                self.logger.warning(f"Alpha Vantage API returned status code {response.status_code}")
                return None
                
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                self.logger.warning(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if "feed" not in data or not data["feed"]:
                self.logger.info(f"No news found for {symbol} in Alpha Vantage")
                return None
            
            # Process the sentiment data
            feed_items = data["feed"]
            
            # Extract relevant ticker sentiment from each article
            ticker_sentiments = []
            articles = []
            
            for item in feed_items:
                # Only include articles explicitly mentioning our symbol
                if "ticker_sentiment" not in item:
                    continue
                    
                for ticker in item["ticker_sentiment"]:
                    if ticker["ticker"] == symbol:
                        # Found sentiment for our symbol
                        sentiment_score = float(ticker["ticker_sentiment_score"])
                        ticker_sentiments.append(sentiment_score)
                        
                        # Add article summary
                        articles.append({
                            "title": item.get("title", ""),
                            "summary": item.get("summary", ""),
                            "source": item.get("source", ""),
                            "url": item.get("url", ""),
                            "time_published": item.get("time_published", ""),
                            "sentiment": sentiment_score
                        })
                        
                        break
            
            # Calculate overall sentiment
            if not ticker_sentiments:
                self.logger.info(f"No sentiment data found for {symbol} in articles")
                return None
                
            # Calculate average sentiment and convert to -100 to 100 scale
            # Alpha Vantage sentiment is -1 to 1 scale
            avg_sentiment = sum(ticker_sentiments) / len(ticker_sentiments)
            scaled_sentiment = avg_sentiment * 100
            
            return {
                "news_sentiment": scaled_sentiment,
                "news_count": len(ticker_sentiments),
                "articles": articles[:5],  # Limit to top 5 articles
                "source": "alpha_vantage"
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching Alpha Vantage sentiment for {symbol}: {str(e)}")
            return None
    
    def _get_news_api_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get news articles and analyze sentiment using NewsAPI.org.
        """
        if not self.news_api_key:
            self.logger.warning("No NewsAPI.org API key provided")
            return None
            
        try:
            # Respect rate limits
            current_time = time.time()
            time_since_last_call = current_time - self.last_news_api_call
            
            if time_since_last_call < self.min_news_api_interval:
                sleep_time = self.min_news_api_interval - time_since_last_call
                self.logger.debug(f"Sleeping for {sleep_time:.2f}s to respect NewsAPI rate limits")
                time.sleep(sleep_time)
            
            # Mark call time
            self.last_news_api_call = time.time()
            
            # Get company name to improve search results
            # This could be enhanced with a proper company name lookup
            company_name = self._get_company_name(symbol)
            
            # Construct query - search for both symbol and company name
            query = f"{symbol} OR {company_name} stock"
            
            # Make API request
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 20,  # Get more articles for better sentiment analysis
                "apiKey": self.news_api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                self.logger.warning(f"NewsAPI returned status code {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            if "articles" not in data or not data["articles"]:
                self.logger.info(f"No news found for {symbol} in NewsAPI")
                return None
            
            articles = data["articles"]
            article_count = len(articles)
            
            # For a full implementation, use a sentiment analysis library like NLTK or TextBlob
            # Here, we'll use a simple keyword-based approach
            positive_keywords = [
                "growth", "profit", "surge", "rise", "gain", "positive", "improvement",
                "outperform", "exceed", "beat", "strong", "upside", "bullish", "opportunity"
            ]
            
            negative_keywords = [
                "loss", "decline", "drop", "fall", "negative", "risk", "concern", "weak",
                "underperform", "miss", "below", "bearish", "downside", "pressure"
            ]
            
            # Calculate sentiment scores for each article
            article_sentiments = []
            processed_articles = []
            
            for article in articles:
                title = article.get("title", "").lower()
                description = article.get("description", "").lower()
                content = article.get("content", "").lower()
                
                # Search for sentiment keywords
                positive_count = 0
                negative_count = 0
                
                # Check title (highest weight)
                for keyword in positive_keywords:
                    if keyword in title:
                        positive_count += 3
                for keyword in negative_keywords:
                    if keyword in title:
                        negative_count += 3
                
                # Check description
                for keyword in positive_keywords:
                    if keyword in description:
                        positive_count += 2
                for keyword in negative_keywords:
                    if keyword in description:
                        negative_count += 2
                
                # Check content
                for keyword in positive_keywords:
                    if keyword in content:
                        positive_count += 1
                for keyword in negative_keywords:
                    if keyword in content:
                        negative_count += 1
                
                # Calculate sentiment for this article (-100 to 100 scale)
                sentiment = 0
                if positive_count > 0 or negative_count > 0:
                    total = positive_count + negative_count
                    sentiment = ((positive_count - negative_count) / total) * 100
                
                article_sentiments.append(sentiment)
                
                # Add to processed articles list
                processed_articles.append({
                    "title": article.get("title", ""),
                    "summary": article.get("description", ""),
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "url": article.get("url", ""),
                    "time_published": article.get("publishedAt", ""),
                    "sentiment": sentiment
                })
            
            # Calculate average sentiment score
            if not article_sentiments:
                self.logger.info(f"No sentiment data found for {symbol} in articles")
                return None
                
            avg_sentiment = sum(article_sentiments) / len(article_sentiments)
            
            # Sort articles by sentiment for the output (most positive first)
            sorted_articles = sorted(processed_articles, key=lambda x: x["sentiment"], reverse=True)
            
            return {
                "news_sentiment": avg_sentiment,
                "news_count": article_count,
                "articles": sorted_articles[:5],  # Top 5 articles
                "source": "news_api"
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching NewsAPI sentiment for {symbol}: {str(e)}")
            return None
    
    def _get_company_name(self, symbol: str) -> str:
        """Helper method to get a company name from a ticker symbol."""
        # Simple lookup for common symbols
        symbol_to_name = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google Alphabet",
            "AMZN": "Amazon",
            "META": "Meta Facebook",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA",
            "JPM": "JPMorgan",
            "JNJ": "Johnson & Johnson",
            "V": "Visa",
            "PG": "Procter & Gamble",
            "DIS": "Disney",
            "HD": "Home Depot",
            "BA": "Boeing",
            "VZ": "Verizon",
            "KO": "Coca Cola",
            "WMT": "Walmart",
            "MCD": "McDonald's"
        }
        
        # Return company name if found, otherwise just return the symbol
        return symbol_to_name.get(symbol.upper(), symbol)
    
    def _get_twitter_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get social media sentiment data from Twitter API.
        """
        if not self.twitter_bearer_token:
            self.logger.warning("No Twitter API credentials provided")
            return None
            
        try:
            # Respect rate limits
            current_time = time.time()
            time_since_last_call = current_time - self.last_twitter_call
            
            if time_since_last_call < self.min_twitter_interval:
                sleep_time = self.min_twitter_interval - time_since_last_call
                self.logger.debug(f"Sleeping for {sleep_time:.2f}s to respect Twitter rate limits")
                time.sleep(sleep_time)
            
            # Mark call time
            self.last_twitter_call = time.time()
            
            # Twitter API v2 endpoint for recent tweets
            url = "https://api.twitter.com/2/tweets/search/recent"
            
            # Search for cashtag of the symbol
            query = f"${symbol} lang:en -is:retweet"
            
            headers = {
                "Authorization": f"Bearer {self.twitter_bearer_token}",
                "User-Agent": "InvestmentBotApp/1.0"
            }
            
            params = {
                "query": query,
                "max_results": 100,  # Maximum allowed
                "tweet.fields": "public_metrics,created_at,entities"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                self.logger.warning(f"Twitter API returned status code {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            if "data" not in data or not data["data"]:
                self.logger.info(f"No tweets found for ${symbol}")
                return None
            
            tweets = data["data"]
            tweet_count = len(tweets)
            
            # Calculate engagement metrics
            total_likes = sum(tweet["public_metrics"]["like_count"] for tweet in tweets)
            total_retweets = sum(tweet["public_metrics"]["retweet_count"] for tweet in tweets)
            total_replies = sum(tweet["public_metrics"]["reply_count"] for tweet in tweets)
            
            # For a real implementation, we would use a sentiment analysis library
            # like VADER or TextBlob to analyze tweet sentiment. For now, we'll use
            # a basic engagement-based proxy for sentiment.
            
            # Calculate sentiment based on engagement (primitive approach)
            # Positive sentiment if likes > retweets + replies (people approve without discussion)
            # Negative sentiment if retweets + replies > likes (high discussion/controversy)
            engagement_ratio = total_likes / max(1, (total_retweets + total_replies))
            
            # Scale to -100 to 100
            # Ratio of 1 = neutral (0)
            # Ratio > 3 = very positive (100)
            # Ratio < 0.33 = very negative (-100)
            if engagement_ratio > 1:
                # Positive sentiment (1 to 3 maps to 0 to 100)
                sentiment_score = min(100, (engagement_ratio - 1) / 2 * 100)
            else:
                # Negative sentiment (1 to 0.33 maps to 0 to -100)
                sentiment_score = max(-100, (engagement_ratio - 1) / (1 - 0.33) * 100)
            
            return {
                "social_sentiment": sentiment_score,
                "social_count": tweet_count,
                "engagement": {
                    "likes": total_likes,
                    "retweets": total_retweets,
                    "replies": total_replies
                },
                "source": "twitter"
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching Twitter sentiment for {symbol}: {str(e)}")
            return None
    
    def _get_fallback_sentiment(self, symbol: str) -> Dict:
        """
        Generate fallback sentiment data when APIs are unavailable.
        Uses deterministic values based on the stock symbol for consistency.
        """
        # List of popular stocks that would have higher mention rates
        popular_stocks = {
            # Tech giants - highest visibility
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            
            # Other high visibility stocks
            "DIS", "NFLX", "INTC", "AMD", "JPM", "BAC", "GS", "V", "MA", 
            "WMT", "TGT", "HD", "MCD", "KO", "PEP", "JNJ", "PFE", "MRNA",
            "XOM", "CVX", "BA", "F", "GM", "T", "VZ", "COIN", "GME", "AMC"
        }
        
        # Tech stocks tend to have more positive sentiment on social media
        tech_stocks = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
                      "NFLX", "INTC", "AMD", "COIN"}
        
        # Generate deterministic values based on the symbol
        symbol_value = sum(ord(c) for c in symbol.upper())
        
        # Base metrics on stock popularity
        if symbol.upper() in popular_stocks:
            if symbol.upper() in tech_stocks:
                # Popular tech stocks - high mentions, generally positive
                news_count = (symbol_value % 35) + 15  # 15-50 range
                social_count = (symbol_value % 450) + 50  # 50-500 range
                news_sentiment = (symbol_value % 60) + 20  # 20-80 range
                social_sentiment = (symbol_value % 60) + 30  # 30-90 range
            else:
                # Other popular stocks - high mentions, mixed sentiment
                news_count = (symbol_value % 30) + 10  # 10-40 range
                social_count = (symbol_value % 270) + 30  # 30-300 range
                news_sentiment = (symbol_value % 100) - 30  # -30 to 70 range
                social_sentiment = (symbol_value % 120) - 40  # -40 to 80 range
        else:
            # Less popular stocks - fewer mentions, more neutral
            news_count = symbol_value % 11  # 0-10 range
            social_count = symbol_value % 51  # 0-50 range
            news_sentiment = (symbol_value % 80) - 20  # -20 to 60 range
            social_sentiment = (symbol_value % 120) - 60  # -60 to 60 range
        
        # Calculate overall mention volume
        total_mentions = news_count + social_count
        mention_volume = min(100, (total_mentions / 50) * 100)
        
        # Calculate combined sentiment
        if news_count > 0 and social_count > 0:
            combined_sentiment = (news_sentiment * 0.6) + (social_sentiment * 0.4)
        elif news_count > 0:
            combined_sentiment = news_sentiment
        elif social_count > 0:
            combined_sentiment = social_sentiment
        else:
            combined_sentiment = 0
            
        # Convert to 0-100 scale
        sentiment_score = (combined_sentiment + 100) / 2
        
        return {
            'sentiment_score': sentiment_score,
            'news_sentiment': news_sentiment,
            'social_sentiment': social_sentiment,
            'mention_volume': mention_volume,
            'news_count': news_count,
            'social_count': social_count,
            'sentiment_articles': [],  # Empty for fallback
            'sentiment_sources': ['fallback'],
            'timestamp': datetime.now().timestamp()
        }
    
    def _save_to_cache(self, symbol: str, data: Dict) -> None:
        """Save sentiment data to local cache"""
        try:
            cache_file = self.cache_dir / f"{symbol.upper()}_sentiment.json"
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            self.logger.debug(f"Sentiment data for {symbol} saved to cache")
        except Exception as e:
            self.logger.error(f"Error saving sentiment to cache: {str(e)}")

    def _get_from_cache(self, symbol: str) -> Optional[Dict]:
        """Get sentiment data from local cache if available and not expired"""
        try:
            cache_file = self.cache_dir / f"{symbol.upper()}_sentiment.json"
            if not cache_file.exists():
                return None
                
            # Check if cache is expired
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.cache_expiry:
                self.logger.debug(f"Sentiment cache for {symbol} is expired")
                return None
                
            with open(cache_file, 'r') as f:
                data = json.load(f)
            self.logger.debug(f"Sentiment data for {symbol} loaded from cache")
            return data
            
        except Exception as e:
            self.logger.error(f"Error reading sentiment from cache: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the analyzer
    analyzer = NewsSentimentAnalyzer()
    
    # Test with a popular stock
    sentiment = analyzer.get_sentiment_data("AAPL")
    print(json.dumps(sentiment, indent=2))