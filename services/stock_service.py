"""
Stock Service
Business logic for stock analysis, recommendations, and data processing
Separates business logic from route handlers
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from models import db, StockAnalysis, User, StockPreference
from .api_client import UnifiedAPIClient
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from ml_components.adaptive_learning_db import AdaptiveLearningDB

logger = logging.getLogger(__name__)

class StockService:
    """Service class for stock-related business logic"""
    
    def __init__(self, api_client: UnifiedAPIClient = None):
        """Initialize with API client and analyzer"""
        self.api_client = api_client or UnifiedAPIClient()
        self.analyzer = EnhancedStockAnalyzer()
    
    def analyze_stock(self, symbol: str, user_id: Optional[int] = None, market: str = 'US') -> Dict[str, Any]:
        """
        Comprehensive stock analysis with user personalization
        
        Args:
            symbol: Stock symbol to analyze
            user_id: Optional user ID for personalized analysis
            market: Market type ('US' or 'Saudi')
            
        Returns:
            Complete analysis results dictionary
        """
        try:
            # Get stock data from unified API client
            stock_data = self.api_client.get_stock_data(symbol)
            
            # Get news sentiment
            sentiment_data = self.api_client.get_news_sentiment(
                symbol, 
                stock_data.get('company_name')
            )
            
            # Perform technical analysis
            technical_analysis = self._perform_technical_analysis(stock_data)
            
            # Perform fundamental analysis
            fundamental_analysis = self._perform_fundamental_analysis(stock_data, market)
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(
                stock_data, sentiment_data, technical_analysis
            )
            
            # Get personalized recommendations if user provided
            personalized_score = None
            if user_id:
                personalized_score = self._get_personalized_score(symbol, user_id, {
                    'price': stock_data.get('price', 0),
                    'pe_ratio': stock_data.get('pe_ratio', 0),
                    'sector': stock_data.get('sector', 'Unknown'),
                    'sentiment_score': overall_sentiment.get('score', 0),
                    'technical_score': technical_analysis.get('score', 0)
                })
            
            # Compile complete analysis
            analysis_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'stock_data': stock_data,
                'technical_analysis': technical_analysis,
                'fundamental_analysis': fundamental_analysis,
                'sentiment_analysis': {
                    'overall_sentiment': overall_sentiment,
                    'news_sentiment': sentiment_data
                },
                'personalized_score': personalized_score,
                'recommendation': self._generate_recommendation(
                    technical_analysis, fundamental_analysis, overall_sentiment, personalized_score
                )
            }
            
            # Save analysis to database if user provided
            if user_id:
                self._save_analysis(user_id, symbol, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            raise
    
    def _perform_technical_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis on stock data"""
        try:
            history = stock_data.get('history', [])
            if not history:
                return {'score': 0, 'indicators': {}, 'signals': []}
            
            df = pd.DataFrame(history)
            if 'Close' not in df.columns or len(df) < 20:
                return {'score': 0, 'indicators': {}, 'signals': []}
            
            indicators = {}
            signals = []
            
            # Calculate moving averages
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=min(50, len(df))).mean()
            
            current_price = df['Close'].iloc[-1]
            ma_20 = df['MA_20'].iloc[-1]
            ma_50 = df['MA_50'].iloc[-1]
            
            indicators['ma_20'] = ma_20
            indicators['ma_50'] = ma_50
            indicators['current_price'] = current_price
            
            # Generate signals
            if current_price > ma_20:
                signals.append({'type': 'bullish', 'indicator': 'MA_20', 'message': 'Price above 20-day MA'})
            else:
                signals.append({'type': 'bearish', 'indicator': 'MA_20', 'message': 'Price below 20-day MA'})
            
            if ma_20 > ma_50:
                signals.append({'type': 'bullish', 'indicator': 'MA_Cross', 'message': '20-day MA above 50-day MA'})
            else:
                signals.append({'type': 'bearish', 'indicator': 'MA_Cross', 'message': '20-day MA below 50-day MA'})
            
            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            indicators['rsi'] = current_rsi
            
            if current_rsi > 70:
                signals.append({'type': 'bearish', 'indicator': 'RSI', 'message': 'Overbought (RSI > 70)'})
            elif current_rsi < 30:
                signals.append({'type': 'bullish', 'indicator': 'RSI', 'message': 'Oversold (RSI < 30)'})
            
            # Calculate score based on signals
            bullish_signals = len([s for s in signals if s['type'] == 'bullish'])
            total_signals = len(signals)
            score = (bullish_signals / total_signals) * 100 if total_signals > 0 else 50
            
            return {
                'score': round(score, 2),
                'indicators': indicators,
                'signals': signals,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return {'score': 0, 'indicators': {}, 'signals': [], 'error': str(e)}
    
    def _perform_fundamental_analysis(self, stock_data: Dict[str, Any], market: str) -> Dict[str, Any]:
        """Perform fundamental analysis based on market type"""
        try:
            # Market-specific thresholds (Naif Al-Rasheed model)
            if market.upper() == 'SAUDI':
                pe_threshold = 20
                rotc_threshold = 12
            else:  # US market
                pe_threshold = 25
                rotc_threshold = 15
            
            metrics = {}
            signals = []
            
            # P/E Ratio analysis
            pe_ratio = stock_data.get('pe_ratio')
            if pe_ratio:
                metrics['pe_ratio'] = pe_ratio
                if pe_ratio < pe_threshold:
                    signals.append({'type': 'bullish', 'metric': 'PE', 'message': f'P/E ratio {pe_ratio:.2f} below threshold {pe_threshold}'})
                else:
                    signals.append({'type': 'bearish', 'metric': 'PE', 'message': f'P/E ratio {pe_ratio:.2f} above threshold {pe_threshold}'})
            
            # Market Cap analysis
            market_cap = stock_data.get('market_cap')
            if market_cap:
                metrics['market_cap'] = market_cap
                if market_cap > 1e9:  # $1B+
                    signals.append({'type': 'bullish', 'metric': 'MarketCap', 'message': 'Large cap stock (>$1B)'})
            
            # Dividend Yield analysis
            dividend_yield = stock_data.get('dividend_yield')
            if dividend_yield:
                metrics['dividend_yield'] = dividend_yield * 100  # Convert to percentage
                if dividend_yield > 0.02:  # 2%+
                    signals.append({'type': 'bullish', 'metric': 'Dividend', 'message': f'Dividend yield {dividend_yield*100:.2f}%'})
            
            # Calculate fundamental score
            bullish_signals = len([s for s in signals if s['type'] == 'bullish'])
            total_signals = len(signals)
            score = (bullish_signals / total_signals) * 100 if total_signals > 0 else 50
            
            return {
                'score': round(score, 2),
                'metrics': metrics,
                'signals': signals,
                'market': market,
                'thresholds': {
                    'pe_threshold': pe_threshold,
                    'rotc_threshold': rotc_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Fundamental analysis error: {e}")
            return {'score': 0, 'metrics': {}, 'signals': [], 'error': str(e)}
    
    def _calculate_overall_sentiment(self, stock_data: Dict, sentiment_data: Dict, technical_data: Dict) -> Dict[str, Any]:
        """Calculate overall sentiment score combining multiple factors"""
        try:
            # Weight different components
            weights = {
                'price_momentum': 0.3,
                'news_sentiment': 0.2,
                'technical_score': 0.3,
                'volume_trend': 0.2
            }
            
            scores = {}
            
            # Price momentum (comparing current to recent average)
            history = stock_data.get('history', [])
            if history and len(history) >= 5:
                recent_prices = [day['Close'] for day in history[-5:]]
                current_price = stock_data.get('price', recent_prices[-1])
                avg_recent = sum(recent_prices) / len(recent_prices)
                price_momentum = ((current_price - avg_recent) / avg_recent) * 100
                scores['price_momentum'] = max(-50, min(50, price_momentum))  # Cap at ±50%
            else:
                scores['price_momentum'] = 0
            
            # News sentiment
            news_score = sentiment_data.get('sentiment_score', 0) * 50  # Convert to ±50 range
            scores['news_sentiment'] = news_score
            
            # Technical score (convert 0-100 to ±50)
            tech_score = technical_data.get('score', 50) - 50
            scores['technical_score'] = tech_score
            
            # Volume trend
            if history and len(history) >= 10:
                recent_volumes = [day['Volume'] for day in history[-10:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_volume = stock_data.get('volume', avg_volume)
                if avg_volume > 0:
                    volume_trend = ((current_volume - avg_volume) / avg_volume) * 100
                    scores['volume_trend'] = max(-50, min(50, volume_trend))
                else:
                    scores['volume_trend'] = 0
            else:
                scores['volume_trend'] = 0
            
            # Calculate weighted overall score
            overall_score = sum(scores[key] * weights[key] for key in scores)
            
            # Convert to 0-100 scale for consistency
            normalized_score = (overall_score + 50)  # Convert from ±50 to 0-100
            
            # Determine sentiment category
            if normalized_score >= 70:
                category = 'Very Bullish'
                color = 'success'
            elif normalized_score >= 55:
                category = 'Bullish'
                color = 'success'
            elif normalized_score >= 45:
                category = 'Neutral'
                color = 'warning'
            elif normalized_score >= 30:
                category = 'Bearish'
                color = 'danger'
            else:
                category = 'Very Bearish'
                color = 'danger'
            
            return {
                'score': round(normalized_score, 2),
                'category': category,
                'color': color,
                'components': scores,
                'weights': weights
            }
            
        except Exception as e:
            logger.error(f"Overall sentiment calculation error: {e}")
            return {
                'score': 50,
                'category': 'Neutral',
                'color': 'secondary',
                'components': {},
                'error': str(e)
            }
    
    def _get_personalized_score(self, symbol: str, user_id: int, stock_metrics: Dict) -> Dict[str, Any]:
        """Get personalized recommendation score based on user preferences"""
        try:
            adaptive_learning = AdaptiveLearningDB(user_id)
            
            # Get user's feature preferences
            user_profile = adaptive_learning.get_user_profile_summary()
            
            if not user_profile:
                return {'score': 50, 'explanation': 'No user preferences available'}
            
            # Calculate personalized score
            score = adaptive_learning.calculate_stock_score(stock_metrics)
            
            # Get explanation of why this stock matches user preferences
            explanation = self._generate_personalized_explanation(
                stock_metrics, user_profile
            )
            
            return {
                'score': round(score * 100, 2),  # Convert to 0-100 scale
                'explanation': explanation,
                'user_profile_summary': user_profile
            }
            
        except Exception as e:
            logger.error(f"Personalized scoring error for user {user_id}: {e}")
            return {'score': 50, 'explanation': 'Error calculating personalized score'}
    
    def _generate_personalized_explanation(self, stock_metrics: Dict, user_profile: Dict) -> str:
        """Generate explanation of personalized recommendation"""
        explanations = []
        
        # Check sector preference
        sector = stock_metrics.get('sector', 'Unknown')
        sector_prefs = user_profile.get('sector_preferences', {})
        if sector in sector_prefs and sector_prefs[sector] > 0:
            explanations.append(f"You have shown interest in {sector} sector stocks")
        
        # Check PE ratio preference pattern
        pe_ratio = stock_metrics.get('pe_ratio', 0)
        if pe_ratio > 0 and pe_ratio < 20:
            explanations.append("This stock has an attractive P/E ratio based on your preferences")
        
        # Check sentiment alignment
        sentiment = stock_metrics.get('sentiment_score', 0)
        if sentiment > 0.6:
            explanations.append("Strong positive sentiment aligns with your successful picks")
        
        if not explanations:
            return "This recommendation is based on general market analysis"
        
        return ". ".join(explanations) + "."
    
    def _generate_recommendation(self, technical: Dict, fundamental: Dict, sentiment: Dict, personalized: Dict = None) -> Dict[str, Any]:
        """Generate overall buy/sell/hold recommendation"""
        try:
            # Combine scores with weights
            scores = {
                'technical': technical.get('score', 50),
                'fundamental': fundamental.get('score', 50),
                'sentiment': sentiment.get('score', 50)
            }
            
            # Add personalized score if available
            if personalized:
                scores['personalized'] = personalized.get('score', 50)
                weights = {'technical': 0.25, 'fundamental': 0.25, 'sentiment': 0.25, 'personalized': 0.25}
            else:
                weights = {'technical': 0.4, 'fundamental': 0.4, 'sentiment': 0.2}
            
            # Calculate weighted average
            overall_score = sum(scores[key] * weights[key] for key in scores if key in weights)
            
            # Generate recommendation
            if overall_score >= 70:
                recommendation = 'BUY'
                confidence = 'High'
                color = 'success'
            elif overall_score >= 55:
                recommendation = 'BUY'
                confidence = 'Medium'
                color = 'success'
            elif overall_score >= 45:
                recommendation = 'HOLD'
                confidence = 'Medium'
                color = 'warning'
            else:
                recommendation = 'SELL'
                confidence = 'Medium' if overall_score >= 30 else 'High'
                color = 'danger'
            
            return {
                'action': recommendation,
                'confidence': confidence,
                'score': round(overall_score, 2),
                'color': color,
                'component_scores': scores,
                'weights': weights,
                'reasoning': self._generate_recommendation_reasoning(scores, recommendation)
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return {
                'action': 'HOLD',
                'confidence': 'Low',
                'score': 50,
                'color': 'secondary',
                'error': str(e)
            }
    
    def _generate_recommendation_reasoning(self, scores: Dict, recommendation: str) -> List[str]:
        """Generate reasoning for the recommendation"""
        reasoning = []
        
        if recommendation == 'BUY':
            if scores.get('technical', 0) > 60:
                reasoning.append("Strong technical indicators support upward momentum")
            if scores.get('fundamental', 0) > 60:
                reasoning.append("Solid fundamental metrics indicate good value")
            if scores.get('sentiment', 0) > 60:
                reasoning.append("Positive market sentiment and news coverage")
            if scores.get('personalized', 0) > 60:
                reasoning.append("Aligns well with your investment preferences")
        
        elif recommendation == 'SELL':
            if scores.get('technical', 0) < 40:
                reasoning.append("Technical indicators suggest downward pressure")
            if scores.get('fundamental', 0) < 40:
                reasoning.append("Fundamental analysis shows concerning metrics")
            if scores.get('sentiment', 0) < 40:
                reasoning.append("Negative sentiment and unfavorable news")
        
        else:  # HOLD
            reasoning.append("Mixed signals suggest a wait-and-see approach")
            reasoning.append("Consider monitoring for clearer trends")
        
        return reasoning
    
    def _save_analysis(self, user_id: int, symbol: str, analysis_data: Dict):
        """Save analysis results to database"""
        try:
            analysis = StockAnalysis(
                user_id=user_id,
                symbol=symbol,
                analysis_data=analysis_data,
                date=datetime.now()
            )
            db.session.add(analysis)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving analysis for {symbol}: {e}")
            db.session.rollback()
    
    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized stock recommendations for a user"""
        try:
            adaptive_learning = AdaptiveLearningDB(user_id)
            recommended_stocks = adaptive_learning.get_recommended_stocks(limit)
            
            # Enhance recommendations with current analysis
            enhanced_recommendations = []
            for stock_info in recommended_stocks:
                try:
                    symbol = stock_info['symbol']
                    analysis = self.analyze_stock(symbol, user_id)
                    
                    enhanced_recommendations.append({
                        'symbol': symbol,
                        'recommendation_score': stock_info['score'],
                        'current_analysis': analysis,
                        'reasons': stock_info.get('reasons', [])
                    })
                except Exception as e:
                    logger.warning(f"Could not analyze recommended stock {stock_info.get('symbol', 'unknown')}: {e}")
                    continue
            
            return enhanced_recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return []
    
    def record_user_interaction(self, user_id: int, symbol: str, interaction_type: str, **kwargs):
        """Record user interaction with a stock for learning purposes"""
        try:
            # Update or create stock preference record
            preference = StockPreference.query.filter_by(
                user_id=user_id, symbol=symbol
            ).first()
            
            if not preference:
                preference = StockPreference(user_id=user_id, symbol=symbol)
                db.session.add(preference)
            
            # Update based on interaction type
            if interaction_type == 'view':
                preference.view_count += 1
                preference.last_viewed = datetime.now()
                preference.total_view_time += kwargs.get('view_time', 0)
            
            elif interaction_type == 'like':
                preference.liked = True
                preference.feedback_date = datetime.now()
                
                # Store current metrics for learning
                current_analysis = self.analyze_stock(symbol, user_id)
                preference.metrics_at_feedback = current_analysis.get('stock_data', {})
            
            elif interaction_type == 'dislike':
                preference.liked = False
                preference.feedback_date = datetime.now()
            
            elif interaction_type == 'purchase':
                preference.purchased = True
                preference.purchase_date = datetime.now()
                preference.purchase_price = kwargs.get('price')
            
            db.session.commit()
            
            # Update adaptive learning model
            adaptive_learning = AdaptiveLearningDB(user_id)
            adaptive_learning.record_user_feedback(symbol, interaction_type, **kwargs)
            
        except Exception as e:
            logger.error(f"Error recording interaction for user {user_id}, stock {symbol}: {e}")
            db.session.rollback()