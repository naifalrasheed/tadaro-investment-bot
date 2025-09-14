"""
Reflective Learning System for Investment Bot

This module implements a system that enables the investment bot to learn from
its own decisions, evaluate its performance, and improve over time through
a process of structured reflection and analysis.
"""

import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
import pickle
import re
from collections import defaultdict

class ReflectiveInvestmentLearner:
    """
    A system that enables the investment bot to learn from its past decisions
    and improve its investment reasoning process over time.
    """
    
    def __init__(self, user_id: str = "default", 
                memory_system: Any = None,
                data_dir: str = "reflective_data"):
        """
        Initialize the reflective learning system.
        
        Args:
            user_id: Unique identifier for the user
            memory_system: Optional reference to the memory system
            data_dir: Directory to store reflection data
        """
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.memory_system = memory_system
        self.data_dir = data_dir
        self.user_dir = os.path.join(data_dir, f'user_{user_id}')
        
        # Create data directories if they don't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.user_dir):
            os.makedirs(self.user_dir)
            
        # Paths for storing reflection data
        self.decision_history_path = os.path.join(self.user_dir, 'decision_history.json')
        self.outcomes_path = os.path.join(self.user_dir, 'decision_outcomes.json')
        self.insights_path = os.path.join(self.user_dir, 'reflection_insights.json')
        self.weights_path = os.path.join(self.user_dir, 'agent_weights.json')
        
        # Load existing data
        self.decision_history = self._load_decision_history()
        self.decision_outcomes = self._load_decision_outcomes()
        self.insights = self._load_insights()
        self.agent_weights = self._load_agent_weights()
        
    def _load_decision_history(self) -> List[Dict]:
        """Load decision history or create empty list if it doesn't exist."""
        if os.path.exists(self.decision_history_path):
            try:
                with open(self.decision_history_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading decision history: {e}")
                return []
        else:
            return []
    
    def _load_decision_outcomes(self) -> Dict:
        """Load decision outcomes or create empty dict if it doesn't exist."""
        if os.path.exists(self.outcomes_path):
            try:
                with open(self.outcomes_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading decision outcomes: {e}")
                return {}
        else:
            return {}
    
    def _load_insights(self) -> Dict:
        """Load reflection insights or create default if it doesn't exist."""
        if os.path.exists(self.insights_path):
            try:
                with open(self.insights_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading reflection insights: {e}")
                return self._create_default_insights()
        else:
            return self._create_default_insights()
    
    def _create_default_insights(self) -> Dict:
        """Create default insights structure."""
        return {
            "agent_performance": {
                "technical": {"accuracy": 0.0, "confidence_calibration": 0.0, "sample_size": 0},
                "fundamental": {"accuracy": 0.0, "confidence_calibration": 0.0, "sample_size": 0},
                "sentiment": {"accuracy": 0.0, "confidence_calibration": 0.0, "sample_size": 0},
                "risk": {"accuracy": 0.0, "confidence_calibration": 0.0, "sample_size": 0}
            },
            "decision_patterns": {
                "successful_patterns": [],
                "unsuccessful_patterns": []
            },
            "market_conditions": {
                "performance_by_condition": {}
            },
            "learning_progress": {
                "accuracy_trend": [],
                "confidence_calibration_trend": []
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_agent_weights(self) -> Dict:
        """Load agent weights or create default if it doesn't exist."""
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading agent weights: {e}")
                return self._create_default_weights()
        else:
            return self._create_default_weights()
    
    def _create_default_weights(self) -> Dict:
        """Create default agent weights."""
        return {
            "technical": 0.35,
            "fundamental": 0.3,
            "sentiment": 0.15,
            "risk": 0.2
        }
    
    def _save_decision_history(self):
        """Save decision history to file."""
        try:
            with open(self.decision_history_path, 'w') as f:
                json.dump(self.decision_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving decision history: {e}")
    
    def _save_decision_outcomes(self):
        """Save decision outcomes to file."""
        try:
            with open(self.outcomes_path, 'w') as f:
                json.dump(self.decision_outcomes, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving decision outcomes: {e}")
    
    def _save_insights(self):
        """Save reflection insights to file."""
        try:
            self.insights["last_updated"] = datetime.now().isoformat()
            with open(self.insights_path, 'w') as f:
                json.dump(self.insights, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving reflection insights: {e}")
    
    def _save_agent_weights(self):
        """Save agent weights to file."""
        try:
            with open(self.weights_path, 'w') as f:
                json.dump(self.agent_weights, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving agent weights: {e}")
    
    def reflect_on_decisions(self, decisions: List[Dict]) -> Dict:
        """
        Reflect on a batch of investment decisions to extract insights.
        
        Args:
            decisions: List of decision records to reflect on
            
        Returns:
            Dict of insights from the reflection process
        """
        try:
            self.logger.info(f"Reflecting on {len(decisions)} decisions")
            
            # Add decisions to history
            for decision in decisions:
                if decision not in self.decision_history:
                    decision_id = f"{decision['symbol']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.decision_history)}"
                    decision["decision_id"] = decision_id
                    self.decision_history.append(decision)
            
            # Save updated history
            self._save_decision_history()
            
            # Analyze decisions with outcomes
            self._analyze_decision_outcomes()
            
            # Extract decision patterns
            self._extract_decision_patterns()
            
            # Update agent weights based on performance
            self._update_agent_weights()
            
            # Save insights
            self._save_insights()
            
            return self.insights
            
        except Exception as e:
            self.logger.error(f"Error reflecting on decisions: {e}")
            return {}
    
    def record_outcome(self, decision_id: str, outcome: Dict) -> None:
        """
        Record the outcome of a previous investment decision.
        
        Args:
            decision_id: ID of the original decision
            outcome: Actual performance and outcome data
        """
        try:
            self.logger.info(f"Recording outcome for decision {decision_id}")
            
            # Add outcome data
            self.decision_outcomes[decision_id] = {
                "recorded_date": datetime.now().isoformat(),
                "outcome_data": outcome
            }
            
            # Save updated outcomes
            self._save_decision_outcomes()
            
            # Re-analyze with new outcome data
            self._analyze_decision_outcomes()
            self._save_insights()
            
        except Exception as e:
            self.logger.error(f"Error recording outcome: {e}")
    
    def _analyze_decision_outcomes(self) -> None:
        """Analyze decision outcomes to extract agent performance metrics."""
        if not self.decision_outcomes:
            return
            
        try:
            # Initialize performance tracking
            agent_performance = {
                "technical": {"correct": 0, "incorrect": 0, "confidence_error": 0.0},
                "fundamental": {"correct": 0, "incorrect": 0, "confidence_error": 0.0},
                "sentiment": {"correct": 0, "incorrect": 0, "confidence_error": 0.0},
                "risk": {"correct": 0, "incorrect": 0, "confidence_error": 0.0}
            }
            
            # Analyze each decision with an outcome
            for decision_id, outcome_data in self.decision_outcomes.items():
                # Find the original decision
                decision = None
                for d in self.decision_history:
                    if d.get("decision_id") == decision_id:
                        decision = d
                        break
                
                if not decision:
                    continue
                
                outcome = outcome_data["outcome_data"]
                
                # Get actual price change
                actual_change = outcome.get("price_change_pct", 0)
                
                # Get agent predictions and evaluate them
                agent_insights = decision.get("agent_insights", {})
                recommendation = decision.get("recommendation", {})
                
                # Evaluate technical analysis
                if "technical" in agent_insights:
                    technical = agent_insights["technical"]
                    predicted_sentiment = technical.get("sentiment", "neutral")
                    
                    # Check if prediction was correct
                    if (predicted_sentiment == "bullish" and actual_change > 0) or \
                       (predicted_sentiment == "bearish" and actual_change < 0) or \
                       (predicted_sentiment == "neutral" and abs(actual_change) < 0.03):
                        agent_performance["technical"]["correct"] += 1
                    else:
                        agent_performance["technical"]["incorrect"] += 1
                    
                    # Calculate confidence calibration error
                    confidence = technical.get("confidence", 0.5)
                    prediction_confidence = 1.0 if actual_change > 0 and predicted_sentiment == "bullish" else 0.0
                    agent_performance["technical"]["confidence_error"] += abs(confidence - prediction_confidence)
                
                # Evaluate fundamental analysis
                if "fundamental" in agent_insights:
                    fundamental = agent_insights["fundamental"]
                    predicted_outlook = fundamental.get("outlook", "neutral")
                    
                    # Check if prediction was correct (using longer timeframe)
                    if (predicted_outlook in ["positive", "very positive"] and actual_change > 0) or \
                       (predicted_outlook in ["negative", "very negative"] and actual_change < 0) or \
                       (predicted_outlook == "neutral" and abs(actual_change) < 0.05):
                        agent_performance["fundamental"]["correct"] += 1
                    else:
                        agent_performance["fundamental"]["incorrect"] += 1
                    
                    # Calculate confidence calibration error
                    confidence = fundamental.get("confidence", 0.5)
                    prediction_confidence = 1.0 if actual_change > 0 and predicted_outlook in ["positive", "very positive"] else 0.0
                    agent_performance["fundamental"]["confidence_error"] += abs(confidence - prediction_confidence)
                
                # Evaluate sentiment analysis
                if "sentiment" in agent_insights:
                    sentiment = agent_insights["sentiment"]
                    sentiment_score = sentiment.get("score", 50)
                    sentiment_positive = sentiment_score > 55
                    sentiment_negative = sentiment_score < 45
                    
                    # Check if prediction was correct
                    if (sentiment_positive and actual_change > 0) or \
                       (sentiment_negative and actual_change < 0) or \
                       (not sentiment_positive and not sentiment_negative and abs(actual_change) < 0.03):
                        agent_performance["sentiment"]["correct"] += 1
                    else:
                        agent_performance["sentiment"]["incorrect"] += 1
                    
                    # Calculate confidence calibration error
                    confidence = sentiment.get("confidence", 0.5)
                    prediction_confidence = 1.0 if actual_change > 0 and sentiment_positive else 0.0
                    agent_performance["sentiment"]["confidence_error"] += abs(confidence - prediction_confidence)
                
                # Evaluate risk assessment
                if "risk" in agent_insights:
                    risk = agent_insights["risk"]
                    risk_level = risk.get("risk_level", "moderate")
                    high_risk = risk_level in ["high", "very high"]
                    
                    # Check if risk assessment was correct (high risk should correlate with high volatility)
                    volatility = outcome.get("realized_volatility", 0)
                    high_volatility = volatility > 0.02  # 2% daily volatility is high
                    
                    if (high_risk and high_volatility) or (not high_risk and not high_volatility):
                        agent_performance["risk"]["correct"] += 1
                    else:
                        agent_performance["risk"]["incorrect"] += 1
                    
                    # Calculate confidence calibration error
                    confidence = risk.get("confidence", 0.5)
                    prediction_confidence = 1.0 if high_volatility and high_risk else 0.0
                    agent_performance["risk"]["confidence_error"] += abs(confidence - prediction_confidence)
            
            # Calculate performance metrics
            for agent, data in agent_performance.items():
                total = data["correct"] + data["incorrect"]
                if total > 0:
                    accuracy = data["correct"] / total
                    confidence_calibration = 1.0 - (data["confidence_error"] / total)
                    
                    self.insights["agent_performance"][agent] = {
                        "accuracy": accuracy,
                        "confidence_calibration": max(0, confidence_calibration),  # Ensure non-negative
                        "sample_size": total
                    }
            
            # Record accuracy trend
            overall_correct = sum(data["correct"] for data in agent_performance.values())
            overall_total = sum(data["correct"] + data["incorrect"] for data in agent_performance.values())
            
            if overall_total > 0:
                overall_accuracy = overall_correct / overall_total
                self.insights["learning_progress"]["accuracy_trend"].append({
                    "date": datetime.now().isoformat(),
                    "accuracy": overall_accuracy,
                    "sample_size": overall_total
                })
                
                # Keep only the last 20 trend points
                if len(self.insights["learning_progress"]["accuracy_trend"]) > 20:
                    self.insights["learning_progress"]["accuracy_trend"] = self.insights["learning_progress"]["accuracy_trend"][-20:]
            
        except Exception as e:
            self.logger.error(f"Error analyzing decision outcomes: {e}")
    
    def _extract_decision_patterns(self) -> None:
        """Extract patterns from successful and unsuccessful decisions."""
        if not self.decision_outcomes:
            return
            
        try:
            # Get decisions with outcomes
            decisions_with_outcomes = []
            for decision in self.decision_history:
                decision_id = decision.get("decision_id")
                if decision_id in self.decision_outcomes:
                    decision_with_outcome = {
                        **decision,
                        "outcome": self.decision_outcomes[decision_id]["outcome_data"]
                    }
                    decisions_with_outcomes.append(decision_with_outcome)
            
            if not decisions_with_outcomes:
                return
                
            # Separate successful and unsuccessful decisions
            successful = []
            unsuccessful = []
            
            for decision in decisions_with_outcomes:
                outcome = decision.get("outcome", {})
                actual_change = outcome.get("price_change_pct", 0)
                recommendation = decision.get("recommendation", {})
                rec_type = recommendation.get("recommendation", "hold")
                
                # Determine success based on recommendation type and actual change
                success = False
                if rec_type in ["strong_buy", "buy"] and actual_change > 0:
                    success = True
                elif rec_type in ["strong_sell", "sell"] and actual_change < 0:
                    success = True
                elif rec_type == "hold" and abs(actual_change) < 0.03:
                    success = True
                
                if success:
                    successful.append(decision)
                else:
                    unsuccessful.append(decision)
            
            # Extract patterns from successful decisions
            successful_patterns = self._identify_patterns(successful)
            unsuccessful_patterns = self._identify_patterns(unsuccessful)
            
            self.insights["decision_patterns"]["successful_patterns"] = successful_patterns
            self.insights["decision_patterns"]["unsuccessful_patterns"] = unsuccessful_patterns
            
            # Analyze performance by market condition
            self._analyze_market_conditions(decisions_with_outcomes)
            
        except Exception as e:
            self.logger.error(f"Error extracting decision patterns: {e}")
    
    def _identify_patterns(self, decisions: List[Dict]) -> List[Dict]:
        """Identify common patterns in a set of decisions."""
        if not decisions:
            return []
            
        patterns = []
        
        try:
            # Count occurrences of different features
            agent_sentiments = defaultdict(int)
            conflict_types = defaultdict(int)
            conflict_resolutions = defaultdict(int)
            timeframes = defaultdict(int)
            sectors = defaultdict(int)
            risk_levels = defaultdict(int)
            
            # Extract features from decisions
            for decision in decisions:
                agent_insights = decision.get("agent_insights", {})
                recommendation = decision.get("recommendation", {})
                reasoning = decision.get("reasoning", [])
                
                # Agent sentiments/outlooks
                if "technical" in agent_insights:
                    sentiment = agent_insights["technical"].get("sentiment", "neutral")
                    agent_sentiments[f"technical_{sentiment}"] += 1
                
                if "fundamental" in agent_insights:
                    outlook = agent_insights["fundamental"].get("outlook", "neutral")
                    agent_sentiments[f"fundamental_{outlook}"] += 1
                
                if "sentiment" in agent_insights:
                    classification = agent_insights["sentiment"].get("classification", "neutral")
                    agent_sentiments[f"sentiment_{classification}"] += 1
                
                # Conflict patterns
                for step in reasoning:
                    if step.get("step") == "Conflict Resolution":
                        for conflict_type, resolution in step.get("resolution", {}).items():
                            conflict_types[conflict_type] += 1
                            if "resolution" in resolution:
                                conflict_resolutions[resolution["resolution"]] += 1
                
                # Timeframe
                timeframe = recommendation.get("timeframe", "medium_term")
                timeframes[timeframe] += 1
                
                # Sector
                if "fundamental" in agent_insights:
                    sector = agent_insights["fundamental"].get("sector", "Unknown")
                    sectors[sector] += 1
                
                # Risk level
                if "risk" in agent_insights:
                    risk_level = agent_insights["risk"].get("risk_level", "moderate")
                    risk_levels[risk_level] += 1
            
            # Extract significant patterns (occurring in at least 25% of decisions)
            total_decisions = len(decisions)
            min_occurrences = max(2, total_decisions // 4)
            
            # Agent sentiment patterns
            for sentiment, count in agent_sentiments.items():
                if count >= min_occurrences:
                    patterns.append({
                        "type": "agent_sentiment",
                        "pattern": sentiment,
                        "frequency": count / total_decisions
                    })
            
            # Conflict resolution patterns
            for resolution, count in conflict_resolutions.items():
                if count >= min_occurrences:
                    patterns.append({
                        "type": "conflict_resolution",
                        "pattern": resolution,
                        "frequency": count / total_decisions
                    })
            
            # Timeframe patterns
            for timeframe, count in timeframes.items():
                if count >= min_occurrences:
                    patterns.append({
                        "type": "timeframe",
                        "pattern": timeframe,
                        "frequency": count / total_decisions
                    })
            
            # Sector patterns
            for sector, count in sectors.items():
                if count >= min_occurrences:
                    patterns.append({
                        "type": "sector",
                        "pattern": sector,
                        "frequency": count / total_decisions
                    })
            
            # Risk level patterns
            for risk_level, count in risk_levels.items():
                if count >= min_occurrences:
                    patterns.append({
                        "type": "risk_level",
                        "pattern": risk_level,
                        "frequency": count / total_decisions
                    })
            
        except Exception as e:
            self.logger.error(f"Error identifying patterns: {e}")
        
        return patterns
    
    def _analyze_market_conditions(self, decisions: List[Dict]) -> None:
        """Analyze performance under different market conditions."""
        try:
            # Market condition categories
            conditions = {
                "bull_market": [],
                "bear_market": [],
                "high_volatility": [],
                "low_volatility": []
            }
            
            # Categorize decisions by market condition
            for decision in decisions:
                outcome = decision.get("outcome", {})
                market_condition = outcome.get("market_condition", {})
                
                # Bull/bear market
                market_trend = market_condition.get("market_trend", "neutral")
                if market_trend == "bullish":
                    conditions["bull_market"].append(decision)
                elif market_trend == "bearish":
                    conditions["bear_market"].append(decision)
                
                # Volatility
                volatility = market_condition.get("volatility", "normal")
                if volatility == "high":
                    conditions["high_volatility"].append(decision)
                elif volatility == "low":
                    conditions["low_volatility"].append(decision)
            
            # Calculate performance metrics for each condition
            performance_by_condition = {}
            
            for condition, decisions_list in conditions.items():
                if not decisions_list:
                    continue
                    
                # Calculate success rate
                successful = 0
                for decision in decisions_list:
                    outcome = decision.get("outcome", {})
                    actual_change = outcome.get("price_change_pct", 0)
                    recommendation = decision.get("recommendation", {})
                    rec_type = recommendation.get("recommendation", "hold")
                    
                    # Determine success based on recommendation type and actual change
                    if rec_type in ["strong_buy", "buy"] and actual_change > 0:
                        successful += 1
                    elif rec_type in ["strong_sell", "sell"] and actual_change < 0:
                        successful += 1
                    elif rec_type == "hold" and abs(actual_change) < 0.03:
                        successful += 1
                
                success_rate = successful / len(decisions_list)
                
                performance_by_condition[condition] = {
                    "success_rate": success_rate,
                    "sample_size": len(decisions_list)
                }
            
            self.insights["market_conditions"]["performance_by_condition"] = performance_by_condition
            
        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")
    
    def _update_agent_weights(self) -> None:
        """Update agent weights based on performance."""
        try:
            agent_performance = self.insights["agent_performance"]
            
            # Calculate performance scores for each agent
            performance_scores = {}
            total_score = 0
            
            for agent, metrics in agent_performance.items():
                # Only update weights if we have meaningful sample size
                if metrics["sample_size"] < 5:
                    performance_scores[agent] = self.agent_weights[agent]
                    total_score += performance_scores[agent]
                    continue
                
                # Calculate balanced performance score
                accuracy_weight = 0.7
                calibration_weight = 0.3
                
                performance_score = (
                    accuracy_weight * metrics["accuracy"] +
                    calibration_weight * metrics["confidence_calibration"]
                )
                
                # Add small random variation to encourage exploration (0.95-1.05)
                exploration_factor = 1.0 + (np.random.random() * 0.1 - 0.05)
                performance_score *= exploration_factor
                
                performance_scores[agent] = performance_score
                total_score += performance_score
            
            # Normalize to sum to 1
            if total_score > 0:
                for agent in performance_scores:
                    self.agent_weights[agent] = performance_scores[agent] / total_score
            
            # Save updated weights
            self._save_agent_weights()
            
        except Exception as e:
            self.logger.error(f"Error updating agent weights: {e}")
    
    def get_insights(self) -> Dict:
        """Get current reflection insights."""
        return self.insights
    
    def get_agent_weights(self) -> Dict:
        """Get current agent weights."""
        return self.agent_weights
    
    def simulate_outcome(self, decision: Dict, actual_change: float) -> Dict:
        """
        Simulate a decision outcome for testing purposes.
        
        Args:
            decision: Decision record
            actual_change: Actual price change percentage
            
        Returns:
            Simulated outcome data
        """
        outcome = {
            "price_change_pct": actual_change,
            "realized_volatility": abs(actual_change) * 2,  # Simplified volatility
            "market_condition": {
                "market_trend": "bullish" if actual_change > 0 else "bearish",
                "volatility": "high" if abs(actual_change) > 0.05 else "normal"
            },
            "time_horizon": "1 month",
            "simulated": True
        }
        
        return outcome