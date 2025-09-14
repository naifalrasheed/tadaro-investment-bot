"""
Behavioral Bias Analyzer Module

This module implements behavioral finance concepts from the CFA curriculum to detect
and mitigate cognitive and emotional biases in investment decisions.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from models import db, StockPreference
from ml_components.adaptive_learning_db import AdaptiveLearningDB

# Define bias categories based on CFA curriculum
COGNITIVE_BIASES = {
    "availability": {
        "name": "Availability Bias",
        "description": "Overweighting information that is easily recalled, often due to recency or vividness",
        "strategies": [
            "Use systematic checklists to evaluate investments",
            "Look at objective historical data, not just recent events",
            "Seek out less publicized investment opportunities"
        ]
    },
    "representativeness": {
        "name": "Representativeness Bias",
        "description": "Judging probability by how closely something resembles something else",
        "strategies": [
            "Focus on base rates and statistical probabilities",
            "Question whether past patterns are truly predictive",
            "Evaluate each investment on its specific fundamentals"
        ]
    },
    "anchoring": {
        "name": "Anchoring and Adjustment Bias",
        "description": "Over-reliance on first piece of information encountered (the 'anchor')",
        "strategies": [
            "Start analysis from different reference points",
            "Use multiple valuation methods",
            "Explicitly question your initial assumptions"
        ]
    },
    "confirmation": {
        "name": "Confirmation Bias",
        "description": "Seeking and overweighting information that confirms existing beliefs",
        "strategies": [
            "Actively seek contradictory information",
            "Assign someone to play devil's advocate",
            "Track and review confirming and disconfirming evidence"
        ]
    },
    "hindsight": {
        "name": "Hindsight Bias",
        "description": "Perceiving past events as having been predictable",
        "strategies": [
            "Keep a decision journal to record thought process",
            "Focus on process quality, not just outcomes",
            "Study both successful and unsuccessful decisions"
        ]
    },
    "overconfidence": {
        "name": "Overconfidence Bias",
        "description": "Overestimating knowledge, abilities, and precision of information",
        "strategies": [
            "Use confidence intervals in forecasts",
            "Track accuracy of past predictions",
            "Seek diverse viewpoints on investment decisions"
        ]
    },
    "self_attribution": {
        "name": "Self-Attribution Bias",
        "description": "Attributing success to skill and failure to bad luck",
        "strategies": [
            "Conduct honest post-mortems of both successes and failures",
            "Identify specific factors that contributed to outcomes",
            "Focus on improving decision process regardless of outcomes"
        ]
    },
    "recency": {
        "name": "Recency Bias",
        "description": "Overweighting recent events and experiences",
        "strategies": [
            "Examine long-term historical data and cycles",
            "Use dollar-cost averaging to avoid timing based on recent events",
            "Create and follow a long-term investment policy statement"
        ]
    }
}

EMOTIONAL_BIASES = {
    "loss_aversion": {
        "name": "Loss Aversion Bias",
        "description": "Feeling the pain of losses more strongly than the pleasure of gains",
        "strategies": [
            "Set predetermined exit points for investments",
            "Evaluate portfolio less frequently",
            "Frame decisions in terms of total wealth rather than gains/losses"
        ]
    },
    "regret_aversion": {
        "name": "Regret Aversion Bias",
        "description": "Making decisions to avoid feeling future regret",
        "strategies": [
            "Focus on process quality rather than outcomes",
            "Establish and follow systematic investment rules",
            "Recognize that some regret is inevitable with uncertainty"
        ]
    },
    "status_quo": {
        "name": "Status Quo Bias",
        "description": "Preference for current state and resistance to change",
        "strategies": [
            "Set up automatic rebalancing",
            "Regularly review all positions with fresh perspective",
            "Use default options that encourage optimal behavior"
        ]
    },
    "herding": {
        "name": "Herding Bias",
        "description": "Following the behavior of others rather than making independent decisions",
        "strategies": [
            "Focus on fundamental analysis rather than market sentiment",
            "Limit exposure to financial media during market volatility",
            "Document your investment thesis before looking at others' opinions"
        ]
    },
    "endowment": {
        "name": "Endowment Effect",
        "description": "Valuing owned assets more highly than their market value",
        "strategies": [
            "Regularly evaluate holdings as if you were buying them today",
            "Consider opportunity costs of keeping existing investments",
            "Use systematic review processes for all holdings"
        ]
    },
    "self_control": {
        "name": "Self-Control Bias",
        "description": "Failing to act in long-term best interests due to lack of self-discipline",
        "strategies": [
            "Automate saving and investing",
            "Create commitment devices that enforce discipline",
            "Focus on concrete long-term goals rather than abstract ones"
        ]
    }
}

# Combine all biases into one dictionary
ALL_BIASES = {**COGNITIVE_BIASES, **EMOTIONAL_BIASES}


class BehavioralBiasAnalyzer:
    """
    Analyzes user decisions and portfolio actions for common behavioral biases.
    Provides insights and mitigation strategies based on CFA behavioral finance frameworks.
    """
    
    def __init__(self, user_id: int):
        """
        Initialize the behavioral bias analyzer.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.user_learning = AdaptiveLearningDB(user_id)
        
    def analyze_trade_pattern(self, trade_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze trading patterns for behavioral biases.
        
        Args:
            trade_history: List of trading actions with timestamps, symbols, action types, etc.
            
        Returns:
            List of detected biases with evidence and mitigation strategies
        """
        detected_biases = []
        
        # Check for disposition effect (holding losers too long, selling winners too early)
        if self._check_disposition_effect(trade_history):
            detected_biases.append({
                "bias": "loss_aversion",
                "name": ALL_BIASES["loss_aversion"]["name"],
                "evidence": "Pattern of selling winning positions while holding losing positions",
                "mitigation": "Consider setting predefined exit points for both gains and losses"
            })
        
        # Check for overtrading (excessive trading activity)
        if self._check_overtrading(trade_history):
            detected_biases.append({
                "bias": "overconfidence",
                "name": ALL_BIASES["overconfidence"]["name"],
                "evidence": "Trading frequency is significantly above average",
                "mitigation": "Implement a trading plan with predefined rules for entry/exit"
            })
            
        # Check for recency bias (trading based on recent market movements)
        if self._check_recency_bias_in_trades(trade_history):
            detected_biases.append({
                "bias": "recency",
                "name": ALL_BIASES["recency"]["name"],
                "evidence": "Trading pattern follows recent market movements",
                "mitigation": "Consider longer-term performance metrics and zoom out to see the bigger picture"
            })
            
        # Check for herding behavior
        if self._check_herding_in_trades(trade_history):
            detected_biases.append({
                "bias": "herding",
                "name": ALL_BIASES["herding"]["name"],
                "evidence": "Trading activity aligns with broader market trends",
                "mitigation": "Focus on your investment thesis rather than following the crowd"
            })
            
        return detected_biases
    
    def analyze_portfolio_concentration(self, portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze portfolio for concentration biases.
        
        Args:
            portfolio: Portfolio data including holdings, sectors, etc.
            
        Returns:
            List of detected biases with evidence and mitigation strategies
        """
        detected_biases = []
        
        # Check for familiarity bias (overconcentration in familiar sectors/stocks)
        sector_concentration = self._calculate_sector_concentration(portfolio)
        if sector_concentration and max(sector_concentration.values()) > 30:  # If any sector > 30%
            most_concentrated_sector = max(sector_concentration.items(), key=lambda x: x[1])
            detected_biases.append({
                "bias": "familiarity",
                "name": "Familiarity Bias",
                "evidence": f"Portfolio has {most_concentrated_sector[0]} concentration of {most_concentrated_sector[1]:.1f}%",
                "mitigation": "Consider more diversified sector allocation using the portfolio optimizer"
            })
            
        # Check for home bias (overconcentration in domestic market)
        if self._check_home_bias(portfolio):
            detected_biases.append({
                "bias": "home_bias",
                "name": "Home Bias",
                "evidence": "Portfolio has excessive concentration in domestic securities",
                "mitigation": "Consider adding international assets for better diversification"
            })
            
        # Check for status quo bias (unchanged portfolio for extended periods)
        if self._check_status_quo_bias(portfolio):
            detected_biases.append({
                "bias": "status_quo",
                "name": ALL_BIASES["status_quo"]["name"],
                "evidence": "Portfolio has remained largely unchanged for an extended period",
                "mitigation": "Implement regular portfolio reviews and rebalancing"
            })
            
        return detected_biases
    
    def analyze_decision_context(self, 
                                 decision: Dict[str, Any], 
                                 recent_market_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze investment decision in context of market conditions.
        
        Args:
            decision: Details of the investment decision
            recent_market_conditions: Recent market data and trends
            
        Returns:
            List of detected biases with evidence and mitigation strategies
        """
        detected_biases = []
        
        # Check for recency bias (overweighting recent market events)
        if self._check_recency_bias_in_decision(decision, recent_market_conditions):
            detected_biases.append({
                "bias": "recency",
                "name": ALL_BIASES["recency"]["name"],
                "evidence": "Decision appears heavily influenced by recent market movements",
                "mitigation": "Consider longer-term performance metrics and zoom out to see the bigger picture"
            })
            
        # Check for anchoring (fixating on a reference point like purchase price)
        if self._check_anchoring(decision):
            detected_biases.append({
                "bias": "anchoring",
                "name": ALL_BIASES["anchoring"]["name"],
                "evidence": "Decision appears anchored to a specific reference price",
                "mitigation": "Consider the investment based on current fundamentals, not historical prices"
            })
            
        # Check for confirmation bias (seeking only confirming information)
        if self._check_confirmation_bias(decision):
            detected_biases.append({
                "bias": "confirmation",
                "name": ALL_BIASES["confirmation"]["name"],
                "evidence": "Decision rationale shows signs of seeking confirming evidence only",
                "mitigation": "Actively seek contradictory information to test your investment thesis"
            })
            
        # Check for emotional state influence
        if self._check_emotional_influence(decision, recent_market_conditions):
            detected_biases.append({
                "bias": "emotional_influence",
                "name": "Emotional Decision-Making",
                "evidence": "Decision timing coincides with high market volatility or stress",
                "mitigation": "Consider postponing major decisions during periods of market stress"
            })
            
        return detected_biases
    
    def get_user_bias_profile(self) -> Dict[str, Any]:
        """
        Get the user's bias profile based on historical patterns.
        
        Returns:
            Dict containing bias scores and prevalent biases
        """
        # Implement the logic to retrieve and compile user bias profile
        # This would typically read from a database table tracking bias occurrences
        
        # For now, we'll return a placeholder implementation
        # In a real implementation, this would be calculated from historical data
        
        bias_scores = {
            "overconfidence": 7.5,
            "loss_aversion": 6.8,
            "recency": 5.4,
            "confirmation": 4.2,
            "hindsight": 3.8,
            "status_quo": 3.5,
            "herding": 2.9,
            "anchoring": 2.7
        }
        
        # Get top biases
        top_biases = sorted(bias_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_bias_details = []
        
        for bias_type, score in top_biases:
            if bias_type in ALL_BIASES:
                bias_info = ALL_BIASES[bias_type]
                
                # Determine alert level based on score
                if score > 7:
                    alert_level = "danger"
                elif score > 5:
                    alert_level = "warning"
                else:
                    alert_level = "info"
                
                top_bias_details.append({
                    "type": bias_type,
                    "name": bias_info["name"],
                    "score": score,
                    "description": bias_info["description"],
                    "strategy": bias_info["strategies"][0],  # Return first strategy
                    "alert_level": alert_level
                })
        
        return {
            "bias_scores": bias_scores,
            "top_biases": top_bias_details,
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_debiasing_strategies(self) -> Dict[str, Any]:
        """
        Generate personalized debiasing strategies based on user's bias profile.
        
        Returns:
            Dict containing personalized debiasing strategies
        """
        bias_profile = self.get_user_bias_profile()
        top_biases = bias_profile["top_biases"]
        
        strategies = []
        for bias in top_biases:
            bias_type = bias["type"]
            if bias_type in ALL_BIASES:
                bias_strategies = ALL_BIASES[bias_type]["strategies"]
                strategies.append({
                    "bias_type": bias_type,
                    "bias_name": ALL_BIASES[bias_type]["name"],
                    "score": bias["score"],
                    "strategies": bias_strategies
                })
        
        # Add general strategies
        general_strategies = [
            "Maintain an investment diary to track decisions and outcomes",
            "Implement a systematic investment process with clear rules",
            "Set up automatic portfolio rebalancing to enforce discipline",
            "Consider using a checklist for making investment decisions",
            "Regularly review your investment performance objectively"
        ]
        
        return {
            "personalized_strategies": strategies,
            "general_strategies": general_strategies
        }
    
    # Private helper methods
    
    def _check_disposition_effect(self, trade_history: List[Dict[str, Any]]) -> bool:
        """Check for disposition effect (holding losers, selling winners)"""
        if not trade_history or len(trade_history) < 5:  # Need sufficient history
            return False
            
        # Group trades by symbol
        trades_by_symbol = {}
        for trade in trade_history:
            symbol = trade.get("symbol")
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(trade)
        
        # Analyze sell decisions
        winner_sells = 0
        loser_holds = 0
        total_positions = 0
        
        for symbol, trades in trades_by_symbol.items():
            # Sort trades by date
            sorted_trades = sorted(trades, key=lambda x: x.get("timestamp", ""))
            
            # Find buy and sell trades
            buys = [t for t in sorted_trades if t.get("action") == "buy"]
            sells = [t for t in sorted_trades if t.get("action") == "sell"]
            
            if not buys:  # Skip if no buy trades
                continue
                
            total_positions += 1
            
            if sells:  # If there are sell trades
                # Calculate average buy price
                avg_buy_price = sum(b.get("price", 0) * b.get("quantity", 0) for b in buys) / sum(b.get("quantity", 0) for b in buys)
                
                # Get last sell
                last_sell = max(sells, key=lambda x: x.get("timestamp", ""))
                sell_price = last_sell.get("price", 0)
                
                # Check if selling a winner
                if sell_price > avg_buy_price:
                    winner_sells += 1
            else:  # No sells - check if it's a loser
                # Check current price vs average buy price
                avg_buy_price = sum(b.get("price", 0) * b.get("quantity", 0) for b in buys) / sum(b.get("quantity", 0) for b in buys)
                current_price = sorted_trades[-1].get("current_price", avg_buy_price)
                
                # Check if holding a loser
                if current_price < avg_buy_price:
                    loser_holds += 1
        
        # Calculate disposition effect metrics
        if total_positions == 0:
            return False
            
        winner_sell_ratio = winner_sells / total_positions if total_positions > 0 else 0
        loser_hold_ratio = loser_holds / total_positions if total_positions > 0 else 0
        
        # If both ratios are high, this suggests disposition effect
        return winner_sell_ratio > 0.5 and loser_hold_ratio > 0.4
    
    def _check_overtrading(self, trade_history: List[Dict[str, Any]]) -> bool:
        """Check for overtrading (excessive trading activity)"""
        if not trade_history:
            return False
            
        # Calculate trading frequency
        if len(trade_history) < 2:
            return False
            
        # Sort trades by date
        sorted_trades = sorted(trade_history, key=lambda x: x.get("timestamp", ""))
        
        # Calculate date range
        try:
            start_date = datetime.fromisoformat(sorted_trades[0].get("timestamp", "").replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(sorted_trades[-1].get("timestamp", "").replace('Z', '+00:00'))
            
            # Calculate date difference in days
            date_diff = (end_date - start_date).days
            if date_diff < 1:  # Avoid division by zero
                date_diff = 1
                
            # Calculate trades per month (30 days)
            trades_per_month = len(trade_history) / date_diff * 30
            
            # More than 10 trades per month might indicate overtrading
            return trades_per_month > 10
            
        except (ValueError, TypeError):
            self.logger.error("Error parsing dates in trade history")
            return False
    
    def _check_recency_bias_in_trades(self, trade_history: List[Dict[str, Any]]) -> bool:
        """Check for recency bias in trading patterns"""
        if not trade_history or len(trade_history) < 5:
            return False
            
        # Get recent market trends (ideally this would come from market data)
        # For simplicity, we'll use a placeholder approach
        recent_uptrend_sectors = ["Technology", "Healthcare"]
        recent_downtrend_sectors = ["Energy", "Utilities"]
        
        # Count trades in trending sectors
        uptrend_buys = 0
        downtrend_sells = 0
        
        for trade in trade_history:
            sector = trade.get("sector", "")
            action = trade.get("action", "")
            
            if action == "buy" and sector in recent_uptrend_sectors:
                uptrend_buys += 1
            elif action == "sell" and sector in recent_downtrend_sectors:
                downtrend_sells += 1
        
        # Calculate percentage of trades showing recency bias
        recency_bias_trades = uptrend_buys + downtrend_sells
        recency_bias_percentage = recency_bias_trades / len(trade_history)
        
        # If more than 60% of trades follow recent trends, this suggests recency bias
        return recency_bias_percentage > 0.6
    
    def _check_herding_in_trades(self, trade_history: List[Dict[str, Any]]) -> bool:
        """Check for herding behavior in trades"""
        if not trade_history or len(trade_history) < 5:
            return False
            
        # This would ideally compare user trades with broader market flows
        # For a placeholder implementation, we'll focus on popular stocks
        
        popular_stocks = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"]
        
        # Count trades in popular stocks
        popular_buys = 0
        
        for trade in trade_history:
            symbol = trade.get("symbol", "")
            action = trade.get("action", "")
            
            if action == "buy" and symbol in popular_stocks:
                popular_buys += 1
        
        # Calculate percentage of buy trades in popular stocks
        buy_trades = sum(1 for trade in trade_history if trade.get("action") == "buy")
        if buy_trades == 0:
            return False
            
        popular_buy_percentage = popular_buys / buy_trades
        
        # If more than 70% of buys are in popular stocks, this suggests herding
        return popular_buy_percentage > 0.7
    
    def _calculate_sector_concentration(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """Calculate sector concentration percentages"""
        if not portfolio or "holdings" not in portfolio:
            return {}
            
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return {}
            
        # Calculate total portfolio value
        total_value = sum(holding.get("current_value", 0) for holding in holdings)
        if total_value == 0:
            return {}
            
        # Calculate sector values
        sector_values = {}
        for holding in holdings:
            sector = holding.get("sector", "Unknown")
            value = holding.get("current_value", 0)
            
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += value
        
        # Calculate sector percentages
        sector_percentages = {sector: (value / total_value) * 100 for sector, value in sector_values.items()}
        
        return sector_percentages
    
    def _check_home_bias(self, portfolio: Dict[str, Any]) -> bool:
        """Check for home bias (overconcentration in domestic market)"""
        if not portfolio or "holdings" not in portfolio:
            return False
            
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return False
            
        # Calculate total portfolio value
        total_value = sum(holding.get("current_value", 0) for holding in holdings)
        if total_value == 0:
            return False
            
        # Calculate domestic vs international value
        domestic_value = sum(holding.get("current_value", 0) for holding in holdings 
                          if holding.get("country", "US") == "US")
        
        # Calculate domestic percentage
        domestic_percentage = (domestic_value / total_value) * 100
        
        # If more than 80% in domestic securities, this suggests home bias
        # Note: This threshold should be adjusted based on the size of the domestic market
        return domestic_percentage > 80
    
    def _check_status_quo_bias(self, portfolio: Dict[str, Any]) -> bool:
        """Check for status quo bias (unchanged portfolio)"""
        if not portfolio:
            return False
            
        # Check last transaction date
        last_transaction = portfolio.get("last_transaction_date")
        if not last_transaction:
            return False
            
        try:
            last_date = datetime.fromisoformat(last_transaction.replace('Z', '+00:00'))
            days_since_last_transaction = (datetime.now() - last_date).days
            
            # If no transactions in 180 days (approximately 6 months), this suggests status quo bias
            return days_since_last_transaction > 180
            
        except (ValueError, TypeError):
            self.logger.error("Error parsing last transaction date")
            return False
    
    def _check_recency_bias_in_decision(self, 
                                       decision: Dict[str, Any], 
                                       recent_market_conditions: Dict[str, Any]) -> bool:
        """Check for recency bias in decision"""
        if not decision or not recent_market_conditions:
            return False
            
        # Extract decision details
        symbol = decision.get("symbol", "")
        decision_type = decision.get("decision_type", "")
        rationale = decision.get("rationale", "")
        
        # Extract recent market conditions
        market_trend = recent_market_conditions.get("market_trend", "neutral")
        sector_trends = recent_market_conditions.get("sector_trends", {})
        symbol_recent_performance = recent_market_conditions.get("symbol_performance", {}).get(symbol, {})
        
        # Check for recency bias indicators
        indicators = 0
        
        # Decision aligned with very recent market trend
        if (market_trend == "bullish" and decision_type == "buy") or (market_trend == "bearish" and decision_type == "sell"):
            indicators += 1
            
        # Decision aligned with very recent sector trend
        sector = decision.get("sector", "")
        sector_trend = sector_trends.get(sector, "neutral")
        if (sector_trend == "bullish" and decision_type == "buy") or (sector_trend == "bearish" and decision_type == "sell"):
            indicators += 1
            
        # Decision influenced by recent stock performance
        recent_stock_change = symbol_recent_performance.get("1_week_change", 0)
        if (recent_stock_change > 5 and decision_type == "buy") or (recent_stock_change < -5 and decision_type == "sell"):
            indicators += 1
            
        # Rationale mentions recent events
        recency_keywords = ["recent", "lately", "last week", "yesterday", "today", "this month", "trending"]
        if any(keyword in rationale.lower() for keyword in recency_keywords):
            indicators += 1
            
        # If 3 or more indicators are present, this suggests recency bias
        return indicators >= 3
    
    def _check_anchoring(self, decision: Dict[str, Any]) -> bool:
        """Check for anchoring bias"""
        if not decision:
            return False
            
        # Extract decision details
        rationale = decision.get("rationale", "")
        price = decision.get("price", 0)
        
        # Check for anchoring to specific prices
        anchor_keywords = ["previous high", "all-time high", "52-week", "previous price", "last price", "IPO price", 
                         "originally traded at", "used to be worth", "previously valued at"]
        
        if any(keyword in rationale.lower() for keyword in anchor_keywords):
            return True
            
        # Check for specific price anchoring in buy/sell decisions
        if decision.get("decision_type") == "sell" and decision.get("purchase_price"):
            purchase_price = decision.get("purchase_price", 0)
            # If selling at a specific gain threshold (e.g., 20% gain)
            if 0.95 < (price / purchase_price) < 1.05 or 1.19 < (price / purchase_price) < 1.21:
                return True
                
        return False
    
    def _check_confirmation_bias(self, decision: Dict[str, Any]) -> bool:
        """Check for confirmation bias"""
        if not decision:
            return False
            
        # Extract decision details
        rationale = decision.get("rationale", "")
        
        # Check for one-sided reasoning
        supporting_points = 0
        contradicting_points = 0
        
        # Count supporting vs contradicting points
        support_indicators = ["supports", "confirms", "validates", "reinforces", "proves", "shows"]
        contradict_indicators = ["despite", "however", "although", "risk", "downside", "concern", "challenge", "but", "counterpoint"]
        
        for indicator in support_indicators:
            if indicator in rationale.lower():
                supporting_points += 1
                
        for indicator in contradict_indicators:
            if indicator in rationale.lower():
                contradicting_points += 1
                
        # If there are supporting points but no contradicting points, this suggests confirmation bias
        return supporting_points > 0 and contradicting_points == 0
    
    def _check_emotional_influence(self, 
                                  decision: Dict[str, Any], 
                                  recent_market_conditions: Dict[str, Any]) -> bool:
        """Check for emotional influence in decision making"""
        if not decision or not recent_market_conditions:
            return False
            
        # Extract market conditions
        market_volatility = recent_market_conditions.get("volatility", "normal")
        recent_sharp_moves = recent_market_conditions.get("sharp_moves", False)
        
        # Making significant decisions during high market stress is often emotional
        if (market_volatility == "high" or recent_sharp_moves) and decision.get("decision_type") in ["buy", "sell"]:
            # Check if it's a large position change
            if decision.get("position_size_change", 0) > 20:  # Position size change > 20%
                return True
                
        # Check rationale for emotional language
        rationale = decision.get("rationale", "")
        emotional_keywords = ["fear", "worried", "excited", "thrilled", "concerned", "nervous", "optimistic", 
                            "pessimistic", "afraid", "confident", "hope", "regret", "disappointed", "pleased"]
        
        emotional_count = sum(1 for keyword in emotional_keywords if keyword in rationale.lower())
        
        # If multiple emotional terms are used in rationale, this suggests emotional influence
        return emotional_count >= 2


class UserBiasProfile:
    """
    Tracks and manages a user's behavioral bias tendencies over time.
    """
    
    def __init__(self, user_id: int):
        """
        Initialize the user bias profile.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.bias_scores = self._load_or_initialize_bias_scores()
        self.detection_history = []
        self.logger = logging.getLogger(__name__)
        
    def update_profile(self, detected_biases: List[Dict[str, Any]]) -> None:
        """
        Update the user's bias profile based on new detections.
        
        Args:
            detected_biases: List of detected biases
        """
        for bias in detected_biases:
            bias_type = bias["bias"]
            # Increase the bias score when detected
            if bias_type in self.bias_scores:
                self.bias_scores[bias_type] = min(10, self.bias_scores[bias_type] + 1)
            else:
                self.bias_scores[bias_type] = 1
            
            # Add to detection history
            self.detection_history.append({
                "bias": bias_type,
                "timestamp": datetime.now().isoformat(),
                "context": bias["evidence"]
            })
        
        # Decay other bias scores slightly over time
        for bias_type in self.bias_scores:
            if bias_type not in [b["bias"] for b in detected_biases]:
                self.bias_scores[bias_type] = max(0, self.bias_scores[bias_type] - 0.1)
                
        # Save updated profile
        self._save_bias_profile()
        
    def get_top_biases(self, limit: int = 3) -> List[Tuple[str, float]]:
        """
        Get the user's top biases.
        
        Args:
            limit: Maximum number of biases to return
            
        Returns:
            List of tuples containing bias type and score
        """
        sorted_biases = sorted(self.bias_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_biases[:limit]
        
    def generate_debiasing_strategy(self) -> List[Dict[str, Any]]:
        """
        Generate a personalized debiasing strategy based on user's bias profile.
        
        Returns:
            List of debiasing strategies for top biases
        """
        top_biases = self.get_top_biases()
        
        strategies = []
        for bias, score in top_biases:
            if score > 5 and bias in ALL_BIASES:  # Only suggest strategies for significant biases
                strategies.append({
                    "bias": bias,
                    "name": ALL_BIASES[bias]["name"],
                    "score": score,
                    "strategies": ALL_BIASES[bias]["strategies"]
                })
                
        return strategies
        
    def _load_or_initialize_bias_scores(self) -> Dict[str, float]:
        """
        Load existing bias scores or initialize new ones.
        
        Returns:
            Dictionary of bias scores
        """
        # In a real implementation, this would load from a database
        # For now, return a dictionary with zero scores for all biases
        return {bias_type: 0.0 for bias_type in ALL_BIASES.keys()}
        
    def _save_bias_profile(self) -> None:
        """Save the bias profile to persistent storage"""
        # In a real implementation, this would save to a database
        self.logger.info(f"Saving bias profile for user {self.user_id}")
        # Example of how this might be implemented with an ORM
        # for bias_type, score in self.bias_scores.items():
        #     bias_profile = UserBiasProfile.query.filter_by(
        #         user_id=self.user_id, 
        #         bias_type=bias_type
        #     ).first()
        #     
        #     if bias_profile:
        #         bias_profile.bias_score = score
        #     else:
        #         new_profile = UserBiasProfile(
        #             user_id=self.user_id,
        #             bias_type=bias_type,
        #             bias_score=score
        #         )
        #         db.session.add(new_profile)
        #     
        # db.session.commit()


class InvestmentDecisionFramework:
    """
    Structured investment decision framework based on CFA curriculum.
    Helps users make and document investment decisions through a systematic process.
    """
    
    def __init__(self, user_id: int):
        """
        Initialize the investment decision framework.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.bias_analyzer = BehavioralBiasAnalyzer(user_id)
        
    def evaluate_investment_thesis(self, symbol: str, user_thesis: str) -> Dict[str, Any]:
        """
        Evaluate and enhance user's investment thesis.
        
        Args:
            symbol: Stock symbol
            user_thesis: User's investment thesis
            
        Returns:
            Dictionary with thesis evaluation and suggestions
        """
        # Define thesis components that should be addressed
        thesis_components = [
            "business_model",
            "competitive_advantage",
            "growth_drivers",
            "risks",
            "valuation_rationale",
            "catalyst_events",
            "time_horizon"
        ]
        
        # Analyze user thesis for completeness
        missing_components = []
        for component in thesis_components:
            if not self._thesis_addresses_component(user_thesis, component):
                missing_components.append(component)
        
        # Generate suggestions for missing components
        suggestions = {}
        for component in missing_components:
            suggestions[component] = self._generate_component_suggestion(symbol, component)
            
        # Provide counterarguments to test robustness
        counterarguments = self._generate_counterarguments(user_thesis, symbol)
        
        return {
            "missing_components": missing_components,
            "suggestions": suggestions,
            "counterarguments": counterarguments,
            "completeness_score": (len(thesis_components) - len(missing_components)) / len(thesis_components) * 100
        }
    
    def document_investment_decision(self, 
                                    symbol: str, 
                                    decision_type: str, 
                                    rationale: str, 
                                    amount: Optional[float] = None, 
                                    price: Optional[float] = None) -> Dict[str, Any]:
        """
        Document an investment decision with structured framework.
        
        Args:
            symbol: Stock symbol
            decision_type: Type of decision (buy, sell, hold)
            rationale: Decision rationale
            amount: Amount of shares/units
            price: Price per share/unit
            
        Returns:
            Documented decision record
        """
        # Get market context and stock metrics
        market_context = self._get_market_context()
        stock_metrics = self._get_current_stock_metrics(symbol)
        
        # Create a structured decision record
        decision_record = {
            "symbol": symbol,
            "decision_type": decision_type,  # buy, sell, hold
            "timestamp": datetime.now().isoformat(),
            "rationale": rationale,
            "amount": amount,
            "price": price,
            "market_context": market_context,
            "stock_metrics": stock_metrics,
            "portfolio_impact": self._calculate_portfolio_impact(symbol, decision_type, amount, price)
        }
        
        # Check for potential biases in the decision
        biases = self.bias_analyzer.analyze_decision_context(decision_record, market_context)
        if biases:
            decision_record["potential_biases"] = biases
            
        # Save the decision record
        self._save_decision_record(decision_record)
        
        return decision_record
    
    def create_investment_policy_statement(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a personalized investment policy statement.
        
        Args:
            user_profile: User profile data
            
        Returns:
            Investment policy statement
        """
        # Generate IPS based on user profile and preferences
        return {
            "investment_objectives": self._generate_investment_objectives(user_profile),
            "risk_constraints": self._generate_risk_constraints(user_profile),
            "liquidity_requirements": self._generate_liquidity_requirements(user_profile),
            "time_horizon": self._determine_time_horizon(user_profile),
            "tax_considerations": self._determine_tax_considerations(user_profile),
            "asset_allocation_targets": self._generate_asset_allocation(user_profile),
            "rebalancing_policy": self._generate_rebalancing_policy(user_profile),
            "performance_evaluation": self._generate_performance_evaluation_criteria(user_profile)
        }
    
    # Private helper methods
    
    def _thesis_addresses_component(self, thesis: str, component: str) -> bool:
        """Check if thesis addresses a specific component"""
        # Component-specific keywords to look for
        component_keywords = {
            "business_model": ["business model", "revenue", "monetization", "products", "services", "how they make money"],
            "competitive_advantage": ["competitive advantage", "moat", "barrier to entry", "competitive position", "market share", "differentiation"],
            "growth_drivers": ["growth driver", "expansion", "new market", "opportunity", "trend", "increase", "catalyst", "tailwind"],
            "risks": ["risk", "threat", "challenge", "headwind", "competition", "concern", "downside", "uncertainty"],
            "valuation_rationale": ["valuation", "undervalued", "overvalued", "price target", "multiple", "P/E", "discount", "premium"],
            "catalyst_events": ["catalyst", "upcoming", "event", "release", "announcement", "trigger", "milestone"],
            "time_horizon": ["time horizon", "timeframe", "short term", "medium term", "long term", "years", "months", "hold period"]
        }
        
        # Check if any component keywords are present in the thesis
        return any(keyword in thesis.lower() for keyword in component_keywords.get(component, []))
    
    def _generate_component_suggestion(self, symbol: str, component: str) -> str:
        """Generate a suggestion for a missing thesis component"""
        # Suggestions for each component
        component_suggestions = {
            "business_model": f"Consider describing how {symbol} generates revenue and profits, including main products and services.",
            "competitive_advantage": f"Explain what gives {symbol} an edge over competitors, such as technology, scale, brand, or network effects.",
            "growth_drivers": f"Identify what will drive {symbol}'s growth in the future, such as market expansion, new products, or industry trends.",
            "risks": f"Address potential risks to {symbol}'s business, such as competition, regulation, or market changes.",
            "valuation_rationale": f"Explain why you believe {symbol} is appropriately valued, undervalued, or overvalued relative to peers or intrinsic value.",
            "catalyst_events": f"Consider what specific events or developments might trigger a change in {symbol}'s valuation or market perception.",
            "time_horizon": "Clarify your expected investment timeframe, whether short-term, medium-term, or long-term."
        }
        
        return component_suggestions.get(component, "Consider addressing this component in your thesis.")
    
    def _generate_counterarguments(self, thesis: str, symbol: str) -> List[str]:
        """Generate counterarguments to test thesis robustness"""
        # In a real implementation, this would generate counter-thesis points
        # For now, return standard counterarguments
        
        # These would ideally be based on actual data and analysis
        standard_counterarguments = [
            f"Consider the impact of rising interest rates on {symbol}'s valuation multiples and growth trajectory.",
            f"What would happen to {symbol} if sector rotation leads to decreased investor interest in this industry?",
            f"How exposed is {symbol} to disruption from new technologies or business models?",
            f"Have you considered how {symbol}'s revenue and margins might be affected in an economic downturn?",
            f"Is there a risk of increased regulation impacting {symbol}'s business model or growth potential?"
        ]
        
        # Return a subset of counterarguments
        return standard_counterarguments[:3]
    
    def _get_market_context(self) -> Dict[str, Any]:
        """Get current market context data"""
        # In a real implementation, this would fetch actual market data
        # For now, return sample data
        return {
            "market_trend": "bullish",  # bullish, bearish, neutral
            "volatility": "normal",  # low, normal, high
            "sector_trends": {
                "Technology": "bullish",
                "Healthcare": "neutral",
                "Consumer Discretionary": "bullish",
                "Financials": "bearish",
                "Energy": "bearish"
            },
            "recent_events": [
                "Fed meeting yesterday resulted in unchanged rates",
                "Technology earnings generally exceeding expectations",
                "GDP growth reported at 2.8% annualized last quarter"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_current_stock_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get current metrics for a stock"""
        # In a real implementation, this would fetch actual stock data
        # For now, return sample data
        return {
            "symbol": symbol,
            "current_price": 150.25,
            "pe_ratio": 25.3,
            "market_cap": 1250000000,
            "52w_high": 175.50,
            "52w_low": 120.75,
            "50d_ma": 148.50,
            "200d_ma": 142.25,
            "ytd_return": 12.5,
            "dividend_yield": 1.8,
            "beta": 1.2,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_portfolio_impact(self, 
                                   symbol: str, 
                                   decision_type: str, 
                                   amount: Optional[float], 
                                   price: Optional[float]) -> Dict[str, Any]:
        """Calculate the impact of a decision on the portfolio"""
        # In a real implementation, this would calculate actual portfolio impacts
        # For now, return sample data
        return {
            "pre_decision_allocation": 5.2,  # Percentage allocation before decision
            "post_decision_allocation": 7.8,  # Percentage allocation after decision
            "sector_impact": 2.5,  # Percentage point change in sector allocation
            "portfolio_beta_change": 0.05,  # Change in portfolio beta
            "diversification_impact": "slight decrease",  # Impact on diversification
            "liquidity_impact": "minimal"  # Impact on portfolio liquidity
        }
    
    def _save_decision_record(self, decision_record: Dict[str, Any]) -> None:
        """Save decision record to database"""
        # In a real implementation, this would save to a database
        self.logger.info(f"Saving decision record for user {self.user_id}, symbol {decision_record['symbol']}")
        # Example of implementation with ORM
        # new_decision = InvestmentDecision(
        #     user_id=self.user_id,
        #     symbol=decision_record['symbol'],
        #     decision_type=decision_record['decision_type'],
        #     rationale=decision_record['rationale'],
        #     amount=decision_record['amount'],
        #     price=decision_record['price'],
        #     market_context=json.dumps(decision_record['market_context']),
        #     stock_metrics=json.dumps(decision_record['stock_metrics']),
        #     portfolio_impact=json.dumps(decision_record['portfolio_impact']),
        #     potential_biases=json.dumps(decision_record.get('potential_biases', [])),
        #     timestamp=datetime.now()
        # )
        # db.session.add(new_decision)
        # db.session.commit()
    
    def _generate_investment_objectives(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate investment objectives based on user profile"""
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")
        investment_goals = user_profile.get("investment_goals", [])
        
        # Map risk tolerance to return targets
        return_targets = {
            "conservative": {"target": "3-5%", "description": "Focus on capital preservation with modest growth"},
            "moderate": {"target": "5-8%", "description": "Balance between capital growth and preservation"},
            "aggressive": {"target": "8-12%", "description": "Focus on capital growth with higher volatility tolerance"},
            "very_aggressive": {"target": "12%+", "description": "Maximum growth with high volatility tolerance"}
        }
        
        return {
            "return_target": return_targets.get(risk_tolerance, return_targets["moderate"]),
            "primary_objectives": self._map_goals_to_objectives(investment_goals),
            "constraints": self._identify_constraints(user_profile)
        }
    
    def _map_goals_to_objectives(self, goals: List[str]) -> List[str]:
        """Map user goals to investment objectives"""
        # Sample mapping
        goals_to_objectives = {
            "retirement": "Long-term capital growth with increasing income component as retirement approaches",
            "education": "Capital growth with liquidity timed for education expenses",
            "house_purchase": "Capital preservation with high liquidity for near-term home purchase",
            "wealth_accumulation": "Maximum long-term capital growth with dividend reinvestment",
            "income": "Generate consistent income through dividends and interest",
            "legacy": "Long-term growth with focus on tax efficiency and estate planning"
        }
        
        return [goals_to_objectives.get(goal, "General capital growth") for goal in goals]
    
    def _identify_constraints(self, user_profile: Dict[str, Any]) -> List[str]:
        """Identify investment constraints from user profile"""
        constraints = []
        
        if user_profile.get("liquidity_needs", "low") == "high":
            constraints.append("Maintain high portfolio liquidity for short-term needs")
            
        if user_profile.get("time_horizon", "long") == "short":
            constraints.append("Short investment horizon requires lower volatility")
            
        if user_profile.get("tax_situation", "normal") == "high":
            constraints.append("Focus on tax-efficient investments and strategies")
            
        # Add any user-specified constraints
        if user_profile.get("specific_constraints"):
            constraints.extend(user_profile.get("specific_constraints", []))
            
        return constraints
    
    def _generate_risk_constraints(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk constraints based on user profile"""
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")
        
        # Map risk tolerance to constraints
        risk_constraints = {
            "conservative": {
                "max_volatility": "8%",
                "max_drawdown": "10%",
                "var_limit": "5% (95% confidence)",
                "beta_target": "0.6-0.8"
            },
            "moderate": {
                "max_volatility": "12%",
                "max_drawdown": "15%",
                "var_limit": "8% (95% confidence)",
                "beta_target": "0.8-1.0"
            },
            "aggressive": {
                "max_volatility": "18%",
                "max_drawdown": "25%",
                "var_limit": "12% (95% confidence)",
                "beta_target": "1.0-1.2"
            },
            "very_aggressive": {
                "max_volatility": "25%+",
                "max_drawdown": "35%+",
                "var_limit": "15%+ (95% confidence)",
                "beta_target": "1.2+"
            }
        }
        
        return risk_constraints.get(risk_tolerance, risk_constraints["moderate"])
    
    def _generate_liquidity_requirements(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate liquidity requirements based on user profile"""
        liquidity_needs = user_profile.get("liquidity_needs", "low")
        emergency_fund_months = user_profile.get("emergency_fund_months", 3)
        
        # Map liquidity needs to requirements
        liquidity_requirements = {
            "low": {
                "cash_allocation": "2-5%",
                "illiquid_assets_max": "30%",
                "redemption_terms": "Some positions may have longer lockups"
            },
            "medium": {
                "cash_allocation": "5-10%",
                "illiquid_assets_max": "20%",
                "redemption_terms": "Majority of positions should be liquid within one week"
            },
            "high": {
                "cash_allocation": "10-15%",
                "illiquid_assets_max": "10%",
                "redemption_terms": "Most positions should be liquid within three days"
            },
            "very_high": {
                "cash_allocation": "15%+",
                "illiquid_assets_max": "5%",
                "redemption_terms": "Daily liquidity for vast majority of portfolio"
            }
        }
        
        result = liquidity_requirements.get(liquidity_needs, liquidity_requirements["medium"])
        result["emergency_fund"] = f"{emergency_fund_months} months of expenses"
        
        return result
    
    def _determine_time_horizon(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Determine investment time horizon"""
        primary_goal = user_profile.get("primary_goal", "")
        age = user_profile.get("age", 35)
        retirement_age = user_profile.get("retirement_age", 65)
        
        # Determine time horizon based on goals and age
        if primary_goal == "retirement":
            years_to_retirement = max(0, retirement_age - age)
            if years_to_retirement > 15:
                horizon = "long"
                description = f"Long-term ({years_to_retirement} years to retirement)"
            elif years_to_retirement > 5:
                horizon = "medium"
                description = f"Medium-term ({years_to_retirement} years to retirement)"
            else:
                horizon = "short"
                description = f"Short-term (approaching retirement in {years_to_retirement} years)"
        elif primary_goal in ["education", "house_purchase"]:
            years_to_goal = user_profile.get("years_to_goal", 10)
            if years_to_goal > 10:
                horizon = "long"
                description = f"Long-term ({years_to_goal} years to {primary_goal})"
            elif years_to_goal > 3:
                horizon = "medium"
                description = f"Medium-term ({years_to_goal} years to {primary_goal})"
            else:
                horizon = "short"
                description = f"Short-term (approaching {primary_goal} in {years_to_goal} years)"
        else:
            # Default based on age
            if age < 40:
                horizon = "long"
                description = "Long-term growth focus with 20+ year horizon"
            elif age < 55:
                horizon = "medium"
                description = "Medium to long-term focus with 10-20 year horizon"
            else:
                horizon = "medium"
                description = "Medium-term focus with transition to income"
                
        return {
            "horizon": horizon,
            "description": description,
            "investment_stages": self._generate_investment_stages(horizon, user_profile)
        }
    
    def _generate_investment_stages(self, horizon: str, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate investment stages based on time horizon"""
        if horizon == "short":
            return [{
                "phase": "Capital Preservation",
                "duration": "1-3 years",
                "focus": "Protect principal and maintain liquidity",
                "asset_allocation": "Heavy fixed income and cash, minimal equity exposure"
            }]
        elif horizon == "medium":
            return [
                {
                    "phase": "Growth Phase",
                    "duration": "1-5 years",
                    "focus": "Moderate capital growth with reasonable risk",
                    "asset_allocation": "Balanced equity and fixed income allocation"
                },
                {
                    "phase": "Transition Phase",
                    "duration": "5-7 years",
                    "focus": "Begin reducing risk as goal approaches",
                    "asset_allocation": "Gradually shifting from growth to preservation"
                }
            ]
        else:  # long horizon
            return [
                {
                    "phase": "Aggressive Growth",
                    "duration": "1-10 years",
                    "focus": "Maximum capital growth with higher risk tolerance",
                    "asset_allocation": "Predominantly equities with targeted alternative investments"
                },
                {
                    "phase": "Sustainable Growth",
                    "duration": "10-20 years",
                    "focus": "Continued growth with moderating risk",
                    "asset_allocation": "Still equity-focused but with increasing diversification"
                },
                {
                    "phase": "Preservation & Income",
                    "duration": "20+ years",
                    "focus": "Shift toward preservation and income generation",
                    "asset_allocation": "More balanced approach with increasing fixed income"
                }
            ]
    
    def _determine_tax_considerations(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Determine tax considerations for investment strategy"""
        tax_bracket = user_profile.get("tax_bracket", "medium")
        has_tax_advantaged_accounts = user_profile.get("has_tax_advantaged_accounts", True)
        
        # Tax strategy based on bracket
        if tax_bracket == "high":
            tax_strategy = "Tax-efficiency is a high priority. Focus on tax-advantaged accounts, municipal bonds, and ETFs with low turnover."
        elif tax_bracket == "medium":
            tax_strategy = "Balance tax-efficiency with investment goals. Utilize tax-advantaged accounts while maintaining flexibility."
        else:
            tax_strategy = "Tax-efficiency is less critical. Focus primarily on investment goals and appropriate asset allocation."
            
        # Account prioritization
        account_priority = []
        if has_tax_advantaged_accounts:
            if tax_bracket in ["high", "medium"]:
                account_priority = [
                    "401(k)/IRA up to match",
                    "HSA (if eligible)",
                    "Remainder of 401(k)/IRA contribution",
                    "Taxable accounts"
                ]
            else:
                account_priority = [
                    "401(k)/IRA up to match",
                    "Taxable accounts for flexibility",
                    "Remainder of 401(k)/IRA contribution"
                ]
        else:
            account_priority = ["Taxable accounts with tax-efficient investment selection"]
            
        return {
            "tax_strategy": tax_strategy,
            "account_priority": account_priority,
            "tax_loss_harvesting": tax_bracket != "low",
            "tax_efficient_investments": ["ETFs", "Index funds", "Municipal bonds" if tax_bracket == "high" else "Taxable bonds"]
        }
    
    def _generate_asset_allocation(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate target asset allocation"""
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")
        time_horizon = user_profile.get("time_horizon", "long")
        
        # Basic allocations based on risk tolerance and time horizon
        allocations = {
            "conservative": {
                "short": {"equities": 20, "fixed_income": 50, "alternatives": 5, "cash": 25},
                "medium": {"equities": 30, "fixed_income": 55, "alternatives": 10, "cash": 5},
                "long": {"equities": 40, "fixed_income": 45, "alternatives": 10, "cash": 5}
            },
            "moderate": {
                "short": {"equities": 30, "fixed_income": 50, "alternatives": 5, "cash": 15},
                "medium": {"equities": 50, "fixed_income": 40, "alternatives": 5, "cash": 5},
                "long": {"equities": 60, "fixed_income": 30, "alternatives": 5, "cash": 5}
            },
            "aggressive": {
                "short": {"equities": 50, "fixed_income": 30, "alternatives": 10, "cash": 10},
                "medium": {"equities": 70, "fixed_income": 20, "alternatives": 5, "cash": 5},
                "long": {"equities": 80, "fixed_income": 10, "alternatives": 5, "cash": 5}
            },
            "very_aggressive": {
                "short": {"equities": 60, "fixed_income": 20, "alternatives": 15, "cash": 5},
                "medium": {"equities": 80, "fixed_income": 5, "alternatives": 10, "cash": 5},
                "long": {"equities": 90, "fixed_income": 0, "alternatives": 5, "cash": 5}
            }
        }
        
        # Get basic allocation
        basic_allocation = allocations.get(risk_tolerance, allocations["moderate"]).get(time_horizon, allocations["moderate"]["medium"])
        
        # Further break down equity allocation
        equity_allocation = {}
        if risk_tolerance in ["conservative", "moderate"]:
            equity_allocation = {
                "large_cap": 60,
                "mid_cap": 20,
                "small_cap": 10,
                "international_developed": 20,
                "international_emerging": 10,
                "reits": 5
            }
        else:
            equity_allocation = {
                "large_cap": 40,
                "mid_cap": 20,
                "small_cap": 15,
                "international_developed": 15,
                "international_emerging": 15,
                "reits": 5
            }
            
        # Normalize to 100%
        total = sum(equity_allocation.values())
        equity_allocation = {k: round(v / total * 100) for k, v in equity_allocation.items()}
        
        return {
            "primary_allocation": basic_allocation,
            "equity_allocation": equity_allocation,
            "allocation_ranges": {
                "equities": f"{max(0, basic_allocation['equities'] - 10)}-{min(100, basic_allocation['equities'] + 10)}%",
                "fixed_income": f"{max(0, basic_allocation['fixed_income'] - 10)}-{min(100, basic_allocation['fixed_income'] + 10)}%",
                "alternatives": f"{max(0, basic_allocation['alternatives'] - 5)}-{min(100, basic_allocation['alternatives'] + 5)}%",
                "cash": f"{max(0, basic_allocation['cash'] - 5)}-{min(100, basic_allocation['cash'] + 5)}%"
            }
        }
    
    def _generate_rebalancing_policy(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate portfolio rebalancing policy"""
        trading_frequency = user_profile.get("trading_frequency", "occasional")
        tax_sensitivity = user_profile.get("tax_sensitivity", "medium")
        
        # Determine rebalancing frequency and thresholds
        if trading_frequency == "frequent":
            frequency = "Quarterly review with threshold-based rebalancing"
        elif trading_frequency == "occasional":
            frequency = "Semi-annual review with threshold-based rebalancing"
        else:
            frequency = "Annual review with threshold-based rebalancing"
            
        # Thresholds based on tax sensitivity
        if tax_sensitivity == "high":
            thresholds = "Wider thresholds (±7.5%) to reduce tax impact from frequent rebalancing"
        elif tax_sensitivity == "medium":
            thresholds = "Standard thresholds (±5%) for asset classes, wider for individual positions"
        else:
            thresholds = "Tighter thresholds (±5%) for more precise adherence to target allocation"
            
        return {
            "frequency": frequency,
            "thresholds": thresholds,
            "methodology": "Threshold-based rebalancing with opportunistic adjustments",
            "tax_considerations": "Utilize new contributions and withdrawals for rebalancing when possible to minimize tax impact" if tax_sensitivity in ["high", "medium"] else "Rebalance as needed regardless of tax consequences"
        }
    
    def _generate_performance_evaluation_criteria(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance evaluation criteria"""
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")
        time_horizon = user_profile.get("time_horizon", "medium")
        
        # Select appropriate benchmarks
        if risk_tolerance in ["conservative", "moderate"] and time_horizon in ["short", "medium"]:
            primary_benchmark = "60/40 Blend (60% S&P 500, 40% Bloomberg US Aggregate Bond Index)"
        elif risk_tolerance in ["conservative", "moderate"] and time_horizon == "long":
            primary_benchmark = "70/30 Blend (70% S&P 500, 30% Bloomberg US Aggregate Bond Index)"
        elif risk_tolerance in ["aggressive", "very_aggressive"] and time_horizon in ["short", "medium"]:
            primary_benchmark = "80/20 Blend (80% S&P 500, 20% Bloomberg US Aggregate Bond Index)"
        else:
            primary_benchmark = "90/10 Blend (90% S&P 500, 10% Bloomberg US Aggregate Bond Index)"
            
        # Evaluation metrics based on risk tolerance
        if risk_tolerance in ["conservative", "moderate"]:
            key_metrics = ["Sharpe Ratio", "Sortino Ratio", "Maximum Drawdown", "Upside/Downside Capture Ratio"]
        else:
            key_metrics = ["Total Return", "Alpha", "Information Ratio", "Beta", "Volatility"]
            
        return {
            "primary_benchmark": primary_benchmark,
            "secondary_benchmarks": ["S&P 500", "Bloomberg US Aggregate Bond Index", "MSCI ACWI"],
            "evaluation_frequency": "Quarterly review with annual comprehensive analysis",
            "key_metrics": key_metrics,
            "minimum_evaluation_period": "Full market cycle (typically 3-5 years) for meaningful assessment"
        }