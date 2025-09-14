from .valuation_analyzer import ValuationAnalyzer
from .improved_ml_engine import ImprovedMLEngine
from .fundamental_analysis import FundamentalAnalyzer
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import logging
import yfinance as yf
from datetime import datetime, timedelta

class IntegratedAnalysis:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ml_engine = ImprovedMLEngine()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.valuation_analyzer = ValuationAnalyzer()
        self.symbol = None
        self.weights = {
            'value_company': {
                'fundamental': 0.6,
                'technical': 0.2,
                'valuation': 0.2
            },
            'growth_company': {
                'fundamental': 0.5,
                'technical': 0.3,
                'valuation': 0.2
            }
        }

    def _validate_percentage(self, value: float, min_val: float = -100, max_val: float = 100) -> float:
        """Validate and cap percentage values"""
        try:
            if not isinstance(value, (int, float)) or np.isnan(value):
                return 0.0
            return float(min(max(value, min_val), max_val))
        except:
            return 0.0

    def _validate_ratio(self, value: float, min_val: float = 0, max_val: float = 1) -> float:
        """Validate and cap ratio values"""
        try:
            if not isinstance(value, (int, float)) or np.isnan(value):
                return min_val
            return float(min(max(value, min_val), max_val))
        except:
            return min_val

    def analyze_stock(self, symbol: str) -> Dict:
        try:
            self.symbol = symbol
            self.logger.info(f"Fetching data for {symbol}...")
            
            # Get valuation analysis
            valuation_analysis = self.valuation_analyzer.calculate_company_valuation(symbol)
            
            # Get other analyses
            rotc_analysis = self.fundamental_analyzer.analyze_rotc_trend(symbol)
            growth_analysis = self.fundamental_analyzer.analyze_growth_metrics(symbol)
            technical_analysis = self.get_technical_analysis(symbol)
            risk_metrics = self.calculate_risk_metrics(symbol)
            
            fundamental_score = self.fundamental_analyzer.calculate_fundamental_score(
                rotc_analysis or {}, 
                growth_analysis or {}
            )
            
            company_type = fundamental_score.get('company_type', 'value')
            weights = self.weights[f'{company_type}_company']
            
            integrated_score = self.calculate_integrated_score(
                fundamental_score or {},
                technical_analysis or {},
                valuation_analysis or {},
                weights,
                risk_metrics or {}
            )
            
            # Construct the result dictionary with a structure that matches what the template expects
            return {
                'symbol': symbol,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'company_type': company_type,
                'fundamental_analysis': {
                    'score': fundamental_score.get('fundamental_score', 0),
                    'rotc_data': rotc_analysis,
                    'growth_data': growth_analysis
                },
                'technical_analysis': technical_analysis or {},
                'valuation_analysis': valuation_analysis or {},
                'risk_metrics': risk_metrics or {},
                'integrated_score': integrated_score,
                'recommendation': self.generate_recommendation(
                    integrated_score, 
                    risk_metrics or {},
                    valuation_analysis or {}
                ),
                # Add the integrated_analysis key that the template is looking for
                'integrated_analysis': {
                    'fundamental_analysis': {
                        'rotc_data': rotc_analysis,
                        'growth_data': growth_analysis
                    },
                    'technical_analysis': technical_analysis or {},
                    'valuation_analysis': valuation_analysis or {}
                }
            }
                
        except Exception as e:
            self.logger.error(f"Error in integrated analysis: {str(e)}")
            return {}

    def normalize_confidence(self, raw_confidence: float) -> float:
        """Normalize and cap confidence level between 0-100%."""
        if not isinstance(raw_confidence, (int, float)) or np.isnan(raw_confidence):
            return 0.0
        capped_confidence = min(max(raw_confidence, 0), 100)  # Cap confidence
        self.logger.debug(f"Raw Confidence: {raw_confidence}, Capped Confidence: {capped_confidence}")
        return capped_confidence

    def get_technical_analysis(self, symbol: str) -> Dict:
        try:
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.Timedelta(days=365)
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date)

            if data.empty:
                return self._get_default_technical_analysis()

            # Prepare features (now returns DataFrame only)
            features_df, targets_series = self.ml_engine.prepare_features(data)
            if features_df.empty:
                return self._get_default_technical_analysis()

            # Calculate returns for targets
            returns = data['Close'].pct_change().shift(-1)  # Next day returns

            # Align features and targets
            features_df = features_df[:-1]  # Remove last row since we won't have target
            returns = returns[:-1]  # Remove last row (NaN from shift)
            
            # Ensure index alignment
            common_index = features_df.index.intersection(returns.index)
            features_df = features_df.loc[common_index]
            returns = returns.loc[common_index]

            if len(features_df) > 0:
                # Train model
                training_features = features_df.values
                training_targets = returns.values
                self.ml_engine.train_model(training_features, training_targets)

                # Prepare latest features for prediction
                latest_features = features_df.iloc[-1:].values
                prediction, confidence = self.ml_engine.predict(latest_features)

                # Ensure scalar values
                prediction = float(np.mean(prediction) if isinstance(prediction, np.ndarray) else prediction)
                confidence = float(np.mean(confidence) if isinstance(confidence, np.ndarray) else confidence)
                
                current_price = float(data['Close'].iloc[-1])
                technical_score = self.calculate_technical_score(prediction, confidence, data)

                return {
                    'success': True,
                    'ml_prediction': prediction,
                    'confidence': confidence,
                    'technical_score': technical_score,
                    'price_metrics': {
                        'current_price': current_price,
                        'predicted_price': current_price * (1 + prediction),
                        'volatility': float(data['Close'].pct_change().std() * np.sqrt(252))
                    }
                }

            return self._get_default_technical_analysis()

        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {str(e)}")
            return self._get_default_technical_analysis()

    def _get_default_technical_analysis(self) -> Dict:
        """Modified default technical analysis with current price."""
        try:
            if self.symbol:  # Add class variable for current symbol
                stock = yf.Ticker(self.symbol)
                current = stock.history(period='1d')
                if not current.empty:
                    current_price = float(current['Close'].iloc[-1])
                    return {
                        'success': False,
                        'ml_prediction': 0.0,
                        'confidence': 0.0,
                        'technical_score': 50.0,
                        'price_metrics': {
                            'current_price': current_price,
                            'predicted_price': current_price,  # Same as current when no prediction
                            'volatility': 0.0
                        }
                    }
            return {
                'success': False,
                'ml_prediction': 0.0,
                'confidence': 0.0,
                'technical_score': 50.0,
                'price_metrics': {
                    'current_price': 0.0,
                    'predicted_price': 0.0,
                    'volatility': 0.0
                }
            }
        except Exception as e:
            self.logger.error(f"Error in default technical analysis: {str(e)}")
            return {
                'success': False,
                'ml_prediction': 0.0,
                'confidence': 0.0,
                'technical_score': 50.0,
                'price_metrics': {
                    'current_price': 0.0,
                    'predicted_price': 0.0,
                    'volatility': 0.0
                }
            }

    def calculate_technical_score(self, prediction: float, confidence: float, price_data: pd.DataFrame) -> float:
        try:
            returns = price_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) # Annualize daily volatility
            
            prediction_score = min(max(50 + (prediction / volatility) * 100, 0), 100)      
            confidence_score = min(max(confidence, 0), 100)  # Ensure normalized confidence is used
            
            momentum = returns.mean() * 252 # Annualized momentum
            momentum_score = min(max(50 + (momentum / volatility) * 100, 0), 100)
            
            # Weighted technical score
            technical_score = (
                prediction_score * 0.4 +
                confidence_score * 0.4 +
                momentum_score * 0.2
            )
            
            self.logger.debug(f"Prediction Score: {prediction_score}, Confidence Score: {confidence_score}, Momentum Score: {momentum_score}")
            return float(min(max(technical_score, 0), 100))
            
        except Exception as e:
            self.logger.error(f"Error calculating technical score: {str(e)}")
            return 50.0

    def calculate_integrated_score(self, fundamental_score: Dict, technical_analysis: Dict, 
                             valuation_analysis: Dict, weights: Dict, risk_metrics: Dict) -> float:
        try:
            fundamental_weight = weights.get('fundamental', 0.6)
            technical_weight = weights.get('technical', 0.2)
            valuation_weight = weights.get('valuation', 0.2)
            
            fundamental_base = fundamental_score.get('fundamental_score', 0)
            technical_base = technical_analysis.get('technical_score', 0)
            
            valuation_score = self.calculate_valuation_score(valuation_analysis)
            
            volatility = risk_metrics.get('volatility', 0)
            risk_factor = max(1 - (volatility - 20) / 100, 0.5) if volatility > 20 else 1
            
            final_score = (
                fundamental_base * fundamental_weight +
                technical_base * technical_weight +
                valuation_score * valuation_weight
            ) * risk_factor
            
            return float(min(max(final_score, 0), 100))
            
        except Exception as e:
            self.logger.error(f"Error calculating integrated score: {str(e)}")
            return 0.0

    def calculate_risk_metrics(self, symbol: str) -> Dict:
        """Calculate risk metrics for a given stock symbol."""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1y")
            
            if data.empty:
                self.logger.warning(f"No data available for symbol: {symbol}")
                return {}
        
            # Calculate returns with NaN handling
            returns = data['Close'].pct_change().dropna()
            if len(returns) < 30:
                self.logger.warning(f"Not enough data points for returns for symbol: {symbol}")
                return {}
            
            # Annual Volatility
            daily_volatility = returns.std()
            annual_volatility = daily_volatility * np.sqrt(252) * 100  # Convert to percentage
            self.logger.debug(f"Annual Volatility for {symbol}: {annual_volatility}")
            
            # Maximum Drawdown
            peak = data['Close'].cummax()
            drawdown = (data['Close'] - peak) / peak
            max_drawdown = drawdown.min() * 100  # Convert to percentage
            self.logger.debug(f"Max Drawdown for {symbol}: {max_drawdown}")
            
            # VaR (Value at Risk at 95%)
            var_95 = np.percentile(returns, 5) * 100  # Convert to percentage
            self.logger.debug(f"VaR at 95% for {symbol}: {var_95}")
            
            # Sharpe Ratio Calculation
            avg_return = returns.mean()
            sharpe_ratio = (avg_return * np.sqrt(252)) / daily_volatility if daily_volatility != 0 else 0
            self.logger.debug(f"Sharpe Ratio for {symbol}: {sharpe_ratio}")
            
            # Return risk metrics with validation
            return {
                'volatility': self._validate_percentage(annual_volatility, 0, 100),
                'max_drawdown': self._validate_percentage(max_drawdown, -100, 0),
                'var_95': self._validate_percentage(var_95, -50, 0),
                'sharpe_ratio': self._validate_ratio(sharpe_ratio, -3, 3),
                'avg_return': self._validate_percentage(avg_return * 252 * 100, -100, 100),
                'risk_level': 'High' if annual_volatility > 30 else 'Moderate' if annual_volatility > 15 else 'Low'
            }
                    
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}

    def calculate_valuation_score(self, valuation_analysis: Dict) -> float:
        try:
            if not valuation_analysis.get('success', False):
                return 50.0
            
            target_price = valuation_analysis.get('target_price', 0)
            current_price = valuation_analysis.get('current_price', 0)
            confidence = valuation_analysis.get('confidence', 0)
            
            if current_price <= 0 or target_price <= 0:
                return 50.0
            
            upside = ((target_price / current_price) - 1) * 100
            
            base_score = 50 + (upside / 2)
            base_score = min(max(base_score, 0), 100)
            
            final_score = base_score * confidence
            
            return float(final_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating valuation score: {str(e)}")
            return 50.0

    def generate_recommendation(self, integrated_score: float, risk_metrics: Dict, 
                              valuation_analysis: Dict) -> Dict:
        try:
            volatility = risk_metrics.get('volatility', 0)
            
            if volatility > 30:
                thresholds = {'strong_buy': 85, 'buy': 65, 'hold': 45, 'reduce': 25}
            else:
                thresholds = {'strong_buy': 80, 'buy': 60, 'hold': 40, 'reduce': 20}
            
            if integrated_score >= thresholds['strong_buy']:
                action = "Strong Buy"
                reasoning = ["Strong fundamentals and technical indicators"]
            elif integrated_score >= thresholds['buy']:
                action = "Buy"
                reasoning = ["Good overall metrics with positive outlook"]
            elif integrated_score >= thresholds['hold']:
                action = "Hold"
                reasoning = ["Mixed signals, monitor for changes"]
            elif integrated_score >= thresholds['reduce']:
                action = "Reduce"
                reasoning = ["Weak performance metrics"]
            else:
                action = "Sell"
                reasoning = ["Poor fundamental and technical indicators"]
            
            if valuation_analysis.get('success', False):
                upside = valuation_analysis.get('upside_potential', 0)
                if abs(upside) > 15:
                    reasoning.append(
                        f"{'Significant upside' if upside > 0 else 'Significant downside'} "
                        f"potential of {abs(upside):.1f}%"
                    )
            
            if volatility > 30:
                reasoning.append("High volatility environment - consider position sizing")
            
            if valuation_analysis.get('success', False):
                reasoning.append(f"Valuation based on {valuation_analysis.get('primary_method', 'DCF')}")
            
            return {
                'action': action,
                'score': float(integrated_score),
                'reasoning': reasoning,
                'risk_context': 'High' if volatility > 30 else 'Normal',
                'valuation_confidence': valuation_analysis.get('confidence', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {str(e)}")
            return {}
        