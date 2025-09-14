# src/user_profiling/risk_profiler.py

from typing import Dict, List
try:
    from .questionnaire import InvestmentQuestionnaire  # Package import
except ImportError:
    from questionnaire import InvestmentQuestionnaire  # Direct import

class RiskProfiler:
    def __init__(self):
        self.questionnaire = InvestmentQuestionnaire()
        self.risk_profile = None
        self.investment_constraints = {
            'min_return': 0,
            'max_risk': 0,
            'investment_horizon': 0,
            'preferred_sectors': [],
            'excluded_sectors': []
        }

    def create_profile(self) -> Dict:
        """Create a complete risk profile for the user"""
        # Run questionnaire
        risk_scores = self.questionnaire.conduct_questionnaire()
        
        # Get additional investment preferences
        self._get_investment_preferences()
        
        # Calculate investment constraints
        self._calculate_investment_constraints(risk_scores)
        
        self.risk_profile = {
            'risk_scores': risk_scores,
            'constraints': self.investment_constraints,
            'summary': self.questionnaire.get_result_summary()
        }
        
        return self.risk_profile

    def _get_investment_preferences(self):
        """Collect additional investment preferences"""
        print("\n=== Additional Investment Preferences ===")
        
        # Get sector preferences
        print("\nSelect preferred sectors (comma-separated numbers, empty for none):")
        sectors = [
            "Technology", "Healthcare", "Financial", "Consumer", 
            "Industrial", "Energy", "Materials", "Utilities", "Real Estate"
        ]
        for i, sector in enumerate(sectors, 1):
            print(f"{i}. {sector}")
        
        sector_input = input("\nEnter preferred sectors: ").strip()
        if sector_input:
            try:
                sector_indices = [int(x) - 1 for x in sector_input.split(',')]
                self.investment_constraints['preferred_sectors'] = [sectors[i] for i in sector_indices if 0 <= i < len(sectors)]
            except ValueError as e:
                print(f"Invalid input: {e}, no sector preferences recorded")
        
        # Get excluded sectors
        excluded_input = input("\nEnter sectors to exclude: ").strip()
        if excluded_input:
            try:
                excluded_indices = [int(x) - 1 for x in excluded_input.split(',')]
                self.investment_constraints['excluded_sectors'] = [sectors[i] for i in excluded_indices if 0 <= i < len(sectors)]
            except ValueError as e:
                print(f"Invalid input: {e}, no sector exclusions recorded")

    def _calculate_investment_constraints(self, risk_scores: Dict):
        """Calculate investment constraints based on risk scores"""
        # Calculate max risk tolerance
        risk_tolerance = risk_scores['risk_tolerance']
        loss_attitude = risk_scores['loss_attitude']
        
        # Risk limits based on profile
        if risk_tolerance < 20:
            self.investment_constraints['max_risk'] = 10
            self.investment_constraints['min_return'] = 5
        elif risk_tolerance < 40:
            self.investment_constraints['max_risk'] = 15
            self.investment_constraints['min_return'] = 7
        elif risk_tolerance < 60:
            self.investment_constraints['max_risk'] = 20
            self.investment_constraints['min_return'] = 9
        elif risk_tolerance < 80:
            self.investment_constraints['max_risk'] = 25
            self.investment_constraints['min_return'] = 12
        else:
            self.investment_constraints['max_risk'] = 30
            self.investment_constraints['min_return'] = 15

        # Validate loss_attitude is within expected range
        loss_attitude = max(0, min(100, loss_attitude))
        
        # Adjust based on loss attitude
        risk_adjustment = (loss_attitude - 50) / 100  # -0.5 to 0.5
        self.investment_constraints['max_risk'] *= (1 + risk_adjustment)
        
        # Set investment horizon based on time horizon score
        time_horizon = risk_scores['time_horizon']
        if time_horizon < 30:
            self.investment_constraints['investment_horizon'] = 1
        elif time_horizon < 50:
            self.investment_constraints['investment_horizon'] = 3
        elif time_horizon < 70:
            self.investment_constraints['investment_horizon'] = 5
        else:
            self.investment_constraints['investment_horizon'] = 10

    def get_profile(self) -> Dict:
        """Get the current risk profile"""
        return self.risk_profile if self.risk_profile else None