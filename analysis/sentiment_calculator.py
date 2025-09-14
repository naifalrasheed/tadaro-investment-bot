# src/analysis/sentiment_calculator.py
from typing import Dict, Optional, Union, Any
import logging
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    from data.news_sentiment_analyzer import NewsSentimentAnalyzer
    HAS_NEWS_SENTIMENT = True
except ImportError:
    HAS_NEWS_SENTIMENT = False
    
class SentimentCalculator:
    """
    Calculates comprehensive sentiment scores for stocks based on various inputs:
    - Price momentum (30%)
    - ROTC (Return on Total Capital) (30%)
    - Free Cash Flow (20%)
    - Twitter mentions (10%)
    - NewsAPI mentions (10%)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize news sentiment analyzer if available
        if HAS_NEWS_SENTIMENT:
            self.news_sentiment = NewsSentimentAnalyzer()
        else:
            self.news_sentiment = None
            self.logger.warning("News sentiment analyzer not available - using simulated sentiment")
    
    def calculate_sentiment(self, 
                          symbol: str, 
                          price_history: pd.DataFrame, 
                          current_price: float,
                          week_52_high: float,
                          week_52_low: float,
                          ytd_performance: float,
                          rotc: Optional[float] = None,
                          daily_change: Optional[float] = None,
                          custom_weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Calculate comprehensive sentiment score using multiple components
        
        Args:
            symbol: Stock ticker symbol
            price_history: Historical price data
            current_price: Current stock price
            week_52_high: 52-week high price
            week_52_low: 52-week low price
            ytd_performance: Year-to-date performance (percentage)
            rotc: Return on Total Capital (percentage), optional
            daily_change: Daily price change percentage, optional
            custom_weights: Optional dictionary of custom weights for components
            
        Returns:
            Dict containing sentiment score and component scores
        """
        sentiment_score = 0
        components = {}
        
        # Try to get config for sentiment weights
        try:
            from config import DevelopmentConfig as Config
            weights = Config.SENTIMENT_SOURCE_WEIGHTS
        except (ImportError, AttributeError):
            # Default weights if config not available
            weights = {
                'price_momentum': 0.3,  # Price momentum (30%)
                'rotc': 0.3,           # Return on Total Capital (30%)
                'free_cash_flow': 0.2,  # Positive Free Cash Flow (20%)
                'twitter': 0.1,         # Twitter mentions (10%)
                'news_api': 0.1         # NewsAPI mentions (10%)
            }
            
        # If custom weights are provided, use them
        if custom_weights:
            print(f"SentimentCalculator: Received custom weights: {custom_weights}")
            # Create a fresh weights dictionary
            weights = {}
            
            # Convert percentage weights (0-100) to decimal (0-1)
            if 'price_momentum_weight' in custom_weights:
                weights['price_momentum'] = custom_weights['price_momentum_weight'] / 100
            if 'week_52_range_weight' in custom_weights:
                weights['week_52_range'] = custom_weights['week_52_range_weight'] / 100
            if 'ytd_performance_weight' in custom_weights:
                weights['ytd_performance'] = custom_weights['ytd_performance_weight'] / 100
            if 'news_sentiment_weight' in custom_weights:
                weights['twitter'] = custom_weights['news_sentiment_weight'] / 200  # Split between Twitter and NewsAPI
                weights['news_api'] = custom_weights['news_sentiment_weight'] / 200
            if 'rotc_weight' in custom_weights:
                weights['rotc'] = custom_weights['rotc_weight'] / 100
                
            # Ensure weights sum to 1.0
            total = sum(weights.values())
            if total > 0:
                for key in weights:
                    weights[key] = weights[key] / total
                
            print(f"SentimentCalculator: Normalized weights: {weights}")
            self.logger.info(f"Using custom weights for sentiment calculation: {weights}")
        
        # Component 1: Recent price trend 
        trend_score = self._calculate_price_momentum(price_history)
        momentum_weight = weights.get('price_momentum', 0.3)
        momentum_contribution = trend_score * momentum_weight
        components['price_momentum'] = {
            'score': trend_score,
            'weight': momentum_weight,
            'contribution': momentum_contribution
        }
        sentiment_score += momentum_contribution
        print(f"Price momentum: score={trend_score}, weight={momentum_weight}, contribution={momentum_contribution}")
        
        # Component 2: Return on Total Capital
        rotc_score = self._calculate_rotc_contribution(rotc)
        rotc_weight = weights.get('rotc', 0.3)
        rotc_contribution = rotc_score * rotc_weight
        components['rotc'] = {
            'score': rotc_score,
            'weight': rotc_weight,
            'contribution': rotc_contribution
        }
        sentiment_score += rotc_contribution
        print(f"ROTC: score={rotc_score}, weight={rotc_weight}, contribution={rotc_contribution}")
        
        # Component 3: 52-Week Range position
        week_52_position = self._calculate_52_week_position(current_price, week_52_high, week_52_low)
        week_52_weight = weights.get('week_52_range', 0.2)
        week_52_contribution = week_52_position * week_52_weight
        components['week_52_range'] = {
            'score': week_52_position,
            'weight': week_52_weight,
            'contribution': week_52_contribution
        }
        sentiment_score += week_52_contribution
        print(f"52-Week Range: score={week_52_position}, weight={week_52_weight}, contribution={week_52_contribution}")
        
        # Component 4: YTD Performance
        ytd_score = self._calculate_ytd_contribution(ytd_performance)
        ytd_weight = weights.get('ytd_performance', 0.2)
        ytd_contribution = ytd_score * ytd_weight
        components['ytd_performance'] = {
            'score': ytd_score,
            'weight': ytd_weight,
            'contribution': ytd_contribution
        }
        sentiment_score += ytd_contribution
        print(f"YTD Performance: score={ytd_score}, weight={ytd_weight}, contribution={ytd_contribution}")
        
        # Get news sentiment data if available (will contain both Twitter and NewsAPI)
        if self.news_sentiment is not None:
            news_data = self.news_sentiment.get_sentiment_data(symbol)
            
            # Component 5: Twitter Mentions 
            if news_data and 'social_sentiment' in news_data:
                twitter_score = news_data['social_sentiment']
                # Convert from -100 to 100 scale to 0 to 100 scale
                twitter_score = (twitter_score + 100) / 2
            else:
                twitter_score = self._calculate_twitter_sentiment(symbol, daily_change)
                
            # Use half of the news_sentiment_weight for Twitter
            twitter_weight = weights.get('twitter', weights.get('news_sentiment_weight', 10) / 200)
            twitter_contribution = twitter_score * twitter_weight
            components['twitter'] = {
                'score': twitter_score,
                'weight': twitter_weight,
                'contribution': twitter_contribution
            }
            sentiment_score += twitter_contribution
            print(f"Twitter Sentiment: score={twitter_score}, weight={twitter_weight}, contribution={twitter_contribution}")
            
            # Component 6: NewsAPI Mentions 
            if news_data and 'news_sentiment' in news_data:
                news_api_score = news_data['news_sentiment']
                # Convert from -100 to 100 scale to 0 to 100 scale
                news_api_score = (news_api_score + 100) / 2
            else:
                news_api_score = self._calculate_news_api_sentiment(symbol, ytd_performance)
                
            # Use half of the news_sentiment_weight for NewsAPI
            news_api_weight = weights.get('news_api', weights.get('news_sentiment_weight', 10) / 200)
            news_api_contribution = news_api_score * news_api_weight
            components['news_api'] = {
                'score': news_api_score,
                'weight': news_api_weight,
                'contribution': news_api_contribution
            }
            sentiment_score += news_api_contribution
            print(f"News API Sentiment: score={news_api_score}, weight={news_api_weight}, contribution={news_api_contribution}")
        else:
            # Fallback if news sentiment analyzer is not available
            twitter_score = self._calculate_twitter_sentiment(symbol, daily_change)
            # Use half of the news_sentiment_weight for Twitter
            twitter_weight = weights.get('twitter', weights.get('news_sentiment_weight', 10) / 200)
            twitter_contribution = twitter_score * twitter_weight
            components['twitter'] = {
                'score': twitter_score,
                'weight': twitter_weight,
                'contribution': twitter_contribution
            }
            sentiment_score += twitter_contribution
            print(f"Twitter Sentiment (fallback): score={twitter_score}, weight={twitter_weight}, contribution={twitter_contribution}")
            
            news_api_score = self._calculate_news_api_sentiment(symbol, ytd_performance)
            # Use half of the news_sentiment_weight for NewsAPI
            news_api_weight = weights.get('news_api', weights.get('news_sentiment_weight', 10) / 200)
            news_api_contribution = news_api_score * news_api_weight
            components['news_api'] = {
                'score': news_api_score,
                'weight': news_api_weight,
                'contribution': news_api_contribution
            }
            sentiment_score += news_api_contribution
            print(f"News API Sentiment (fallback): score={news_api_score}, weight={news_api_weight}, contribution={news_api_contribution}")
        
        # Ensure final score is between 0 and 100
        final_score = max(0, min(100, sentiment_score))
        
        # Determine sentiment label
        if final_score >= 70:
            sentiment_label = "Bullish"
        elif final_score >= 40:
            sentiment_label = "Neutral"
        else:
            sentiment_label = "Bearish"
        
        print(f"FINAL SENTIMENT: Raw score={sentiment_score}, Final score={final_score}, Label={sentiment_label}")
            
        return {
            'sentiment_score': final_score,
            'sentiment_label': sentiment_label,
            'components': components
        }
    
    def _calculate_price_momentum(self, price_history: pd.DataFrame) -> float:
        """Calculate price momentum component based on moving averages"""
        try:
            if price_history is None or len(price_history) < 30 or 'Close' not in price_history.columns:
                print("Insufficient price history data for momentum calculation, using neutral value")
                return 50  # Neutral score if insufficient data
                
            # Compare 10-day vs 30-day moving averages
            ma_10 = price_history['Close'].tail(10).mean()
            ma_30 = price_history['Close'].tail(30).mean()
            
            # Calculate trend factor as percentage difference
            trend_factor = (ma_10 / ma_30 - 1) * 100
            
            # Scale to 0-100 range for this component
            # Values typically range from -10% to +10%, scale accordingly
            if trend_factor > 0:
                # Positive momentum, scale 0% to 10% to range 50-100
                scaled_score = 50 + min(50, trend_factor * 5)
            else:
                # Negative momentum, scale 0% to -10% to range 50-0
                scaled_score = 50 + max(-50, trend_factor * 5)
                
            return scaled_score
            
        except Exception as e:
            self.logger.error(f"Error calculating price momentum: {str(e)}")
            return 50  # Return neutral score on error
    
    def _calculate_52_week_position(self, current_price: float, high: float, low: float) -> float:
        """Calculate position in 52-week range component"""
        try:
            if high <= low or current_price <= 0:
                return 50  # Neutral score for invalid inputs
                
            # Calculate position in range (0 to 1)
            range_position = (current_price - low) / (high - low)
            
            # Scale to 0-100 score
            # 0 = price at 52-week low
            # 100 = price at 52-week high
            scaled_score = range_position * 100
            
            return scaled_score
            
        except Exception as e:
            self.logger.error(f"Error calculating 52-week position: {str(e)}")
            return 50  # Return neutral score on error
    
    def _calculate_ytd_contribution(self, ytd_performance: float) -> float:
        """Calculate YTD performance component"""
        try:
            # Scale YTD performance to 0-100 range
            # Typical annual returns range from -50% to +50%
            # We'll use that as our scaling reference
            if ytd_performance > 0:
                # Positive YTD, scale 0% to 50% to range 50-100
                scaled_score = 50 + min(50, ytd_performance)
            else:
                # Negative YTD, scale 0% to -50% to range 50-0
                scaled_score = 50 + max(-50, ytd_performance)
                
            return scaled_score
            
        except Exception as e:
            self.logger.error(f"Error calculating YTD contribution: {str(e)}")
            return 50  # Return neutral score on error
    
    def _calculate_free_cash_flow_contribution(self, rotc: Optional[float], ytd_performance: Optional[float]) -> float:
        """Calculate the Free Cash Flow component using proxies"""
        try:
            # If we don't have direct FCF data, we can use ROTC as a rough proxy
            # since companies with high ROTC often have good FCF
            if rotc is None:
                # If no ROTC data, estimate based on YTD performance if available
                if ytd_performance is not None:
                    # Companies with strong YTD gains often have better FCF
                    if ytd_performance > 20:
                        return 80  # Very good
                    elif ytd_performance > 10:
                        return 70  # Good
                    elif ytd_performance > 0:
                        return 60  # Positive
                    elif ytd_performance > -10:
                        return 40  # Below average
                    else:
                        return 30  # Poor
                return 50  # Neutral if no data
            
            # Use ROTC as proxy for FCF quality
            # Companies with high ROTC often generate strong free cash flow
            if rotc > 20:
                base_score = 85  # Excellent FCF likely
            elif rotc > 15:
                base_score = 75  # Very good FCF likely
            elif rotc > 10:
                base_score = 65  # Good FCF likely
            elif rotc > 5:
                base_score = 55  # Above average FCF likely
            elif rotc > 0:
                base_score = 45  # Average FCF likely
            else:
                base_score = 30  # Poor FCF likely
                
            # Adjust based on YTD performance if available
            if ytd_performance is not None:
                # Positive YTD performance often indicates improving FCF
                score_adjust = ytd_performance / 4  # Less weight than ROTC
                return max(0, min(100, base_score + score_adjust))
                
            return base_score
            
        except Exception as e:
            self.logger.error(f"Error calculating FCF contribution: {str(e)}")
            return 50  # Return neutral score on error
    
    def _calculate_twitter_sentiment(self, symbol: str, daily_change: Optional[float] = None) -> float:
        """Calculate Twitter sentiment component using deterministic values"""
        try:
            # This fallback is used when we don't have direct API access or
            # when the news sentiment analyzer doesn't provide Twitter data
            
            # Generate a deterministic value based on the symbol
            # Convert symbol to a number value (0-100) based on its characters
            symbol_value = (sum(ord(c) for c in symbol.upper()) % 40) + 30  # Base value between 30-70
            
            # Popular tech stocks tend to have more positive Twitter sentiment
            popular_tech = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"}
            other_popular = {"JPM", "WMT", "DIS", "V", "HD", "BA", "PG", "JNJ", "KO", "MCD"}
            
            # Base sentiment on stock type
            if symbol.upper() in popular_tech:
                base_sentiment = symbol_value + 20  # Tech gets a high boost (50-90)
            elif symbol.upper() in other_popular:
                base_sentiment = symbol_value + 10  # Other popular stocks get a medium boost (40-80)
            else:
                base_sentiment = symbol_value  # Other stocks stay at base value (30-70)
            
            # Cap at 100
            base_sentiment = min(100, base_sentiment)
            
            # Factor in recent price changes if available
            if daily_change is not None:
                # Recent price changes affect sentiment (positive changes → positive sentiment)
                sentiment_adjust = daily_change * 3  # Twitter reacts strongly to daily moves
                base_sentiment = max(0, min(100, base_sentiment + sentiment_adjust))
            
            return base_sentiment
            
        except Exception as e:
            self.logger.error(f"Error calculating Twitter sentiment: {str(e)}")
            return 50  # Return neutral score on error
            
    def _calculate_news_api_sentiment(self, symbol: str, ytd_performance: Optional[float] = None) -> float:
        """Calculate NewsAPI sentiment component using deterministic values"""
        try:
            # This fallback is used when we don't have direct API access or
            # when the news sentiment analyzer doesn't provide NewsAPI data
            
            # Generate a different deterministic value than Twitter sentiment
            # Calculate a base value between 25-65 based on the symbol
            symbol_value = (sum(ord(c) * 2 for c in symbol.upper()) % 40) + 25
            
            # Different types of companies get different news coverage
            large_caps = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "JNJ", "V", "PG", "WMT"}
            mid_caps = {"ROKU", "ETSY", "SNAP", "TWTR", "PINS", "SPOT", "DOCU", "ZM", "U", "DASH", "ABNB"}
            volatile = {"GME", "AMC", "BBBY", "BB", "NOK", "WISH", "CLOV", "PLTR", "NIO", "HOOD"}
            
            # Base sentiment on company category
            if symbol.upper() in large_caps:
                base_sentiment = symbol_value + 15  # Large caps get a significant boost (40-80)
            elif symbol.upper() in mid_caps:
                base_sentiment = symbol_value + 10  # Mid caps get a moderate boost (35-75)
            elif symbol.upper() in volatile:
                # Volatile stocks are more varied - some positive, some negative
                if symbol_value > 45:  # Use the base value to determine if positive or negative
                    base_sentiment = symbol_value + 15  # Higher volatility, positive (60-80)
                else:
                    base_sentiment = symbol_value - 15  # Higher volatility, negative (10-30)
            else:
                base_sentiment = symbol_value  # Other stocks stay at base value (25-65)
            
            # Cap between 0 and 100
            base_sentiment = max(0, min(100, base_sentiment))
            
            # Factor in YTD performance if available (news tends to follow trends)
            if ytd_performance is not None:
                # Strong performers tend to get more positive coverage
                sentiment_adjust = ytd_performance / 4  # Moderate effect
                base_sentiment = max(0, min(100, base_sentiment + sentiment_adjust))
            
            return base_sentiment
            
        except Exception as e:
            self.logger.error(f"Error calculating NewsAPI sentiment: {str(e)}")
            return 50  # Return neutral score on error
    
    def _calculate_rotc_contribution(self, rotc: Optional[float]) -> float:
        """Calculate Return on Total Capital component"""
        try:
            if rotc is None:
                return 50  # Neutral score if no ROTC data
            
            # Scale ROTC to 0-100 range
            # Industry average ROTC is around 7-10%
            # Below 0% is very poor, above 20% is excellent
            if rotc <= 0:
                scaled_score = 0  # Negative ROTC is poor
            elif rotc < 5:
                scaled_score = 20 + (rotc / 5) * 20  # 0-5% ROTC maps to 20-40
            elif rotc < 10:
                scaled_score = 40 + ((rotc - 5) / 5) * 20  # 5-10% ROTC maps to 40-60
            elif rotc < 15:
                scaled_score = 60 + ((rotc - 10) / 5) * 20  # 10-15% ROTC maps to 60-80
            else:
                scaled_score = 80 + min(20, (rotc - 15) / 5 * 20)  # 15-20%+ ROTC maps to 80-100
                
            return scaled_score
            
        except Exception as e:
            self.logger.error(f"Error calculating ROTC contribution: {str(e)}")
            return 50  # Return neutral score on error