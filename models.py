from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    analyses = db.relationship('StockAnalysis', backref='user', lazy=True)
    portfolios = db.relationship('Portfolio', backref='user', lazy=True)
    stock_preferences = db.relationship('StockPreference', backref='user', lazy=True)
    feature_weights = db.relationship('FeatureWeight', backref='user', lazy=True)
    prediction_records = db.relationship('PredictionRecord', backref='user', lazy=True)
    sentiment_configs = db.relationship('SentimentConfig', backref='user', lazy=True)
    # CFA-related relationships
    bias_profiles = db.relationship('UserBiasProfile', backref='user', lazy=True)
    investment_decisions = db.relationship('InvestmentDecision', backref='user', lazy=True)
    risk_profile = db.relationship('UserRiskProfile', backref='user', lazy=True, uselist=False)
    
    # Flag to indicate if user has completed initial profiling
    has_completed_profiling = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        # Use pbkdf2:sha256 method which generates shorter hashes (~87 chars vs 169 chars)
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StockAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    analysis_data = db.Column(db.JSON)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    stocks = db.Column(db.JSON)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class StockPreference(db.Model):
    """Records user's interactions with and preferences for stocks"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    sector = db.Column(db.String(50))
    
    # Interaction data
    view_count = db.Column(db.Integer, default=0)
    last_viewed = db.Column(db.DateTime)
    total_view_time = db.Column(db.Float, default=0)  # in seconds
    
    # Explicit feedback
    liked = db.Column(db.Boolean, nullable=True)  # True=liked, False=disliked, None=no feedback
    feedback_date = db.Column(db.DateTime)
    
    # Purchase data
    purchased = db.Column(db.Boolean, default=False)
    purchase_date = db.Column(db.DateTime)
    purchase_price = db.Column(db.Float)
    
    # For tracking which metrics this stock exhibited when user liked it
    metrics_at_feedback = db.Column(db.JSON)
    
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', name='_user_stock_uc'),)

class FeatureWeight(db.Model):
    """Stores personalized feature importance weights for each user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Feature weights (0.0 to 1.0)
    price_momentum_weight = db.Column(db.Float, default=0.2)
    weekly_range_weight = db.Column(db.Float, default=0.1)
    ytd_performance_weight = db.Column(db.Float, default=0.2)
    news_sentiment_weight = db.Column(db.Float, default=0.1)
    rotc_weight = db.Column(db.Float, default=0.1)
    pe_ratio_weight = db.Column(db.Float, default=0.1)
    dividend_yield_weight = db.Column(db.Float, default=0.1)
    volume_change_weight = db.Column(db.Float, default=0.05)
    market_cap_weight = db.Column(db.Float, default=0.05)
    
    # Custom user-defined weights (optional)
    custom_weights = db.Column(db.JSON)
    
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SectorPreference(db.Model):
    """Tracks user's sector preferences based on interactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sector = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, default=0.0)  # -10 to +10 scale
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'sector', name='_user_sector_uc'),)

class PredictionRecord(db.Model):
    """Records prediction accuracy to improve future recommendations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    predicted_value = db.Column(db.Float)  # Could be price, sentiment, etc.
    actual_value = db.Column(db.Float)
    error = db.Column(db.Float)  # Absolute difference between predicted and actual
    prediction_type = db.Column(db.String(50))  # e.g., 'price', 'sentiment', 'user_preference'
    
    # Optional: serialized features used for this prediction
    features_used = db.Column(db.JSON)
    
class SentimentConfig(db.Model):
    """User's configurable sentiment analysis weights"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    price_momentum_weight = db.Column(db.Integer, default=40)  # 0-100
    week_52_range_weight = db.Column(db.Integer, default=20)   # 0-100
    ytd_performance_weight = db.Column(db.Integer, default=20) # 0-100
    news_sentiment_weight = db.Column(db.Integer, default=10)  # 0-100
    rotc_weight = db.Column(db.Integer, default=10)           # 0-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SentimentConfig {self.name} for User {self.user_id}>'
    
    def validate(self):
        """Ensure weights sum to 100%"""
        total = (self.price_momentum_weight + self.week_52_range_weight + 
                 self.ytd_performance_weight + self.news_sentiment_weight + 
                 self.rotc_weight)
        return total == 100
    
    def as_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price_momentum_weight': self.price_momentum_weight,
            'week_52_range_weight': self.week_52_range_weight,
            'ytd_performance_weight': self.ytd_performance_weight,
            'news_sentiment_weight': self.news_sentiment_weight,
            'rotc_weight': self.rotc_weight,
            'is_default': self.is_default
        }

class UserBiasProfile(db.Model):
    """Tracks user behavioral bias profiles based on CFA concepts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bias_type = db.Column(db.String(50), nullable=False)  # e.g., 'loss_aversion', 'recency'
    bias_score = db.Column(db.Float, default=0.0)  # 0.0-10.0 scale
    detection_count = db.Column(db.Integer, default=0)  # Number of times detected
    last_detected = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'bias_type', name='_user_bias_type_uc'),)
    
    def __repr__(self):
        return f'<UserBiasProfile {self.bias_type}:{self.bias_score} for User {self.user_id}>'

class InvestmentDecision(db.Model):
    """Records investment decisions with CFA-based structure"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    decision_type = db.Column(db.String(20), nullable=False)  # buy, sell, hold
    rationale = db.Column(db.Text)
    amount = db.Column(db.Float)  # Shares/units
    price = db.Column(db.Float)   # Price per share/unit
    market_context = db.Column(db.JSON)  # Market conditions at time of decision
    stock_metrics = db.Column(db.JSON)   # Stock metrics at time of decision
    portfolio_impact = db.Column(db.JSON)  # Impact on portfolio
    potential_biases = db.Column(db.JSON)  # Detected biases in decision
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InvestmentDecision {self.decision_type} {self.symbol} by User {self.user_id}>'

class UserRiskProfile(db.Model):
    """User risk profile based on CFA concepts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_horizon = db.Column(db.Integer, default=0)  # 0-100 scale
    risk_tolerance = db.Column(db.Integer, default=0)  # 0-100 scale
    investment_knowledge = db.Column(db.Integer, default=0)  # 0-100 scale
    income_stability = db.Column(db.Integer, default=0)  # 0-100 scale
    loss_attitude = db.Column(db.Integer, default=0)  # 0-100 scale
    
    # Investment constraints
    max_risk = db.Column(db.Float, default=0)
    min_return = db.Column(db.Float, default=0)
    investment_horizon = db.Column(db.Integer, default=0)  # in years
    
    # Sector preferences
    preferred_sectors = db.Column(db.JSON)
    excluded_sectors = db.Column(db.JSON)
    
    # IPS (Investment Policy Statement)
    investment_policy = db.Column(db.JSON)
    
    # Profile category (conservative, moderate, aggressive, etc.)
    profile_category = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserRiskProfile {self.profile_category} for User {self.user_id}>'
    
    @classmethod
    def get_default_for_user(cls, user_id):
        """Get the default sentiment config for a user"""
        default = cls.query.filter_by(user_id=user_id, is_default=True).first()
        if default is None:
            # Create default config if none exists
            default = cls(
                user_id=user_id,
                name="Default",
                is_default=True,
                price_momentum_weight=40,
                week_52_range_weight=20,
                ytd_performance_weight=20,
                news_sentiment_weight=10,
                rotc_weight=10
            )
            db.session.add(default)
            db.session.commit()
        return default

# Preset configurations
SENTIMENT_PRESETS = [
    {
        'name': 'Default',
        'price_momentum_weight': 40,
        'week_52_range_weight': 20,
        'ytd_performance_weight': 20,
        'news_sentiment_weight': 10,
        'rotc_weight': 10
    },
    {
        'name': 'Technical Focus',
        'price_momentum_weight': 60,
        'week_52_range_weight': 30,
        'ytd_performance_weight': 10,
        'news_sentiment_weight': 0,
        'rotc_weight': 0
    },
    {
        'name': 'Fundamental Focus',
        'price_momentum_weight': 10,
        'week_52_range_weight': 10,
        'ytd_performance_weight': 10,
        'news_sentiment_weight': 10,
        'rotc_weight': 60
    },
    {
        'name': 'News Focus',
        'price_momentum_weight': 20,
        'week_52_range_weight': 10,
        'ytd_performance_weight': 10,
        'news_sentiment_weight': 50,
        'rotc_weight': 10
    },
    {
        'name': 'Balanced',
        'price_momentum_weight': 20,
        'week_52_range_weight': 20,
        'ytd_performance_weight': 20,
        'news_sentiment_weight': 20,
        'rotc_weight': 20
    }
]