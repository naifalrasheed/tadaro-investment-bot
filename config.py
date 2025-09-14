import os

class Config:
    # API Keys - Using environment variables with defaults
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', "FRFZAADBV18NJXSB")
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', "15f001975f4746228da3259e64012a69")
    
    # MongoDB settings
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'investment_bot')
    COLLECTIONS = {
        'feedback': 'user_feedback',
        'profiles': 'user_profiles',
        'watchlist': 'stock_watchlist'
    }
    
    # Portfolio settings
    MAX_STOCKS_PER_SECTOR = 10
    TARGET_SECTORS = 5
    MAX_POSITION_SIZE = 0.20  # Maximum 20% in any single stock
    
    # Risk parameters
    MAX_ANNUAL_VOLATILITY = 0.25  # 25% maximum volatility
    RISK_FREE_RATE = 0.03  # 3% risk-free rate assumption
    
    # Data settings
    HISTORICAL_YEARS = 2
    UPDATE_INTERVAL_HOURS = 24
    
    # Technical Analysis Parameters
    MOVING_AVG_SHORT = 50   # 50-day moving average
    MOVING_AVG_LONG = 200   # 200-day moving average
    
    # Monte Carlo simulation settings
    NUM_SIMULATIONS = 10000
    
    # Sector preferences (example weights)
    SECTOR_WEIGHTS = {
        'Technology': 0.25,
        'Healthcare': 0.20,
        'Financial': 0.15,
        'Consumer': 0.15,
        'Industrial': 0.15,
        'Energy': 0.10
    }
    
    # Financial metrics thresholds
    MIN_MARKET_CAP = 1e9  # $1 billion minimum
    MIN_DAILY_VOLUME = 1e6  # $1 million minimum daily volume
    MIN_PRICE = 5.0  # $5 minimum stock price
    
    # Data source weights for sentiment analysis
    SENTIMENT_SOURCE_WEIGHTS = {
        'price_momentum': 0.3,  # Price momentum (30%)
        'rotc': 0.3,           # Return on Total Capital (30%)
        'free_cash_flow': 0.2,  # Positive Free Cash Flow (20%)
        'twitter': 0.1,         # Twitter mentions (10%)
        'news_api': 0.1         # NewsAPI mentions (10%)
    }
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        assert sum(cls.SECTOR_WEIGHTS.values()) == 1.0, "Sector weights must sum to 1.0"
        assert cls.MAX_POSITION_SIZE <= 0.25, "Maximum position size cannot exceed 25%"
        assert cls.NUM_SIMULATIONS >= 1000, "Need at least 1000 simulations"
        assert sum(cls.SENTIMENT_SOURCE_WEIGHTS.values()) == 1.0, "Sentiment source weights must sum to 1.0"
        return True