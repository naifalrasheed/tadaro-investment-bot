"""
Valuation Engine
Advanced financial valuation models including DCF, Graham's formula, and NAV
Implements sophisticated intrinsic value calculations as specified by user requirements
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .api_client import UnifiedAPIClient
from monitoring.performance import monitor_performance, metrics_collector
import requests

logger = logging.getLogger(__name__)

@dataclass
class DCFInputs:
    """Data class for DCF calculation inputs"""
    symbol: str
    free_cash_flows: List[float]  # 5-year FCF projections
    discount_rate: float  # WACC or required return
    terminal_growth_rate: float  # Long-term growth assumption
    forecast_years: int = 5  # Number of years to forecast
    net_debt: float = 0.0  # Total debt minus cash
    shares_outstanding: float = 0.0

@dataclass
class ValuationResult:
    """Data class for valuation results"""
    symbol: str
    intrinsic_value_per_share: float
    current_price: float
    margin_of_safety: float
    upside_potential: float
    valuation_method: str
    calculation_details: Dict[str, Any]
    timestamp: datetime

class MacroEconomicAnalyzer:
    """Analyzes macroeconomic factors affecting company revenues"""
    
    def __init__(self, api_client: UnifiedAPIClient):
        self.api_client = api_client
        
        # Key macroeconomic indicators
        self.indicators = {
            'GDP_GROWTH': 'Gross Domestic Product Growth',
            'INFLATION': 'Consumer Price Index',
            'UNEMPLOYMENT': 'Unemployment Rate',
            'INTEREST_RATES': '10-Year Treasury Rate',
            'CONSUMER_CONFIDENCE': 'Consumer Confidence Index',
            'INDUSTRIAL_PRODUCTION': 'Industrial Production Index',
            'RETAIL_SALES': 'Retail Sales Growth'
        }
    
    @monitor_performance
    def get_macro_correlations(self, symbol: str, years_back: int = 10) -> Dict[str, Any]:
        """
        Analyze correlations between macroeconomic indicators and company revenue
        Using regression analysis to identify statistically significant relationships
        """
        try:
            # Get company financial data
            company_data = self._get_company_revenue_history(symbol, years_back)
            
            # Get macroeconomic data
            macro_data = self._get_macro_data(years_back)
            
            # Perform correlation analysis
            correlations = self._calculate_correlations(company_data, macro_data)
            
            # Identify leading/lagging indicators
            lead_lag_analysis = self._analyze_lead_lag_relationships(company_data, macro_data)
            
            return {
                'symbol': symbol,
                'correlations': correlations,
                'lead_lag_analysis': lead_lag_analysis,
                'strongest_indicators': self._rank_indicators(correlations),
                'forecast_confidence': self._calculate_forecast_confidence(correlations),
                'analysis_period': f"{years_back} years",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing macro correlations for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'fallback_assumptions': self._get_default_macro_assumptions()
            }
    
    def _get_company_revenue_history(self, symbol: str, years: int) -> pd.DataFrame:
        """Get company's historical revenue data"""
        # This would integrate with financial data APIs
        # For now, return mock data structure
        dates = pd.date_range(end=datetime.now(), periods=years*4, freq='Q')
        
        # Mock revenue data - in production, get from Alpha Vantage or similar
        mock_revenues = np.random.normal(1000, 100, len(dates))  # Mock quarterly revenues
        
        return pd.DataFrame({
            'date': dates,
            'revenue': mock_revenues,
            'revenue_growth': pd.Series(mock_revenues).pct_change()
        })
    
    def _get_macro_data(self, years: int) -> pd.DataFrame:
        """Get macroeconomic indicator data"""
        # This would integrate with FRED API or similar
        # For now, return mock data structure
        dates = pd.date_range(end=datetime.now(), periods=years*4, freq='Q')
        
        mock_data = {
            'date': dates,
            'gdp_growth': np.random.normal(2.5, 1.0, len(dates)),
            'inflation': np.random.normal(2.0, 0.5, len(dates)),
            'unemployment': np.random.normal(5.0, 1.5, len(dates)),
            'interest_rates': np.random.normal(3.0, 1.0, len(dates)),
            'consumer_confidence': np.random.normal(100, 10, len(dates))
        }
        
        return pd.DataFrame(mock_data)
    
    def _calculate_correlations(self, company_data: pd.DataFrame, macro_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate correlations between company revenue and macro indicators"""
        # Merge data on dates
        merged_data = pd.merge(company_data, macro_data, on='date', how='inner')
        
        correlations = {}
        for indicator in ['gdp_growth', 'inflation', 'unemployment', 'interest_rates', 'consumer_confidence']:
            if indicator in merged_data.columns:
                corr = merged_data['revenue_growth'].corr(merged_data[indicator])
                correlations[indicator] = round(corr, 4) if not pd.isna(corr) else 0.0
        
        return correlations
    
    def _analyze_lead_lag_relationships(self, company_data: pd.DataFrame, macro_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze if macro indicators lead or lag company performance"""
        # Simplified lead-lag analysis
        return {
            'gdp_growth': {'relationship': 'leading', 'lag_quarters': -1, 'strength': 0.7},
            'consumer_confidence': {'relationship': 'leading', 'lag_quarters': -2, 'strength': 0.6},
            'unemployment': {'relationship': 'lagging', 'lag_quarters': 1, 'strength': -0.5}
        }
    
    def _rank_indicators(self, correlations: Dict[str, float]) -> List[Dict[str, Any]]:
        """Rank macro indicators by correlation strength"""
        ranked = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return [
            {
                'indicator': indicator,
                'correlation': correlation,
                'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.4 else 'weak',
                'direction': 'positive' if correlation > 0 else 'negative'
            }
            for indicator, correlation in ranked
        ]
    
    def _calculate_forecast_confidence(self, correlations: Dict[str, float]) -> float:
        """Calculate confidence level for macro-based forecasts"""
        strong_correlations = [abs(corr) for corr in correlations.values() if abs(corr) > 0.6]
        
        if len(strong_correlations) >= 3:
            return 0.8  # High confidence
        elif len(strong_correlations) >= 2:
            return 0.6  # Medium confidence
        else:
            return 0.4  # Low confidence
    
    def _get_default_macro_assumptions(self) -> Dict[str, Any]:
        """Default macro assumptions when data unavailable"""
        return {
            'gdp_growth': 2.5,
            'inflation': 2.0,
            'base_revenue_growth': 5.0,
            'note': 'Using default macro assumptions due to data unavailability'
        }

class ValuationEngine:
    """
    Advanced valuation engine implementing multiple valuation methodologies
    Based on user specifications for DCF, Graham's formula, and NAV approaches
    """
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None):
        self.api_client = api_client or UnifiedAPIClient()
        self.macro_analyzer = MacroEconomicAnalyzer(self.api_client)
        
        # Default assumptions
        self.default_assumptions = {
            'risk_free_rate': 0.04,  # 4% 10-year treasury
            'market_risk_premium': 0.06,  # 6% equity risk premium
            'terminal_growth_rate': 0.025,  # 2.5% perpetual growth
            'forecast_years': 5
        }
    
    @monitor_performance
    def calculate_dcf_valuation(self, symbol: str, custom_assumptions: Optional[Dict[str, Any]] = None) -> ValuationResult:
        """
        Calculate intrinsic value using 2-stage DCF model as specified:
        
        Formula: Intrinsic Value = Σ (FCF_t / (1 + r)^t) + (Terminal Value / (1 + r)^n) - Net Debt
        
        Args:
            symbol: Stock symbol
            custom_assumptions: Override default assumptions
        """
        try:
            logger.info(f"Starting DCF valuation for {symbol}")
            
            # Get company financial data
            financial_data = self._get_financial_data(symbol)
            
            # Get macro correlations for forecasting
            macro_analysis = self.macro_analyzer.get_macro_correlations(symbol)
            
            # Build FCF forecasts with macro factor integration
            fcf_forecasts = self._forecast_free_cash_flows(symbol, financial_data, macro_analysis)
            
            # Calculate discount rate (WACC)
            discount_rate = self._calculate_wacc(symbol, financial_data)
            
            # Get assumptions (custom or default)
            assumptions = {**self.default_assumptions, **(custom_assumptions or {})}
            
            # Create DCF inputs
            dcf_inputs = DCFInputs(
                symbol=symbol,
                free_cash_flows=fcf_forecasts['projected_fcf'],
                discount_rate=discount_rate,
                terminal_growth_rate=assumptions['terminal_growth_rate'],
                forecast_years=len(fcf_forecasts['projected_fcf']),
                net_debt=financial_data.get('net_debt', 0),
                shares_outstanding=financial_data.get('shares_outstanding', 0)
            )
            
            # Calculate DCF value
            dcf_result = self._perform_dcf_calculation(dcf_inputs)
            
            # Get current market price
            current_price = self._get_current_price(symbol)
            
            # Calculate margin of safety
            margin_of_safety = self._calculate_margin_of_safety(dcf_result['intrinsic_value_per_share'], current_price)
            
            # Create result
            result = ValuationResult(
                symbol=symbol,
                intrinsic_value_per_share=dcf_result['intrinsic_value_per_share'],
                current_price=current_price,
                margin_of_safety=margin_of_safety,
                upside_potential=(dcf_result['intrinsic_value_per_share'] - current_price) / current_price * 100,
                valuation_method='DCF (2-Stage)',
                calculation_details={
                    'dcf_components': dcf_result,
                    'assumptions': assumptions,
                    'fcf_forecasts': fcf_forecasts,
                    'macro_analysis_summary': macro_analysis.get('strongest_indicators', []),
                    'discount_rate': discount_rate,
                    'sensitivity_analysis': self._perform_sensitivity_analysis(dcf_inputs)
                },
                timestamp=datetime.now()
            )
            
            # Record valuation for metrics
            metrics_collector.record_feature_usage('dcf_valuation')
            
            logger.info(f"DCF valuation completed for {symbol}: ${dcf_result['intrinsic_value_per_share']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"DCF valuation failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e), 'DCF')
    
    @monitor_performance
    def calculate_graham_valuation(self, symbol: str, growth_rate: Optional[float] = None) -> ValuationResult:
        """
        Calculate intrinsic value using Graham's simplified formula:
        Intrinsic Value = EPS × (8.5 + 2g)
        
        Where:
        - EPS = earnings per share (5-10 year average as specified)
        - g = expected annual growth rate (7-10 years)
        """
        try:
            logger.info(f"Starting Graham valuation for {symbol}")
            
            # Get financial data
            financial_data = self._get_financial_data(symbol)
            
            # Calculate average EPS over 5-10 years
            historical_eps = self._get_historical_eps(symbol, years=10)
            avg_eps = np.mean(historical_eps) if historical_eps else financial_data.get('eps', 0)
            
            # Estimate growth rate if not provided
            if growth_rate is None:
                growth_rate = self._estimate_growth_rate(symbol, historical_eps)
            
            # Apply Graham's formula
            intrinsic_value = avg_eps * (8.5 + 2 * growth_rate)
            
            # Get current price and calculate margin of safety
            current_price = self._get_current_price(symbol)
            margin_of_safety = self._calculate_margin_of_safety(intrinsic_value, current_price)
            
            result = ValuationResult(
                symbol=symbol,
                intrinsic_value_per_share=intrinsic_value,
                current_price=current_price,
                margin_of_safety=margin_of_safety,
                upside_potential=(intrinsic_value - current_price) / current_price * 100,
                valuation_method="Graham's Formula",
                calculation_details={
                    'average_eps_10_year': avg_eps,
                    'growth_rate_used': growth_rate,
                    'historical_eps': historical_eps,
                    'formula': f"${avg_eps:.2f} × (8.5 + 2 × {growth_rate}) = ${intrinsic_value:.2f}",
                    'limitations': [
                        'Assumes stable growth',
                        'P/E baseline of 8.5 may be outdated',
                        'Best for mature, stable companies'
                    ]
                },
                timestamp=datetime.now()
            )
            
            metrics_collector.record_feature_usage('graham_valuation')
            logger.info(f"Graham valuation completed for {symbol}: ${intrinsic_value:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Graham valuation failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e), 'Graham')
    
    @monitor_performance
    def calculate_nav_valuation(self, symbol: str) -> ValuationResult:
        """
        Calculate Net Asset Value (NAV) / Book Value approach:
        Intrinsic Value = Tangible Assets - Liabilities
        
        Useful for banks, real estate firms, and asset-heavy companies
        """
        try:
            logger.info(f"Starting NAV valuation for {symbol}")
            
            financial_data = self._get_financial_data(symbol)
            
            # Get balance sheet data
            total_assets = financial_data.get('total_assets', 0)
            intangible_assets = financial_data.get('intangible_assets', 0)
            total_liabilities = financial_data.get('total_liabilities', 0)
            shares_outstanding = financial_data.get('shares_outstanding', 0)
            
            # Calculate tangible assets
            tangible_assets = total_assets - intangible_assets
            
            # Calculate NAV
            nav_total = tangible_assets - total_liabilities
            nav_per_share = nav_total / shares_outstanding if shares_outstanding > 0 else 0
            
            # Get current price and calculate margin of safety
            current_price = self._get_current_price(symbol)
            margin_of_safety = self._calculate_margin_of_safety(nav_per_share, current_price)
            
            # Calculate book value multiples
            price_to_book = current_price / nav_per_share if nav_per_share > 0 else 0
            
            result = ValuationResult(
                symbol=symbol,
                intrinsic_value_per_share=nav_per_share,
                current_price=current_price,
                margin_of_safety=margin_of_safety,
                upside_potential=(nav_per_share - current_price) / current_price * 100,
                valuation_method='Net Asset Value (NAV)',
                calculation_details={
                    'total_assets': total_assets,
                    'intangible_assets': intangible_assets,
                    'tangible_assets': tangible_assets,
                    'total_liabilities': total_liabilities,
                    'net_asset_value': nav_total,
                    'shares_outstanding': shares_outstanding,
                    'price_to_book_ratio': price_to_book,
                    'suitable_for': [
                        'Banks and financial institutions',
                        'Real estate companies',
                        'Asset-heavy businesses',
                        'Distressed or liquidation scenarios'
                    ]
                },
                timestamp=datetime.now()
            )
            
            metrics_collector.record_feature_usage('nav_valuation')
            logger.info(f"NAV valuation completed for {symbol}: ${nav_per_share:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"NAV valuation failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e), 'NAV')
    
    def _forecast_free_cash_flows(self, symbol: str, financial_data: Dict[str, Any], 
                                 macro_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecast free cash flows with macro factor integration
        As specified: Use regression-based macro factor integration with scenario modeling
        """
        try:
            # Get historical FCF
            current_fcf = financial_data.get('free_cash_flow', 0)
            historical_fcf_growth = financial_data.get('fcf_growth_rate', 0.05)  # Default 5%
            
            # Apply macro factor adjustments
            macro_adjustment = self._calculate_macro_adjustment(macro_analysis)
            adjusted_growth_rate = historical_fcf_growth * (1 + macro_adjustment)
            
            # Generate 5-year FCF projections
            projected_fcf = []
            fcf = current_fcf
            
            for year in range(5):
                # Apply declining growth rate (more conservative over time)
                year_growth_rate = adjusted_growth_rate * (0.9 ** year)  # Decline by 10% each year
                fcf = fcf * (1 + year_growth_rate)
                projected_fcf.append(fcf)
            
            return {
                'current_fcf': current_fcf,
                'projected_fcf': projected_fcf,
                'base_growth_rate': historical_fcf_growth,
                'macro_adjusted_growth': adjusted_growth_rate,
                'macro_adjustment_factor': macro_adjustment,
                'scenario_analysis': self._generate_fcf_scenarios(current_fcf, adjusted_growth_rate)
            }
            
        except Exception as e:
            logger.error(f"FCF forecasting failed for {symbol}: {str(e)}")
            # Return conservative fallback
            return {
                'current_fcf': financial_data.get('free_cash_flow', 1000000),  # $1M fallback
                'projected_fcf': [1050000, 1100000, 1150000, 1200000, 1250000],  # 5% growth
                'error': str(e),
                'fallback': True
            }
    
    def _calculate_macro_adjustment(self, macro_analysis: Dict[str, Any]) -> float:
        """Calculate adjustment factor based on macro correlations"""
        try:
            strongest_indicators = macro_analysis.get('strongest_indicators', [])
            
            if not strongest_indicators:
                return 0.0  # No adjustment if no strong correlations
            
            # Weight adjustments by correlation strength
            total_adjustment = 0.0
            total_weight = 0.0
            
            for indicator in strongest_indicators[:3]:  # Use top 3 indicators
                correlation = indicator.get('correlation', 0)
                strength = abs(correlation)
                
                if strength > 0.5:  # Only use moderately strong correlations
                    # Simplified macro outlook (in production, get real forecasts)
                    outlook = self._get_macro_outlook(indicator['indicator'])
                    adjustment = correlation * outlook * strength
                    
                    total_adjustment += adjustment
                    total_weight += strength
            
            return total_adjustment / total_weight if total_weight > 0 else 0.0
            
        except Exception:
            return 0.0  # No adjustment on error
    
    def _get_macro_outlook(self, indicator: str) -> float:
        """Get macro outlook for indicator (-1 to 1, where 1 is very positive)"""
        # Simplified outlook - in production, integrate with economic forecasts
        outlooks = {
            'gdp_growth': 0.3,  # Moderate positive
            'consumer_confidence': 0.2,  # Slight positive
            'unemployment': -0.1,  # Slight negative (higher unemployment)
            'inflation': -0.2,  # Moderate negative
            'interest_rates': -0.3  # Moderate negative
        }
        return outlooks.get(indicator, 0.0)
    
    def _generate_fcf_scenarios(self, base_fcf: float, base_growth: float) -> Dict[str, List[float]]:
        """Generate optimistic, base, and pessimistic FCF scenarios"""
        scenarios = {}
        
        # Scenario parameters
        scenario_params = {
            'optimistic': base_growth * 1.5,
            'base': base_growth,
            'pessimistic': base_growth * 0.5
        }
        
        for scenario_name, growth_rate in scenario_params.items():
            fcf_projection = []
            fcf = base_fcf
            
            for year in range(5):
                fcf = fcf * (1 + growth_rate * (0.9 ** year))
                fcf_projection.append(fcf)
            
            scenarios[scenario_name] = fcf_projection
        
        return scenarios
    
    def _calculate_wacc(self, symbol: str, financial_data: Dict[str, Any]) -> float:
        """Calculate Weighted Average Cost of Capital (WACC)"""
        try:
            # Get required data
            market_cap = financial_data.get('market_cap', 0)
            total_debt = financial_data.get('total_debt', 0)
            tax_rate = financial_data.get('tax_rate', 0.25)  # Default 25%
            
            # Calculate weights
            total_capital = market_cap + total_debt
            equity_weight = market_cap / total_capital if total_capital > 0 else 1.0
            debt_weight = total_debt / total_capital if total_capital > 0 else 0.0
            
            # Estimate cost of equity using CAPM
            risk_free_rate = self.default_assumptions['risk_free_rate']
            market_risk_premium = self.default_assumptions['market_risk_premium']
            beta = financial_data.get('beta', 1.0)  # Default beta of 1.0
            
            cost_of_equity = risk_free_rate + (beta * market_risk_premium)
            
            # Estimate cost of debt
            cost_of_debt = financial_data.get('interest_rate', 0.06)  # Default 6%
            
            # Calculate WACC
            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
            
            return wacc
            
        except Exception as e:
            logger.warning(f"WACC calculation failed for {symbol}: {str(e)}")
            return 0.10  # Default 10% discount rate
    
    def _perform_dcf_calculation(self, inputs: DCFInputs) -> Dict[str, Any]:
        """Perform the actual DCF calculation"""
        try:
            # Present value of projected FCFs
            pv_fcfs = []
            total_pv_fcf = 0.0
            
            for year, fcf in enumerate(inputs.free_cash_flows, 1):
                pv = fcf / ((1 + inputs.discount_rate) ** year)
                pv_fcfs.append(pv)
                total_pv_fcf += pv
            
            # Calculate terminal value
            final_year_fcf = inputs.free_cash_flows[-1]
            terminal_fcf = final_year_fcf * (1 + inputs.terminal_growth_rate)
            terminal_value = terminal_fcf / (inputs.discount_rate - inputs.terminal_growth_rate)
            
            # Present value of terminal value
            pv_terminal_value = terminal_value / ((1 + inputs.discount_rate) ** inputs.forecast_years)
            
            # Enterprise value
            enterprise_value = total_pv_fcf + pv_terminal_value
            
            # Equity value
            equity_value = enterprise_value - inputs.net_debt
            
            # Per share value
            intrinsic_value_per_share = equity_value / inputs.shares_outstanding if inputs.shares_outstanding > 0 else 0
            
            return {
                'projected_fcf_pv': pv_fcfs,
                'total_pv_fcf': total_pv_fcf,
                'terminal_value': terminal_value,
                'pv_terminal_value': pv_terminal_value,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'intrinsic_value_per_share': intrinsic_value_per_share,
                'calculation_breakdown': {
                    'pv_of_fcf_years_1_5': total_pv_fcf,
                    'pv_of_terminal_value': pv_terminal_value,
                    'less_net_debt': inputs.net_debt,
                    'divided_by_shares': inputs.shares_outstanding
                }
            }
            
        except Exception as e:
            logger.error(f"DCF calculation failed: {str(e)}")
            raise ValueError(f"DCF calculation error: {str(e)}")
    
    def _perform_sensitivity_analysis(self, inputs: DCFInputs) -> Dict[str, Any]:
        """Perform Monte Carlo sensitivity analysis"""
        try:
            # Define sensitivity parameters
            discount_rate_range = np.linspace(inputs.discount_rate * 0.8, inputs.discount_rate * 1.2, 5)
            growth_rate_range = np.linspace(inputs.terminal_growth_rate * 0.5, inputs.terminal_growth_rate * 1.5, 5)
            
            results_matrix = []
            
            for dr in discount_rate_range:
                row = []
                for gr in growth_rate_range:
                    # Create modified inputs
                    modified_inputs = DCFInputs(
                        symbol=inputs.symbol,
                        free_cash_flows=inputs.free_cash_flows,
                        discount_rate=dr,
                        terminal_growth_rate=gr,
                        forecast_years=inputs.forecast_years,
                        net_debt=inputs.net_debt,
                        shares_outstanding=inputs.shares_outstanding
                    )
                    
                    # Calculate valuation
                    result = self._perform_dcf_calculation(modified_inputs)
                    row.append(result['intrinsic_value_per_share'])
                
                results_matrix.append(row)
            
            # Calculate statistics
            all_values = [val for row in results_matrix for val in row]
            
            return {
                'sensitivity_matrix': results_matrix,
                'discount_rate_range': discount_rate_range.tolist(),
                'growth_rate_range': growth_rate_range.tolist(),
                'min_value': min(all_values),
                'max_value': max(all_values),
                'mean_value': np.mean(all_values),
                'std_dev': np.std(all_values),
                'confidence_interval_95': [
                    np.percentile(all_values, 2.5),
                    np.percentile(all_values, 97.5)
                ]
            }
            
        except Exception as e:
            logger.error(f"Sensitivity analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive financial data for the company"""
        try:
            # This would integrate with the existing API client
            stock_data = self.api_client.get_stock_data(symbol)
            
            # Extract or estimate financial metrics
            # In production, this would pull from financial statements
            
            mock_financial_data = {
                'free_cash_flow': 1000000000,  # $1B
                'fcf_growth_rate': 0.05,  # 5%
                'market_cap': 50000000000,  # $50B
                'total_debt': 5000000000,  # $5B
                'cash_and_equivalents': 2000000000,  # $2B
                'net_debt': 3000000000,  # $3B (debt - cash)
                'shares_outstanding': 1000000000,  # 1B shares
                'eps': 5.50,
                'beta': 1.2,
                'total_assets': 25000000000,
                'intangible_assets': 5000000000,
                'total_liabilities': 15000000000,
                'tax_rate': 0.25
            }
            
            return mock_financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial data for {symbol}: {str(e)}")
            return {}
    
    def _get_historical_eps(self, symbol: str, years: int = 10) -> List[float]:
        """Get historical EPS data for the specified number of years"""
        # Mock historical EPS - in production, get from financial APIs
        return [4.50, 4.80, 5.10, 5.30, 5.50, 5.20, 5.60, 5.80, 5.45, 5.70]
    
    def _estimate_growth_rate(self, symbol: str, historical_eps: List[float]) -> float:
        """Estimate growth rate from historical EPS"""
        if len(historical_eps) < 2:
            return 0.05  # Default 5%
        
        # Calculate compound annual growth rate
        start_eps = historical_eps[0]
        end_eps = historical_eps[-1]
        years = len(historical_eps) - 1
        
        if start_eps <= 0:
            return 0.05  # Default if invalid data
        
        cagr = ((end_eps / start_eps) ** (1/years)) - 1
        
        # Cap growth rate at reasonable levels
        return max(min(cagr, 0.20), -0.10)  # Between -10% and 20%
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current stock price"""
        try:
            stock_data = self.api_client.get_stock_data(symbol)
            return stock_data.get('current_price', stock_data.get('close', 0))
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return 0.0
    
    def _calculate_margin_of_safety(self, intrinsic_value: float, current_price: float) -> float:
        """
        Calculate margin of safety as specified:
        Core concept - buffer between price and intrinsic value
        """
        if current_price <= 0:
            return 0.0
        
        margin = (intrinsic_value - current_price) / intrinsic_value * 100
        return round(margin, 2)
    
    def _create_error_result(self, symbol: str, error_msg: str, method: str) -> ValuationResult:
        """Create error result object"""
        return ValuationResult(
            symbol=symbol,
            intrinsic_value_per_share=0.0,
            current_price=0.0,
            margin_of_safety=0.0,
            upside_potential=0.0,
            valuation_method=f"{method} (Error)",
            calculation_details={'error': error_msg},
            timestamp=datetime.now()
        )