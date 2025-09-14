# src/user_profiling/profile_analyzer.py

from typing import Dict, List
from .risk_profiler import RiskProfiler

class ProfileAnalyzer:
    def __init__(self):
        self.risk_profiler = RiskProfiler()
        
    def analyze_profile(self) -> Dict:
        """Analyze user profile and generate investment recommendations"""
        profile = self.risk_profiler.create_profile()
        
        recommendations = {
            'portfolio_type': self._determine_portfolio_type(profile),
            'asset_allocation': self._recommend_asset_allocation(profile),
            'investment_strategy': self._recommend_strategy(profile),
            'rebalancing_frequency': self._recommend_rebalancing(profile),
            'risk_constraints': self._get_risk_constraints(profile)
        }
        
        return recommendations
    
    def _determine_portfolio_type(self, profile: Dict) -> str:
        """Determine appropriate portfolio type"""
        risk_tolerance = profile['risk_scores']['risk_tolerance']
        
        if risk_tolerance < 30:
            return "Conservative Income"
        elif risk_tolerance < 50:
            return "Balanced Income"
        elif risk_tolerance < 70:
            return "Growth"
        else:
            return "Aggressive Growth"
    
    def _recommend_asset_allocation(self, profile: Dict) -> Dict:
        """Recommend asset allocation based on profile"""
        risk_tolerance = profile['risk_scores']['risk_tolerance']
        time_horizon = profile['risk_scores']['time_horizon']
        
        # Base allocations
        if risk_tolerance < 30:
            allocation = {'stocks': 30, 'bonds': 60, 'cash': 10}
        elif risk_tolerance < 50:
            allocation = {'stocks': 50, 'bonds': 40, 'cash': 10}
        elif risk_tolerance < 70:
            allocation = {'stocks': 70, 'bonds': 25, 'cash': 5}
        else:
            allocation = {'stocks': 85, 'bonds': 10, 'cash': 5}
            
        # Adjust based on time horizon
        if time_horizon > 70:  # Long-term
            allocation['stocks'] += 5
            allocation['bonds'] -= 5
            
        return allocation
    
    def _recommend_strategy(self, profile: Dict) -> List[str]:
        """Recommend investment strategies"""
        strategies = []
        risk_tolerance = profile['risk_scores']['risk_tolerance']
        knowledge = profile['risk_scores']['investment_knowledge']
        
        if risk_tolerance < 30:
            strategies.append("Focus on blue-chip stocks and government bonds")
            strategies.append("Emphasize dividend-paying stocks")
        elif risk_tolerance < 50:
            strategies.append("Mix of growth and value stocks")
            strategies.append("Include corporate bonds")
        else:
            strategies.append("Emphasis on growth stocks")
            strategies.append("Consider international markets")
            
        if knowledge > 60:
            strategies.append("Consider options strategies for income")
            
        return strategies
    
    def _recommend_rebalancing(self, profile: Dict) -> str:
        """Recommend rebalancing frequency"""
        risk_tolerance = profile['risk_scores']['risk_tolerance']
        
        if risk_tolerance < 30:
            return "Semi-annually"
        elif risk_tolerance < 60:
            return "Quarterly"
        else:
            return "Monthly"
    
    def _get_risk_constraints(self, profile: Dict) -> Dict:
        """Get risk constraints for portfolio optimization"""
        constraints = profile['constraints']
        return {
            'target_return': constraints['min_return'],
            'max_risk': constraints['max_risk'],
            'investment_horizon': constraints['investment_horizon'],
            'preferred_sectors': constraints['preferred_sectors'],
            'excluded_sectors': constraints['excluded_sectors']
        }