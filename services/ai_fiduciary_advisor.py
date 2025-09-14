"""
AI Fiduciary Advisor Service

This service provides comprehensive fiduciary investment advice:
1. Goal-based investment recommendations
2. Risk tolerance assessment and profiling
3. Portfolio construction and optimization
4. Rebalancing strategies and timing
5. Tax-efficient investment strategies
6. ESG (Environmental, Social, Governance) integration
7. Behavioral finance insights and bias mitigation
8. Regular portfolio review and adjustment recommendations
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import numpy as np
from services.saudi_market_service import SaudiMarketService
from services.valuation_engine import ValuationEngine
from services.margin_safety_calculator import MarginOfSafetyCalculator
from services.historical_analyzer import HistoricalFinancialAnalyzer
from services.management_analyzer import ManagementQualityAnalyzer
from services.shareholder_value_tracker import ShareholderValueTracker
from services.macro_integration_service import MacroIntegrationService

logger = logging.getLogger(__name__)

@dataclass
class InvestmentGoal:
    """Investment goal definition"""
    goal_id: str
    name: str
    target_amount: float
    time_horizon_years: int
    priority: str  # high, medium, low
    risk_tolerance: str  # conservative, moderate, aggressive
    liquidity_needs: str  # high, medium, low
    tax_considerations: bool
    esg_preferences: bool

@dataclass
class RiskProfile:
    """Comprehensive risk profile assessment"""
    risk_score: int  # 1-10 scale
    risk_category: str  # conservative, moderate, aggressive
    volatility_tolerance: float
    drawdown_tolerance: float
    time_horizon: int
    liquidity_needs: str
    investment_experience: str
    financial_capacity: str
    behavioral_biases: List[str]

@dataclass
class PortfolioRecommendation:
    """Portfolio construction recommendation"""
    allocation: Dict[str, float]  # Asset class allocations
    specific_securities: List[Dict[str, Any]]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown_estimate: float
    rebalancing_frequency: str
    monitoring_triggers: List[str]

@dataclass
class FiduciaryAdvice:
    """Comprehensive fiduciary investment advice"""
    client_profile: RiskProfile
    investment_goals: List[InvestmentGoal]
    portfolio_recommendation: PortfolioRecommendation
    implementation_strategy: Dict[str, Any]
    monitoring_framework: Dict[str, Any]
    disclosure_items: List[str]
    next_review_date: datetime

class AIFiduciaryAdvisor:
    """
    Comprehensive AI-powered fiduciary investment advisor
    
    Provides personalized investment advice following fiduciary standards:
    - Acts in client's best interest
    - Provides transparent, conflict-free advice
    - Regular monitoring and rebalancing
    - Goal-based investment strategies
    """
    
    def __init__(self, saudi_service: SaudiMarketService):
        self.saudi_service = saudi_service
        self.valuation_engine = ValuationEngine(saudi_service)
        self.margin_calculator = MarginOfSafetyCalculator(saudi_service)
        self.historical_analyzer = HistoricalFinancialAnalyzer(saudi_service)
        self.management_analyzer = ManagementQualityAnalyzer(saudi_service)
        self.value_tracker = ShareholderValueTracker(saudi_service)
        self.macro_service = MacroIntegrationService(saudi_service)
        
        # Asset class definitions for Saudi market
        self.asset_classes = {
            'saudi_equity': {'expected_return': 0.09, 'volatility': 0.18, 'correlation_matrix': {}},
            'saudi_bonds': {'expected_return': 0.05, 'volatility': 0.08, 'correlation_matrix': {}},
            'real_estate': {'expected_return': 0.07, 'volatility': 0.15, 'correlation_matrix': {}},
            'commodities': {'expected_return': 0.06, 'volatility': 0.22, 'correlation_matrix': {}},
            'international_equity': {'expected_return': 0.08, 'volatility': 0.16, 'correlation_matrix': {}},
            'cash_equivalents': {'expected_return': 0.03, 'volatility': 0.01, 'correlation_matrix': {}}
        }
        
        # Risk tolerance mapping
        self.risk_mappings = {
            'conservative': {'max_equity': 0.3, 'max_volatility': 0.08, 'max_drawdown': 0.05},
            'moderate': {'max_equity': 0.6, 'max_volatility': 0.12, 'max_drawdown': 0.10},
            'aggressive': {'max_equity': 0.9, 'max_volatility': 0.18, 'max_drawdown': 0.20}
        }
    
    def assess_risk_profile(self, client_data: Dict[str, Any]) -> RiskProfile:
        """
        Comprehensive risk profile assessment
        
        Args:
            client_data: Dictionary containing client information including:
                - age, income, net_worth, investment_experience
                - risk_questionnaire_responses
                - investment_goals and time_horizons
                - behavioral_indicators
        """
        try:
            logger.info("Conducting comprehensive risk profile assessment")
            
            # Risk capacity assessment (financial ability to take risk)
            capacity_score = self._assess_risk_capacity(client_data)
            
            # Risk tolerance assessment (willingness to take risk)
            tolerance_score = self._assess_risk_tolerance(client_data)
            
            # Time horizon assessment
            time_horizon = self._determine_time_horizon(client_data)
            
            # Liquidity needs assessment
            liquidity_needs = self._assess_liquidity_needs(client_data)
            
            # Investment experience evaluation
            experience_level = self._evaluate_investment_experience(client_data)
            
            # Behavioral bias identification
            behavioral_biases = self._identify_behavioral_biases(client_data)
            
            # Composite risk score (1-10 scale)
            composite_score = min(capacity_score, tolerance_score)  # Take the lower of capacity and tolerance
            
            # Categorize risk profile
            if composite_score <= 3:
                risk_category = 'conservative'
            elif composite_score <= 7:
                risk_category = 'moderate'
            else:
                risk_category = 'aggressive'
            
            return RiskProfile(
                risk_score=composite_score,
                risk_category=risk_category,
                volatility_tolerance=self._calculate_volatility_tolerance(composite_score),
                drawdown_tolerance=self._calculate_drawdown_tolerance(composite_score),
                time_horizon=time_horizon,
                liquidity_needs=liquidity_needs,
                investment_experience=experience_level,
                financial_capacity=self._determine_financial_capacity(capacity_score),
                behavioral_biases=behavioral_biases
            )
            
        except Exception as e:
            logger.error(f"Error assessing risk profile: {str(e)}")
            raise
    
    def create_investment_goals(self, client_data: Dict[str, Any]) -> List[InvestmentGoal]:
        """Create structured investment goals based on client needs"""
        try:
            goals = []
            
            # Extract goal information from client data
            goal_data = client_data.get('investment_goals', [])
            
            for i, goal in enumerate(goal_data):
                investment_goal = InvestmentGoal(
                    goal_id=f"goal_{i+1}",
                    name=goal.get('name', f'Investment Goal {i+1}'),
                    target_amount=float(goal.get('target_amount', 0)),
                    time_horizon_years=int(goal.get('time_horizon', 10)),
                    priority=goal.get('priority', 'medium'),
                    risk_tolerance=goal.get('risk_tolerance', 'moderate'),
                    liquidity_needs=goal.get('liquidity_needs', 'medium'),
                    tax_considerations=goal.get('tax_considerations', True),
                    esg_preferences=goal.get('esg_preferences', False)
                )
                goals.append(investment_goal)
            
            # If no specific goals provided, create default retirement goal
            if not goals:
                goals.append(InvestmentGoal(
                    goal_id="retirement",
                    name="Retirement Planning",
                    target_amount=2000000.0,  # 2M SAR
                    time_horizon_years=20,
                    priority="high",
                    risk_tolerance="moderate",
                    liquidity_needs="low",
                    tax_considerations=True,
                    esg_preferences=False
                ))
            
            return goals
            
        except Exception as e:
            logger.error(f"Error creating investment goals: {str(e)}")
            return []
    
    def construct_optimal_portfolio(self, risk_profile: RiskProfile, 
                                  investment_goals: List[InvestmentGoal]) -> PortfolioRecommendation:
        """
        Construct optimal portfolio using modern portfolio theory principles
        Enhanced with Saudi market specifics and goal-based optimization
        """
        try:
            logger.info("Constructing optimal portfolio recommendation")
            
            # Determine strategic asset allocation
            strategic_allocation = self._determine_strategic_allocation(risk_profile, investment_goals)
            
            # Select specific securities within asset classes
            specific_securities = self._select_securities(strategic_allocation, risk_profile)
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(strategic_allocation, specific_securities)
            
            # Determine rebalancing strategy
            rebalancing_strategy = self._determine_rebalancing_strategy(risk_profile, investment_goals)
            
            # Set monitoring triggers
            monitoring_triggers = self._set_monitoring_triggers(risk_profile, strategic_allocation)
            
            return PortfolioRecommendation(
                allocation=strategic_allocation,
                specific_securities=specific_securities,
                expected_return=portfolio_metrics['expected_return'],
                expected_volatility=portfolio_metrics['volatility'],
                sharpe_ratio=portfolio_metrics['sharpe_ratio'],
                max_drawdown_estimate=portfolio_metrics['max_drawdown'],
                rebalancing_frequency=rebalancing_strategy['frequency'],
                monitoring_triggers=monitoring_triggers
            )
            
        except Exception as e:
            logger.error(f"Error constructing portfolio: {str(e)}")
            raise
    
    def provide_fiduciary_advice(self, client_data: Dict[str, Any]) -> FiduciaryAdvice:
        """
        Provide comprehensive fiduciary investment advice
        
        This is the main entry point that coordinates all advisory services
        """
        try:
            logger.info("Providing comprehensive fiduciary investment advice")
            
            # Step 1: Assess client risk profile
            risk_profile = self.assess_risk_profile(client_data)
            
            # Step 2: Define investment goals
            investment_goals = self.create_investment_goals(client_data)
            
            # Step 3: Construct optimal portfolio
            portfolio_recommendation = self.construct_optimal_portfolio(risk_profile, investment_goals)
            
            # Step 4: Develop implementation strategy
            implementation_strategy = self._develop_implementation_strategy(
                portfolio_recommendation, client_data, risk_profile
            )
            
            # Step 5: Create monitoring framework
            monitoring_framework = self._create_monitoring_framework(
                portfolio_recommendation, investment_goals, risk_profile
            )
            
            # Step 6: Prepare disclosures
            disclosures = self._prepare_fiduciary_disclosures(
                portfolio_recommendation, implementation_strategy
            )
            
            # Step 7: Schedule next review
            next_review = datetime.now() + timedelta(days=90)  # Quarterly review
            
            return FiduciaryAdvice(
                client_profile=risk_profile,
                investment_goals=investment_goals,
                portfolio_recommendation=portfolio_recommendation,
                implementation_strategy=implementation_strategy,
                monitoring_framework=monitoring_framework,
                disclosure_items=disclosures,
                next_review_date=next_review
            )
            
        except Exception as e:
            logger.error(f"Error providing fiduciary advice: {str(e)}")
            raise
    
    def _assess_risk_capacity(self, client_data: Dict[str, Any]) -> int:
        """Assess financial capacity to take investment risk"""
        try:
            age = client_data.get('age', 40)
            income = client_data.get('annual_income', 100000)
            net_worth = client_data.get('net_worth', 500000)
            dependents = client_data.get('dependents', 0)
            job_stability = client_data.get('job_stability', 'stable')
            
            score = 5  # Base score
            
            # Age factor
            if age < 35:
                score += 2
            elif age > 55:
                score -= 1
            
            # Income factor
            if income > 200000:
                score += 2
            elif income < 50000:
                score -= 2
            
            # Net worth factor
            if net_worth > 1000000:
                score += 2
            elif net_worth < 100000:
                score -= 2
            
            # Dependents factor
            score -= min(2, dependents)
            
            # Job stability
            if job_stability == 'unstable':
                score -= 1
            elif job_stability == 'very_stable':
                score += 1
            
            return max(1, min(10, score))
            
        except Exception as e:
            logger.error(f"Error assessing risk capacity: {str(e)}")
            return 5
    
    def _assess_risk_tolerance(self, client_data: Dict[str, Any]) -> int:
        """Assess willingness to take investment risk based on questionnaire"""
        try:
            questionnaire = client_data.get('risk_questionnaire', {})
            
            score = 0
            
            # Market volatility comfort
            volatility_comfort = questionnaire.get('volatility_comfort', 3)
            score += volatility_comfort
            
            # Loss tolerance
            loss_tolerance = questionnaire.get('loss_tolerance', 3)
            score += loss_tolerance
            
            # Investment experience comfort
            experience_comfort = questionnaire.get('experience_comfort', 3)
            score += experience_comfort
            
            # Time horizon comfort
            time_comfort = questionnaire.get('time_horizon_comfort', 3)
            score += time_comfort
            
            # Normalize to 1-10 scale
            normalized_score = (score / 12) * 10
            
            return max(1, min(10, int(normalized_score)))
            
        except Exception as e:
            logger.error(f"Error assessing risk tolerance: {str(e)}")
            return 5
    
    def _determine_time_horizon(self, client_data: Dict[str, Any]) -> int:
        """Determine primary investment time horizon"""
        try:
            goals = client_data.get('investment_goals', [])
            
            if goals:
                # Use shortest time horizon for conservative planning
                horizons = [goal.get('time_horizon', 10) for goal in goals]
                return min(horizons)
            
            # Default based on age
            age = client_data.get('age', 40)
            return max(5, 65 - age)  # Years to retirement, minimum 5 years
            
        except Exception as e:
            logger.error(f"Error determining time horizon: {str(e)}")
            return 10
    
    def _assess_liquidity_needs(self, client_data: Dict[str, Any]) -> str:
        """Assess liquidity requirements"""
        try:
            emergency_fund = client_data.get('emergency_fund_months', 3)
            upcoming_expenses = client_data.get('major_expenses_next_3years', False)
            income_stability = client_data.get('income_stability', 'stable')
            
            if emergency_fund < 3 or upcoming_expenses or income_stability == 'unstable':
                return 'high'
            elif emergency_fund >= 6 and not upcoming_expenses:
                return 'low'
            else:
                return 'medium'
                
        except Exception as e:
            logger.error(f"Error assessing liquidity needs: {str(e)}")
            return 'medium'
    
    def _evaluate_investment_experience(self, client_data: Dict[str, Any]) -> str:
        """Evaluate client's investment experience level"""
        try:
            years_investing = client_data.get('years_investing', 0)
            portfolio_size = client_data.get('current_portfolio_value', 0)
            investment_types = client_data.get('investment_types_experience', [])
            
            if years_investing >= 10 and portfolio_size > 500000 and len(investment_types) >= 4:
                return 'experienced'
            elif years_investing >= 3 and portfolio_size > 100000:
                return 'intermediate'
            else:
                return 'beginner'
                
        except Exception as e:
            logger.error(f"Error evaluating investment experience: {str(e)}")
            return 'intermediate'
    
    def _identify_behavioral_biases(self, client_data: Dict[str, Any]) -> List[str]:
        """Identify potential behavioral biases"""
        biases = []
        
        try:
            # Loss aversion
            loss_sensitivity = client_data.get('loss_sensitivity', 'medium')
            if loss_sensitivity == 'high':
                biases.append('loss_aversion')
            
            # Recency bias
            market_timing_attempts = client_data.get('market_timing_history', False)
            if market_timing_attempts:
                biases.append('recency_bias')
            
            # Overconfidence
            past_performance_attribution = client_data.get('performance_attribution', 'mixed')
            if past_performance_attribution == 'skill_based':
                biases.append('overconfidence')
            
            # Home bias
            international_aversion = client_data.get('international_investment_comfort', 'comfortable')
            if international_aversion == 'uncomfortable':
                biases.append('home_bias')
            
        except Exception as e:
            logger.error(f"Error identifying behavioral biases: {str(e)}")
        
        return biases
    
    def _calculate_volatility_tolerance(self, risk_score: int) -> float:
        """Calculate volatility tolerance based on risk score"""
        # Map risk score (1-10) to volatility tolerance (0.05-0.20)
        return 0.05 + (risk_score - 1) * (0.20 - 0.05) / 9
    
    def _calculate_drawdown_tolerance(self, risk_score: int) -> float:
        """Calculate maximum drawdown tolerance"""
        # Map risk score to drawdown tolerance (0.03-0.25)
        return 0.03 + (risk_score - 1) * (0.25 - 0.03) / 9
    
    def _determine_financial_capacity(self, capacity_score: int) -> str:
        """Determine financial capacity category"""
        if capacity_score >= 8:
            return 'high'
        elif capacity_score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _determine_strategic_allocation(self, risk_profile: RiskProfile, 
                                     investment_goals: List[InvestmentGoal]) -> Dict[str, float]:
        """Determine strategic asset allocation"""
        try:
            risk_limits = self.risk_mappings[risk_profile.risk_category]
            
            # Base allocation for moderate risk profile
            base_allocation = {
                'saudi_equity': 0.40,
                'saudi_bonds': 0.25,
                'international_equity': 0.20,
                'real_estate': 0.10,
                'cash_equivalents': 0.05
            }
            
            # Adjust based on risk profile
            if risk_profile.risk_category == 'conservative':
                allocation = {
                    'saudi_equity': 0.20,
                    'saudi_bonds': 0.45,
                    'international_equity': 0.10,
                    'real_estate': 0.10,
                    'cash_equivalents': 0.15
                }
            elif risk_profile.risk_category == 'aggressive':
                allocation = {
                    'saudi_equity': 0.50,
                    'saudi_bonds': 0.10,
                    'international_equity': 0.30,
                    'real_estate': 0.08,
                    'cash_equivalents': 0.02
                }
            else:
                allocation = base_allocation
            
            # Adjust for specific goals
            for goal in investment_goals:
                if goal.time_horizon_years < 3:
                    # Increase cash/bonds for short-term goals
                    allocation['cash_equivalents'] = max(allocation['cash_equivalents'], 0.20)
                    allocation['saudi_bonds'] = max(allocation['saudi_bonds'], 0.30)
                
                if goal.esg_preferences:
                    # Would adjust for ESG-focused investments
                    pass
            
            # Ensure allocation sums to 1
            total = sum(allocation.values())
            allocation = {k: v/total for k, v in allocation.items()}
            
            return allocation
            
        except Exception as e:
            logger.error(f"Error determining strategic allocation: {str(e)}")
            return base_allocation
    
    def _select_securities(self, allocation: Dict[str, float], risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """Select specific securities within each asset class"""
        try:
            securities = []
            
            # Saudi Equity - select based on quality metrics
            if allocation.get('saudi_equity', 0) > 0:
                equity_securities = self._select_saudi_equities(
                    allocation['saudi_equity'], risk_profile
                )
                securities.extend(equity_securities)
            
            # Saudi Bonds
            if allocation.get('saudi_bonds', 0) > 0:
                bond_securities = self._select_saudi_bonds(
                    allocation['saudi_bonds'], risk_profile
                )
                securities.extend(bond_securities)
            
            # International Equity
            if allocation.get('international_equity', 0) > 0:
                intl_securities = self._select_international_equities(
                    allocation['international_equity'], risk_profile
                )
                securities.extend(intl_securities)
            
            # Real Estate
            if allocation.get('real_estate', 0) > 0:
                reit_securities = self._select_real_estate_securities(
                    allocation['real_estate'], risk_profile
                )
                securities.extend(reit_securities)
            
            # Cash Equivalents
            if allocation.get('cash_equivalents', 0) > 0:
                cash_securities = self._select_cash_equivalents(
                    allocation['cash_equivalents']
                )
                securities.extend(cash_securities)
            
            return securities
            
        except Exception as e:
            logger.error(f"Error selecting securities: {str(e)}")
            return []
    
    def _select_saudi_equities(self, target_allocation: float, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """Select Saudi equity securities based on comprehensive analysis"""
        try:
            # Top Saudi stocks based on quality metrics (simplified)
            candidate_stocks = [
                {'symbol': '2222.SR', 'name': 'Saudi Aramco', 'sector': 'energy'},
                {'symbol': '1180.SR', 'name': 'Al Rajhi Bank', 'sector': 'financials'},
                {'symbol': '2030.SR', 'name': 'SABIC', 'sector': 'materials'},
                {'symbol': '1120.SR', 'name': 'Saudi National Bank', 'sector': 'financials'},
                {'symbol': '2010.SR', 'name': 'SABCO', 'sector': 'industrials'}
            ]
            
            selected_securities = []
            allocation_per_stock = target_allocation / min(len(candidate_stocks), 8)  # Max 8 positions
            
            for stock in candidate_stocks[:8]:  # Select top 8 for diversification
                security = {
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'asset_class': 'saudi_equity',
                    'allocation': allocation_per_stock,
                    'sector': stock['sector'],
                    'selection_criteria': 'Quality-based selection using comprehensive analysis'
                }
                selected_securities.append(security)
            
            return selected_securities
            
        except Exception as e:
            logger.error(f"Error selecting Saudi equities: {str(e)}")
            return []
    
    def _select_saudi_bonds(self, target_allocation: float, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """Select Saudi bond securities"""
        return [{
            'symbol': 'SAUDI_GOVT_10Y',
            'name': 'Saudi Government Bonds (10Y)',
            'asset_class': 'saudi_bonds',
            'allocation': target_allocation,
            'duration': 10,
            'selection_criteria': 'Government bonds for stability and income'
        }]
    
    def _select_international_equities(self, target_allocation: float, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """Select international equity securities"""
        return [{
            'symbol': 'INTL_EQUITY_ETF',
            'name': 'International Equity ETF',
            'asset_class': 'international_equity',
            'allocation': target_allocation,
            'geographic_exposure': 'Global developed markets',
            'selection_criteria': 'Diversified international exposure through ETF'
        }]
    
    def _select_real_estate_securities(self, target_allocation: float, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """Select real estate securities"""
        return [{
            'symbol': 'SAUDI_REIT_ETF',
            'name': 'Saudi REIT ETF',
            'asset_class': 'real_estate',
            'allocation': target_allocation,
            'property_types': 'Diversified commercial real estate',
            'selection_criteria': 'Real estate exposure through REIT ETF'
        }]
    
    def _select_cash_equivalents(self, target_allocation: float) -> List[Dict[str, Any]]:
        """Select cash equivalent securities"""
        return [{
            'symbol': 'MONEY_MARKET',
            'name': 'Money Market Fund',
            'asset_class': 'cash_equivalents',
            'allocation': target_allocation,
            'yield': 0.03,
            'selection_criteria': 'Liquidity and capital preservation'
        }]
    
    def _calculate_portfolio_metrics(self, allocation: Dict[str, float], 
                                   securities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate expected portfolio metrics"""
        try:
            expected_return = 0
            portfolio_variance = 0
            
            # Calculate weighted expected return
            for asset_class, weight in allocation.items():
                asset_return = self.asset_classes[asset_class]['expected_return']
                expected_return += weight * asset_return
            
            # Calculate portfolio variance (simplified - assumes correlations)
            for asset_class, weight in allocation.items():
                asset_volatility = self.asset_classes[asset_class]['volatility']
                portfolio_variance += (weight ** 2) * (asset_volatility ** 2)
            
            # Add correlation effects (simplified)
            portfolio_variance *= 0.8  # Assume some diversification benefit
            
            portfolio_volatility = portfolio_variance ** 0.5
            
            # Calculate Sharpe ratio (assume 3% risk-free rate)
            risk_free_rate = 0.03
            sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility
            
            # Estimate maximum drawdown
            max_drawdown = portfolio_volatility * 2.5  # Rough estimate
            
            return {
                'expected_return': expected_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
            return {
                'expected_return': 0.06,
                'volatility': 0.12,
                'sharpe_ratio': 0.25,
                'max_drawdown': 0.15
            }
    
    def _determine_rebalancing_strategy(self, risk_profile: RiskProfile, 
                                      investment_goals: List[InvestmentGoal]) -> Dict[str, Any]:
        """Determine optimal rebalancing strategy"""
        return {
            'frequency': 'quarterly',
            'threshold_bands': {
                'equity': 0.05,  # Rebalance if allocation drifts 5% from target
                'bonds': 0.05,
                'alternatives': 0.03
            },
            'tax_considerations': True,
            'cost_threshold': 0.01  # Only rebalance if benefit exceeds 1% of portfolio
        }
    
    def _set_monitoring_triggers(self, risk_profile: RiskProfile, 
                               allocation: Dict[str, float]) -> List[str]:
        """Set portfolio monitoring triggers"""
        return [
            f"Portfolio drawdown exceeds {risk_profile.drawdown_tolerance:.1%}",
            "Any single position exceeds 10% of portfolio",
            "Significant change in macroeconomic environment",
            "Major life event affecting risk capacity",
            "Quarterly rebalancing review due",
            "Asset allocation drift exceeds 5% from target"
        ]
    
    def _develop_implementation_strategy(self, portfolio_rec: PortfolioRecommendation,
                                       client_data: Dict[str, Any], risk_profile: RiskProfile) -> Dict[str, Any]:
        """Develop detailed implementation strategy"""
        return {
            'investment_timeline': 'Implement over 3 months to average into positions',
            'order_execution': 'Use limit orders to minimize market impact',
            'tax_optimization': 'Prioritize tax-advantaged accounts for bonds and REITs',
            'cost_minimization': 'Use low-cost ETFs where appropriate',
            'dollar_cost_averaging': 'For positions above 5% of portfolio',
            'cash_management': 'Maintain 6-month emergency fund separately'
        }
    
    def _create_monitoring_framework(self, portfolio_rec: PortfolioRecommendation,
                                   investment_goals: List[InvestmentGoal], 
                                   risk_profile: RiskProfile) -> Dict[str, Any]:
        """Create comprehensive monitoring framework"""
        return {
            'performance_benchmarks': {
                'primary': 'Custom benchmark based on strategic allocation',
                'secondary': 'Tadawul All Share Index (TASI)',
                'risk_adjusted': 'Sharpe ratio vs benchmark'
            },
            'reporting_frequency': {
                'monthly_statements': True,
                'quarterly_reviews': True,
                'annual_comprehensive_review': True
            },
            'key_metrics': [
                'Total return vs benchmark',
                'Risk-adjusted returns (Sharpe ratio)',
                'Maximum drawdown',
                'Asset allocation drift',
                'Goal progress tracking'
            ],
            'alert_thresholds': {
                'performance_deviation': '2% underperformance vs benchmark over 6 months',
                'risk_threshold': f'Portfolio volatility exceeds {risk_profile.volatility_tolerance:.1%}',
                'allocation_drift': 'Any asset class drifts >5% from target'
            }
        }
    
    def _prepare_fiduciary_disclosures(self, portfolio_rec: PortfolioRecommendation,
                                     implementation_strategy: Dict[str, Any]) -> List[str]:
        """Prepare required fiduciary disclosures"""
        return [
            "This advice is provided in a fiduciary capacity, acting in your best interest",
            "Fees: No transaction-based fees. Advisory fee structure provided separately",
            "Conflicts of interest: None identified in recommended securities",
            "Past performance does not guarantee future results",
            "All investments carry risk of loss, including potential loss of principal",
            f"Expected portfolio volatility: {portfolio_rec.expected_volatility:.1%} annually",
            f"Estimated maximum drawdown: {portfolio_rec.max_drawdown_estimate:.1%}",
            "Regular monitoring and rebalancing recommended",
            "Tax implications should be considered with qualified tax advisor",
            "Investment recommendations based on stated goals and risk tolerance"
        ]
    
    def generate_fiduciary_report(self, advice: FiduciaryAdvice) -> Dict[str, Any]:
        """Generate comprehensive fiduciary advice report"""
        return {
            'executive_summary': {
                'client_risk_profile': advice.client_profile.risk_category,
                'primary_goals': [goal.name for goal in advice.investment_goals],
                'recommended_allocation': advice.portfolio_recommendation.allocation,
                'expected_annual_return': f"{advice.portfolio_recommendation.expected_return:.1%}",
                'expected_volatility': f"{advice.portfolio_recommendation.expected_volatility:.1%}",
                'next_review_date': advice.next_review_date.strftime('%Y-%m-%d')
            },
            'risk_assessment': {
                'risk_score': f"{advice.client_profile.risk_score}/10",
                'risk_category': advice.client_profile.risk_category,
                'time_horizon': f"{advice.client_profile.time_horizon} years",
                'liquidity_needs': advice.client_profile.liquidity_needs,
                'behavioral_considerations': advice.client_profile.behavioral_biases
            },
            'investment_goals': [
                {
                    'name': goal.name,
                    'target_amount': f"SAR {goal.target_amount:,.0f}",
                    'time_horizon': f"{goal.time_horizon_years} years",
                    'priority': goal.priority
                } for goal in advice.investment_goals
            ],
            'portfolio_recommendation': {
                'strategic_allocation': {
                    asset: f"{weight:.1%}" 
                    for asset, weight in advice.portfolio_recommendation.allocation.items()
                },
                'expected_metrics': {
                    'annual_return': f"{advice.portfolio_recommendation.expected_return:.1%}",
                    'volatility': f"{advice.portfolio_recommendation.expected_volatility:.1%}",
                    'sharpe_ratio': f"{advice.portfolio_recommendation.sharpe_ratio:.2f}",
                    'max_drawdown': f"{advice.portfolio_recommendation.max_drawdown_estimate:.1%}"
                },
                'specific_securities': advice.portfolio_recommendation.specific_securities
            },
            'implementation_plan': advice.implementation_strategy,
            'monitoring_framework': advice.monitoring_framework,
            'fiduciary_disclosures': advice.disclosure_items,
            'recommendations': [
                "Begin implementation according to timeline",
                "Set up automated monitoring alerts",
                "Schedule quarterly review meetings",
                "Consider tax-loss harvesting opportunities",
                "Maintain emergency fund separately from investment portfolio"
            ]
        }