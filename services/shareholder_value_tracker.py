"""
Shareholder Value Tracking Service

This service analyzes how well management creates value for shareholders through:
1. Total shareholder return (TSR) analysis
2. Dividend policy consistency and growth
3. Share buyback programs effectiveness
4. Capital allocation efficiency
5. ROE and ROIC trends vs cost of capital
6. Value creation vs value destruction analysis
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
class ShareholderValueMetrics:
    """Container for shareholder value metrics"""
    symbol: str
    analysis_date: datetime
    tsr_1y: float
    tsr_3y: float
    tsr_5y: float
    dividend_yield: float
    dividend_growth_rate: float
    dividend_consistency_score: float
    buyback_yield: float
    buyback_effectiveness: float
    capital_allocation_score: float
    roe_trend: str
    roic_trend: str
    value_creation_score: float
    peer_comparison_rank: int
    value_drivers: List[str]
    value_destroyers: List[str]

@dataclass
class DividendAnalysis:
    """Detailed dividend policy analysis"""
    dividend_history: List[Dict[str, Any]]
    growth_rate: float
    consistency_years: int
    payout_ratio: float
    coverage_ratio: float
    sustainability_score: float
    policy_changes: List[Dict[str, Any]]

@dataclass
class CapitalAllocation:
    """Capital allocation efficiency analysis"""
    reinvestment_rate: float
    roic_on_incremental_capital: float
    capex_efficiency: float
    acquisition_track_record: float
    debt_management_score: float
    cash_management_score: float
    overall_score: float

class ShareholderValueTracker:
    """
    Comprehensive shareholder value tracking and analysis
    
    Evaluates management's effectiveness in creating shareholder value
    through various metrics and long-term trend analysis
    """
    
    def __init__(self, saudi_service: SaudiMarketService):
        self.saudi_service = saudi_service
        self.financial_calc = FinancialCalculations()
        
    def analyze_shareholder_value(self, symbol: str, years: int = 5) -> ShareholderValueMetrics:
        """
        Comprehensive shareholder value analysis
        
        Args:
            symbol: Stock symbol to analyze
            years: Number of years for historical analysis
            
        Returns:
            ShareholderValueMetrics with complete analysis
        """
        try:
            logger.info(f"Starting shareholder value analysis for {symbol}")
            
            # Get comprehensive financial data
            stock_data = self.saudi_service.get_stock_data(symbol, years * 365)
            financial_data = self.saudi_service.get_financial_statements(symbol)
            
            if not stock_data or not financial_data:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Calculate Total Shareholder Return (TSR)
            tsr_metrics = self._calculate_tsr_metrics(symbol, stock_data)
            
            # Analyze dividend policy
            dividend_analysis = self._analyze_dividend_policy(symbol, financial_data)
            
            # Evaluate share buyback programs
            buyback_metrics = self._analyze_buyback_programs(symbol, financial_data)
            
            # Assess capital allocation efficiency
            capital_allocation = self._analyze_capital_allocation(symbol, financial_data)
            
            # Calculate profitability trends
            roe_trend, roic_trend = self._analyze_profitability_trends(financial_data)
            
            # Overall value creation score
            value_creation_score = self._calculate_value_creation_score(
                tsr_metrics, dividend_analysis, buyback_metrics, capital_allocation
            )
            
            # Identify value drivers and destroyers
            drivers, destroyers = self._identify_value_factors(
                tsr_metrics, dividend_analysis, capital_allocation, financial_data
            )
            
            # Peer comparison ranking
            peer_rank = self._calculate_peer_ranking(symbol, value_creation_score)
            
            return ShareholderValueMetrics(
                symbol=symbol,
                analysis_date=datetime.now(),
                tsr_1y=tsr_metrics['1y'],
                tsr_3y=tsr_metrics['3y'],
                tsr_5y=tsr_metrics['5y'],
                dividend_yield=dividend_analysis.dividend_history[-1]['yield'] if dividend_analysis.dividend_history else 0,
                dividend_growth_rate=dividend_analysis.growth_rate,
                dividend_consistency_score=dividend_analysis.consistency_years / years * 100,
                buyback_yield=buyback_metrics['yield'],
                buyback_effectiveness=buyback_metrics['effectiveness'],
                capital_allocation_score=capital_allocation.overall_score,
                roe_trend=roe_trend,
                roic_trend=roic_trend,
                value_creation_score=value_creation_score,
                peer_comparison_rank=peer_rank,
                value_drivers=drivers,
                value_destroyers=destroyers
            )
            
        except Exception as e:
            logger.error(f"Error in shareholder value analysis for {symbol}: {str(e)}")
            raise
    
    def _calculate_tsr_metrics(self, symbol: str, stock_data: List[Dict]) -> Dict[str, float]:
        """Calculate Total Shareholder Return for different periods"""
        try:
            if len(stock_data) < 252:  # Need at least 1 year of data
                return {'1y': 0, '3y': 0, '5y': 0}
            
            current_price = stock_data[0]['close']
            
            # Calculate TSR including dividends
            tsr_1y = self._calculate_period_tsr(stock_data, 252, current_price)  # 1 year
            tsr_3y = self._calculate_period_tsr(stock_data, 252 * 3, current_price)  # 3 years
            tsr_5y = self._calculate_period_tsr(stock_data, 252 * 5, current_price)  # 5 years
            
            return {
                '1y': tsr_1y,
                '3y': tsr_3y,
                '5y': tsr_5y
            }
            
        except Exception as e:
            logger.error(f"Error calculating TSR metrics: {str(e)}")
            return {'1y': 0, '3y': 0, '5y': 0}
    
    def _calculate_period_tsr(self, stock_data: List[Dict], days_back: int, current_price: float) -> float:
        """Calculate TSR for a specific period"""
        if len(stock_data) <= days_back:
            return 0
        
        start_price = stock_data[min(days_back, len(stock_data) - 1)]['close']
        
        # Price appreciation
        price_return = (current_price - start_price) / start_price
        
        # Estimate dividend yield (simplified - would need actual dividend data)
        estimated_dividend_yield = 0.03  # Assume 3% average dividend yield
        
        # Total return
        total_return = price_return + (estimated_dividend_yield * (days_back / 252))
        
        # Annualize the return
        years = days_back / 252
        if years > 0:
            annualized_return = (1 + total_return) ** (1/years) - 1
        else:
            annualized_return = total_return
        
        return annualized_return * 100  # Return as percentage
    
    def _analyze_dividend_policy(self, symbol: str, financial_data: Dict) -> DividendAnalysis:
        """Analyze dividend policy and consistency"""
        try:
            # Extract dividend information from financial statements
            dividend_history = []
            
            # Get cash flow statements for dividend payments
            cash_flows = financial_data.get('cash_flow', [])
            income_statements = financial_data.get('income_statement', [])
            
            for i, cf in enumerate(cash_flows[:5]):  # Last 5 years
                try:
                    dividends_paid = abs(cf.get('dividends_paid', 0))
                    
                    if i < len(income_statements):
                        net_income = income_statements[i].get('net_income', 1)
                        shares_outstanding = income_statements[i].get('shares_outstanding', 1000000)
                        
                        if shares_outstanding > 0:
                            dps = dividends_paid / shares_outstanding
                            payout_ratio = (dividends_paid / net_income) if net_income > 0 else 0
                            
                            dividend_history.append({
                                'year': cf.get('date', f'Year_{i}'),
                                'dividends_paid': dividends_paid,
                                'dps': dps,
                                'payout_ratio': payout_ratio,
                                'yield': dps * 100 / 50  # Estimated yield (simplified)
                            })
                except (KeyError, TypeError, ZeroDivisionError):
                    continue
            
            # Calculate growth rate
            growth_rate = self._calculate_dividend_growth_rate(dividend_history)
            
            # Consistency analysis
            consistency_years = self._analyze_dividend_consistency(dividend_history)
            
            # Coverage and sustainability
            latest_payout = dividend_history[0]['payout_ratio'] if dividend_history else 0
            coverage_ratio = 1 / latest_payout if latest_payout > 0 else float('inf')
            sustainability_score = min(100, (1 - latest_payout) * 100) if latest_payout <= 1 else 0
            
            return DividendAnalysis(
                dividend_history=dividend_history,
                growth_rate=growth_rate,
                consistency_years=consistency_years,
                payout_ratio=latest_payout,
                coverage_ratio=coverage_ratio,
                sustainability_score=sustainability_score,
                policy_changes=self._identify_policy_changes(dividend_history)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing dividend policy: {str(e)}")
            return DividendAnalysis([], 0, 0, 0, 0, 0, [])
    
    def _calculate_dividend_growth_rate(self, dividend_history: List[Dict]) -> float:
        """Calculate compound annual growth rate of dividends"""
        if len(dividend_history) < 2:
            return 0
        
        try:
            # Sort by year (most recent first)
            sorted_history = sorted(dividend_history, key=lambda x: x['year'], reverse=True)
            
            latest_dps = sorted_history[0]['dps']
            earliest_dps = sorted_history[-1]['dps']
            years = len(sorted_history) - 1
            
            if earliest_dps > 0 and years > 0:
                cagr = (latest_dps / earliest_dps) ** (1/years) - 1
                return cagr * 100
            
        except (KeyError, TypeError, ZeroDivisionError):
            pass
        
        return 0
    
    def _analyze_dividend_consistency(self, dividend_history: List[Dict]) -> int:
        """Count consecutive years of dividend payments"""
        if not dividend_history:
            return 0
        
        consistent_years = 0
        for dividend in dividend_history:
            if dividend['dividends_paid'] > 0:
                consistent_years += 1
            else:
                break
        
        return consistent_years
    
    def _identify_policy_changes(self, dividend_history: List[Dict]) -> List[Dict[str, Any]]:
        """Identify significant dividend policy changes"""
        changes = []
        
        if len(dividend_history) < 2:
            return changes
        
        for i in range(len(dividend_history) - 1):
            current = dividend_history[i]
            previous = dividend_history[i + 1]
            
            # Check for cuts, increases, or eliminations
            dps_change = (current['dps'] - previous['dps']) / previous['dps'] if previous['dps'] > 0 else 0
            
            if abs(dps_change) > 0.2:  # 20% change threshold
                change_type = "increase" if dps_change > 0 else "cut"
                changes.append({
                    'year': current['year'],
                    'type': change_type,
                    'magnitude': dps_change * 100,
                    'description': f"Dividend {change_type} of {abs(dps_change*100):.1f}%"
                })
        
        return changes
    
    def _analyze_buyback_programs(self, symbol: str, financial_data: Dict) -> Dict[str, float]:
        """Analyze share buyback programs effectiveness"""
        try:
            cash_flows = financial_data.get('cash_flow', [])
            balance_sheets = financial_data.get('balance_sheet', [])
            
            total_buybacks = 0
            share_reduction = 0
            
            # Calculate buybacks over the period
            for i, cf in enumerate(cash_flows[:5]):
                buybacks = abs(cf.get('stock_repurchase', 0))
                total_buybacks += buybacks
                
                # Track share count reduction
                if i < len(balance_sheets) - 1:
                    current_shares = balance_sheets[i].get('shares_outstanding', 0)
                    previous_shares = balance_sheets[i + 1].get('shares_outstanding', current_shares)
                    
                    if previous_shares > 0:
                        share_reduction += (previous_shares - current_shares) / previous_shares
            
            # Calculate metrics
            market_cap = 10000000000  # Simplified - would need actual market cap
            buyback_yield = (total_buybacks / 5) / market_cap * 100  # Annual average
            
            # Effectiveness score based on share reduction and timing
            effectiveness = min(100, share_reduction * 100) if share_reduction > 0 else 0
            
            return {
                'yield': buyback_yield,
                'effectiveness': effectiveness,
                'total_buybacks': total_buybacks,
                'share_reduction': share_reduction * 100
            }
            
        except Exception as e:
            logger.error(f"Error analyzing buyback programs: {str(e)}")
            return {'yield': 0, 'effectiveness': 0, 'total_buybacks': 0, 'share_reduction': 0}
    
    def _analyze_capital_allocation(self, symbol: str, financial_data: Dict) -> CapitalAllocation:
        """Analyze capital allocation efficiency"""
        try:
            income_statements = financial_data.get('income_statement', [])
            balance_sheets = financial_data.get('balance_sheet', [])
            cash_flows = financial_data.get('cash_flow', [])
            
            if not all([income_statements, balance_sheets, cash_flows]):
                return CapitalAllocation(0, 0, 0, 0, 0, 0, 0)
            
            # Calculate reinvestment rate
            reinvestment_rate = self._calculate_reinvestment_rate(income_statements, cash_flows)
            
            # ROIC on incremental capital
            roic_incremental = self._calculate_incremental_roic(income_statements, balance_sheets)
            
            # Capex efficiency
            capex_efficiency = self._calculate_capex_efficiency(income_statements, cash_flows)
            
            # Debt management score
            debt_score = self._analyze_debt_management(balance_sheets, income_statements)
            
            # Cash management score
            cash_score = self._analyze_cash_management(balance_sheets, cash_flows)
            
            # Overall score (weighted average)
            overall_score = (
                reinvestment_rate * 0.2 +
                roic_incremental * 0.3 +
                capex_efficiency * 0.2 +
                debt_score * 0.15 +
                cash_score * 0.15
            )
            
            return CapitalAllocation(
                reinvestment_rate=reinvestment_rate,
                roic_on_incremental_capital=roic_incremental,
                capex_efficiency=capex_efficiency,
                acquisition_track_record=50,  # Simplified - would need M&A data
                debt_management_score=debt_score,
                cash_management_score=cash_score,
                overall_score=overall_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing capital allocation: {str(e)}")
            return CapitalAllocation(0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_reinvestment_rate(self, income_statements: List, cash_flows: List) -> float:
        """Calculate reinvestment rate"""
        if not income_statements or not cash_flows:
            return 0
        
        try:
            latest_income = income_statements[0]
            latest_cf = cash_flows[0]
            
            net_income = latest_income.get('net_income', 0)
            capex = abs(latest_cf.get('capital_expenditure', 0))
            change_wc = latest_cf.get('change_in_working_capital', 0)
            
            if net_income > 0:
                reinvestment = (capex + change_wc) / net_income
                return min(100, reinvestment * 100)
            
        except (KeyError, TypeError, ZeroDivisionError):
            pass
        
        return 0
    
    def _calculate_incremental_roic(self, income_statements: List, balance_sheets: List) -> float:
        """Calculate ROIC on incremental invested capital"""
        if len(income_statements) < 2 or len(balance_sheets) < 2:
            return 0
        
        try:
            # Change in operating income
            current_oi = income_statements[0].get('operating_income', 0)
            previous_oi = income_statements[1].get('operating_income', 0)
            delta_oi = current_oi - previous_oi
            
            # Change in invested capital
            current_ic = balance_sheets[0].get('total_assets', 0) - balance_sheets[0].get('current_liabilities', 0)
            previous_ic = balance_sheets[1].get('total_assets', 0) - balance_sheets[1].get('current_liabilities', 0)
            delta_ic = current_ic - previous_ic
            
            if delta_ic > 0:
                incremental_roic = (delta_oi / delta_ic) * 100
                return max(0, min(100, incremental_roic))
            
        except (KeyError, TypeError, ZeroDivisionError):
            pass
        
        return 0
    
    def _calculate_capex_efficiency(self, income_statements: List, cash_flows: List) -> float:
        """Calculate capital expenditure efficiency"""
        if not income_statements or not cash_flows:
            return 0
        
        try:
            # Average capex vs revenue growth correlation
            capex_efficiency = 50  # Simplified calculation
            
            # Would implement detailed analysis of:
            # - Capex as % of revenue
            # - Revenue growth per dollar of capex
            # - Asset utilization improvements
            
            return capex_efficiency
            
        except Exception:
            return 0
    
    def _analyze_debt_management(self, balance_sheets: List, income_statements: List) -> float:
        """Analyze debt management effectiveness"""
        if not balance_sheets or not income_statements:
            return 50
        
        try:
            latest_bs = balance_sheets[0]
            latest_is = income_statements[0]
            
            total_debt = latest_bs.get('total_debt', 0)
            total_equity = latest_bs.get('total_equity', 1)
            interest_expense = abs(latest_is.get('interest_expense', 0))
            ebit = latest_is.get('ebit', 1)
            
            # Debt-to-equity ratio score
            de_ratio = total_debt / total_equity if total_equity > 0 else 0
            de_score = max(0, 100 - (de_ratio * 50))  # Penalize high leverage
            
            # Interest coverage score
            interest_coverage = ebit / interest_expense if interest_expense > 0 else float('inf')
            coverage_score = min(100, interest_coverage * 10)
            
            # Combined score
            debt_score = (de_score + coverage_score) / 2
            return min(100, debt_score)
            
        except (KeyError, TypeError, ZeroDivisionError):
            return 50
    
    def _analyze_cash_management(self, balance_sheets: List, cash_flows: List) -> float:
        """Analyze cash management effectiveness"""
        if not balance_sheets or not cash_flows:
            return 50
        
        try:
            latest_bs = balance_sheets[0]
            latest_cf = cash_flows[0]
            
            cash_and_equivalents = latest_bs.get('cash_and_equivalents', 0)
            total_assets = latest_bs.get('total_assets', 1)
            free_cash_flow = latest_cf.get('free_cash_flow', 0)
            
            # Cash efficiency (not too much, not too little)
            cash_ratio = cash_and_equivalents / total_assets
            optimal_cash_ratio = 0.05  # 5% is often considered optimal
            
            cash_efficiency = 100 - abs(cash_ratio - optimal_cash_ratio) * 1000
            cash_efficiency = max(0, min(100, cash_efficiency))
            
            # FCF generation consistency
            fcf_score = min(100, max(0, free_cash_flow / total_assets * 1000)) if free_cash_flow > 0 else 0
            
            # Combined score
            cash_score = (cash_efficiency + fcf_score) / 2
            return cash_score
            
        except (KeyError, TypeError, ZeroDivisionError):
            return 50
    
    def _analyze_profitability_trends(self, financial_data: Dict) -> Tuple[str, str]:
        """Analyze ROE and ROIC trends"""
        try:
            income_statements = financial_data.get('income_statement', [])
            balance_sheets = financial_data.get('balance_sheet', [])
            
            if len(income_statements) < 3 or len(balance_sheets) < 3:
                return "Insufficient data", "Insufficient data"
            
            # Calculate ROE trends
            roe_values = []
            for i in range(min(3, len(income_statements))):
                net_income = income_statements[i].get('net_income', 0)
                equity = balance_sheets[i].get('total_equity', 1)
                
                if equity > 0:
                    roe = net_income / equity
                    roe_values.append(roe)
            
            roe_trend = self._determine_trend(roe_values)
            
            # Calculate ROIC trends (simplified)
            roic_values = []
            for i in range(min(3, len(income_statements))):
                operating_income = income_statements[i].get('operating_income', 0)
                total_assets = balance_sheets[i].get('total_assets', 1)
                current_liabilities = balance_sheets[i].get('current_liabilities', 0)
                invested_capital = total_assets - current_liabilities
                
                if invested_capital > 0:
                    roic = operating_income / invested_capital
                    roic_values.append(roic)
            
            roic_trend = self._determine_trend(roic_values)
            
            return roe_trend, roic_trend
            
        except Exception as e:
            logger.error(f"Error analyzing profitability trends: {str(e)}")
            return "Error", "Error"
    
    def _determine_trend(self, values: List[float]) -> str:
        """Determine if values show improving, declining, or stable trend"""
        if len(values) < 2:
            return "Insufficient data"
        
        try:
            if len(values) == 2:
                return "Improving" if values[0] > values[1] else "Declining" if values[0] < values[1] else "Stable"
            
            # For 3+ values, check overall trend
            slope = np.polyfit(range(len(values)), values, 1)[0]
            
            if slope > 0.02:  # 2% improvement threshold
                return "Improving"
            elif slope < -0.02:  # 2% decline threshold
                return "Declining"
            else:
                return "Stable"
                
        except Exception:
            return "Error"
    
    def _calculate_value_creation_score(self, tsr_metrics: Dict, dividend_analysis: DividendAnalysis,
                                      buyback_metrics: Dict, capital_allocation: CapitalAllocation) -> float:
        """Calculate overall value creation score"""
        try:
            # TSR component (40% weight)
            tsr_score = max(0, min(100, (tsr_metrics['5y'] + 10) * 2))  # Normalize around 5% return
            
            # Dividend component (25% weight)
            dividend_score = min(100, dividend_analysis.sustainability_score + 
                               dividend_analysis.consistency_years * 10)
            
            # Buyback component (15% weight)
            buyback_score = buyback_metrics['effectiveness']
            
            # Capital allocation component (20% weight)
            allocation_score = capital_allocation.overall_score
            
            # Weighted average
            overall_score = (
                tsr_score * 0.4 +
                dividend_score * 0.25 +
                buyback_score * 0.15 +
                allocation_score * 0.2
            )
            
            return min(100, max(0, overall_score))
            
        except Exception as e:
            logger.error(f"Error calculating value creation score: {str(e)}")
            return 50
    
    def _identify_value_factors(self, tsr_metrics: Dict, dividend_analysis: DividendAnalysis,
                              capital_allocation: CapitalAllocation, financial_data: Dict) -> Tuple[List[str], List[str]]:
        """Identify key value drivers and destroyers"""
        drivers = []
        destroyers = []
        
        # Analyze TSR performance
        if tsr_metrics['5y'] > 10:
            drivers.append("Strong 5-year total shareholder return")
        elif tsr_metrics['5y'] < 0:
            destroyers.append("Negative 5-year total shareholder return")
        
        # Analyze dividend policy
        if dividend_analysis.growth_rate > 5:
            drivers.append("Consistent dividend growth")
        elif dividend_analysis.consistency_years < 3:
            destroyers.append("Inconsistent dividend policy")
        
        # Analyze capital allocation
        if capital_allocation.overall_score > 70:
            drivers.append("Efficient capital allocation")
        elif capital_allocation.overall_score < 40:
            destroyers.append("Poor capital allocation decisions")
        
        # Analyze debt management
        if capital_allocation.debt_management_score > 70:
            drivers.append("Strong debt management")
        elif capital_allocation.debt_management_score < 40:
            destroyers.append("Excessive leverage or poor debt management")
        
        return drivers, destroyers
    
    def _calculate_peer_ranking(self, symbol: str, value_creation_score: float) -> int:
        """Calculate ranking against peer companies"""
        # Simplified implementation - would need actual peer data
        # Assume companies with scores > 70 are in top 25%
        if value_creation_score > 70:
            return 1  # Top quartile
        elif value_creation_score > 50:
            return 2  # Second quartile
        elif value_creation_score > 30:
            return 3  # Third quartile
        else:
            return 4  # Bottom quartile
    
    def generate_shareholder_value_report(self, metrics: ShareholderValueMetrics) -> Dict[str, Any]:
        """Generate comprehensive shareholder value report"""
        return {
            'executive_summary': {
                'overall_score': metrics.value_creation_score,
                'peer_ranking': f"Quartile {metrics.peer_comparison_rank}",
                'key_strengths': metrics.value_drivers,
                'key_concerns': metrics.value_destroyers
            },
            'tsr_analysis': {
                '1_year': f"{metrics.tsr_1y:.1f}%",
                '3_year': f"{metrics.tsr_3y:.1f}%",
                '5_year': f"{metrics.tsr_5y:.1f}%"
            },
            'dividend_analysis': {
                'current_yield': f"{metrics.dividend_yield:.2f}%",
                'growth_rate': f"{metrics.dividend_growth_rate:.1f}%",
                'consistency_score': f"{metrics.dividend_consistency_score:.0f}%"
            },
            'capital_allocation': {
                'overall_score': f"{metrics.capital_allocation_score:.0f}/100",
                'profitability_trend': f"ROE: {metrics.roe_trend}, ROIC: {metrics.roic_trend}"
            },
            'recommendations': self._generate_recommendations(metrics)
        }
    
    def _generate_recommendations(self, metrics: ShareholderValueMetrics) -> List[str]:
        """Generate actionable recommendations for management"""
        recommendations = []
        
        if metrics.value_creation_score < 50:
            recommendations.append("Focus on improving capital allocation efficiency")
        
        if metrics.tsr_5y < 5:
            recommendations.append("Review strategic initiatives to improve long-term returns")
        
        if metrics.dividend_consistency_score < 80:
            recommendations.append("Establish clearer dividend policy and communication")
        
        if metrics.capital_allocation_score < 60:
            recommendations.append("Reassess investment priorities and ROI thresholds")
        
        if not recommendations:
            recommendations.append("Continue current value creation strategies")
        
        return recommendations