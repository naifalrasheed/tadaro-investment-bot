"""
Database integration for the Adaptive Learning System

This module provides functions to interact with the database models for the adaptive learning system,
making it easier to store and retrieve user preferences, feature weights, and prediction records.
"""

from datetime import datetime
from models import db, StockPreference, FeatureWeight, SectorPreference, PredictionRecord
import json
import numpy as np

class AdaptiveLearningDB:
    """
    Database interface for the adaptive learning system.
    Handles database operations for storing and retrieving user preferences.
    """
    
    def __init__(self, user_id):
        """
        Initialize with a user ID.
        
        Args:
            user_id (int): Database ID for the current user
        """
        self.user_id = user_id
    
    def record_stock_view(self, symbol, sector=None, view_duration=None):
        """
        Record that a user viewed a particular stock.
        
        Args:
            symbol (str): The stock symbol
            sector (str, optional): The stock's sector
            view_duration (float, optional): Time spent viewing in seconds
        """
        # Get or create stock preference record
        stock_pref = StockPreference.query.filter_by(
            user_id=self.user_id, 
            symbol=symbol
        ).first()
        
        if not stock_pref:
            stock_pref = StockPreference(
                user_id=self.user_id,
                symbol=symbol,
                sector=sector,
                view_count=0,
                total_view_time=0
            )
        
        # Update view data
        stock_pref.view_count += 1
        stock_pref.last_viewed = datetime.utcnow()
        
        if view_duration:
            stock_pref.total_view_time += view_duration
        
        # Commit to database
        db.session.add(stock_pref)
        db.session.commit()
    
    def record_stock_feedback(self, symbol, reaction, stock_data=None):
        """
        Record user's explicit feedback about a stock.
        
        Args:
            symbol (str): The stock symbol
            reaction (str): 'like', 'dislike', or 'purchase'
            stock_data (dict, optional): Stock metrics and features
        """
        # Get or create stock preference record
        stock_pref = StockPreference.query.filter_by(
            user_id=self.user_id, 
            symbol=symbol
        ).first()
        
        if not stock_pref:
            stock_pref = StockPreference(
                user_id=self.user_id,
                symbol=symbol,
                sector=stock_data.get('sector') if stock_data else None
            )
        
        # Update feedback or purchase data
        timestamp = datetime.utcnow()
        
        if reaction == 'like':
            stock_pref.liked = True
            stock_pref.feedback_date = timestamp
            if stock_data:
                stock_pref.metrics_at_feedback = stock_data
                
        elif reaction == 'dislike':
            stock_pref.liked = False
            stock_pref.feedback_date = timestamp
            if stock_data:
                stock_pref.metrics_at_feedback = stock_data
                
        elif reaction == 'purchase':
            stock_pref.purchased = True
            stock_pref.purchase_date = timestamp
            stock_pref.purchase_price = stock_data.get('current_price') if stock_data else None
            # Also mark as liked if purchased
            stock_pref.liked = True
        
        # Update sector preference if sector is available
        if stock_pref.sector:
            self._update_sector_preference(
                stock_pref.sector, 
                1 if reaction in ('like', 'purchase') else -1
            )
        
        # Commit to database
        db.session.add(stock_pref)
        db.session.commit()
        
        # If we have stock data, we might want to use it to update feature weights
        if stock_data and reaction in ('like', 'dislike', 'purchase'):
            self._update_feature_relevance(stock_data, reaction)
            
    def _update_sector_preference(self, sector, score_change):
        """
        Update a sector preference score.
        
        Args:
            sector (str): The sector to update
            score_change (int): Amount to adjust score (+1 for like, -1 for dislike)
        """
        sector_pref = SectorPreference.query.filter_by(
            user_id=self.user_id,
            sector=sector
        ).first()
        
        if not sector_pref:
            sector_pref = SectorPreference(
                user_id=self.user_id,
                sector=sector,
                score=0
            )
        
        # Update score (keeping within bounds)
        new_score = sector_pref.score + score_change
        sector_pref.score = max(min(new_score, 10), -10)  # Keep between -10 and +10
        sector_pref.last_updated = datetime.utcnow()
        
        db.session.add(sector_pref)
        db.session.commit()
    
    def _update_feature_relevance(self, stock_data, reaction):
        """
        Update feature weights based on user feedback.
        
        Args:
            stock_data (dict): Stock metrics and data
            reaction (str): 'like', 'dislike', or 'purchase'
        """
        # Get or create feature weights
        weights = FeatureWeight.query.filter_by(user_id=self.user_id).first()
        
        if not weights:
            weights = FeatureWeight(user_id=self.user_id)
            db.session.add(weights)
            db.session.commit()
        
        # For now, just a basic implementation that focuses on metrics that were
        # particularly strong in stocks the user liked
        
        # If the user liked or purchased this stock
        if reaction in ('like', 'purchase'):
            # If this stock has strong price momentum, slightly increase that weight
            if stock_data.get('price_momentum', 0) > 50:
                weights.price_momentum_weight *= 1.05
            
            # If this stock has a good 52-week position, slightly increase that weight
            if stock_data.get('52_week_range_position', 0) > 0.7:
                weights.weekly_range_weight *= 1.05
            
            # If this stock has strong YTD performance, slightly increase that weight
            if stock_data.get('ytd_performance', 0) > 15:
                weights.ytd_performance_weight *= 1.05
            
            # If this stock has good sentiment, slightly increase that weight
            if stock_data.get('news_sentiment', 0) > 0.6:
                weights.news_sentiment_weight *= 1.05
                
            # If this stock has good ROTC, slightly increase that weight
            if stock_data.get('rotc', 0) > 10:
                weights.rotc_weight *= 1.05
                
            # If this stock has a good PE ratio, slightly increase that weight
            if stock_data.get('pe_ratio', 100) < 20 and stock_data.get('pe_ratio', 0) > 0:
                weights.pe_ratio_weight *= 1.05
                
            # If this stock has good dividend yield, slightly increase that weight
            if stock_data.get('dividend_yield', 0) > 2:
                weights.dividend_yield_weight *= 1.05
                
            # If this stock has good volume, slightly increase that weight
            if stock_data.get('volume_change', 0) > 10:
                weights.volume_change_weight *= 1.05
                
        # If the user disliked this stock, do the opposite
        elif reaction == 'dislike':
            # If this stock has strong price momentum, slightly decrease that weight
            if stock_data.get('price_momentum', 0) > 50:
                weights.price_momentum_weight *= 0.95
            
            # If this stock has a good 52-week position, slightly decrease that weight
            if stock_data.get('52_week_range_position', 0) > 0.7:
                weights.weekly_range_weight *= 0.95
            
            # If this stock has strong YTD performance, slightly decrease that weight
            if stock_data.get('ytd_performance', 0) > 15:
                weights.ytd_performance_weight *= 0.95
            
            # If this stock has good sentiment, slightly decrease that weight
            if stock_data.get('news_sentiment', 0) > 0.6:
                weights.news_sentiment_weight *= 0.95
                
            # If this stock has good ROTC, slightly decrease that weight
            if stock_data.get('rotc', 0) > 10:
                weights.rotc_weight *= 0.95
                
            # If this stock has a good PE ratio, slightly decrease that weight
            if stock_data.get('pe_ratio', 100) < 20 and stock_data.get('pe_ratio', 0) > 0:
                weights.pe_ratio_weight *= 0.95
                
            # If this stock has good dividend yield, slightly decrease that weight
            if stock_data.get('dividend_yield', 0) > 2:
                weights.dividend_yield_weight *= 0.95
                
            # If this stock has good volume, slightly decrease that weight
            if stock_data.get('volume_change', 0) > 10:
                weights.volume_change_weight *= 0.95
                
        # Normalize weights to sum to 1.0
        total = (
            weights.price_momentum_weight + 
            weights.weekly_range_weight + 
            weights.ytd_performance_weight + 
            weights.news_sentiment_weight + 
            weights.rotc_weight + 
            weights.pe_ratio_weight + 
            weights.dividend_yield_weight + 
            weights.volume_change_weight +
            weights.market_cap_weight
        )
        
        # Normalize only if total is not 0
        if total > 0:
            weights.price_momentum_weight /= total
            weights.weekly_range_weight /= total
            weights.ytd_performance_weight /= total
            weights.news_sentiment_weight /= total
            weights.rotc_weight /= total
            weights.pe_ratio_weight /= total
            weights.dividend_yield_weight /= total
            weights.volume_change_weight /= total
            weights.market_cap_weight /= total
        
        weights.last_updated = datetime.utcnow()
        db.session.add(weights)
        db.session.commit()
    
    def record_prediction(self, symbol, prediction_type, predicted, actual=None):
        """
        Record a prediction and its actual outcome for future learning.
        
        Args:
            symbol (str): The stock symbol
            prediction_type (str): Type of prediction (e.g., 'price', 'sentiment')
            predicted (float): Predicted value
            actual (float, optional): Actual value if known
        """
        record = PredictionRecord(
            user_id=self.user_id,
            symbol=symbol,
            prediction_type=prediction_type,
            predicted_value=predicted,
            actual_value=actual
        )
        
        if actual is not None:
            record.error = abs(predicted - actual)
        
        db.session.add(record)
        db.session.commit()
    
    def update_prediction_outcome(self, prediction_id, actual_value):
        """
        Update a prediction record with the actual outcome.
        
        Args:
            prediction_id (int): ID of the prediction record
            actual_value (float): Actual observed value
        """
        record = PredictionRecord.query.get(prediction_id)
        
        if record and record.user_id == self.user_id:
            record.actual_value = actual_value
            record.error = abs(record.predicted_value - actual_value)
            db.session.add(record)
            db.session.commit()
    
    def get_user_feature_weights(self):
        """
        Get the user's current feature weights.
        
        Returns:
            dict: Feature weights as a dictionary
        """
        weights = FeatureWeight.query.filter_by(user_id=self.user_id).first()
        
        if not weights:
            weights = FeatureWeight(user_id=self.user_id)
            db.session.add(weights)
            db.session.commit()
        
        return {
            "price_momentum": weights.price_momentum_weight,
            "weekly_range": weights.weekly_range_weight,
            "ytd_performance": weights.ytd_performance_weight,
            "news_sentiment": weights.news_sentiment_weight,
            "rotc": weights.rotc_weight,
            "pe_ratio": weights.pe_ratio_weight,
            "dividend_yield": weights.dividend_yield_weight,
            "volume_change": weights.volume_change_weight,
            "market_cap": weights.market_cap_weight
        }
    
    def get_preferred_sectors(self, limit=5):
        """
        Get the user's most preferred sectors.
        
        Args:
            limit (int): Maximum number of sectors to return
            
        Returns:
            list: List of (sector, score) tuples
        """
        sectors = SectorPreference.query.filter_by(
            user_id=self.user_id
        ).order_by(SectorPreference.score.desc()).limit(limit).all()
        
        return [(s.sector, s.score) for s in sectors if s.score > 0]
    
    def get_disliked_sectors(self, limit=5):
        """
        Get the user's least preferred sectors.
        
        Args:
            limit (int): Maximum number of sectors to return
            
        Returns:
            list: List of (sector, score) tuples
        """
        sectors = SectorPreference.query.filter_by(
            user_id=self.user_id
        ).order_by(SectorPreference.score.asc()).limit(limit).all()
        
        return [(s.sector, s.score) for s in sectors if s.score < 0]
    
    def get_liked_stocks(self, limit=None):
        """
        Get stocks the user has explicitly liked.
        
        Args:
            limit (int, optional): Maximum number of stocks to return
            
        Returns:
            list: List of stock symbols
        """
        query = StockPreference.query.filter_by(
            user_id=self.user_id,
            liked=True
        ).order_by(StockPreference.feedback_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return [s.symbol for s in query.all()]
    
    def get_disliked_stocks(self, limit=None):
        """
        Get stocks the user has explicitly disliked.
        
        Args:
            limit (int, optional): Maximum number of stocks to return
            
        Returns:
            list: List of stock symbols
        """
        query = StockPreference.query.filter_by(
            user_id=self.user_id,
            liked=False
        ).order_by(StockPreference.feedback_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return [s.symbol for s in query.all()]
    
    def get_purchased_stocks(self, limit=None):
        """
        Get stocks the user has purchased.
        
        Args:
            limit (int, optional): Maximum number of stocks to return
            
        Returns:
            list: List of stock symbols
        """
        query = StockPreference.query.filter_by(
            user_id=self.user_id,
            purchased=True
        ).order_by(StockPreference.purchase_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return [s.symbol for s in query.all()]
    
    def get_prediction_accuracy(self, prediction_type=None):
        """
        Get the user's prediction accuracy.
        
        Args:
            prediction_type (str, optional): Type of prediction to filter by
            
        Returns:
            float: Average prediction accuracy (0.0 to 1.0)
        """
        query = PredictionRecord.query.filter_by(user_id=self.user_id)
        
        if prediction_type:
            query = query.filter_by(prediction_type=prediction_type)
        
        # Only include records with both predicted and actual values
        records = [r for r in query.all() if r.actual_value is not None]
        
        if not records:
            return None
        
        errors = [r.error for r in records]
        return float(np.mean(errors)) if errors else None
    
    def get_recommended_stocks(self, stock_data):
        """
        Get personalized stock recommendations based on user preferences and feature weights.
        
        Args:
            stock_data (list): List of dictionaries containing stock data
            
        Returns:
            list: List of recommended stocks with scores
        """
        if not stock_data:
            return []
        
        # Get user's feature weights
        weights = self.get_user_feature_weights()
        
        # Get preferred sectors
        preferred_sectors = [s[0] for s in self.get_preferred_sectors()]
        
        # Score each stock based on user preferences
        scored_stocks = []
        for stock in stock_data:
            score = 0
            symbol = stock.get('symbol', '')
            
            # Base score from features weighted by user preferences
            if 'price_momentum' in stock:
                score += stock['price_momentum'] * weights.get('price_momentum', 0.1)
                
            if '52_week_range_position' in stock:
                score += stock['52_week_range_position'] * 100 * weights.get('weekly_range', 0.1)
                
            if 'ytd_performance' in stock:
                score += stock['ytd_performance'] * weights.get('ytd_performance', 0.1)
                
            if 'news_sentiment' in stock:
                score += stock['news_sentiment'] * 100 * weights.get('news_sentiment', 0.1)
                
            if 'rotc' in stock:
                score += stock['rotc'] * weights.get('rotc', 0.1)
                
            if 'pe_ratio' in stock and stock['pe_ratio'] > 0:
                # Lower PE ratio is better, so invert the relationship
                pe_score = 25 / max(stock['pe_ratio'], 1) * weights.get('pe_ratio', 0.1)
                score += pe_score
                
            if 'dividend_yield' in stock:
                score += stock['dividend_yield'] * weights.get('dividend_yield', 0.1)
                
            if 'volume_change' in stock:
                score += stock['volume_change'] * weights.get('volume_change', 0.1)
                
            # Sector bonus
            if 'sector' in stock and stock['sector'] in preferred_sectors:
                score *= 1.2  # 20% bonus for preferred sectors
            
            # Add to scored list with explanation
            explanation = self._generate_recommendation_explanation(stock, weights, preferred_sectors)
            scored_stocks.append({
                'symbol': symbol,
                'score': score,
                'data': stock,
                'explanation': explanation
            })
        
        # Sort by score
        sorted_stocks = sorted(scored_stocks, key=lambda x: x['score'], reverse=True)
        
        # Return top recommendations (all of them for now)
        return sorted_stocks
    
    def _generate_recommendation_explanation(self, stock, weights, preferred_sectors):
        """
        Generate an explanation for why a stock is recommended.
        
        Args:
            stock (dict): Stock data
            weights (dict): User's feature weights
            preferred_sectors (list): User's preferred sectors
            
        Returns:
            str: Explanation text
        """
        reasons = []
        
        # Check for strong features
        if 'price_momentum' in stock and stock['price_momentum'] > 50:
            reasons.append("Strong price momentum")
            
        if '52_week_range_position' in stock and stock['52_week_range_position'] > 0.7:
            reasons.append("Trading near 52-week high")
            
        if 'ytd_performance' in stock and stock['ytd_performance'] > 15:
            reasons.append(f"Strong YTD performance ({stock['ytd_performance']:.1f}%)")
            
        if 'news_sentiment' in stock and stock['news_sentiment'] > 0.6:
            reasons.append("Positive news sentiment")
            
        if 'rotc' in stock and stock['rotc'] > 12:
            reasons.append(f"High return on invested capital ({stock['rotc']:.1f}%)")
            
        if 'pe_ratio' in stock and 0 < stock['pe_ratio'] < 20:
            reasons.append(f"Attractive P/E ratio ({stock['pe_ratio']:.1f})")
            
        if 'dividend_yield' in stock and stock['dividend_yield'] > 2:
            reasons.append(f"Good dividend yield ({stock['dividend_yield']:.1f}%)")
            
        if 'sector' in stock and stock['sector'] in preferred_sectors:
            reasons.append(f"In your preferred sector: {stock['sector']}")
        
        if not reasons:
            return "Based on your overall preferences"
        
        # Return top 3 reasons
        return ", ".join(reasons[:3])
            
    def get_user_profile_summary(self):
        """
        Generate a summary of the user's investment profile based on preferences.
        
        Returns:
            dict: Summary of user preferences and tendencies
        """
        liked = len(self.get_liked_stocks())
        disliked = len(self.get_disliked_stocks())
        purchased = len(self.get_purchased_stocks())
        
        # Get view counts for most-viewed stocks
        most_viewed = StockPreference.query.filter_by(
            user_id=self.user_id
        ).order_by(StockPreference.view_count.desc()).limit(5).all()
        
        # Get preferred sectors
        preferred_sectors = self.get_preferred_sectors()
        
        # Get feature weights
        weights = self.get_user_feature_weights()
        
        # Get prediction accuracy
        accuracy = self.get_prediction_accuracy()
        
        return {
            "interaction_stats": {
                "liked_stocks": liked,
                "disliked_stocks": disliked,
                "purchased_stocks": purchased,
                "most_viewed": [
                    {"symbol": s.symbol, "views": s.view_count} 
                    for s in most_viewed
                ]
            },
            "preferred_sectors": [s[0] for s in preferred_sectors],
            "feature_weights": weights,
            "prediction_accuracy": accuracy
        }
        
    def reset_user_data(self):
        """
        Reset all user learning data in the system.
        Deletes all preferences, feature weights, and prediction records
        for the current user.
        
        Returns:
            bool: True if reset was successful, False otherwise
        """
        try:
            # Delete all stock preferences
            StockPreference.query.filter_by(user_id=self.user_id).delete()
            
            # Delete all sector preferences
            SectorPreference.query.filter_by(user_id=self.user_id).delete()
            
            # Delete all feature weights
            FeatureWeight.query.filter_by(user_id=self.user_id).delete()
            
            # Delete all prediction records
            PredictionRecord.query.filter_by(user_id=self.user_id).delete()
            
            # Commit the changes
            db.session.commit()
            
            # Initialize default feature weights
            self._initialize_default_weights()
            
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error resetting user data: {e}")
            return False
            
    def _initialize_default_weights(self):
        """Initialize default feature weights for a new or reset user"""
        weights = FeatureWeight(
            user_id=self.user_id,
            price_momentum_weight=1.0,
            weekly_range_weight=1.0,
            ytd_performance_weight=1.0,
            news_sentiment_weight=1.0,
            rotc_weight=1.0,
            pe_ratio_weight=1.0,
            dividend_yield_weight=1.0,
            volume_weight=1.0,
            market_cap_weight=1.0,
            volatility_weight=1.0
        )
        
        db.session.add(weights)
        db.session.commit()