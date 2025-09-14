"""
Macroeconomic Integration Service

This service integrates macroeconomic factors into investment analysis:
1. Economic indicator tracking and correlation analysis
2. Interest rate impact on valuations
3. Currency effects on international investments
4. Sector rotation based on economic cycles
5. Inflation impact on different asset classes
6. GDP growth correlation with market sectors
7. Geopolitical risk assessment
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import numpy as np
from services.saudi_market_service import SaudiMarketService
from utils.financial_calculations import FinancialCalculations

logger = logging.getLogger(__name__)

@dataclass
class MacroEconomicFactors:
    """Container for macroeconomic factors"""
    interest_rates: Dict[str, float]
    inflation_rate: float
    gdp_growth: float
    currency_rates: Dict[str, float]
    oil_prices: float
    unemployment_rate: float
    consumer_confidence: float
    sector_rotation_signals: Dict[str, str]

@dataclass
class SectorImpactAnalysis:
    """Sector-specific macroeconomic impact analysis"""
    sector: str
    interest_rate_sensitivity: float
    inflation_sensitivity: float
    gdp_correlation: float
    currency_sensitivity: float
    oil_price_correlation: float
    current_cycle_position: str
    recommended_allocation: str

@dataclass
class MacroValuationAdjustment:
    """Valuation adjustments based on macro factors"""
    base_valuation: float
    interest_rate_adjustment: float
    inflation_adjustment: float
    currency_adjustment: float
    risk_premium_adjustment: float
    final_adjusted_valuation: float
    confidence_level: float

class MacroIntegrationService:
    """
    Comprehensive macroeconomic integration for investment analysis
    
    Analyzes how macroeconomic factors affect individual securities and sectors
    Provides valuation adjustments and investment recommendations
    """
    
    def __init__(self, saudi_service: SaudiMarketService):
        self.saudi_service = saudi_service
        self.financial_calc = FinancialCalculations()
        
        # Economic cycle definitions
        self.cycle_phases = {
            'expansion': {'gdp_growth': 3.0, 'unemployment': 'declining', 'inflation': 'rising'},
            'peak': {'gdp_growth': 2.0, 'unemployment': 'low', 'inflation': 'high'},
            'contraction': {'gdp_growth': -1.0, 'unemployment': 'rising', 'inflation': 'falling'},
            'trough': {'gdp_growth': -2.0, 'unemployment': 'high', 'inflation': 'low'}
        }
        
        # Sector sensitivities (simplified - would be calibrated with historical data)
        self.sector_sensitivities = {
            'financials': {'interest_rates': 0.8, 'gdp': 0.7, 'inflation': -0.3},
            'real_estate': {'interest_rates': -0.9, 'gdp': 0.6, 'inflation': 0.4},
            'technology': {'interest_rates': -0.6, 'gdp': 0.5, 'inflation': -0.2},
            'utilities': {'interest_rates': -0.4, 'gdp': 0.2, 'inflation': 0.3},
            'consumer_discretionary': {'interest_rates': -0.5, 'gdp': 0.8, 'inflation': -0.6},
            'consumer_staples': {'interest_rates': -0.2, 'gdp': 0.3, 'inflation': 0.1},
            'healthcare': {'interest_rates': -0.3, 'gdp': 0.2, 'inflation': 0.2},
            'energy': {'interest_rates': -0.2, 'gdp': 0.4, 'oil': 0.9},
            'materials': {'interest_rates': -0.4, 'gdp': 0.7, 'inflation': 0.5},
            'industrials': {'interest_rates': -0.5, 'gdp': 0.8, 'inflation': -0.3}
        }
    
    def get_macro_economic_factors(self) -> MacroEconomicFactors:
        """
        Gather current macroeconomic factors
        In production, this would connect to various economic data APIs
        """
        try:
            logger.info("Gathering macroeconomic factors")
            
            # Simplified implementation - would connect to actual economic APIs
            # Such as FRED (Federal Reserve Economic Data), World Bank, IMF, etc.
            
            return MacroEconomicFactors(
                interest_rates={
                    'saudi_policy_rate': 5.50,  # SAMA policy rate
                    'us_fed_rate': 5.25,        # Federal funds rate
                    '10y_saudi_bond': 4.8,      # 10-year Saudi government bond
                    '10y_us_treasury': 4.5      # 10-year US Treasury
                },
                inflation_rate=2.8,             # Saudi CPI inflation
                gdp_growth=4.1,                 # Saudi GDP growth forecast
                currency_rates={
                    'USD_SAR': 3.75,            # Fixed exchange rate
                    'EUR_SAR': 4.10,
                    'GBP_SAR': 4.75
                },
                oil_prices=85.0,                # Brent crude per barrel
                unemployment_rate=5.2,          # Saudi unemployment rate
                consumer_confidence=108.5,      # Consumer confidence index
                sector_rotation_signals={
                    'financials': 'positive',
                    'energy': 'positive',
                    'technology': 'neutral',
                    'real_estate': 'negative'
                }
            )
            
        except Exception as e:
            logger.error(f"Error gathering macro factors: {str(e)}")
            raise
    
    def analyze_sector_macro_impact(self, sector: str, macro_factors: MacroEconomicFactors) -> SectorImpactAnalysis:
        """Analyze how macroeconomic factors impact a specific sector"""
        try:
            logger.info(f"Analyzing macro impact for sector: {sector}")
            
            sensitivities = self.sector_sensitivities.get(sector.lower(), {
                'interest_rates': 0, 'gdp': 0, 'inflation': 0, 'oil': 0
            })
            
            # Calculate impact scores
            interest_rate_sensitivity = sensitivities.get('interest_rates', 0)
            inflation_sensitivity = sensitivities.get('inflation', 0)
            gdp_correlation = sensitivities.get('gdp', 0)
            oil_correlation = sensitivities.get('oil', 0)
            
            # Determine current economic cycle position
            cycle_position = self._determine_economic_cycle(macro_factors)
            
            # Generate allocation recommendation
            allocation_rec = self._generate_sector_allocation_recommendation(
                sector, macro_factors, sensitivities, cycle_position
            )
            
            return SectorImpactAnalysis(
                sector=sector,
                interest_rate_sensitivity=interest_rate_sensitivity,
                inflation_sensitivity=inflation_sensitivity,
                gdp_correlation=gdp_correlation,
                currency_sensitivity=0.0,  # Simplified for Saudi market
                oil_price_correlation=oil_correlation,
                current_cycle_position=cycle_position,
                recommended_allocation=allocation_rec
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sector macro impact: {str(e)}")
            raise
    
    def adjust_valuation_for_macro(self, base_valuation: float, symbol: str, 
                                 sector: str, macro_factors: MacroEconomicFactors) -> MacroValuationAdjustment:
        """Adjust security valuation based on macroeconomic factors"""
        try:
            logger.info(f"Adjusting valuation for {symbol} based on macro factors")
            
            # Get sector impact analysis
            sector_analysis = self.analyze_sector_macro_impact(sector, macro_factors)
            
            # Calculate individual adjustments
            interest_adjustment = self._calculate_interest_rate_adjustment(
                base_valuation, macro_factors, sector_analysis
            )
            
            inflation_adjustment = self._calculate_inflation_adjustment(
                base_valuation, macro_factors, sector_analysis
            )
            
            currency_adjustment = self._calculate_currency_adjustment(
                base_valuation, symbol, macro_factors
            )
            
            risk_premium_adjustment = self._calculate_risk_premium_adjustment(
                base_valuation, macro_factors, sector
            )
            
            # Apply adjustments
            adjusted_valuation = (
                base_valuation + 
                interest_adjustment + 
                inflation_adjustment + 
                currency_adjustment + 
                risk_premium_adjustment
            )
            
            # Calculate confidence level
            confidence = self._calculate_adjustment_confidence(macro_factors, sector)
            
            return MacroValuationAdjustment(
                base_valuation=base_valuation,
                interest_rate_adjustment=interest_adjustment,
                inflation_adjustment=inflation_adjustment,
                currency_adjustment=currency_adjustment,
                risk_premium_adjustment=risk_premium_adjustment,
                final_adjusted_valuation=adjusted_valuation,
                confidence_level=confidence
            )
            
        except Exception as e:
            logger.error(f"Error adjusting valuation for macro factors: {str(e)}")
            raise
    
    def _determine_economic_cycle(self, macro_factors: MacroEconomicFactors) -> str:
        """Determine current position in economic cycle"""
        try:
            gdp_growth = macro_factors.gdp_growth
            inflation = macro_factors.inflation_rate
            unemployment = macro_factors.unemployment_rate
            
            # Simplified cycle determination logic
            if gdp_growth > 3 and inflation < 3 and unemployment < 6:
                return 'expansion'
            elif gdp_growth > 2 and inflation > 3:
                return 'peak'
            elif gdp_growth < 0:
                return 'contraction'
            else:
                return 'trough'
                
        except Exception:
            return 'unknown'
    
    def _generate_sector_allocation_recommendation(self, sector: str, macro_factors: MacroEconomicFactors,
                                                 sensitivities: Dict, cycle_position: str) -> str:
        """Generate sector allocation recommendation based on macro environment"""
        try:
            # Calculate sector favorability score
            score = 0
            
            # Interest rate impact
            if macro_factors.interest_rates['saudi_policy_rate'] > 4:  # High rates
                score += sensitivities.get('interest_rates', 0) * -1
            else:
                score += sensitivities.get('interest_rates', 0)
            
            # GDP growth impact
            if macro_factors.gdp_growth > 3:  # Strong growth
                score += sensitivities.get('gdp', 0)
            elif macro_factors.gdp_growth < 1:  # Weak growth
                score += sensitivities.get('gdp', 0) * -1
            
            # Inflation impact
            if macro_factors.inflation_rate > 3:  # High inflation
                score += sensitivities.get('inflation', 0)
            
            # Oil price impact (specific to Saudi market)
            if sector.lower() == 'energy' and macro_factors.oil_prices > 80:
                score += 0.5
            
            # Generate recommendation
            if score > 0.3:
                return 'overweight'
            elif score < -0.3:
                return 'underweight'
            else:
                return 'neutral'
                
        except Exception:
            return 'neutral'
    
    def _calculate_interest_rate_adjustment(self, base_valuation: float, macro_factors: MacroEconomicFactors,
                                          sector_analysis: SectorImpactAnalysis) -> float:
        """Calculate valuation adjustment based on interest rate environment"""
        try:
            current_rate = macro_factors.interest_rates['saudi_policy_rate']
            neutral_rate = 3.5  # Assumed neutral rate for Saudi Arabia
            
            rate_deviation = current_rate - neutral_rate
            sensitivity = sector_analysis.interest_rate_sensitivity
            
            # Adjustment as percentage of base valuation
            adjustment_pct = rate_deviation * sensitivity * -0.1  # -10% per 1% rate change for high sensitivity sectors
            
            return base_valuation * adjustment_pct
            
        except Exception as e:
            logger.error(f"Error calculating interest rate adjustment: {str(e)}")
            return 0
    
    def _calculate_inflation_adjustment(self, base_valuation: float, macro_factors: MacroEconomicFactors,
                                      sector_analysis: SectorImpactAnalysis) -> float:
        """Calculate valuation adjustment based on inflation environment"""
        try:
            current_inflation = macro_factors.inflation_rate
            target_inflation = 2.0  # Saudi Arabia's inflation target
            
            inflation_deviation = current_inflation - target_inflation
            sensitivity = sector_analysis.inflation_sensitivity
            
            # Adjustment based on inflation sensitivity
            adjustment_pct = inflation_deviation * sensitivity * 0.05  # 5% per 1% inflation change
            
            return base_valuation * adjustment_pct
            
        except Exception as e:
            logger.error(f"Error calculating inflation adjustment: {str(e)}")
            return 0
    
    def _calculate_currency_adjustment(self, base_valuation: float, symbol: str,
                                     macro_factors: MacroEconomicFactors) -> float:
        """Calculate valuation adjustment based on currency factors"""
        try:
            # For Saudi market, SAR is pegged to USD, so minimal currency risk
            # This would be more relevant for international investments
            
            usd_sar_rate = macro_factors.currency_rates['USD_SAR']
            expected_rate = 3.75  # Official peg rate
            
            # Very small adjustment due to peg stability
            rate_deviation = (usd_sar_rate - expected_rate) / expected_rate
            
            # Minimal impact due to currency peg
            adjustment_pct = rate_deviation * 0.01
            
            return base_valuation * adjustment_pct
            
        except Exception as e:
            logger.error(f"Error calculating currency adjustment: {str(e)}")
            return 0
    
    def _calculate_risk_premium_adjustment(self, base_valuation: float, macro_factors: MacroEconomicFactors,
                                         sector: str) -> float:
        """Calculate risk premium adjustment based on macro uncertainty"""
        try:
            # Base risk premium
            base_risk_premium = 0.02  # 2%
            
            # Adjust based on economic uncertainty indicators
            uncertainty_factors = []
            
            # Interest rate volatility
            rate_level = macro_factors.interest_rates['saudi_policy_rate']
            if rate_level > 6 or rate_level < 2:
                uncertainty_factors.append(0.01)
            
            # Inflation uncertainty
            if macro_factors.inflation_rate > 4 or macro_factors.inflation_rate < 0:
                uncertainty_factors.append(0.01)
            
            # Oil price dependency (Saudi-specific)
            if macro_factors.oil_prices < 60 or macro_factors.oil_prices > 100:
                uncertainty_factors.append(0.015)
            
            # Calculate total risk premium
            total_risk_premium = base_risk_premium + sum(uncertainty_factors)
            
            # Apply as negative adjustment to valuation
            adjustment_pct = -total_risk_premium
            
            return base_valuation * adjustment_pct
            
        except Exception as e:
            logger.error(f"Error calculating risk premium adjustment: {str(e)}")
            return 0
    
    def _calculate_adjustment_confidence(self, macro_factors: MacroEconomicFactors, sector: str) -> float:
        """Calculate confidence level of macro adjustments"""
        try:
            confidence_factors = []
            
            # Data quality/availability
            confidence_factors.append(0.8)  # Assume 80% base confidence
            
            # Economic environment stability
            if 2 < macro_factors.gdp_growth < 5 and 1 < macro_factors.inflation_rate < 4:
                confidence_factors.append(0.9)  # High confidence in stable environment
            else:
                confidence_factors.append(0.6)  # Lower confidence in volatile environment
            
            # Sector-specific factors
            if sector.lower() in ['energy', 'financials']:  # Well-understood macro relationships
                confidence_factors.append(0.85)
            else:
                confidence_factors.append(0.7)
            
            # Calculate weighted average confidence
            return statistics.mean(confidence_factors)
            
        except Exception as e:
            logger.error(f"Error calculating adjustment confidence: {str(e)}")
            return 0.5
    
    def generate_macro_scenario_analysis(self, symbol: str, sector: str, 
                                       base_valuation: float) -> Dict[str, MacroValuationAdjustment]:
        """Generate valuation under different macroeconomic scenarios"""
        try:
            scenarios = {}
            
            # Current scenario
            current_macro = self.get_macro_economic_factors()
            scenarios['current'] = self.adjust_valuation_for_macro(
                base_valuation, symbol, sector, current_macro
            )
            
            # Bull scenario - favorable macro conditions
            bull_macro = self._create_bull_scenario(current_macro)
            scenarios['bull'] = self.adjust_valuation_for_macro(
                base_valuation, symbol, sector, bull_macro
            )
            
            # Bear scenario - unfavorable macro conditions
            bear_macro = self._create_bear_scenario(current_macro)
            scenarios['bear'] = self.adjust_valuation_for_macro(
                base_valuation, symbol, sector, bear_macro
            )
            
            # Stress scenario - extreme conditions
            stress_macro = self._create_stress_scenario(current_macro)
            scenarios['stress'] = self.adjust_valuation_for_macro(
                base_valuation, symbol, sector, stress_macro
            )
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating macro scenarios: {str(e)}")
            return {}
    
    def _create_bull_scenario(self, base_macro: MacroEconomicFactors) -> MacroEconomicFactors:
        """Create bullish macroeconomic scenario"""
        return MacroEconomicFactors(
            interest_rates={
                'saudi_policy_rate': max(2.0, base_macro.interest_rates['saudi_policy_rate'] - 1.0),
                'us_fed_rate': max(2.0, base_macro.interest_rates['us_fed_rate'] - 1.0),
                '10y_saudi_bond': max(2.5, base_macro.interest_rates['10y_saudi_bond'] - 0.5),
                '10y_us_treasury': max(2.5, base_macro.interest_rates['10y_us_treasury'] - 0.5)
            },
            inflation_rate=max(1.5, base_macro.inflation_rate - 0.5),
            gdp_growth=min(6.0, base_macro.gdp_growth + 1.5),
            currency_rates=base_macro.currency_rates,  # Pegged
            oil_prices=min(110.0, base_macro.oil_prices + 15.0),
            unemployment_rate=max(3.0, base_macro.unemployment_rate - 1.0),
            consumer_confidence=min(130.0, base_macro.consumer_confidence + 15.0),
            sector_rotation_signals={k: 'positive' for k in base_macro.sector_rotation_signals}
        )
    
    def _create_bear_scenario(self, base_macro: MacroEconomicFactors) -> MacroEconomicFactors:
        """Create bearish macroeconomic scenario"""
        return MacroEconomicFactors(
            interest_rates={
                'saudi_policy_rate': min(8.0, base_macro.interest_rates['saudi_policy_rate'] + 1.5),
                'us_fed_rate': min(8.0, base_macro.interest_rates['us_fed_rate'] + 1.5),
                '10y_saudi_bond': min(7.0, base_macro.interest_rates['10y_saudi_bond'] + 1.0),
                '10y_us_treasury': min(7.0, base_macro.interest_rates['10y_us_treasury'] + 1.0)
            },
            inflation_rate=min(5.0, base_macro.inflation_rate + 1.5),
            gdp_growth=max(-1.0, base_macro.gdp_growth - 2.0),
            currency_rates=base_macro.currency_rates,  # Pegged
            oil_prices=max(50.0, base_macro.oil_prices - 20.0),
            unemployment_rate=min(8.0, base_macro.unemployment_rate + 2.0),
            consumer_confidence=max(80.0, base_macro.consumer_confidence - 20.0),
            sector_rotation_signals={k: 'negative' for k in base_macro.sector_rotation_signals}
        )
    
    def _create_stress_scenario(self, base_macro: MacroEconomicFactors) -> MacroEconomicFactors:
        """Create stress test macroeconomic scenario"""
        return MacroEconomicFactors(
            interest_rates={
                'saudi_policy_rate': min(10.0, base_macro.interest_rates['saudi_policy_rate'] + 3.0),
                'us_fed_rate': min(10.0, base_macro.interest_rates['us_fed_rate'] + 3.0),
                '10y_saudi_bond': min(9.0, base_macro.interest_rates['10y_saudi_bond'] + 2.0),
                '10y_us_treasury': min(9.0, base_macro.interest_rates['10y_us_treasury'] + 2.0)
            },
            inflation_rate=min(8.0, base_macro.inflation_rate + 3.0),
            gdp_growth=max(-5.0, base_macro.gdp_growth - 4.0),
            currency_rates=base_macro.currency_rates,  # Assume peg holds
            oil_prices=max(30.0, base_macro.oil_prices - 35.0),
            unemployment_rate=min(12.0, base_macro.unemployment_rate + 4.0),
            consumer_confidence=max(60.0, base_macro.consumer_confidence - 40.0),
            sector_rotation_signals={k: 'negative' for k in base_macro.sector_rotation_signals}
        )
    
    def generate_macro_integration_report(self, symbol: str, sector: str, base_valuation: float) -> Dict[str, Any]:
        """Generate comprehensive macroeconomic integration report"""
        try:
            # Get current macro factors
            macro_factors = self.get_macro_economic_factors()
            
            # Analyze sector impact
            sector_analysis = self.analyze_sector_macro_impact(sector, macro_factors)
            
            # Adjust valuation
            valuation_adjustment = self.adjust_valuation_for_macro(
                base_valuation, symbol, sector, macro_factors
            )
            
            # Generate scenarios
            scenarios = self.generate_macro_scenario_analysis(symbol, sector, base_valuation)
            
            return {
                'executive_summary': {
                    'base_valuation': base_valuation,
                    'macro_adjusted_valuation': valuation_adjustment.final_adjusted_valuation,
                    'adjustment_magnitude': valuation_adjustment.final_adjusted_valuation - base_valuation,
                    'confidence_level': f"{valuation_adjustment.confidence_level:.1%}",
                    'economic_cycle': self._determine_economic_cycle(macro_factors)
                },
                'current_macro_environment': {
                    'policy_rate': f"{macro_factors.interest_rates['saudi_policy_rate']:.2f}%",
                    'inflation': f"{macro_factors.inflation_rate:.1f}%",
                    'gdp_growth': f"{macro_factors.gdp_growth:.1f}%",
                    'oil_price': f"${macro_factors.oil_prices:.0f}/bbl",
                    'consumer_confidence': f"{macro_factors.consumer_confidence:.1f}"
                },
                'sector_analysis': {
                    'sector': sector_analysis.sector,
                    'interest_rate_sensitivity': sector_analysis.interest_rate_sensitivity,
                    'gdp_correlation': sector_analysis.gdp_correlation,
                    'recommended_allocation': sector_analysis.recommended_allocation,
                    'cycle_position': sector_analysis.current_cycle_position
                },
                'valuation_adjustments': {
                    'interest_rate_impact': valuation_adjustment.interest_rate_adjustment,
                    'inflation_impact': valuation_adjustment.inflation_adjustment,
                    'currency_impact': valuation_adjustment.currency_adjustment,
                    'risk_premium_impact': valuation_adjustment.risk_premium_adjustment
                },
                'scenario_analysis': {
                    'bull_case': scenarios.get('bull', {}).final_adjusted_valuation,
                    'bear_case': scenarios.get('bear', {}).final_adjusted_valuation,
                    'stress_case': scenarios.get('stress', {}).final_adjusted_valuation
                },
                'recommendations': self._generate_macro_recommendations(
                    valuation_adjustment, sector_analysis, macro_factors
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating macro integration report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_macro_recommendations(self, valuation_adjustment: MacroValuationAdjustment,
                                      sector_analysis: SectorImpactAnalysis,
                                      macro_factors: MacroEconomicFactors) -> List[str]:
        """Generate actionable macroeconomic recommendations"""
        recommendations = []
        
        # Valuation-based recommendations
        adjustment_magnitude = abs(valuation_adjustment.final_adjusted_valuation - valuation_adjustment.base_valuation)
        if adjustment_magnitude > valuation_adjustment.base_valuation * 0.1:
            if valuation_adjustment.final_adjusted_valuation > valuation_adjustment.base_valuation:
                recommendations.append("Macro environment is favorable - consider increasing position size")
            else:
                recommendations.append("Macro headwinds identified - consider reducing position size")
        
        # Interest rate recommendations
        if abs(valuation_adjustment.interest_rate_adjustment) > valuation_adjustment.base_valuation * 0.05:
            if macro_factors.interest_rates['saudi_policy_rate'] > 5:
                recommendations.append("High interest rates negatively impact sector - monitor rate policy closely")
            else:
                recommendations.append("Favorable interest rate environment supports valuations")
        
        # Sector allocation recommendations
        if sector_analysis.recommended_allocation == 'overweight':
            recommendations.append(f"Macro environment favors {sector_analysis.sector} sector - consider overweight allocation")
        elif sector_analysis.recommended_allocation == 'underweight':
            recommendations.append(f"Macro conditions challenge {sector_analysis.sector} sector - consider underweight allocation")
        
        # Oil price specific (Saudi market)
        if macro_factors.oil_prices > 90:
            recommendations.append("High oil prices support Saudi economy - positive for domestic sectors")
        elif macro_factors.oil_prices < 65:
            recommendations.append("Low oil prices pressure Saudi economy - focus on non-oil sectors")
        
        if not recommendations:
            recommendations.append("Current macro environment is neutral - maintain existing allocations")
        
        return recommendations