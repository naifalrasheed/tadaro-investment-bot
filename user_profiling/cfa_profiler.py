# src/user_profiling/cfa_profiler.py

from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime
import numpy as np

from models import db, User, UserRiskProfile, UserBiasProfile, InvestmentDecision
from behavioral.behavioral_bias_analyzer import BehavioralBiasAnalyzer, UserBiasProfile as BehavioralUserBiasProfile, InvestmentDecisionFramework, COGNITIVE_BIASES, EMOTIONAL_BIASES
from portfolio.advanced_portfolio_analytics import AdvancedPortfolioAnalytics

class CFAProfiler:
    """
    CFA-based user profiler that integrates behavioral finance and advanced portfolio analytics
    to create comprehensive user investment profiles.
    """
    
    def __init__(self, user_id: int):
        """
        Initialize the CFA profiler.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.bias_analyzer = BehavioralBiasAnalyzer(user_id)
        self.decision_framework = InvestmentDecisionFramework(user_id)
        self.portfolio_analytics = AdvancedPortfolioAnalytics()
        
    def process_questionnaire_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process questionnaire responses and create user profile.
        
        Args:
            responses: Dictionary of questionnaire responses
            
        Returns:
            Dictionary with processed profile data
        """
        # Process traditional risk profiling questions
        risk_scores = self._calculate_risk_scores(responses)
        
        # Process behavioral bias questions
        bias_scores = self._calculate_bias_scores(responses)
        
        # Process sector preferences
        preferred_sectors = self._process_sector_preferences(responses)
        excluded_sectors = self._process_sector_exclusions(responses)
        
        # Calculate investment constraints
        investment_constraints = self._calculate_investment_constraints(risk_scores)
        
        # Determine profile category
        profile_category = self._determine_profile_category(risk_scores)
        
        # Create Investment Policy Statement
        user_profile = {
            "risk_scores": risk_scores,
            "profile_category": profile_category,
            "preferred_sectors": preferred_sectors,
            "excluded_sectors": excluded_sectors
        }
        investment_policy = self.decision_framework.create_investment_policy_statement(user_profile)
        
        # Create asset allocation
        asset_allocation = self._generate_asset_allocation(risk_scores, profile_category)
        
        # Combine all data
        profile_data = {
            "risk_scores": risk_scores,
            "bias_scores": bias_scores,
            "preferred_sectors": preferred_sectors,
            "excluded_sectors": excluded_sectors,
            "investment_constraints": investment_constraints,
            "profile_category": profile_category,
            "investment_policy": investment_policy,
            "asset_allocation": asset_allocation,
            "top_biases": self._get_top_biases(bias_scores)
        }
        
        # Save to database
        self._save_profile_to_db(profile_data)
        
        return profile_data
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the user's saved profile.
        
        Returns:
            Dictionary with profile data
        """
        # Get profile from database
        risk_profile = UserRiskProfile.query.filter_by(user_id=self.user_id).first()
        if not risk_profile:
            return None
            
        # Get bias profile
        bias_profiles = UserBiasProfile.query.filter_by(user_id=self.user_id).all()
        bias_scores = {profile.bias_type: profile.bias_score for profile in bias_profiles}
            
        # Build profile data
        profile_data = {
            "risk_scores": {
                "time_horizon": risk_profile.time_horizon,
                "risk_tolerance": risk_profile.risk_tolerance,
                "investment_knowledge": risk_profile.investment_knowledge,
                "income_stability": risk_profile.income_stability,
                "loss_attitude": risk_profile.loss_attitude
            },
            "bias_scores": bias_scores,
            "preferred_sectors": risk_profile.preferred_sectors,
            "excluded_sectors": risk_profile.excluded_sectors,
            "investment_constraints": {
                "max_risk": risk_profile.max_risk,
                "min_return": risk_profile.min_return,
                "investment_horizon": risk_profile.investment_horizon
            },
            "profile_category": risk_profile.profile_category,
            "investment_policy": risk_profile.investment_policy,
            "asset_allocation": self._generate_asset_allocation_from_profile(risk_profile),
            "top_biases": self._get_top_biases(bias_scores)
        }
        
        return profile_data
    
    def update_user_profile(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the user's profile with new data.
        
        Args:
            new_data: Dictionary with updated profile data
            
        Returns:
            Dictionary with updated profile data
        """
        # Get existing profile
        risk_profile = UserRiskProfile.query.filter_by(user_id=self.user_id).first()
        if not risk_profile:
            return None
            
        # Update risk profile
        if "risk_scores" in new_data:
            risk_scores = new_data["risk_scores"]
            risk_profile.time_horizon = risk_scores.get("time_horizon", risk_profile.time_horizon)
            risk_profile.risk_tolerance = risk_scores.get("risk_tolerance", risk_profile.risk_tolerance)
            risk_profile.investment_knowledge = risk_scores.get("investment_knowledge", risk_profile.investment_knowledge)
            risk_profile.income_stability = risk_scores.get("income_stability", risk_profile.income_stability)
            risk_profile.loss_attitude = risk_scores.get("loss_attitude", risk_profile.loss_attitude)
            
        # Update investment constraints
        if "investment_constraints" in new_data:
            constraints = new_data["investment_constraints"]
            risk_profile.max_risk = constraints.get("max_risk", risk_profile.max_risk)
            risk_profile.min_return = constraints.get("min_return", risk_profile.min_return)
            risk_profile.investment_horizon = constraints.get("investment_horizon", risk_profile.investment_horizon)
            
        # Update sector preferences
        if "preferred_sectors" in new_data:
            risk_profile.preferred_sectors = new_data["preferred_sectors"]
            
        if "excluded_sectors" in new_data:
            risk_profile.excluded_sectors = new_data["excluded_sectors"]
            
        # Update profile category
        if "profile_category" in new_data:
            risk_profile.profile_category = new_data["profile_category"]
            
        # Update investment policy
        if "investment_policy" in new_data:
            risk_profile.investment_policy = new_data["investment_policy"]
            
        # Update bias scores
        if "bias_scores" in new_data:
            for bias_type, score in new_data["bias_scores"].items():
                bias_profile = UserBiasProfile.query.filter_by(user_id=self.user_id, bias_type=bias_type).first()
                if bias_profile:
                    bias_profile.bias_score = score
                    bias_profile.last_updated = datetime.utcnow()
                else:
                    new_bias = UserBiasProfile(
                        user_id=self.user_id,
                        bias_type=bias_type,
                        bias_score=score,
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(new_bias)
        
        # Save changes
        risk_profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Return updated profile
        return self.get_user_profile()
    
    def get_behavioral_insights(self) -> Dict[str, Any]:
        """
        Get behavioral finance insights for the user.
        
        Returns:
            Dictionary with behavioral insights
        """
        # Get bias profile
        user_bias_profile = self.bias_analyzer.get_user_bias_profile()
        
        # Get debiasing strategies
        debiasing_strategies = self.bias_analyzer.generate_debiasing_strategies()
        
        return {
            "bias_profile": user_bias_profile,
            "debiasing_strategies": debiasing_strategies
        }
    
    def record_investment_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record an investment decision with CFA framework.
        
        Args:
            decision_data: Dictionary with decision data
            
        Returns:
            Dictionary with recorded decision and analysis
        """
        # Process the decision with the framework
        decision_record = self.decision_framework.document_investment_decision(
            symbol=decision_data.get("symbol", ""),
            decision_type=decision_data.get("decision_type", ""),
            rationale=decision_data.get("rationale", ""),
            amount=decision_data.get("amount"),
            price=decision_data.get("price")
        )
        
        # Return the decision record
        return decision_record
    
    # Private helper methods
    
    def _calculate_risk_scores(self, responses: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk scores from questionnaire responses"""
        risk_scores = {
            "time_horizon": 0,
            "risk_tolerance": 0,
            "investment_knowledge": 0,
            "income_stability": 0,
            "loss_attitude": 0
        }
        
        # Time horizon questions
        if "th_1" in responses and "th_2" in responses:
            time_horizon_score = (int(responses["th_1"]) + int(responses["th_2"])) / 2
            risk_scores["time_horizon"] = (time_horizon_score / 5) * 100
            
        # Risk tolerance questions
        if "rt_1" in responses and "rt_2" in responses:
            risk_tolerance_score = (int(responses["rt_1"]) + int(responses["rt_2"])) / 2
            risk_scores["risk_tolerance"] = (risk_tolerance_score / 5) * 100
            
        # Investment knowledge questions
        if "ik_1" in responses:
            investment_knowledge_score = int(responses["ik_1"])
            risk_scores["investment_knowledge"] = (investment_knowledge_score / 5) * 100
            
        # Income stability questions
        if "is_1" in responses:
            income_stability_score = int(responses["is_1"])
            risk_scores["income_stability"] = (income_stability_score / 5) * 100
            
        # Loss attitude questions
        if "la_1" in responses:
            loss_attitude_score = int(responses["la_1"])
            risk_scores["loss_attitude"] = (loss_attitude_score / 5) * 100
            
        return risk_scores
    
    def _calculate_bias_scores(self, responses: Dict[str, Any]) -> Dict[str, float]:
        """Calculate behavioral bias scores from questionnaire responses"""
        bias_scores = {
            "loss_aversion": 0,
            "herding": 0,
            "recency": 0,
            "overconfidence": 0,
            "availability": 0,
            "anchoring": 0,
            "confirmation": 0,
            "status_quo": 0
        }
        
        # Map question responses to biases
        if "ba_1" in responses:  # Loss aversion question
            loss_aversion_score = 6 - int(responses["ba_1"])  # Reverse score (5=low bias, 1=high bias)
            bias_scores["loss_aversion"] = (loss_aversion_score / 5) * 10  # Scale to 0-10
            
        if "ba_2" in responses:  # Herding question
            herding_score = 6 - int(responses["ba_2"])  # Reverse score (5=low bias, 1=high bias)
            bias_scores["herding"] = (herding_score / 5) * 10  # Scale to 0-10
            
        if "ba_3" in responses:  # Recency bias question
            recency_score = 6 - int(responses["ba_3"])  # Reverse score (5=low bias, 1=high bias)
            bias_scores["recency"] = (recency_score / 5) * 10  # Scale to 0-10
            
        # Set defaults for other biases that don't have direct questions
        bias_scores["overconfidence"] = 5.0  # Default midpoint
        bias_scores["availability"] = 5.0
        bias_scores["anchoring"] = 5.0
        bias_scores["confirmation"] = 5.0
        bias_scores["status_quo"] = 5.0
        
        # Adjust based on related responses
        # If user has high risk tolerance, they might have higher overconfidence
        if "rt_1" in responses and int(responses["rt_1"]) > 3:
            bias_scores["overconfidence"] += 1.0
            
        # If user has high recency bias, they likely have high availability bias too
        if bias_scores["recency"] > 7:
            bias_scores["availability"] = min(10, bias_scores["recency"] + 1)
            
        return bias_scores
    
    def _process_sector_preferences(self, responses: Dict[str, Any]) -> List[str]:
        """Process sector preferences from responses"""
        if "preferred_sectors" in responses:
            if isinstance(responses["preferred_sectors"], list):
                return responses["preferred_sectors"]
            elif isinstance(responses["preferred_sectors"], str):
                return [responses["preferred_sectors"]]
        return []
    
    def _process_sector_exclusions(self, responses: Dict[str, Any]) -> List[str]:
        """Process sector exclusions from responses"""
        if "excluded_sectors" in responses:
            if isinstance(responses["excluded_sectors"], list):
                return responses["excluded_sectors"]
            elif isinstance(responses["excluded_sectors"], str):
                return [responses["excluded_sectors"]]
        return []
    
    def _calculate_investment_constraints(self, risk_scores: Dict[str, float]) -> Dict[str, Any]:
        """Calculate investment constraints based on risk scores"""
        investment_constraints = {
            "max_risk": 0,
            "min_return": 0,
            "investment_horizon": 0
        }
        
        # Calculate max risk tolerance
        risk_tolerance = risk_scores.get("risk_tolerance", 50)
        loss_attitude = risk_scores.get("loss_attitude", 50)
        
        # Risk limits based on profile
        if risk_tolerance < 20:
            investment_constraints["max_risk"] = 10
            investment_constraints["min_return"] = 5
        elif risk_tolerance < 40:
            investment_constraints["max_risk"] = 15
            investment_constraints["min_return"] = 7
        elif risk_tolerance < 60:
            investment_constraints["max_risk"] = 20
            investment_constraints["min_return"] = 9
        elif risk_tolerance < 80:
            investment_constraints["max_risk"] = 25
            investment_constraints["min_return"] = 12
        else:
            investment_constraints["max_risk"] = 30
            investment_constraints["min_return"] = 15
        
        # Adjust based on loss attitude
        risk_adjustment = (loss_attitude - 50) / 100  # -0.5 to 0.5
        investment_constraints["max_risk"] *= (1 + risk_adjustment)
        
        # Set investment horizon based on time horizon score
        time_horizon = risk_scores.get("time_horizon", 50)
        if time_horizon < 30:
            investment_constraints["investment_horizon"] = 1
        elif time_horizon < 50:
            investment_constraints["investment_horizon"] = 3
        elif time_horizon < 70:
            investment_constraints["investment_horizon"] = 5
        else:
            investment_constraints["investment_horizon"] = 10
            
        return investment_constraints
    
    def _determine_profile_category(self, risk_scores: Dict[str, float]) -> str:
        """Determine profile category based on risk scores"""
        risk_tolerance = risk_scores.get("risk_tolerance", 50)
        time_horizon = risk_scores.get("time_horizon", 50)
        loss_attitude = risk_scores.get("loss_attitude", 50)
        
        # Calculate weighted risk score
        weighted_score = (risk_tolerance * 0.5) + (time_horizon * 0.3) + (loss_attitude * 0.2)
        
        # Determine category
        if weighted_score < 30:
            return "Conservative"
        elif weighted_score < 50:
            return "Moderately Conservative"
        elif weighted_score < 70:
            return "Moderate"
        elif weighted_score < 85:
            return "Moderately Aggressive"
        else:
            return "Aggressive"
    
    def _generate_asset_allocation(self, risk_scores: Dict[str, float], profile_category: str) -> Dict[str, float]:
        """Generate asset allocation based on risk profile"""
        risk_tolerance = risk_scores.get("risk_tolerance", 50)
        time_horizon = risk_scores.get("time_horizon", 50)
        
        # Base allocations by profile category
        allocations = {
            "Conservative": {
                "equities": 20,
                "fixed_income": 60,
                "alternatives": 5,
                "cash": 15
            },
            "Moderately Conservative": {
                "equities": 40,
                "fixed_income": 45,
                "alternatives": 10,
                "cash": 5
            },
            "Moderate": {
                "equities": 55,
                "fixed_income": 35,
                "alternatives": 7,
                "cash": 3
            },
            "Moderately Aggressive": {
                "equities": 70,
                "fixed_income": 20,
                "alternatives": 8,
                "cash": 2
            },
            "Aggressive": {
                "equities": 85,
                "fixed_income": 5,
                "alternatives": 8,
                "cash": 2
            }
        }
        
        # Get base allocation
        base_allocation = allocations.get(profile_category, allocations["Moderate"])
        
        # Adjust based on time horizon
        if time_horizon > 70:  # Long time horizon
            # Increase equities, decrease cash
            base_allocation["equities"] = min(95, base_allocation["equities"] + 5)
            base_allocation["cash"] = max(1, base_allocation["cash"] - 3)
        elif time_horizon < 30:  # Short time horizon
            # Decrease equities, increase cash
            base_allocation["equities"] = max(10, base_allocation["equities"] - 10)
            base_allocation["cash"] = min(25, base_allocation["cash"] + 10)
            
        return base_allocation
    
    def _generate_asset_allocation_from_profile(self, risk_profile: UserRiskProfile) -> Dict[str, float]:
        """Generate asset allocation from saved risk profile"""
        # Use saved investment policy if available
        if risk_profile.investment_policy and "primary_allocation" in risk_profile.investment_policy:
            return risk_profile.investment_policy["primary_allocation"]
            
        # Otherwise generate based on profile category
        risk_scores = {
            "risk_tolerance": risk_profile.risk_tolerance,
            "time_horizon": risk_profile.time_horizon
        }
        return self._generate_asset_allocation(risk_scores, risk_profile.profile_category)
    
    def _get_top_biases(self, bias_scores: Dict[str, float], limit: int = 3) -> List[Dict[str, Any]]:
        """Get top biases with details"""
        sorted_biases = sorted(bias_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        top_biases = []
        
        for bias_type, score in sorted_biases:
            # Look up bias info
            if bias_type in COGNITIVE_BIASES:
                bias_info = COGNITIVE_BIASES[bias_type]
            elif bias_type in EMOTIONAL_BIASES:
                bias_info = EMOTIONAL_BIASES[bias_type]
            else:
                continue
                
            # Determine alert level
            if score > 7:
                alert_level = "danger"
            elif score > 5:
                alert_level = "warning"
            else:
                alert_level = "info"
                
            top_biases.append({
                "type": bias_type,
                "name": bias_info["name"],
                "score": score,
                "description": bias_info["description"],
                "strategy": bias_info["strategies"][0],
                "alert_level": alert_level
            })
            
        return top_biases
    
    def _save_profile_to_db(self, profile_data: Dict[str, Any]) -> None:
        """Save profile data to database"""
        try:
            # Get user
            user = User.query.get(self.user_id)
            if not user:
                self.logger.error(f"User {self.user_id} not found")
                return
                
            # Check if profile already exists
            existing_profile = UserRiskProfile.query.filter_by(user_id=self.user_id).first()
            
            if existing_profile:
                # Update existing profile
                existing_profile.time_horizon = profile_data["risk_scores"]["time_horizon"]
                existing_profile.risk_tolerance = profile_data["risk_scores"]["risk_tolerance"]
                existing_profile.investment_knowledge = profile_data["risk_scores"]["investment_knowledge"]
                existing_profile.income_stability = profile_data["risk_scores"]["income_stability"]
                existing_profile.loss_attitude = profile_data["risk_scores"]["loss_attitude"]
                
                existing_profile.max_risk = profile_data["investment_constraints"]["max_risk"]
                existing_profile.min_return = profile_data["investment_constraints"]["min_return"]
                existing_profile.investment_horizon = profile_data["investment_constraints"]["investment_horizon"]
                
                existing_profile.preferred_sectors = profile_data["preferred_sectors"]
                existing_profile.excluded_sectors = profile_data["excluded_sectors"]
                
                existing_profile.profile_category = profile_data["profile_category"]
                existing_profile.investment_policy = profile_data["investment_policy"]
                
                existing_profile.updated_at = datetime.utcnow()
            else:
                # Create new profile
                new_profile = UserRiskProfile(
                    user_id=self.user_id,
                    time_horizon=profile_data["risk_scores"]["time_horizon"],
                    risk_tolerance=profile_data["risk_scores"]["risk_tolerance"],
                    investment_knowledge=profile_data["risk_scores"]["investment_knowledge"],
                    income_stability=profile_data["risk_scores"]["income_stability"],
                    loss_attitude=profile_data["risk_scores"]["loss_attitude"],
                    
                    max_risk=profile_data["investment_constraints"]["max_risk"],
                    min_return=profile_data["investment_constraints"]["min_return"],
                    investment_horizon=profile_data["investment_constraints"]["investment_horizon"],
                    
                    preferred_sectors=profile_data["preferred_sectors"],
                    excluded_sectors=profile_data["excluded_sectors"],
                    
                    profile_category=profile_data["profile_category"],
                    investment_policy=profile_data["investment_policy"]
                )
                db.session.add(new_profile)
                
            # Save bias scores
            for bias_type, score in profile_data["bias_scores"].items():
                existing_bias = UserBiasProfile.query.filter_by(user_id=self.user_id, bias_type=bias_type).first()
                
                if existing_bias:
                    existing_bias.bias_score = score
                    existing_bias.last_updated = datetime.utcnow()
                else:
                    new_bias = UserBiasProfile(
                        user_id=self.user_id,
                        bias_type=bias_type,
                        bias_score=score,
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(new_bias)
                    
            # Mark user as having completed profiling
            user.has_completed_profiling = True
            
            # Commit changes
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error saving profile to database: {str(e)}")
            db.session.rollback()
            raise