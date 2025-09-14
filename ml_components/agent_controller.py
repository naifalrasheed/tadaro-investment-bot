"""
Agent Controller - Main orchestration layer for the investment bot's multi-agent system.

This module implements the LLM Controller Agent that coordinates the specialized
financial analysis agents, manages the memory system, and implements the ReAct pattern.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import numpy as np
from datetime import datetime

from .adaptive_learning import AdaptiveLearningSystem
from .fundamental_analysis import FundamentalAnalyzer

class AgentController:
    """
    LLM Controller Agent that coordinates the multi-agent investment system.
    
    This controller implements:
    1. Chain-of-Thought reasoning for investment decisions
    2. ReAct pattern for market analysis
    3. Coordination of specialized agents
    4. Memory management
    5. Reflective learning
    """
    
    def __init__(self, user_id: str = "default", config_path: Optional[str] = None):
        """
        Initialize the agent controller with all required components.
        
        Args:
            user_id: Unique identifier for the user
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize memory system
        self.memory = AdaptiveLearningSystem(user_id)
        
        # Placeholder for specialized agents - will be filled when those modules are implemented
        self.agents = {}
        
        # Storage for reasoning history
        self.reasoning_history = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            "agent_weights": {
                "technical": 0.35,
                "fundamental": 0.3,
                "sentiment": 0.15,
                "risk": 0.2
            },
            "reflection_frequency": 5,  # Reflect after every 5 recommendations
            "confidence_threshold": 0.7,  # Minimum confidence to make a recommendation
            "rag_enabled": True,
            "debug_mode": False
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    return {**default_config, **config}
            except Exception as e:
                self.logger.error(f"Error loading config from {config_path}: {e}")
                
        return default_config
    
    def analyze_stock(self, symbol: str, market_data: Dict, fundamental_data: Dict) -> Dict:
        """
        Analyze a stock using the multi-agent system with Chain-of-Thought reasoning.
        
        Args:
            symbol: Stock ticker symbol
            market_data: Technical market data for the stock
            fundamental_data: Fundamental financial data for the stock
            
        Returns:
            Dict containing analysis results and recommendation
        """
        self.logger.info(f"Starting multi-agent analysis for {symbol}")
        
        # Step 1: Retrieve relevant context from memory
        user_preferences = self.memory.get_user_profile_summary()
        
        # Step 2: Initialize collection for agent results
        agent_results = {}
        
        # This is a placeholder until the specialized agents are implemented
        # For now, perform a simplified analysis using existing components
        try:
            # Basic technical analysis using existing components
            technical_sentiment = "neutral"
            technical_confidence = 0.5
            
            agent_results["technical"] = {
                "sentiment": technical_sentiment,
                "confidence": technical_confidence,
                "key_indicators": {"trend": "neutral", "momentum": "neutral"},
                "volatility": 0.5
            }
            
            # Basic fundamental analysis using existing components
            health_score = 0.5
            fundamental_outlook = "stable"
            
            agent_results["fundamental"] = {
                "health": "average",
                "health_score": health_score,
                "outlook": fundamental_outlook,
                "confidence": 0.5,
                "key_metrics": {},
                "sector": fundamental_data.get("sector", "Unknown"),
                "metrics": {"dividend_yield": 0}
            }
            
            # Placeholder for sentiment analysis
            agent_results["sentiment"] = {
                "score": 50,  # 0-100 scale
                "classification": "neutral",
                "confidence": 0.5,
                "sources": [],
                "data_age_days": 30
            }
            
            # Placeholder for risk assessment
            agent_results["risk"] = {
                "risk_level": "moderate",
                "risk_score": 0.5,  # 0-1 scale
                "confidence": 0.5,
                "key_risks": []
            }
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {e}")
            return {"error": str(e), "status": "failed"}
        
        # Step 3: Chain-of-Thought reasoning to synthesize outputs
        reasoning_steps = self._reason_through_analysis(symbol, agent_results)
        
        # Step 4: Form final recommendation
        recommendation = self._form_recommendation(symbol, agent_results, reasoning_steps)
        
        # Step 5: Store reasoning in memory for reflection
        self.reasoning_history.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "agent_results": agent_results,
            "reasoning": reasoning_steps,
            "recommendation": recommendation
        })
        
        return {
            "symbol": symbol,
            "recommendation": recommendation,
            "confidence": recommendation["confidence"],
            "agent_insights": agent_results,
            "reasoning": reasoning_steps if self.config["debug_mode"] else None
        }
    
    def _reason_through_analysis(self, symbol: str, agent_results: Dict) -> List[Dict]:
        """
        Implement Chain-of-Thought reasoning about the stock analysis.
        
        Args:
            symbol: Stock ticker symbol
            agent_results: Results from each specialized agent
            
        Returns:
            List of reasoning steps
        """
        reasoning = []
        
        # Step 1: Assess technical indicators
        technical_sentiment = agent_results["technical"]["sentiment"]
        reasoning.append({
            "step": "Technical Analysis",
            "thought": f"Technical indicators for {symbol} suggest a {technical_sentiment} outlook.",
            "evidence": agent_results["technical"]["key_indicators"],
            "confidence": agent_results["technical"]["confidence"]
        })
        
        # Step 2: Consider fundamental metrics
        fundamental_health = agent_results["fundamental"]["health"]
        reasoning.append({
            "step": "Fundamental Analysis",
            "thought": f"Fundamental analysis shows {symbol} to be in {fundamental_health} financial health.",
            "evidence": agent_results["fundamental"]["key_metrics"],
            "confidence": agent_results["fundamental"]["confidence"]
        })
        
        # Step 3: Evaluate market sentiment
        sentiment_score = agent_results["sentiment"]["score"]
        reasoning.append({
            "step": "Sentiment Analysis",
            "thought": f"Market sentiment for {symbol} is {sentiment_score}.",
            "evidence": agent_results["sentiment"]["sources"],
            "confidence": agent_results["sentiment"]["confidence"]
        })
        
        # Step 4: Assess risk factors
        risk_level = agent_results["risk"]["risk_level"]
        reasoning.append({
            "step": "Risk Assessment",
            "thought": f"The risk level for {symbol} is considered {risk_level}.",
            "evidence": agent_results["risk"]["key_risks"],
            "confidence": agent_results["risk"]["confidence"]
        })
        
        # Step 5: Resolve conflicts between analyses
        conflicts = self._identify_conflicts(agent_results)
        if conflicts:
            reasoning.append({
                "step": "Conflict Resolution",
                "thought": "There are conflicting signals that need to be resolved.",
                "evidence": conflicts,
                "resolution": self._resolve_conflicts(conflicts, agent_results)
            })
        
        # Step 6: Consider user preferences
        user_profile = self.memory.get_user_profile_summary()
        reasoning.append({
            "step": "User Preference Alignment",
            "thought": "Assessing alignment with user's investment preferences.",
            "preference_match": self._calculate_preference_match(symbol, agent_results, user_profile)
        })
        
        return reasoning
    
    def _identify_conflicts(self, agent_results: Dict) -> List[Dict]:
        """Identify conflicts between different agent analyses."""
        conflicts = []
        
        # Compare technical and fundamental outlook
        if agent_results["technical"]["sentiment"] != agent_results["fundamental"]["outlook"]:
            conflicts.append({
                "type": "technical_fundamental_mismatch",
                "description": "Technical and fundamental analyses have different outlooks",
                "technical_view": agent_results["technical"]["sentiment"],
                "fundamental_view": agent_results["fundamental"]["outlook"]
            })
        
        # Check if sentiment conflicts with technical/fundamental
        sentiment = agent_results["sentiment"]["classification"]
        if (sentiment == "positive" and agent_results["technical"]["sentiment"] == "bearish") or \
           (sentiment == "negative" and agent_results["technical"]["sentiment"] == "bullish"):
            conflicts.append({
                "type": "sentiment_technical_mismatch",
                "description": "Sentiment analysis conflicts with technical outlook",
                "sentiment_view": sentiment,
                "technical_view": agent_results["technical"]["sentiment"]
            })
            
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict], agent_results: Dict) -> Dict:
        """Resolve conflicts between agent analyses."""
        resolution = {}
        
        for conflict in conflicts:
            if conflict["type"] == "technical_fundamental_mismatch":
                # Resolve based on confidence and time horizon
                tech_confidence = agent_results["technical"]["confidence"]
                fund_confidence = agent_results["fundamental"]["confidence"]
                
                if tech_confidence > fund_confidence * 1.5:
                    resolution[conflict["type"]] = {
                        "resolution": "favor_technical",
                        "reason": "Technical analysis has significantly higher confidence"
                    }
                elif fund_confidence > tech_confidence * 1.5:
                    resolution[conflict["type"]] = {
                        "resolution": "favor_fundamental",
                        "reason": "Fundamental analysis has significantly higher confidence"
                    }
                else:
                    resolution[conflict["type"]] = {
                        "resolution": "balanced_view",
                        "reason": "Similar confidence levels - considering both perspectives"
                    }
                    
            elif conflict["type"] == "sentiment_technical_mismatch":
                # Consider recency of sentiment data
                sentiment_age = agent_results["sentiment"].get("data_age_days", 30)
                
                if sentiment_age <= 7:  # Recent sentiment
                    resolution[conflict["type"]] = {
                        "resolution": "favor_sentiment",
                        "reason": "Recent sentiment data may indicate changing market perception"
                    }
                else:
                    resolution[conflict["type"]] = {
                        "resolution": "favor_technical",
                        "reason": "Technical signals with older sentiment data"
                    }
                    
        return resolution
    
    def _calculate_preference_match(self, symbol: str, agent_results: Dict, user_profile: Dict) -> Dict:
        """Calculate how well the stock matches user preferences."""
        # Extract relevant features from agent results
        features = {
            "price_momentum": 0.5,  # placeholder
            "weekly_range": 0.5,     # placeholder
            "ytd_performance": 0.5,  # placeholder
            "news_sentiment": agent_results["sentiment"]["score"] / 100,
            "rotc": agent_results["fundamental"].get("metrics", {}).get("rotc", 0),
            "pe_ratio": agent_results["fundamental"].get("metrics", {}).get("pe_ratio", 0),
            "dividend_yield": agent_results["fundamental"].get("metrics", {}).get("dividend_yield", 0),
            "volume_change": 0.5,    # placeholder
            "market_cap": 0.5        # placeholder
        }
        
        # Check sector preferences
        sector = agent_results["fundamental"]["sector"]
        preferred_sectors = user_profile.get("preferred_sectors", [])
        sector_match = sector in preferred_sectors
        
        # Calculate match score using adaptive learning prediction
        match_score = 0.5  # default neutral score
        
        # Use memory system to predict if user would like this stock
        predicted_preference = self.memory.predict_stock_preference(features)
        if "probability" in predicted_preference:
            match_score = predicted_preference["probability"]
        
        return {
            "match_score": match_score,
            "sector_match": sector_match,
            "predicted_preference": predicted_preference
        }
    
    def _form_recommendation(self, symbol: str, agent_results: Dict, reasoning_steps: List[Dict]) -> Dict:
        """
        Form the final recommendation based on agent outputs and reasoning.
        
        Args:
            symbol: Stock ticker symbol
            agent_results: Results from each specialized agent
            reasoning_steps: The chain-of-thought reasoning steps
            
        Returns:
            Dictionary containing the recommendation
        """
        # Calculate weighted recommendation score
        weights = self.config["agent_weights"]
        
        # Transform sentiments to numeric scores
        sentiment_map = {"bullish": 1.0, "neutral": 0.5, "bearish": 0.0}
        technical_score = sentiment_map.get(agent_results["technical"]["sentiment"], 0.5)
        
        fundamental_score = agent_results["fundamental"]["health_score"]
        sentiment_score = agent_results["sentiment"]["score"] / 100  # Normalize to 0-1
        risk_score = 1 - agent_results["risk"]["risk_score"]  # Invert risk (high risk → low score)
        
        # Calculate weighted score
        weighted_score = (
            weights["technical"] * technical_score +
            weights["fundamental"] * fundamental_score +
            weights["sentiment"] * sentiment_score +
            weights["risk"] * risk_score
        )
        
        # Determine recommendation type based on score
        if weighted_score >= 0.7:
            rec_type = "strong_buy"
        elif weighted_score >= 0.6:
            rec_type = "buy"
        elif weighted_score >= 0.4:
            rec_type = "hold"
        elif weighted_score >= 0.3:
            rec_type = "sell"
        else:
            rec_type = "strong_sell"
            
        # Calculate confidence based on agent confidences and agreement
        confidence_values = [
            agent_results["technical"]["confidence"],
            agent_results["fundamental"]["confidence"],
            agent_results["sentiment"]["confidence"],
            agent_results["risk"]["confidence"]
        ]
        
        # Base confidence on the average of agent confidences
        avg_confidence = sum(confidence_values) / len(confidence_values)
        
        # Adjust confidence based on agent agreement
        scores = [technical_score, fundamental_score, sentiment_score, risk_score]
        score_variance = np.var(scores)
        agreement_factor = 1 - min(score_variance * 2, 0.5)  # Lower variance means higher agreement
        
        final_confidence = avg_confidence * agreement_factor
        
        # Generate explanation from reasoning steps
        explanation = self._generate_explanation(reasoning_steps, rec_type)
        
        timeframe = self._determine_timeframe(agent_results)
        
        return {
            "recommendation": rec_type,
            "score": weighted_score,
            "confidence": final_confidence,
            "explanation": explanation,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_explanation(self, reasoning_steps: List[Dict], recommendation: str) -> str:
        """Generate a natural language explanation for the recommendation."""
        # Extract key points from reasoning
        technical_point = reasoning_steps[0]["thought"]
        fundamental_point = reasoning_steps[1]["thought"]
        sentiment_point = reasoning_steps[2]["thought"]
        risk_point = reasoning_steps[3]["thought"]
        
        # Check for conflicts and their resolution
        conflict_resolution = ""
        for step in reasoning_steps:
            if step.get("step") == "Conflict Resolution" and step.get("resolution"):
                resolution = step["resolution"]
                if resolution:
                    conflict_keys = list(resolution.keys())
                    if conflict_keys:
                        first_conflict = resolution[conflict_keys[0]]
                        conflict_resolution = f" While there was a conflict between {conflict_keys[0].replace('_', ' ')}, {first_conflict['reason']}."
        
        # Map recommendation to explanation text
        rec_map = {
            "strong_buy": "strongly recommend buying",
            "buy": "recommend buying",
            "hold": "recommend holding",
            "sell": "recommend selling",
            "strong_sell": "strongly recommend selling"
        }
        
        explanation = (
            f"Based on our analysis, we {rec_map.get(recommendation, 'recommend')} this stock. "
            f"{technical_point} {fundamental_point} {sentiment_point} {risk_point}{conflict_resolution}"
        )
        
        return explanation
    
    def _determine_timeframe(self, agent_results: Dict) -> str:
        """Determine the appropriate timeframe for the recommendation."""
        # Default to medium term
        timeframe = "medium_term"
        
        # Check technical signals for short-term outlook
        technical = agent_results["technical"]
        if technical.get("volatility", 0) > 0.8:
            timeframe = "short_term"
        
        # Check fundamentals for long-term outlook
        fundamental = agent_results["fundamental"]
        if fundamental.get("health_score", 0) > 0.7 and fundamental.get("outlook", "") == "positive":
            timeframe = "long_term"
            
        return timeframe