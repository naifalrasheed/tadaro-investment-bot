"""
Margin of Safety Calculator
Implements Benjamin Graham's core investment principle
Buffer between price and intrinsic value for protection against mistakes, bad luck, and market volatility
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from .valuation_engine import ValuationEngine, ValuationResult
from monitoring.performance import monitor_performance, metrics_collector

logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """Safety level categories"""
    EXCELLENT = "excellent"      # 40%+ margin
    GOOD = "good"               # 25-40% margin
    ADEQUATE = "adequate"       # 15-25% margin
    MINIMAL = "minimal"         # 5-15% margin
    UNSAFE = "unsafe"           # <5% margin
    OVERVALUED = "overvalued"   # Negative margin

class CompanyQuality(Enum):
    """Company quality assessment"""
    HIGH_QUALITY = "high_quality"
    MEDIUM_QUALITY = "medium_quality"
    LOW_QUALITY = "low_quality"
    SPECULATIVE = "speculative"

@dataclass
class MarginOfSafetyResult:
    """Result of margin of safety analysis"""
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_percentage: float
    safety_level: SafetyLevel
    company_quality: CompanyQuality
    recommended_margin: float
    recommendation: str
    risk_assessment: Dict[str, Any]
    quality_factors: Dict[str, Any]
    timestamp: datetime

class MarginOfSafetyCalculator:
    """
    Implements Benjamin Graham's margin of safety principle
    
    Core Concept: Buy with a buffer between price and value
    Key Lessons:
    - You never know exactly what a business is worth
    - Buy for much less than you think it's worth
    - Separates investors from speculators
    - All sound investing rests on this idea
    """
    
    def __init__(self, valuation_engine: Optional[ValuationEngine] = None):
        self.valuation_engine = valuation_engine or ValuationEngine()
        
        # Margin requirements by company quality
        self.quality_margins = {
            CompanyQuality.HIGH_QUALITY: 0.20,      # 20% minimum
            CompanyQuality.MEDIUM_QUALITY: 0.30,    # 30% minimum
            CompanyQuality.LOW_QUALITY: 0.40,       # 40% minimum
            CompanyQuality.SPECULATIVE: 0.50        # 50% minimum
        }
        
        # Safety level thresholds
        self.safety_thresholds = {
            SafetyLevel.EXCELLENT: 0.40,
            SafetyLevel.GOOD: 0.25,
            SafetyLevel.ADEQUATE: 0.15,
            SafetyLevel.MINIMAL: 0.05,
            SafetyLevel.UNSAFE: 0.0
        }
    
    @monitor_performance
    def analyze_margin_of_safety(self, symbol: str, valuation_method: str = 'dcf') -> MarginOfSafetyResult:
        """
        Comprehensive margin of safety analysis
        
        Args:
            symbol: Stock symbol
            valuation_method: 'dcf', 'graham', 'nav', or 'all'
        """
        try:
            logger.info(f"Analyzing margin of safety for {symbol} using {valuation_method} method")
            
            # Get intrinsic value based on method
            if valuation_method == 'dcf':
                valuation_result = self.valuation_engine.calculate_dcf_valuation(symbol)
            elif valuation_method == 'graham':
                valuation_result = self.valuation_engine.calculate_graham_valuation(symbol)
            elif valuation_method == 'nav':
                valuation_result = self.valuation_engine.calculate_nav_valuation(symbol)
            elif valuation_method == 'all':
                return self._analyze_all_methods(symbol)
            else:
                raise ValueError(f"Unknown valuation method: {valuation_method}")
            
            # Assess company quality
            company_quality = self._assess_company_quality(symbol)
            
            # Calculate margin of safety
            margin_percentage = valuation_result.margin_of_safety
            
            # Determine safety level
            safety_level = self._determine_safety_level(margin_percentage)
            
            # Get recommended margin for this company quality
            recommended_margin = self.quality_margins[company_quality] * 100  # Convert to percentage
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                margin_percentage, 
                safety_level, 
                company_quality,
                recommended_margin
            )
            
            # Perform risk assessment
            risk_assessment = self._assess_investment_risks(symbol, valuation_result, company_quality)
            
            # Get quality factors
            quality_factors = self._get_quality_factors(symbol)
            
            result = MarginOfSafetyResult(
                symbol=symbol,
                intrinsic_value=valuation_result.intrinsic_value_per_share,
                current_price=valuation_result.current_price,
                margin_percentage=margin_percentage,
                safety_level=safety_level,
                company_quality=company_quality,
                recommended_margin=recommended_margin,
                recommendation=recommendation,
                risk_assessment=risk_assessment,
                quality_factors=quality_factors,
                timestamp=datetime.now()
            )
            
            # Record analysis
            metrics_collector.record_feature_usage('margin_safety_analysis')
            
            logger.info(f"Margin of safety analysis completed for {symbol}: {margin_percentage:.1f}% ({safety_level.value})")
            return result
            
        except Exception as e:
            logger.error(f"Margin of safety analysis failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e))
    
    def _analyze_all_methods(self, symbol: str) -> MarginOfSafetyResult:
        """Analyze using all valuation methods and provide consensus"""
        try:
            # Get all valuations
            dcf_result = self.valuation_engine.calculate_dcf_valuation(symbol)
            graham_result = self.valuation_engine.calculate_graham_valuation(symbol)
            nav_result = self.valuation_engine.calculate_nav_valuation(symbol)
            
            # Calculate consensus intrinsic value (weighted average)
            valuations = [
                {'value': dcf_result.intrinsic_value_per_share, 'weight': 0.5, 'method': 'DCF'},
                {'value': graham_result.intrinsic_value_per_share, 'weight': 0.3, 'method': 'Graham'},
                {'value': nav_result.intrinsic_value_per_share, 'weight': 0.2, 'method': 'NAV'}
            ]
            
            # Remove zero/error valuations
            valid_valuations = [v for v in valuations if v['value'] > 0]
            
            if not valid_valuations:
                raise ValueError("All valuation methods failed")
            
            # Calculate weighted average
            total_weight = sum(v['weight'] for v in valid_valuations)
            consensus_value = sum(v['value'] * v['weight'] for v in valid_valuations) / total_weight
            
            # Use current price from any valid result
            current_price = next(r.current_price for r in [dcf_result, graham_result, nav_result] if r.current_price > 0)
            
            # Calculate consensus margin
            consensus_margin = (consensus_value - current_price) / consensus_value * 100 if consensus_value > 0 else 0
            
            # Assess quality and safety
            company_quality = self._assess_company_quality(symbol)
            safety_level = self._determine_safety_level(consensus_margin)
            recommended_margin = self.quality_margins[company_quality] * 100
            
            # Create comprehensive result
            recommendation = self._generate_consensus_recommendation(
                valid_valuations, 
                consensus_value, 
                current_price,
                consensus_margin,
                company_quality
            )
            
            return MarginOfSafetyResult(
                symbol=symbol,
                intrinsic_value=consensus_value,
                current_price=current_price,
                margin_percentage=consensus_margin,
                safety_level=safety_level,
                company_quality=company_quality,
                recommended_margin=recommended_margin,
                recommendation=recommendation,
                risk_assessment=self._assess_consensus_risks(valid_valuations, consensus_margin),
                quality_factors=self._get_quality_factors(symbol),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"All-methods analysis failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e))
    
    def _assess_company_quality(self, symbol: str) -> CompanyQuality:
        """
        Assess company quality based on fundamental metrics
        Higher quality companies require lower margins of safety
        """
        try:
            # This would integrate with fundamental analysis
            # For now, use simplified quality assessment
            
            # Get basic financial health indicators
            quality_score = 0
            
            # Mock quality assessment - in production, analyze:
            # - Debt levels
            # - Earnings consistency
            # - Return on equity
            # - Profit margins
            # - Market position
            # - Management quality
            
            # For demonstration, assign quality based on symbol characteristics
            # In production, this would be comprehensive fundamental analysis
            
            quality_score = np.random.choice([1, 2, 3, 4], p=[0.1, 0.3, 0.4, 0.2])
            
            if quality_score >= 4:
                return CompanyQuality.HIGH_QUALITY
            elif quality_score >= 3:
                return CompanyQuality.MEDIUM_QUALITY
            elif quality_score >= 2:
                return CompanyQuality.LOW_QUALITY
            else:
                return CompanyQuality.SPECULATIVE
                
        except Exception as e:
            logger.warning(f"Quality assessment failed for {symbol}: {str(e)}")
            return CompanyQuality.MEDIUM_QUALITY  # Default to medium quality
    
    def _determine_safety_level(self, margin_percentage: float) -> SafetyLevel:
        """Determine safety level based on margin percentage"""
        margin_decimal = margin_percentage / 100
        
        if margin_decimal < 0:
            return SafetyLevel.OVERVALUED
        elif margin_decimal < self.safety_thresholds[SafetyLevel.UNSAFE]:
            return SafetyLevel.UNSAFE
        elif margin_decimal < self.safety_thresholds[SafetyLevel.MINIMAL]:
            return SafetyLevel.MINIMAL
        elif margin_decimal < self.safety_thresholds[SafetyLevel.ADEQUATE]:
            return SafetyLevel.ADEQUATE
        elif margin_decimal < self.safety_thresholds[SafetyLevel.GOOD]:
            return SafetyLevel.GOOD
        else:
            return SafetyLevel.EXCELLENT
    
    def _generate_recommendation(self, margin_percentage: float, safety_level: SafetyLevel,
                               company_quality: CompanyQuality, recommended_margin: float) -> str:
        """Generate investment recommendation based on margin analysis"""
        
        if safety_level == SafetyLevel.OVERVALUED:
            return f"❌ AVOID - Stock is overvalued. Current price exceeds intrinsic value."
        
        elif safety_level == SafetyLevel.UNSAFE:
            return f"⚠️ HIGH RISK - Margin of safety ({margin_percentage:.1f}%) is below safe levels. Consider waiting for better entry point."
        
        elif safety_level == SafetyLevel.MINIMAL:
            if company_quality == CompanyQuality.HIGH_QUALITY:
                return f"⚡ CAUTIOUS BUY - High quality company with minimal margin ({margin_percentage:.1f}%). Acceptable for blue-chip stocks."
            else:
                return f"⚠️ RISKY - Minimal margin ({margin_percentage:.1f}%) for {company_quality.value.replace('_', ' ')} company. Higher risk investment."
        
        elif safety_level == SafetyLevel.ADEQUATE:
            return f"✅ REASONABLE BUY - Adequate margin of safety ({margin_percentage:.1f}%). Suitable for conservative investors."
        
        elif safety_level == SafetyLevel.GOOD:
            return f"🎯 STRONG BUY - Good margin of safety ({margin_percentage:.1f}%). Solid investment opportunity with downside protection."
        
        else:  # EXCELLENT
            return f"🏆 EXCELLENT BUY - Outstanding margin of safety ({margin_percentage:.1f}%). Exceptional value opportunity with significant downside protection."
    
    def _generate_consensus_recommendation(self, valuations: List[Dict], consensus_value: float,
                                        current_price: float, consensus_margin: float,
                                        company_quality: CompanyQuality) -> str:
        """Generate recommendation based on consensus of multiple methods"""
        
        methods_summary = ", ".join([f"{v['method']}: ${v['value']:.2f}" for v in valuations])
        
        base_rec = self._generate_recommendation(
            consensus_margin, 
            self._determine_safety_level(consensus_margin),
            company_quality,
            self.quality_margins[company_quality] * 100
        )
        
        consensus_note = f"\\n\\n📊 CONSENSUS VALUATION: ${consensus_value:.2f}\\n" \
                        f"Methods used: {methods_summary}\\n" \
                        f"Agreement level: {self._calculate_valuation_agreement(valuations)}"
        
        return base_rec + consensus_note
    
    def _calculate_valuation_agreement(self, valuations: List[Dict]) -> str:
        """Calculate how much the different valuation methods agree"""
        if len(valuations) < 2:
            return "Single method"
        
        values = [v['value'] for v in valuations]
        mean_val = np.mean(values)
        std_dev = np.std(values)
        coefficient_of_variation = std_dev / mean_val if mean_val > 0 else 1
        
        if coefficient_of_variation < 0.1:
            return "High agreement (values within 10%)"
        elif coefficient_of_variation < 0.2:
            return "Moderate agreement (values within 20%)"
        else:
            return "Low agreement (significant valuation differences)"
    
    def _assess_investment_risks(self, symbol: str, valuation_result: ValuationResult,
                                company_quality: CompanyQuality) -> Dict[str, Any]:
        """Assess specific investment risks"""
        return {
            'valuation_risk': self._assess_valuation_risk(valuation_result),
            'business_risk': self._assess_business_risk(symbol, company_quality),
            'market_risk': self._assess_market_risk(symbol),
            'liquidity_risk': self._assess_liquidity_risk(symbol),
            'overall_risk_score': self._calculate_overall_risk_score(company_quality, valuation_result.margin_of_safety)
        }
    
    def _assess_valuation_risk(self, valuation_result: ValuationResult) -> Dict[str, Any]:
        """Assess risks related to valuation uncertainty"""
        return {
            'method_reliability': self._get_method_reliability(valuation_result.valuation_method),
            'assumption_sensitivity': 'High' if 'sensitivity_analysis' in valuation_result.calculation_details else 'Unknown',
            'forecast_uncertainty': 'Medium',  # Based on forecast horizon
            'risk_level': 'Medium'
        }
    
    def _assess_business_risk(self, symbol: str, company_quality: CompanyQuality) -> Dict[str, Any]:
        """Assess business-specific risks"""
        return {
            'competitive_position': 'Strong' if company_quality == CompanyQuality.HIGH_QUALITY else 'Moderate',
            'industry_cyclicality': 'Medium',  # Would analyze industry
            'regulatory_risk': 'Low',  # Would analyze sector
            'management_risk': 'Low' if company_quality == CompanyQuality.HIGH_QUALITY else 'Medium',
            'risk_level': 'Low' if company_quality == CompanyQuality.HIGH_QUALITY else 'Medium'
        }
    
    def _assess_market_risk(self, symbol: str) -> Dict[str, Any]:
        """Assess market-related risks"""
        return {
            'beta_risk': 'Medium',  # Would get actual beta
            'correlation_to_market': 'High',
            'volatility': 'Medium',
            'liquidity': 'High',  # Assume liquid for major stocks
            'risk_level': 'Medium'
        }
    
    def _assess_liquidity_risk(self, symbol: str) -> Dict[str, Any]:
        """Assess liquidity risks"""
        return {
            'trading_volume': 'High',  # Would get actual volume
            'bid_ask_spread': 'Narrow',
            'market_depth': 'Good',
            'risk_level': 'Low'
        }
    
    def _calculate_overall_risk_score(self, company_quality: CompanyQuality, margin: float) -> str:
        """Calculate overall investment risk score"""
        quality_score = {
            CompanyQuality.HIGH_QUALITY: 1,
            CompanyQuality.MEDIUM_QUALITY: 2,
            CompanyQuality.LOW_QUALITY: 3,
            CompanyQuality.SPECULATIVE: 4
        }[company_quality]
        
        margin_score = 1 if margin > 30 else 2 if margin > 20 else 3 if margin > 10 else 4
        
        combined_score = (quality_score + margin_score) / 2
        
        if combined_score <= 1.5:
            return "Low Risk"
        elif combined_score <= 2.5:
            return "Medium Risk"
        elif combined_score <= 3.5:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def _get_method_reliability(self, method: str) -> str:
        """Get reliability assessment for valuation method"""
        reliability_map = {
            'DCF (2-Stage)': 'High for mature companies, Medium for growth stocks',
            "Graham's Formula": 'Medium - best for stable, mature companies',
            'Net Asset Value (NAV)': 'High for asset-heavy companies',
            'Revenue Multiple': 'Low - rough approximation only'
        }
        return reliability_map.get(method, 'Unknown')
    
    def _get_quality_factors(self, symbol: str) -> Dict[str, Any]:
        """Get factors that determine company quality"""
        # This would analyze actual financial metrics
        # For now, return mock quality factors
        return {
            'financial_strength': {
                'debt_to_equity': 0.3,  # Low debt
                'current_ratio': 2.1,   # Good liquidity
                'interest_coverage': 15.0,  # Strong coverage
                'assessment': 'Strong'
            },
            'profitability': {
                'roe': 0.18,  # 18% ROE
                'roa': 0.12,  # 12% ROA
                'profit_margin': 0.15,  # 15% margins
                'assessment': 'Good'
            },
            'growth_consistency': {
                'revenue_growth_stability': 'Consistent',
                'earnings_growth_stability': 'Stable',
                'assessment': 'Reliable'
            },
            'competitive_position': {
                'market_share': 'Leading',
                'brand_strength': 'Strong',
                'moat_quality': 'Wide moat',
                'assessment': 'Excellent'
            }
        }
    
    def _create_error_result(self, symbol: str, error_msg: str) -> MarginOfSafetyResult:
        """Create error result for failed analysis"""
        return MarginOfSafetyResult(
            symbol=symbol,
            intrinsic_value=0.0,
            current_price=0.0,
            margin_percentage=0.0,
            safety_level=SafetyLevel.UNSAFE,
            company_quality=CompanyQuality.SPECULATIVE,
            recommended_margin=50.0,
            recommendation=f"❌ ANALYSIS FAILED - {error_msg}",
            risk_assessment={'error': error_msg},
            quality_factors={'error': error_msg},
            timestamp=datetime.now()
        )
    
    def calculate_position_size(self, margin_result: MarginOfSafetyResult, portfolio_value: float,
                              max_position_percent: float = 0.05) -> Dict[str, Any]:
        """
        Calculate appropriate position size based on margin of safety and risk
        
        Args:
            margin_result: Margin of safety analysis result
            portfolio_value: Total portfolio value
            max_position_percent: Maximum percentage of portfolio for single position
        """
        try:
            # Base position size on safety level and company quality
            base_size_map = {
                (SafetyLevel.EXCELLENT, CompanyQuality.HIGH_QUALITY): 0.05,  # 5%
                (SafetyLevel.EXCELLENT, CompanyQuality.MEDIUM_QUALITY): 0.04,  # 4%
                (SafetyLevel.GOOD, CompanyQuality.HIGH_QUALITY): 0.04,  # 4%
                (SafetyLevel.GOOD, CompanyQuality.MEDIUM_QUALITY): 0.03,  # 3%
                (SafetyLevel.ADEQUATE, CompanyQuality.HIGH_QUALITY): 0.03,  # 3%
                (SafetyLevel.ADEQUATE, CompanyQuality.MEDIUM_QUALITY): 0.02,  # 2%
                (SafetyLevel.MINIMAL, CompanyQuality.HIGH_QUALITY): 0.02,  # 2%
            }
            
            # Get recommended position size
            key = (margin_result.safety_level, margin_result.company_quality)
            position_percent = base_size_map.get(key, 0.01)  # Default 1%
            
            # Apply maximum position limit
            position_percent = min(position_percent, max_position_percent)
            
            # Calculate dollar amounts
            position_value = portfolio_value * position_percent
            shares_to_buy = int(position_value / margin_result.current_price) if margin_result.current_price > 0 else 0
            actual_position_value = shares_to_buy * margin_result.current_price
            actual_position_percent = actual_position_value / portfolio_value * 100
            
            return {
                'recommended_position_percent': position_percent * 100,
                'recommended_position_value': position_value,
                'shares_to_buy': shares_to_buy,
                'actual_position_value': actual_position_value,
                'actual_position_percent': actual_position_percent,
                'rationale': self._get_position_rationale(margin_result.safety_level, margin_result.company_quality),
                'risk_considerations': [
                    f"Safety level: {margin_result.safety_level.value}",
                    f"Company quality: {margin_result.company_quality.value.replace('_', ' ')}",
                    f"Margin of safety: {margin_result.margin_percentage:.1f}%"
                ]
            }
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {str(e)}")
            return {
                'error': str(e),
                'recommended_position_percent': 1.0,
                'shares_to_buy': 0
            }
    
    def _get_position_rationale(self, safety_level: SafetyLevel, company_quality: CompanyQuality) -> str:
        """Get rationale for position sizing recommendation"""
        if safety_level == SafetyLevel.EXCELLENT:
            return f"Large position justified by excellent margin of safety and {company_quality.value.replace('_', ' ')} quality"
        elif safety_level == SafetyLevel.GOOD:
            return f"Moderate position appropriate for good safety margin and {company_quality.value.replace('_', ' ')} quality"
        elif safety_level == SafetyLevel.ADEQUATE:
            return f"Conservative position due to adequate but not exceptional safety margin"
        else:
            return f"Minimal position due to limited safety margin and/or quality concerns"