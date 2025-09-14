"""
Specialized Financial Agents for Investment Bot

This module implements the dedicated analysis agents that specialize
in different aspects of investment analysis:
- Technical Analysis Agent
- Fundamental Analysis Agent
- Sentiment Analysis Agent
- Risk Assessment Agent

Each agent has specialized knowledge and capabilities for its domain.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from .ml_engine import MarketMLEngine, MarketPatternLearner, MarketPredictor

class BaseAgent:
    """Base class for all specialized agents with common functionality."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
    def format_confidence(self, confidence: float) -> float:
        """Format confidence to be in 0-1 range"""
        return min(max(float(confidence), 0.0), 1.0)
    
    def get_recommendation(self) -> Dict:
        """Return a recommendation stub - to be implemented by subclasses"""
        return {
            "confidence": 0.0,
            "recommendation": "neutral",
            "explanation": "Base agent does not provide recommendations"
        }

class TechnicalAnalysisAgent(BaseAgent):
    """
    Agent specializing in technical market analysis.
    
    This agent analyzes price patterns, trends, and technical indicators
    to predict future price movements.
    """
    
    def __init__(self, ml_engine: Optional[MarketMLEngine] = None):
        """
        Initialize the technical analysis agent.
        
        Args:
            ml_engine: Optional ML engine to use for predictions
        """
        super().__init__("technical_analysis")
        self.ml_engine = ml_engine or MarketMLEngine()
        self.predictor = MarketPredictor(self.ml_engine)
        
    def analyze(self, symbol: str, market_data: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """
        Perform technical analysis on the given market data.
        
        Args:
            symbol: Stock ticker symbol
            market_data: Dictionary containing market data (OHLCV)
            user_preferences: Optional user preferences to personalize analysis
            
        Returns:
            Dictionary containing technical analysis results
        """
        try:
            self.logger.info(f"Performing technical analysis for {symbol}")
            
            # Extract price data
            df = self._prepare_dataframe(market_data)
            if df.empty:
                return self._get_default_result(symbol)
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Determine trend
            trend = self._determine_trend(df, indicators)
            
            # Calculate support and resistance
            support, resistance = self._calculate_support_resistance(df)
            
            # Use ML engine for prediction if available
            ml_prediction = {}
            if len(df) >= 20:  # Ensure enough data for ML prediction
                ml_prediction = self.predictor.predict_price_movement(df)
            
            # Determine overall sentiment
            sentiment, confidence = self._determine_sentiment(trend, indicators, ml_prediction)
            
            volatility = self._calculate_volatility(df)
            
            return {
                "symbol": symbol,
                "sentiment": sentiment,
                "confidence": self.format_confidence(confidence),
                "key_indicators": indicators,
                "trend": trend,
                "support": support,
                "resistance": resistance,
                "volatility": volatility,
                "ml_prediction": ml_prediction.get("predicted_movement", 0),
                "timeframe": ml_prediction.get("time_horizon", "medium_term"),
                "overall_score": self._calculate_overall_score(sentiment, confidence, trend, indicators, volatility, ml_prediction)
            }
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return self._get_default_result(symbol)
    
    def _prepare_dataframe(self, market_data: Dict) -> pd.DataFrame:
        """Convert market data dictionary to pandas DataFrame."""
        try:
            if "history" in market_data and isinstance(market_data["history"], pd.DataFrame):
                return market_data["history"].copy()
                
            if "history" in market_data and isinstance(market_data["history"], dict):
                return pd.DataFrame(market_data["history"])
                
            # Handle case where market_data itself is the OHLCV data
            if "Open" in market_data and "Close" in market_data:
                return pd.DataFrame(market_data)
                
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error preparing dataframe: {e}")
            return pd.DataFrame()
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators from price data."""
        indicators = {}
        
        try:
            # Simple Moving Averages
            df["SMA20"] = df["Close"].rolling(window=20).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()
            df["SMA200"] = df["Close"].rolling(window=200).mean()
            
            # Price relative to SMAs
            last_close = df["Close"].iloc[-1]
            indicators["above_SMA20"] = last_close > df["SMA20"].iloc[-1]
            indicators["above_SMA50"] = last_close > df["SMA50"].iloc[-1]
            indicators["above_SMA200"] = last_close > df["SMA200"].iloc[-1]
            
            # Golden/Death cross
            indicators["golden_cross"] = (
                df["SMA50"].iloc[-1] > df["SMA200"].iloc[-1] and 
                df["SMA50"].iloc[-2] <= df["SMA200"].iloc[-2]
            )
            indicators["death_cross"] = (
                df["SMA50"].iloc[-1] < df["SMA200"].iloc[-1] and 
                df["SMA50"].iloc[-2] >= df["SMA200"].iloc[-2]
            )
            
            # RSI
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))
            indicators["RSI"] = df["RSI"].iloc[-1]
            indicators["RSI_overbought"] = indicators["RSI"] > 70
            indicators["RSI_oversold"] = indicators["RSI"] < 30
            
            # MACD
            df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
            df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = df["EMA12"] - df["EMA26"]
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["Histogram"] = df["MACD"] - df["Signal"]
            
            indicators["MACD"] = df["MACD"].iloc[-1]
            indicators["MACD_Signal"] = df["Signal"].iloc[-1]
            indicators["MACD_Histogram"] = df["Histogram"].iloc[-1]
            indicators["MACD_positive"] = df["MACD"].iloc[-1] > df["Signal"].iloc[-1]
            
            # Bollinger Bands
            df["BB_Middle"] = df["Close"].rolling(window=20).mean()
            df["BB_Std"] = df["Close"].rolling(window=20).std()
            df["BB_Upper"] = df["BB_Middle"] + 2 * df["BB_Std"]
            df["BB_Lower"] = df["BB_Middle"] - 2 * df["BB_Std"]
            
            indicators["BB_Position"] = (last_close - df["BB_Lower"].iloc[-1]) / (df["BB_Upper"].iloc[-1] - df["BB_Lower"].iloc[-1])
            indicators["BB_Width"] = (df["BB_Upper"].iloc[-1] - df["BB_Lower"].iloc[-1]) / df["BB_Middle"].iloc[-1]
            
            # Volume analysis
            df["Volume_SMA20"] = df["Volume"].rolling(window=20).mean()
            indicators["volume_trend"] = "increasing" if df["Volume"].iloc[-1] > df["Volume_SMA20"].iloc[-1] else "decreasing"
            
            # Momentum
            df["ROC"] = df["Close"].pct_change(periods=10) * 100
            indicators["momentum"] = df["ROC"].iloc[-1]
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            
        return indicators
    
    def _determine_trend(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Determine the overall trend based on multiple indicators."""
        trend = {}
        
        try:
            # Short-term trend (5-10 days)
            short_term_signals = [
                indicators.get("above_SMA20", False),
                indicators.get("RSI", 50) > 50,
                indicators.get("MACD_positive", False)
            ]
            short_term_score = sum(short_term_signals) / len(short_term_signals)
            
            # Medium-term trend (20-50 days)
            medium_term_signals = [
                indicators.get("above_SMA50", False),
                df["Close"].iloc[-1] > df["Close"].iloc[-20],
                indicators.get("golden_cross", False),
                not indicators.get("death_cross", False)
            ]
            medium_term_score = sum(medium_term_signals) / len(medium_term_signals)
            
            # Long-term trend (100+ days)
            long_term_signals = [
                indicators.get("above_SMA200", False),
                df["Close"].iloc[-1] > df["Close"].iloc[-100] if len(df) >= 100 else None
            ]
            # Filter out None values
            long_term_signals = [s for s in long_term_signals if s is not None]
            long_term_score = sum(long_term_signals) / len(long_term_signals) if long_term_signals else 0.5
            
            # Overall trend classification
            trend = {
                "short_term": {
                    "score": short_term_score,
                    "classification": "bullish" if short_term_score > 0.6 else "bearish" if short_term_score < 0.4 else "neutral"
                },
                "medium_term": {
                    "score": medium_term_score,
                    "classification": "bullish" if medium_term_score > 0.6 else "bearish" if medium_term_score < 0.4 else "neutral"
                },
                "long_term": {
                    "score": long_term_score,
                    "classification": "bullish" if long_term_score > 0.6 else "bearish" if long_term_score < 0.4 else "neutral"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error determining trend: {e}")
            trend = {
                "short_term": {"score": 0.5, "classification": "neutral"},
                "medium_term": {"score": 0.5, "classification": "neutral"},
                "long_term": {"score": 0.5, "classification": "neutral"}
            }
            
        return trend
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Calculate support and resistance levels."""
        support, resistance = 0.0, 0.0
        
        try:
            if len(df) < 20:
                return support, resistance
                
            # Simple approach: look for recent highs and lows
            last_close = df["Close"].iloc[-1]
            recent_lows = df["Low"].rolling(window=5).min().iloc[-20:]
            recent_highs = df["High"].rolling(window=5).max().iloc[-20:]
            
            # Find support levels below current price
            support_candidates = recent_lows[recent_lows < last_close]
            if not support_candidates.empty:
                support = support_candidates.max()
            else:
                support = df["Low"].min()
                
            # Find resistance levels above current price
            resistance_candidates = recent_highs[recent_highs > last_close]
            if not resistance_candidates.empty:
                resistance = resistance_candidates.min()
            else:
                resistance = df["High"].max()
                
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            
        return support, resistance
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate recent volatility."""
        try:
            if len(df) < 20:
                return 0.5
                
            # Calculate average true range
            df["H-L"] = df["High"] - df["Low"]
            df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
            df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
            df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
            df["ATR"] = df["TR"].rolling(window=14).mean()
            
            # Normalize ATR by price level
            atr_pct = df["ATR"].iloc[-1] / df["Close"].iloc[-1]
            
            # Return normalized volatility (0-1 scale)
            # A typical stock might have 1-2% daily ATR
            volatility = min(atr_pct * 50, 1.0)
            return volatility
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.5
    
    def _determine_sentiment(self, trend: Dict, indicators: Dict, ml_prediction: Dict) -> Tuple[str, float]:
        """Determine overall sentiment and confidence based on indicators and ML."""
        try:
            # Weight the different timeframes
            trend_score = (
                0.5 * trend["short_term"]["score"] +
                0.3 * trend["medium_term"]["score"] +
                0.2 * trend["long_term"]["score"]
            )
            
            # Factor in some indicators
            indicator_score = 0.5  # Neutral default
            indicator_signals = []
            
            if "RSI" in indicators:
                rsi = indicators["RSI"]
                if rsi > 70:
                    indicator_signals.append(0.2)  # Overbought
                elif rsi < 30:
                    indicator_signals.append(0.8)  # Oversold
                else:
                    indicator_signals.append(rsi / 100)
            
            if "MACD_positive" in indicators:
                indicator_signals.append(0.7 if indicators["MACD_positive"] else 0.3)
                
            if "BB_Position" in indicators:
                bb_pos = indicators["BB_Position"]
                # Map Bollinger position to a 0-1 score
                if bb_pos < 0:
                    bb_score = 0.8  # Below lower band, potential bounce
                elif bb_pos > 1:
                    bb_score = 0.2  # Above upper band, potential drop
                else:
                    bb_score = 0.5  # Within bands
                indicator_signals.append(bb_score)
                
            if indicator_signals:
                indicator_score = sum(indicator_signals) / len(indicator_signals)
            
            # Include ML prediction if available
            ml_score = 0.5
            if "predicted_movement" in ml_prediction:
                pred_move = ml_prediction["predicted_movement"]
                # Convert prediction to 0-1 scale
                if pred_move > 0:
                    ml_score = min(0.5 + pred_move * 5, 1.0)  # Positive prediction
                else:
                    ml_score = max(0.5 + pred_move * 5, 0.0)  # Negative prediction
            
            # Combine scores with weights
            final_score = 0.4 * trend_score + 0.4 * indicator_score + 0.2 * ml_score
            
            # Determine sentiment
            if final_score > 0.65:
                sentiment = "bullish"
            elif final_score < 0.35:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
                
            # Confidence is higher when score is closer to extremes
            confidence = 2 * abs(final_score - 0.5)
            
            return sentiment, confidence
            
        except Exception as e:
            self.logger.error(f"Error determining sentiment: {e}")
            return "neutral", 0.5
    
    def _calculate_overall_score(self, sentiment, confidence, trend, indicators, volatility, ml_prediction):
        """Calculate a comprehensive overall technical score from all factors.
        
        Returns:
            float: Score from 0-100, with higher values being more bullish
        """
        # Base score starts at 50 (neutral)
        score = 50.0
        
        # 1. Adjust for sentiment (up to 20 points)
        if sentiment == 'bullish':
            score += 20 * confidence
        elif sentiment == 'bearish':
            score -= 20 * confidence
        
        # 2. Adjust for trends (up to 30 points)
        if 'short_term' in trend and 'classification' in trend['short_term']:
            if trend['short_term']['classification'] == 'bullish':
                score += 10
            elif trend['short_term']['classification'] == 'bearish':
                score -= 10
                
        if 'medium_term' in trend and 'classification' in trend['medium_term']:
            if trend['medium_term']['classification'] == 'bullish':
                score += 15
            elif trend['medium_term']['classification'] == 'bearish':
                score -= 15
        
        if 'long_term' in trend and 'classification' in trend['long_term']:
            if trend['long_term']['classification'] == 'bullish':
                score += 5
            elif trend['long_term']['classification'] == 'bearish':
                score -= 5
        
        # 3. Adjust for key indicators (up to 15 points)
        # RSI
        if indicators.get('RSI', 50) > 70:
            score -= 5  # Overbought is bearish
        elif indicators.get('RSI', 50) < 30:
            score += 5  # Oversold is bullish for mean reversion
            
        # Moving average crossovers
        if indicators.get('ma_crossover_bullish', False):
            score += 10
        if indicators.get('ma_crossover_bearish', False):
            score -= 10
            
        # Price relative to moving averages
        if indicators.get('price_above_ma50', False):
            score += 5
        if indicators.get('price_above_ma200', False):
            score += 5
        
        # 4. Factor in ML prediction if available (up to 15 points)
        if ml_prediction and 'predicted_movement' in ml_prediction:
            pred_movement = ml_prediction['predicted_movement']
            pred_confidence = ml_prediction.get('confidence', 0.5)
            score += pred_movement * 15 * pred_confidence
        
        # Ensure score is within bounds
        return min(max(round(score, 1), 0), 100)
    
    def _get_default_result(self, symbol: str) -> Dict:
        """Return default result when analysis fails."""
        return {
            "symbol": symbol,
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_indicators": {},
            "trend": {
                "short_term": {"score": 0.5, "classification": "neutral"},
                "medium_term": {"score": 0.5, "classification": "neutral"},
                "long_term": {"score": 0.5, "classification": "neutral"}
            },
            "support": 0,
            "resistance": 0,
            "volatility": 0.5,
            "ml_prediction": 0,
            "timeframe": "medium_term",
            "overall_score": 50  # Default neutral score
        }


class FundamentalAnalysisAgent(BaseAgent):
    """
    Agent specializing in fundamental company analysis.
    
    This agent analyzes financial statements, valuation metrics,
    and business fundamentals to evaluate company health.
    """
    
    def __init__(self):
        """Initialize the fundamental analysis agent."""
        super().__init__("fundamental_analysis")
        
    def analyze(self, symbol: str, fundamental_data: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """
        Perform fundamental analysis on the given financial data.
        
        Args:
            symbol: Stock ticker symbol
            fundamental_data: Dictionary containing fundamental financial data
            user_preferences: Optional user preferences to personalize analysis
            
        Returns:
            Dictionary containing fundamental analysis results
        """
        try:
            self.logger.info(f"Performing fundamental analysis for {symbol}")
            
            # Extract key metrics
            metrics = self._extract_metrics(fundamental_data)
            
            # Calculate financial health score
            health_score, health_details = self._calculate_financial_health(metrics)
            
            # Determine valuation
            valuation, valuation_details = self._analyze_valuation(metrics)
            
            # Assess growth prospects
            growth, growth_details = self._analyze_growth(metrics)
            
            # Determine company classification
            classification = self._classify_company(metrics, growth)
            
            # Calculate ROTC and other profitability metrics
            profitability = self._analyze_profitability(metrics)
            
            # Overall outlook
            outlook, confidence = self._determine_outlook(health_score, valuation, growth, profitability)
            
            return {
                "symbol": symbol,
                "health": self._health_score_to_label(health_score),
                "health_score": health_score,
                "outlook": outlook,
                "confidence": self.format_confidence(confidence),
                "key_metrics": metrics,
                "health_details": health_details,
                "valuation_details": valuation_details,
                "growth_details": growth_details,
                "profitability": profitability,
                "classification": classification,
                "sector": fundamental_data.get("sector", "Unknown"),
                "metrics": metrics  # Include raw metrics for other agents
            }
            
        except Exception as e:
            self.logger.error(f"Error in fundamental analysis for {symbol}: {e}")
            return self._get_default_result(symbol)
    
    def _extract_metrics(self, fundamental_data: Dict) -> Dict:
        """Extract and normalize key metrics from fundamental data."""
        metrics = {}
        
        try:
            # Financial statement data
            income_statement = fundamental_data.get("income_statement", {})
            balance_sheet = fundamental_data.get("balance_sheet", {})
            cash_flow = fundamental_data.get("cash_flow", {})
            
            # Current financial metrics
            metrics["revenue"] = income_statement.get("totalRevenue", 0)
            metrics["net_income"] = income_statement.get("netIncome", 0)
            metrics["ebitda"] = income_statement.get("ebitda", 0)
            metrics["gross_profit"] = income_statement.get("grossProfit", 0)
            
            # Growth metrics (if available)
            metrics["revenue_growth"] = fundamental_data.get("revenue_growth", 0)
            metrics["eps_growth"] = fundamental_data.get("eps_growth", 0)
            metrics["ebitda_growth"] = fundamental_data.get("ebitda_growth", 0)
            
            # Balance sheet metrics
            metrics["total_assets"] = balance_sheet.get("totalAssets", 0)
            metrics["total_debt"] = balance_sheet.get("totalDebt", 0)
            metrics["cash"] = balance_sheet.get("cash", 0)
            metrics["equity"] = balance_sheet.get("totalStockholderEquity", 0)
            
            # Cash flow metrics
            metrics["operating_cash_flow"] = cash_flow.get("operatingCashflow", 0)
            metrics["capital_expenditure"] = cash_flow.get("capitalExpenditures", 0)
            metrics["free_cash_flow"] = metrics["operating_cash_flow"] - abs(metrics["capital_expenditure"])
            
            # Valuation metrics
            metrics["market_cap"] = fundamental_data.get("market_cap", 0)
            metrics["pe_ratio"] = fundamental_data.get("pe_ratio", 0)
            metrics["ps_ratio"] = fundamental_data.get("ps_ratio", 0) if fundamental_data.get("ps_ratio", 0) else (metrics["market_cap"] / metrics["revenue"] if metrics["revenue"] else 0)
            metrics["pb_ratio"] = fundamental_data.get("pb_ratio", 0)
            metrics["dividend_yield"] = fundamental_data.get("dividend_yield", 0)
            
            # Calculate additional ratios
            metrics["debt_to_equity"] = metrics["total_debt"] / metrics["equity"] if metrics["equity"] else 0
            metrics["current_ratio"] = balance_sheet.get("totalCurrentAssets", 0) / balance_sheet.get("totalCurrentLiabilities", 1)
            metrics["profit_margin"] = metrics["net_income"] / metrics["revenue"] if metrics["revenue"] else 0
            metrics["fcf_margin"] = metrics["free_cash_flow"] / metrics["revenue"] if metrics["revenue"] else 0
            
            # EV metrics
            metrics["enterprise_value"] = metrics["market_cap"] + metrics["total_debt"] - metrics["cash"]
            metrics["ev_to_ebitda"] = metrics["enterprise_value"] / metrics["ebitda"] if metrics["ebitda"] else 0
            metrics["ev_to_revenue"] = metrics["enterprise_value"] / metrics["revenue"] if metrics["revenue"] else 0
            
            # Cap metrics for extreme values
            for key in metrics:
                if isinstance(metrics[key], (int, float)):
                    if metrics[key] == float('inf') or metrics[key] == float('-inf'):
                        metrics[key] = 0
            
        except Exception as e:
            self.logger.error(f"Error extracting metrics: {e}")
            
        return metrics
    
    def _calculate_financial_health(self, metrics: Dict) -> Tuple[float, Dict]:
        """Calculate financial health score and details."""
        health_details = {}
        
        try:
            # Liquidity assessment
            liquidity_score = 0.5  # Default neutral
            if metrics["current_ratio"] >= 2:
                liquidity_score = 1.0
            elif metrics["current_ratio"] >= 1:
                liquidity_score = 0.75
            elif metrics["current_ratio"] >= 0.8:
                liquidity_score = 0.5
            else:
                liquidity_score = 0.25
                
            health_details["liquidity"] = {
                "score": liquidity_score,
                "assessment": "strong" if liquidity_score > 0.7 else "adequate" if liquidity_score > 0.4 else "weak",
                "current_ratio": metrics["current_ratio"]
            }
            
            # Debt assessment
            debt_score = 0.5  # Default neutral
            if metrics["debt_to_equity"] <= 0.1:
                debt_score = 1.0
            elif metrics["debt_to_equity"] <= 0.5:
                debt_score = 0.8
            elif metrics["debt_to_equity"] <= 1:
                debt_score = 0.6
            elif metrics["debt_to_equity"] <= 2:
                debt_score = 0.3
            else:
                debt_score = 0.1
                
            health_details["debt"] = {
                "score": debt_score,
                "assessment": "minimal" if debt_score > 0.8 else "manageable" if debt_score > 0.5 else "significant" if debt_score > 0.3 else "excessive",
                "debt_to_equity": metrics["debt_to_equity"]
            }
            
            # Profitability assessment
            profit_score = 0.5  # Default neutral
            if metrics["profit_margin"] >= 0.2:
                profit_score = 1.0
            elif metrics["profit_margin"] >= 0.1:
                profit_score = 0.8
            elif metrics["profit_margin"] >= 0.05:
                profit_score = 0.6
            elif metrics["profit_margin"] >= 0:
                profit_score = 0.4
            else:
                profit_score = 0.2
                
            health_details["profitability"] = {
                "score": profit_score,
                "assessment": "excellent" if profit_score > 0.8 else "good" if profit_score > 0.6 else "fair" if profit_score > 0.4 else "poor",
                "profit_margin": metrics["profit_margin"]
            }
            
            # Cash flow assessment
            cash_score = 0.5  # Default neutral
            if metrics["fcf_margin"] >= 0.15:
                cash_score = 1.0
            elif metrics["fcf_margin"] >= 0.1:
                cash_score = 0.8
            elif metrics["fcf_margin"] >= 0.05:
                cash_score = 0.6
            elif metrics["fcf_margin"] >= 0:
                cash_score = 0.4
            else:
                cash_score = 0.2
                
            health_details["cash_flow"] = {
                "score": cash_score,
                "assessment": "strong" if cash_score > 0.8 else "healthy" if cash_score > 0.6 else "adequate" if cash_score > 0.4 else "weak",
                "fcf_margin": metrics["fcf_margin"]
            }
            
            # Overall health score (weighted average)
            health_score = (
                0.25 * liquidity_score +
                0.25 * debt_score +
                0.25 * profit_score +
                0.25 * cash_score
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating financial health: {e}")
            health_score = 0.5
            health_details = {}
            
        return health_score, health_details
    
    def _analyze_valuation(self, metrics: Dict) -> Tuple[Dict, Dict]:
        """Analyze company valuation metrics."""
        valuation = {}
        details = {}
        
        try:
            # P/E assessment
            if metrics["pe_ratio"] <= 0:  # Negative earnings
                pe_assessment = "negative earnings"
                pe_score = 0.3
            elif metrics["pe_ratio"] <= 10:
                pe_assessment = "potentially undervalued"
                pe_score = 0.9
            elif metrics["pe_ratio"] <= 15:
                pe_assessment = "reasonably valued"
                pe_score = 0.7
            elif metrics["pe_ratio"] <= 25:
                pe_assessment = "fully valued"
                pe_score = 0.5
            elif metrics["pe_ratio"] <= 40:
                pe_assessment = "premium valuation"
                pe_score = 0.3
            else:
                pe_assessment = "expensive"
                pe_score = 0.1
                
            details["pe_ratio"] = {
                "value": metrics["pe_ratio"],
                "assessment": pe_assessment,
                "score": pe_score
            }
            
            # P/S assessment
            if metrics["ps_ratio"] <= 1:
                ps_assessment = "potentially undervalued"
                ps_score = 0.9
            elif metrics["ps_ratio"] <= 3:
                ps_assessment = "reasonably valued"
                ps_score = 0.7
            elif metrics["ps_ratio"] <= 5:
                ps_assessment = "fully valued"
                ps_score = 0.5
            elif metrics["ps_ratio"] <= 10:
                ps_assessment = "premium valuation"
                ps_score = 0.3
            else:
                ps_assessment = "expensive"
                ps_score = 0.1
                
            details["ps_ratio"] = {
                "value": metrics["ps_ratio"],
                "assessment": ps_assessment,
                "score": ps_score
            }
            
            # EV/EBITDA assessment
            if metrics["ev_to_ebitda"] <= 0:  # Negative EBITDA
                ev_ebitda_assessment = "negative EBITDA"
                ev_ebitda_score = 0.3
            elif metrics["ev_to_ebitda"] <= 6:
                ev_ebitda_assessment = "potentially undervalued"
                ev_ebitda_score = 0.9
            elif metrics["ev_to_ebitda"] <= 10:
                ev_ebitda_assessment = "reasonably valued"
                ev_ebitda_score = 0.7
            elif metrics["ev_to_ebitda"] <= 15:
                ev_ebitda_assessment = "fully valued"
                ev_ebitda_score = 0.5
            elif metrics["ev_to_ebitda"] <= 25:
                ev_ebitda_assessment = "premium valuation"
                ev_ebitda_score = 0.3
            else:
                ev_ebitda_assessment = "expensive"
                ev_ebitda_score = 0.1
                
            details["ev_to_ebitda"] = {
                "value": metrics["ev_to_ebitda"],
                "assessment": ev_ebitda_assessment,
                "score": ev_ebitda_score
            }
            
            # Overall valuation assessment
            # Use EV/EBITDA as primary, fall back to P/E, then P/S
            if metrics["ev_to_ebitda"] > 0:
                valuation_score = ev_ebitda_score
                primary_metric = "ev_to_ebitda"
            elif metrics["pe_ratio"] > 0:
                valuation_score = pe_score
                primary_metric = "pe_ratio"
            else:
                valuation_score = ps_score
                primary_metric = "ps_ratio"
                
            if valuation_score >= 0.8:
                valuation_assessment = "undervalued"
            elif valuation_score >= 0.6:
                valuation_assessment = "reasonably valued"
            elif valuation_score >= 0.4:
                valuation_assessment = "fairly valued"
            elif valuation_score >= 0.2:
                valuation_assessment = "premium valuation"
            else:
                valuation_assessment = "expensive"
                
            valuation = {
                "assessment": valuation_assessment,
                "score": valuation_score,
                "primary_metric": primary_metric
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing valuation: {e}")
            valuation = {"assessment": "uncertain", "score": 0.5, "primary_metric": None}
            details = {}
            
        return valuation, details
    
    def _analyze_growth(self, metrics: Dict) -> Tuple[Dict, Dict]:
        """Analyze company growth metrics."""
        growth = {}
        details = {}
        
        try:
            # Revenue growth assessment
            if metrics["revenue_growth"] >= 0.3:
                revenue_assessment = "exceptional growth"
                revenue_score = 1.0
            elif metrics["revenue_growth"] >= 0.15:
                revenue_assessment = "strong growth"
                revenue_score = 0.8
            elif metrics["revenue_growth"] >= 0.05:
                revenue_assessment = "moderate growth"
                revenue_score = 0.6
            elif metrics["revenue_growth"] >= 0:
                revenue_assessment = "slow growth"
                revenue_score = 0.4
            else:
                revenue_assessment = "declining"
                revenue_score = 0.2
                
            details["revenue_growth"] = {
                "value": metrics["revenue_growth"],
                "assessment": revenue_assessment,
                "score": revenue_score
            }
            
            # EPS growth assessment
            if metrics["eps_growth"] >= 0.3:
                eps_assessment = "exceptional growth"
                eps_score = 1.0
            elif metrics["eps_growth"] >= 0.15:
                eps_assessment = "strong growth"
                eps_score = 0.8
            elif metrics["eps_growth"] >= 0.05:
                eps_assessment = "moderate growth"
                eps_score = 0.6
            elif metrics["eps_growth"] >= 0:
                eps_assessment = "slow growth"
                eps_score = 0.4
            else:
                eps_assessment = "declining"
                eps_score = 0.2
                
            details["eps_growth"] = {
                "value": metrics["eps_growth"],
                "assessment": eps_assessment,
                "score": eps_score
            }
            
            # EBITDA growth assessment
            if metrics["ebitda_growth"] >= 0.3:
                ebitda_assessment = "exceptional growth"
                ebitda_score = 1.0
            elif metrics["ebitda_growth"] >= 0.15:
                ebitda_assessment = "strong growth"
                ebitda_score = 0.8
            elif metrics["ebitda_growth"] >= 0.05:
                ebitda_assessment = "moderate growth"
                ebitda_score = 0.6
            elif metrics["ebitda_growth"] >= 0:
                ebitda_assessment = "slow growth"
                ebitda_score = 0.4
            else:
                ebitda_assessment = "declining"
                ebitda_score = 0.2
                
            details["ebitda_growth"] = {
                "value": metrics["ebitda_growth"],
                "assessment": ebitda_assessment,
                "score": ebitda_score
            }
            
            # Overall growth assessment (weighted average)
            growth_score = (
                0.4 * revenue_score +
                0.3 * eps_score +
                0.3 * ebitda_score
            )
            
            if growth_score >= 0.8:
                growth_assessment = "exceptional growth"
            elif growth_score >= 0.6:
                growth_assessment = "strong growth"
            elif growth_score >= 0.4:
                growth_assessment = "moderate growth"
            elif growth_score >= 0.2:
                growth_assessment = "slow growth"
            else:
                growth_assessment = "declining"
                
            growth = {
                "assessment": growth_assessment,
                "score": growth_score
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing growth: {e}")
            growth = {"assessment": "uncertain", "score": 0.5}
            details = {}
            
        return growth, details
    
    def _analyze_profitability(self, metrics: Dict) -> Dict:
        """Analyze company profitability metrics including ROTC."""
        profitability = {}
        
        try:
            # Calculate ROTC (Return on Tangible Capital)
            # ROTC = NOPAT / Tangible Capital
            # NOPAT = EBIT * (1 - tax rate)
            
            # Estimate EBIT if not available
            ebit = metrics.get("ebit", metrics.get("ebitda", 0) * 0.8)  # Rough estimate if not available
            
            # Estimate effective tax rate, default to 25% if not available
            tax_rate = metrics.get("effective_tax_rate", 0.25)
            
            # Calculate NOPAT
            nopat = ebit * (1 - tax_rate)
            
            # Estimate Tangible Capital
            # Tangible Capital = Total Assets - Goodwill - Intangibles - Excess Cash - Non-Interest-Bearing Liabilities
            total_assets = metrics["total_assets"]
            goodwill = metrics.get("goodwill", 0)
            intangibles = metrics.get("intangibles", 0)
            excess_cash = max(0, metrics["cash"] - metrics.get("operating_cash_needs", metrics["revenue"] * 0.1))
            non_interest_liabilities = metrics.get("non_interest_liabilities", total_assets * 0.2)  # Estimate if not available
            
            tangible_capital = total_assets - goodwill - intangibles - excess_cash - non_interest_liabilities
            
            # Calculate ROTC
            rotc = nopat / tangible_capital if tangible_capital > 0 else 0
            
            # ROE
            roe = metrics["net_income"] / metrics["equity"] if metrics["equity"] > 0 else 0
            
            # ROIC (simplified)
            roic = nopat / (metrics["total_debt"] + metrics["equity"]) if (metrics["total_debt"] + metrics["equity"]) > 0 else 0
            
            profitability = {
                "rotc": rotc,
                "rotc_formatted": f"{rotc * 100:.1f}%",
                "roe": roe,
                "roe_formatted": f"{roe * 100:.1f}%",
                "roic": roic,
                "roic_formatted": f"{roic * 100:.1f}%",
                "profit_margin": metrics["profit_margin"],
                "profit_margin_formatted": f"{metrics['profit_margin'] * 100:.1f}%",
                "nopat": nopat,
                "tangible_capital": tangible_capital
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing profitability: {e}")
            profitability = {
                "rotc": 0,
                "rotc_formatted": "0.0%",
                "roe": 0,
                "roe_formatted": "0.0%",
                "roic": 0,
                "roic_formatted": "0.0%",
                "profit_margin": 0,
                "profit_margin_formatted": "0.0%"
            }
            
        return profitability
    
    def _classify_company(self, metrics: Dict, growth: Dict) -> str:
        """Classify company as growth, value, or hybrid."""
        try:
            # Growth indicators
            growth_indicators = 0
            
            if metrics["revenue_growth"] >= 0.15:
                growth_indicators += 1
            if metrics["pe_ratio"] >= 25:
                growth_indicators += 1
            if metrics["ps_ratio"] >= 5:
                growth_indicators += 1
            if growth.get("score", 0) >= 0.7:
                growth_indicators += 2
                
            # Value indicators
            value_indicators = 0
            
            if metrics["dividend_yield"] > 0.02:
                value_indicators += 1
            if metrics["pe_ratio"] > 0 and metrics["pe_ratio"] < 15:
                value_indicators += 1
            if metrics["pb_ratio"] > 0 and metrics["pb_ratio"] < 2:
                value_indicators += 1
            if metrics["profit_margin"] > 0.1:
                value_indicators += 1
                
            # Determine classification
            if growth_indicators >= 3 and value_indicators <= 1:
                return "growth"
            elif value_indicators >= 3 and growth_indicators <= 1:
                return "value"
            else:
                return "hybrid"
                
        except Exception as e:
            self.logger.error(f"Error classifying company: {e}")
            return "unknown"
    
    def _determine_outlook(self, health_score: float, valuation: Dict, growth: Dict, profitability: Dict) -> Tuple[str, float]:
        """Determine overall outlook and confidence."""
        try:
            # Base outlook on health and growth
            base_score = (health_score + growth.get("score", 0.5)) / 2
            
            # Adjust for valuation (inverse relationship - lower valuation is better)
            valuation_adjustment = 0.5 - (valuation.get("score", 0.5) - 0.5)
            
            # Adjust for profitability
            rotc = profitability.get("rotc", 0)
            if rotc > 0.15:
                profitability_bonus = 0.15
            elif rotc > 0.1:
                profitability_bonus = 0.1
            elif rotc > 0.05:
                profitability_bonus = 0.05
            else:
                profitability_bonus = 0
                
            # Calculate final score
            final_score = base_score + valuation_adjustment + profitability_bonus
            final_score = min(max(final_score, 0), 1)  # Ensure in 0-1 range
            
            # Determine outlook
            if final_score >= 0.8:
                outlook = "very positive"
            elif final_score >= 0.6:
                outlook = "positive"
            elif final_score >= 0.4:
                outlook = "neutral"
            elif final_score >= 0.2:
                outlook = "negative"
            else:
                outlook = "very negative"
                
            # Confidence based on data availability
            confidence = 0.8  # Base confidence
            
            # Adjust confidence lower if key metrics are missing
            if profitability.get("rotc", 0) == 0:
                confidence -= 0.1
            if growth.get("score", 0) == 0.5:
                confidence -= 0.1
                
            return outlook, confidence
            
        except Exception as e:
            self.logger.error(f"Error determining outlook: {e}")
            return "neutral", 0.5
    
    def _health_score_to_label(self, score: float) -> str:
        """Convert health score to descriptive label."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "average"
        elif score >= 0.2:
            return "concerning"
        else:
            return "poor"
    
    def _get_default_result(self, symbol: str) -> Dict:
        """Return default result when analysis fails."""
        return {
            "symbol": symbol,
            "health": "unknown",
            "health_score": 0.5,
            "outlook": "neutral",
            "confidence": 0.5,
            "key_metrics": {},
            "health_details": {},
            "valuation_details": {},
            "growth_details": {},
            "profitability": {
                "rotc": 0,
                "rotc_formatted": "0.0%"
            },
            "classification": "unknown",
            "sector": "Unknown",
            "metrics": {}
        }


class SentimentAnalysisAgent(BaseAgent):
    """
    Agent specializing in market sentiment analysis.
    
    This agent analyzes news, social media, and analyst opinions
    to determine market sentiment around a stock.
    """
    
    def __init__(self, rag_system=None):
        """
        Initialize the sentiment analysis agent.
        
        Args:
            rag_system: Optional RAG system for retrieving financial knowledge
        """
        super().__init__("sentiment_analysis")
        # Store RAG system reference for future use
        self.rag_system = rag_system
        
    def analyze(self, symbol: str, sentiment_data: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """
        Analyze sentiment data for the given stock.
        
        Args:
            symbol: Stock ticker symbol
            sentiment_data: Dictionary containing sentiment data sources
            user_preferences: Optional user preferences to personalize analysis
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            self.logger.info(f"Performing sentiment analysis for {symbol}")
            
            # This is a placeholder until RAG is implemented
            # If there's no RAG system, use simpler analysis
            if self.rag_system is None:
                return self._analyze_basic_sentiment(symbol, sentiment_data)
            
            # Rest of the implementation will depend on the RAG system
            # For now, return basic sentiment
            return self._analyze_basic_sentiment(symbol, sentiment_data)
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return self._get_default_result(symbol)
    
    def _analyze_basic_sentiment(self, symbol: str, sentiment_data: Dict) -> Dict:
        """Perform basic sentiment analysis without RAG."""
        # Default neutral sentiment
        sentiment_score = 50
        classification = "neutral"
        confidence = 0.5
        sources = []
        
        try:
            # Extract available sentiment signals
            signals = []
            
            # News sentiment if available
            if "news_sentiment" in sentiment_data:
                news_score = sentiment_data["news_sentiment"]
                signals.append(("news", news_score))
                sources.append({"type": "news", "score": news_score})
            
            # Analyst recommendations if available
            if "analyst_recommendations" in sentiment_data:
                rec = sentiment_data["analyst_recommendations"]
                # Convert to 0-100 scale
                if isinstance(rec, dict):
                    buy = rec.get("buy", 0)
                    hold = rec.get("hold", 0)
                    sell = rec.get("sell", 0)
                    total = buy + hold + sell
                    if total > 0:
                        analyst_score = (buy * 100 + hold * 50) / total
                        signals.append(("analysts", analyst_score))
                        sources.append({"type": "analysts", "score": analyst_score})
            
            # Social media sentiment if available
            if "social_sentiment" in sentiment_data:
                social_score = sentiment_data["social_sentiment"]
                signals.append(("social", social_score))
                sources.append({"type": "social_media", "score": social_score})
            
            # If we have signals, calculate average sentiment
            if signals:
                # Weight different sources
                weights = {
                    "news": 0.5,
                    "analysts": 0.3,
                    "social": 0.2
                }
                
                weighted_sum = 0
                total_weight = 0
                
                for source, score in signals:
                    weight = weights.get(source, 0.1)
                    weighted_sum += score * weight
                    total_weight += weight
                
                if total_weight > 0:
                    sentiment_score = weighted_sum / total_weight
                    
                # Determine classification
                if sentiment_score >= 70:
                    classification = "very positive"
                elif sentiment_score >= 55:
                    classification = "positive"
                elif sentiment_score > 45:
                    classification = "neutral"
                elif sentiment_score > 30:
                    classification = "negative"
                else:
                    classification = "very negative"
                    
                # Confidence based on number and consistency of sources
                confidence = min(0.3 + (len(signals) * 0.2), 0.9)
                
                # Adjust confidence based on agreement
                if len(signals) > 1:
                    scores = [score for _, score in signals]
                    max_diff = max(scores) - min(scores)
                    # Higher difference means lower confidence
                    confidence *= (1 - (max_diff / 100) * 0.5)
            
            # Create sentiment map
            recent_changes = {}
            if "sentiment_change" in sentiment_data:
                recent_changes = sentiment_data["sentiment_change"]
            
            # Estimate data age
            data_age_days = sentiment_data.get("data_age_days", 30)
            
            return {
                "symbol": symbol,
                "score": sentiment_score,
                "classification": classification,
                "confidence": self.format_confidence(confidence),
                "sources": sources,
                "recent_changes": recent_changes,
                "data_age_days": data_age_days
            }
            
        except Exception as e:
            self.logger.error(f"Error in basic sentiment analysis: {e}")
            return self._get_default_result(symbol)
    
    def _get_default_result(self, symbol: str) -> Dict:
        """Return default result when analysis fails."""
        return {
            "symbol": symbol,
            "score": 50,
            "classification": "neutral",
            "confidence": 0.5,
            "sources": [],
            "recent_changes": {},
            "data_age_days": 30
        }


class RiskAssessmentAgent(BaseAgent):
    """
    Agent specializing in risk assessment.
    
    This agent evaluates various risk factors including market,
    financial, operational, and systemic risks.
    """
    
    def __init__(self):
        """Initialize the risk assessment agent."""
        super().__init__("risk_assessment")
        
    def analyze(self, symbol: str, market_data: Dict, fundamental_data: Dict, 
                technical_analysis: Optional[Dict] = None, 
                fundamental_analysis: Optional[Dict] = None) -> Dict:
        """
        Perform risk assessment for the given stock.
        
        Args:
            symbol: Stock ticker symbol
            market_data: Dictionary containing market/price data
            fundamental_data: Dictionary containing fundamental financial data
            technical_analysis: Optional results from technical analysis agent
            fundamental_analysis: Optional results from fundamental analysis agent
            
        Returns:
            Dictionary containing risk assessment results
        """
        try:
            self.logger.info(f"Performing risk assessment for {symbol}")
            
            # Extract risk factors from different sources
            market_risk = self._assess_market_risk(market_data, technical_analysis)
            financial_risk = self._assess_financial_risk(fundamental_data, fundamental_analysis)
            volatility_risk = self._assess_volatility_risk(market_data)
            liquidity_risk = self._assess_liquidity_risk(market_data, fundamental_data)
            
            # Combine risk factors
            risk_factors = {
                "market_risk": market_risk,
                "financial_risk": financial_risk,
                "volatility_risk": volatility_risk,
                "liquidity_risk": liquidity_risk
            }
            
            # Calculate overall risk score (weighted average)
            weights = {
                "market_risk": 0.3,
                "financial_risk": 0.3,
                "volatility_risk": 0.25,
                "liquidity_risk": 0.15
            }
            
            overall_risk_score = sum(
                risk_factors[factor]["score"] * weights[factor]
                for factor in weights
            )
            
            # Determine risk level
            risk_level = self._risk_score_to_level(overall_risk_score)
            
            # Extract key risk factors
            key_risks = self._extract_key_risks(risk_factors)
            
            # Determine confidence
            confidence = self._calculate_confidence(risk_factors)
            
            return {
                "symbol": symbol,
                "risk_level": risk_level,
                "risk_score": overall_risk_score,
                "confidence": self.format_confidence(confidence),
                "risk_factors": risk_factors,
                "key_risks": key_risks
            }
            
        except Exception as e:
            self.logger.error(f"Error in risk assessment for {symbol}: {e}")
            return self._get_default_result(symbol)
    
    def _assess_market_risk(self, market_data: Dict, technical_analysis: Optional[Dict]) -> Dict:
        """Assess market-related risk factors."""
        risk_score = 0.5  # Default moderate risk
        factors = []
        
        try:
            # Use technical analysis if available
            if technical_analysis:
                trend = technical_analysis.get("trend", {})
                
                # Check for bearish trends
                short_term = trend.get("short_term", {}).get("classification", "neutral")
                medium_term = trend.get("medium_term", {}).get("classification", "neutral")
                
                if short_term == "bearish":
                    risk_score += 0.1
                    factors.append("Bearish short-term trend")
                
                if medium_term == "bearish":
                    risk_score += 0.15
                    factors.append("Bearish medium-term trend")
                
                # Check technical indicators
                indicators = technical_analysis.get("key_indicators", {})
                
                if indicators.get("RSI_overbought", False):
                    risk_score += 0.15
                    factors.append("Overbought RSI conditions")
                    
                if indicators.get("death_cross", False):
                    risk_score += 0.2
                    factors.append("Recent death cross")
            
            # Fallback to basic analysis if no technical analysis
            else:
                # Check for basic price trends
                df = None
                if "history" in market_data:
                    if isinstance(market_data["history"], pd.DataFrame):
                        df = market_data["history"]
                    elif isinstance(market_data["history"], dict):
                        df = pd.DataFrame(market_data["history"])
                
                if df is not None and not df.empty:
                    if "Close" in df.columns and len(df) > 20:
                        # Check short-term trend (10 days)
                        if df["Close"].iloc[-1] < df["Close"].iloc[-10]:
                            risk_score += 0.1
                            factors.append("Declining price in the last 10 days")
                        
                        # Check if price is below moving averages
                        sma50 = df["Close"].rolling(window=50).mean()
                        if df["Close"].iloc[-1] < sma50.iloc[-1]:
                            risk_score += 0.1
                            factors.append("Price below 50-day moving average")
            
            # Ensure risk score is in [0, 1] range
            risk_score = min(max(risk_score, 0), 1)
            
            return {
                "score": risk_score,
                "level": self._risk_score_to_level(risk_score),
                "factors": factors
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing market risk: {e}")
            return {"score": 0.5, "level": "moderate", "factors": []}
    
    def _assess_financial_risk(self, fundamental_data: Dict, fundamental_analysis: Optional[Dict]) -> Dict:
        """Assess financial risk factors."""
        risk_score = 0.5  # Default moderate risk
        factors = []
        
        try:
            # Use fundamental analysis if available
            if fundamental_analysis:
                health_score = fundamental_analysis.get("health_score", 0.5)
                
                # Invert health score to get risk (1 - health)
                risk_score = 1 - health_score
                
                # Extract specific risk factors
                health_details = fundamental_analysis.get("health_details", {})
                
                if "debt" in health_details:
                    debt_assessment = health_details["debt"].get("assessment", "")
                    if debt_assessment in ["significant", "excessive"]:
                        factors.append(f"{debt_assessment.capitalize()} debt levels")
                
                if "liquidity" in health_details:
                    liquidity_assessment = health_details["liquidity"].get("assessment", "")
                    if liquidity_assessment == "weak":
                        factors.append("Weak liquidity position")
                
                if "profitability" in health_details:
                    profit_assessment = health_details["profitability"].get("assessment", "")
                    if profit_assessment in ["fair", "poor"]:
                        factors.append(f"{profit_assessment.capitalize()} profitability")
                
                # Check growth concerns
                growth_details = fundamental_analysis.get("growth_details", {})
                if "revenue_growth" in growth_details:
                    if growth_details["revenue_growth"].get("assessment", "") == "declining":
                        factors.append("Declining revenue")
            
            # Fallback to basic analysis if no fundamental analysis
            else:
                balance_sheet = fundamental_data.get("balance_sheet", {})
                income_statement = fundamental_data.get("income_statement", {})
                
                # Check debt levels
                total_debt = balance_sheet.get("totalDebt", 0)
                equity = balance_sheet.get("totalStockholderEquity", 1)  # Avoid division by zero
                
                debt_to_equity = total_debt / equity
                if debt_to_equity > 2:
                    risk_score += 0.2
                    factors.append("High debt-to-equity ratio")
                
                # Check liquidity
                current_assets = balance_sheet.get("totalCurrentAssets", 0)
                current_liabilities = balance_sheet.get("totalCurrentLiabilities", 1)  # Avoid division by zero
                
                current_ratio = current_assets / current_liabilities
                if current_ratio < 1:
                    risk_score += 0.15
                    factors.append("Current ratio below 1.0")
                
                # Check profitability
                net_income = income_statement.get("netIncome", 0)
                revenue = income_statement.get("totalRevenue", 1)  # Avoid division by zero
                
                profit_margin = net_income / revenue
                if profit_margin < 0:
                    risk_score += 0.25
                    factors.append("Negative profit margin")
            
            # Ensure risk score is in [0, 1] range
            risk_score = min(max(risk_score, 0), 1)
            
            return {
                "score": risk_score,
                "level": self._risk_score_to_level(risk_score),
                "factors": factors
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing financial risk: {e}")
            return {"score": 0.5, "level": "moderate", "factors": []}
    
    def _assess_volatility_risk(self, market_data: Dict) -> Dict:
        """Assess volatility-related risk factors."""
        risk_score = 0.5  # Default moderate risk
        factors = []
        
        try:
            # Extract price data
            df = None
            if "history" in market_data:
                if isinstance(market_data["history"], pd.DataFrame):
                    df = market_data["history"]
                elif isinstance(market_data["history"], dict):
                    df = pd.DataFrame(market_data["history"])
            
            if df is not None and not df.empty and "Close" in df.columns and len(df) > 20:
                # Calculate historical volatility
                returns = df["Close"].pct_change().dropna()
                
                # 20-day volatility (annualized)
                volatility_20d = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)
                
                # 60-day volatility (annualized)
                volatility_60d = returns.rolling(window=60).std().iloc[-1] * np.sqrt(252) if len(returns) >= 60 else volatility_20d
                
                # Assess volatility risk
                if volatility_20d > 0.5:  # 50% annualized volatility
                    risk_score = 0.9
                    factors.append("Extremely high volatility")
                elif volatility_20d > 0.3:
                    risk_score = 0.75
                    factors.append("High volatility")
                elif volatility_20d > 0.2:
                    risk_score = 0.6
                    factors.append("Above-average volatility")
                elif volatility_20d < 0.1:
                    risk_score = 0.3
                    factors.append("Low volatility")
                
                # Check if recent volatility is increasing
                if volatility_20d > volatility_60d * 1.5:
                    risk_score += 0.1
                    factors.append("Increasing volatility trend")
                
                # Calculate max drawdown
                rolling_max = df["Close"].rolling(window=60, min_periods=1).max()
                drawdown = (df["Close"] / rolling_max - 1.0)
                max_drawdown = abs(drawdown.min())
                
                if max_drawdown > 0.3:
                    risk_score += 0.1
                    factors.append(f"Large historical drawdown ({max_drawdown:.1%})")
            
            # Ensure risk score is in [0, 1] range
            risk_score = min(max(risk_score, 0), 1)
            
            return {
                "score": risk_score,
                "level": self._risk_score_to_level(risk_score),
                "factors": factors
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing volatility risk: {e}")
            return {"score": 0.5, "level": "moderate", "factors": []}
    
    def _assess_liquidity_risk(self, market_data: Dict, fundamental_data: Dict) -> Dict:
        """Assess liquidity-related risk factors."""
        risk_score = 0.5  # Default moderate risk
        factors = []
        
        try:
            # Extract volume data
            df = None
            if "history" in market_data:
                if isinstance(market_data["history"], pd.DataFrame):
                    df = market_data["history"]
                elif isinstance(market_data["history"], dict):
                    df = pd.DataFrame(market_data["history"])
            
            if df is not None and not df.empty and "Volume" in df.columns and "Close" in df.columns:
                # Calculate average daily volume
                avg_volume = df["Volume"].mean()
                
                # Calculate average daily dollar volume
                avg_dollar_volume = (df["Volume"] * df["Close"]).mean()
                
                # Assess trading liquidity
                if avg_dollar_volume < 1000000:  # Less than $1M daily
                    risk_score = 0.9
                    factors.append("Very low trading liquidity")
                elif avg_dollar_volume < 5000000:  # Less than $5M daily
                    risk_score = 0.75
                    factors.append("Low trading liquidity")
                elif avg_dollar_volume < 20000000:  # Less than $20M daily
                    risk_score = 0.6
                    factors.append("Moderate trading liquidity")
                
                # Check for declining volume
                recent_volume = df["Volume"].iloc[-5:].mean()
                if recent_volume < avg_volume * 0.7:
                    risk_score += 0.1
                    factors.append("Declining trading volume")
            
            # Check float and institutional ownership if available
            market_cap = fundamental_data.get("market_cap", 0)
            float_percent = fundamental_data.get("float_percent", 0.8)
            institutional_ownership = fundamental_data.get("institutional_ownership", 0.5)
            
            # Small float increases risk
            if market_cap > 0 and float_percent < 0.5:
                float_market_cap = market_cap * float_percent
                if float_market_cap < 100000000:  # Less than $100M float
                    risk_score += 0.15
                    factors.append("Limited public float")
            
            # Very high institutional ownership can add liquidity risk
            if institutional_ownership > 0.9:
                risk_score += 0.1
                factors.append("Very high institutional ownership")
            
            # Ensure risk score is in [0, 1] range
            risk_score = min(max(risk_score, 0), 1)
            
            return {
                "score": risk_score,
                "level": self._risk_score_to_level(risk_score),
                "factors": factors
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing liquidity risk: {e}")
            return {"score": 0.5, "level": "moderate", "factors": []}
    
    def _risk_score_to_level(self, score: float) -> str:
        """Convert risk score to descriptive level."""
        if score >= 0.8:
            return "very high"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "moderate"
        elif score >= 0.2:
            return "low"
        else:
            return "very low"
    
    def _extract_key_risks(self, risk_factors: Dict) -> List[str]:
        """Extract the most significant risk factors."""
        all_factors = []
        
        for category, data in risk_factors.items():
            # Only include high or very high risk factors
            if data["level"] in ["high", "very high"]:
                all_factors.extend(data["factors"])
        
        # Return top factors (up to 5)
        return all_factors[:5]
    
    def _calculate_confidence(self, risk_factors: Dict) -> float:
        """Calculate confidence in risk assessment."""
        # Base confidence
        confidence = 0.7
        
        # Reduce confidence if we have fewer factors
        factor_count = sum(len(data["factors"]) for data in risk_factors.values())
        if factor_count < 2:
            confidence -= 0.2
        
        return confidence
    
    def _get_default_result(self, symbol: str) -> Dict:
        """Return default result when analysis fails."""
        return {
            "symbol": symbol,
            "risk_level": "moderate",
            "risk_score": 0.5,
            "confidence": 0.5,
            "risk_factors": {
                "market_risk": {"score": 0.5, "level": "moderate", "factors": []},
                "financial_risk": {"score": 0.5, "level": "moderate", "factors": []},
                "volatility_risk": {"score": 0.5, "level": "moderate", "factors": []},
                "liquidity_risk": {"score": 0.5, "level": "moderate", "factors": []}
            },
            "key_risks": []
        }