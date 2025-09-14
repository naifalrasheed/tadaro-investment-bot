"""
Portfolio Service  
Business logic for portfolio management, optimization, and analysis
Comprehensive service preserving ALL original functionality
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import io

from models import db, Portfolio, User
from .stock_service import StockService

logger = logging.getLogger(__name__)

class PortfolioService:
    """Service class for portfolio-related business logic"""
    
    def __init__(self, stock_service: StockService = None):
        self.stock_service = stock_service or StockService()
    
    def create_portfolio(self, user_id: int, name: str, stocks: List[Dict]) -> Dict[str, Any]:
        """Create a new portfolio for user"""
        try:
            # Validate and enhance stock data
            enhanced_stocks = []
            for stock in stocks:
                enhanced_stock = {
                    'symbol': stock['symbol'].upper().strip(),
                    'shares': float(stock.get('shares', 0)),
                    'purchase_price': float(stock.get('purchase_price', 0)),
                    'purchase_date': stock.get('purchase_date', datetime.now().isoformat()),
                    'sector': stock.get('sector', 'Unknown'),
                    'added_date': datetime.now().isoformat()
                }
                enhanced_stocks.append(enhanced_stock)
            
            portfolio = Portfolio(
                user_id=user_id,
                name=name,
                stocks=enhanced_stocks,
                created_date=datetime.now()
            )
            db.session.add(portfolio)
            db.session.commit()
            
            logger.info(f"Created portfolio '{name}' with {len(enhanced_stocks)} stocks for user {user_id}")
            
            return {
                'id': portfolio.id,
                'name': portfolio.name,
                'stocks': portfolio.stocks,
                'created_date': portfolio.created_date.isoformat(),
                'stock_count': len(enhanced_stocks)
            }
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            db.session.rollback()
            raise
    
    def get_user_portfolios(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all portfolios for a user"""
        portfolios = Portfolio.query.filter_by(user_id=user_id).order_by(Portfolio.created_date.desc()).all()
        
        enhanced_portfolios = []
        for p in portfolios:
            try:
                stock_count = len(p.stocks) if p.stocks else 0
                
                enhanced_portfolios.append({
                    'id': p.id,
                    'name': p.name, 
                    'stocks': p.stocks,
                    'created_date': p.created_date.isoformat(),
                    'stock_count': stock_count,
                    'last_updated': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Error enhancing portfolio {p.id}: {e}")
                enhanced_portfolios.append({
                    'id': p.id,
                    'name': p.name,
                    'stocks': p.stocks or [],
                    'created_date': p.created_date.isoformat() if p.created_date else datetime.now().isoformat(),
                    'stock_count': 0
                })
        
        return enhanced_portfolios
    
    def import_from_file(self, file, user_id: int) -> Dict[str, Any]:
        """Import portfolio from uploaded file (CSV/Excel)"""
        try:
            filename = file.filename.lower()
            
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                raise ValueError("Unsupported file format. Please use CSV or Excel files.")
            
            # Expected columns: Symbol, Shares, Price (optional)
            required_columns = ['symbol']
            if not any(col.lower() in [c.lower() for c in df.columns] for col in required_columns):
                raise ValueError("File must contain at least a 'Symbol' column")
            
            # Normalize column names
            df.columns = [col.lower().strip() for col in df.columns]
            
            stocks = []
            for _, row in df.iterrows():
                symbol = str(row.get('symbol', '')).upper().strip()
                if not symbol:
                    continue
                
                stock = {
                    'symbol': symbol,
                    'shares': float(row.get('shares', 1)),
                    'purchase_price': float(row.get('price', 0)) if pd.notna(row.get('price')) else 0,
                    'sector': str(row.get('sector', 'Unknown')) if pd.notna(row.get('sector')) else 'Unknown'
                }
                stocks.append(stock)
            
            if not stocks:
                raise ValueError("No valid stock data found in file")
            
            # Create portfolio with imported name or default
            portfolio_name = f"Imported Portfolio - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            return self.create_portfolio(user_id, portfolio_name, stocks)
            
        except Exception as e:
            logger.error(f"Error importing portfolio: {e}")
            raise
    
    def calculate_portfolio_value(self, portfolio_id: int) -> Dict[str, Any]:
        """Calculate current portfolio value and metrics"""
        try:
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio or not portfolio.stocks:
                return {'total_value': 0, 'positions': []}
            
            total_value = 0
            positions = []
            total_cost_basis = 0
            
            for stock in portfolio.stocks:
                try:
                    symbol = stock['symbol']
                    shares = float(stock.get('shares', 0))
                    purchase_price = float(stock.get('purchase_price', 0))
                    
                    # Get current stock data
                    stock_data = self.stock_service.api_client.get_stock_data(symbol)
                    current_price = stock_data.get('price', 0)
                    
                    current_value = shares * current_price
                    cost_basis = shares * purchase_price
                    gain_loss = current_value - cost_basis
                    gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
                    
                    position = {
                        'symbol': symbol,
                        'shares': shares,
                        'purchase_price': purchase_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'cost_basis': cost_basis,
                        'gain_loss': gain_loss,
                        'gain_loss_percent': gain_loss_percent,
                        'sector': stock.get('sector', 'Unknown')
                    }
                    
                    positions.append(position)
                    total_value += current_value
                    total_cost_basis += cost_basis
                    
                except Exception as e:
                    logger.warning(f"Error calculating value for {stock.get('symbol', 'unknown')}: {e}")
                    continue
            
            total_gain_loss = total_value - total_cost_basis
            total_gain_loss_percent = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
            
            return {
                'total_value': round(total_value, 2),
                'total_cost_basis': round(total_cost_basis, 2),
                'total_gain_loss': round(total_gain_loss, 2),
                'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                'positions': positions,
                'position_count': len(positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return {'total_value': 0, 'positions': [], 'error': str(e)}
    
    def calculate_performance_metrics(self, portfolio_id: int) -> Dict[str, Any]:
        """Calculate advanced portfolio performance metrics"""
        try:
            portfolio_value = self.calculate_portfolio_value(portfolio_id)
            positions = portfolio_value.get('positions', [])
            
            if not positions:
                return {'metrics': {}, 'error': 'No positions found'}
            
            # Calculate sector allocation
            sector_allocation = {}
            total_value = portfolio_value.get('total_value', 0)
            
            for position in positions:
                sector = position.get('sector', 'Unknown')
                value = position.get('current_value', 0)
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = {'value': 0, 'percentage': 0}
                
                sector_allocation[sector]['value'] += value
                sector_allocation[sector]['percentage'] = (sector_allocation[sector]['value'] / total_value * 100) if total_value > 0 else 0
            
            # Calculate concentration metrics
            position_weights = [pos.get('current_value', 0) / total_value for pos in positions if total_value > 0]
            max_position_weight = max(position_weights) * 100 if position_weights else 0
            
            # Simple risk metrics
            gains_losses = [pos.get('gain_loss_percent', 0) for pos in positions]
            avg_gain_loss = sum(gains_losses) / len(gains_losses) if gains_losses else 0
            volatility = np.std(gains_losses) if len(gains_losses) > 1 else 0
            
            return {
                'sector_allocation': sector_allocation,
                'max_position_weight': round(max_position_weight, 2),
                'average_gain_loss_percent': round(avg_gain_loss, 2),
                'volatility': round(volatility, 2),
                'number_of_positions': len(positions),
                'diversification_score': round(100 - max_position_weight, 2)  # Simple diversification metric
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {'metrics': {}, 'error': str(e)}
    
    def analyze_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """Comprehensive portfolio analysis"""
        try:
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Get current values and performance
            portfolio_value = self.calculate_portfolio_value(portfolio_id)
            performance_metrics = self.calculate_performance_metrics(portfolio_id)
            
            # Analyze individual positions
            position_analyses = []
            for position in portfolio_value.get('positions', []):
                try:
                    symbol = position['symbol']
                    analysis = self.stock_service.analyze_stock(
                        symbol=symbol,
                        user_id=portfolio.user_id,
                        market='US'
                    )
                    
                    position_analysis = {
                        'symbol': symbol,
                        'position_data': position,
                        'stock_analysis': {
                            'recommendation': analysis.get('recommendation', {}),
                            'technical_score': analysis.get('technical_analysis', {}).get('score'),
                            'fundamental_score': analysis.get('fundamental_analysis', {}).get('score'),
                            'sentiment_score': analysis.get('sentiment_analysis', {}).get('overall_sentiment', {}).get('score')
                        }
                    }
                    position_analyses.append(position_analysis)
                    
                except Exception as e:
                    logger.warning(f"Could not analyze position {symbol}: {e}")
                    continue
            
            return {
                'portfolio_id': portfolio_id,
                'portfolio_name': portfolio.name,
                'value_metrics': portfolio_value,
                'performance_metrics': performance_metrics,
                'position_analyses': position_analyses,
                'analysis_date': datetime.now().isoformat(),
                'recommendations': self._generate_portfolio_recommendations(position_analyses, performance_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio {portfolio_id}: {e}")
            raise
    
    def comprehensive_analysis(self, portfolio_id: int) -> Dict[str, Any]:
        """Even more comprehensive analysis including risk metrics"""
        try:
            basic_analysis = self.analyze_portfolio(portfolio_id)
            
            # Add advanced risk metrics
            positions = basic_analysis.get('position_analyses', [])
            
            # Calculate correlation matrix (simplified)
            risk_metrics = self._calculate_risk_metrics(positions)
            
            # Add rebalancing suggestions
            rebalancing_suggestions = self._generate_rebalancing_suggestions(
                basic_analysis.get('performance_metrics', {}),
                positions
            )
            
            return {
                **basic_analysis,
                'risk_metrics': risk_metrics,
                'rebalancing_suggestions': rebalancing_suggestions,
                'comprehensive': True
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise
    
    def optimize_portfolio(self, portfolio_id: int, risk_tolerance: str = 'moderate', method: str = 'sharpe') -> Dict[str, Any]:
        """Portfolio optimization using modern portfolio theory principles"""
        try:
            current_analysis = self.analyze_portfolio(portfolio_id)
            positions = current_analysis.get('position_analyses', [])
            
            if not positions:
                raise ValueError("No positions to optimize")
            
            # Simple optimization logic (placeholder for more sophisticated methods)
            optimization_suggestions = []
            
            for position in positions:
                symbol = position['symbol']
                current_weight = position['position_data'].get('current_value', 0)
                recommendation = position['stock_analysis'].get('recommendation', {})
                
                suggested_action = 'HOLD'
                suggested_weight = current_weight
                
                # Simple optimization based on recommendation scores
                rec_score = recommendation.get('score', 50)
                
                if rec_score >= 70:
                    suggested_action = 'INCREASE'
                    suggested_weight = min(current_weight * 1.2, current_weight + 0.05)  # Increase by up to 20% or 5%
                elif rec_score <= 30:
                    suggested_action = 'DECREASE'
                    suggested_weight = max(current_weight * 0.8, current_weight - 0.05)  # Decrease by up to 20% or 5%
                
                optimization_suggestions.append({
                    'symbol': symbol,
                    'current_weight': current_weight,
                    'suggested_weight': suggested_weight,
                    'suggested_action': suggested_action,
                    'reason': f"Based on recommendation score: {rec_score}"
                })
            
            return {
                'portfolio_id': portfolio_id,
                'optimization_method': method,
                'risk_tolerance': risk_tolerance,
                'current_analysis': current_analysis,
                'optimization_suggestions': optimization_suggestions,
                'optimization_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            raise
    
    def get_portfolio_summary(self, portfolio_id: int) -> Dict[str, Any]:
        """Get portfolio summary for API endpoints"""
        try:
            value_data = self.calculate_portfolio_value(portfolio_id)
            performance_data = self.calculate_performance_metrics(portfolio_id)
            
            return {
                'portfolio_id': portfolio_id,
                'total_value': value_data.get('total_value'),
                'total_gain_loss': value_data.get('total_gain_loss'),
                'total_gain_loss_percent': value_data.get('total_gain_loss_percent'),
                'position_count': value_data.get('position_count'),
                'top_sectors': dict(list(performance_data.get('sector_allocation', {}).items())[:3]),
                'diversification_score': performance_data.get('diversification_score'),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    def _generate_portfolio_recommendations(self, positions: List[Dict], performance_metrics: Dict) -> List[str]:
        """Generate actionable portfolio recommendations"""
        recommendations = []
        
        try:
            # Check concentration risk
            max_weight = performance_metrics.get('max_position_weight', 0)
            if max_weight > 20:
                recommendations.append(f"Consider reducing concentration risk - largest position is {max_weight:.1f}% of portfolio")
            
            # Check diversification
            diversification = performance_metrics.get('diversification_score', 100)
            if diversification < 70:
                recommendations.append("Consider adding more diverse positions to improve diversification")
            
            # Check sector allocation
            sector_allocation = performance_metrics.get('sector_allocation', {})
            if len(sector_allocation) < 3:
                recommendations.append("Consider diversifying across more sectors")
            
            # Analyze individual position recommendations
            strong_buys = [p for p in positions if p.get('stock_analysis', {}).get('recommendation', {}).get('action') == 'BUY']
            sells = [p for p in positions if p.get('stock_analysis', {}).get('recommendation', {}).get('action') == 'SELL']
            
            if len(strong_buys) > 0:
                recommendations.append(f"Consider increasing positions in {len(strong_buys)} stocks with BUY recommendations")
            
            if len(sells) > 0:
                recommendations.append(f"Consider reviewing {len(sells)} positions with SELL recommendations")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _calculate_risk_metrics(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        try:
            if not positions:
                return {}
            
            # Simple risk calculations
            scores = []
            for pos in positions:
                analysis = pos.get('stock_analysis', {})
                tech_score = analysis.get('technical_score', 50)
                fund_score = analysis.get('fundamental_score', 50) 
                sent_score = analysis.get('sentiment_score', 50)
                
                avg_score = (tech_score + fund_score + sent_score) / 3
                scores.append(avg_score)
            
            portfolio_score = sum(scores) / len(scores) if scores else 50
            score_volatility = np.std(scores) if len(scores) > 1 else 0
            
            return {
                'portfolio_score': round(portfolio_score, 2),
                'score_volatility': round(score_volatility, 2),
                'risk_level': 'High' if score_volatility > 20 else 'Medium' if score_volatility > 10 else 'Low'
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _generate_rebalancing_suggestions(self, performance_metrics: Dict, positions: List[Dict]) -> List[Dict]:
        """Generate rebalancing suggestions"""
        suggestions = []
        
        try:
            # Simple rebalancing based on equal weight target
            total_positions = len(positions)
            target_weight = 100 / total_positions if total_positions > 0 else 0
            
            for position in positions:
                symbol = position['symbol']
                current_value = position['position_data'].get('current_value', 0)
                
                # Calculate current weight (this would need total portfolio value)
                # Simplified suggestion logic
                suggestion = {
                    'symbol': symbol,
                    'current_weight': 'N/A',  # Would calculate with total portfolio value
                    'target_weight': f"{target_weight:.1f}%",
                    'action': 'REBALANCE',
                    'priority': 'Medium'
                }
                suggestions.append(suggestion)
            
        except Exception as e:
            logger.warning(f"Error generating rebalancing suggestions: {e}")
        
        return suggestions