"""
Historical Financial Performance Analyzer
5-10 year comprehensive analysis as specified in user requirements:
1. Company profitability over the past 5-10 years
2. Dividend consistency tracking  
3. Debt burden analysis (D/E ratio, interest coverage vs industry)
4. Peer valuation comparison (P/E, P/B ratios)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from .api_client import UnifiedAPIClient
from monitoring.performance import monitor_performance, metrics_collector

logger = logging.getLogger(__name__)

class ProfitabilityTrend(Enum):
    """Profitability trend assessment"""
    CONSISTENTLY_PROFITABLE = "consistently_profitable"
    IMPROVING = "improving"
    DECLINING = "declining"
    VOLATILE = "volatile"
    CONSISTENTLY_UNPROFITABLE = "consistently_unprofitable"

class DividendConsistency(Enum):
    """Dividend payment consistency"""
    EXCELLENT = "excellent"        # 10+ years consistent
    GOOD = "good"                 # 7-9 years consistent
    MODERATE = "moderate"         # 5-6 years consistent
    POOR = "poor"                 # 2-4 years consistent
    NO_DIVIDENDS = "no_dividends" # No dividend history

class DebtLevel(Enum):
    """Debt burden assessment"""
    LOW = "low"           # Conservative debt levels
    MODERATE = "moderate" # Reasonable debt levels
    HIGH = "high"         # Elevated debt levels
    EXCESSIVE = "excessive" # Dangerous debt levels

@dataclass
class HistoricalAnalysisResult:
    """Result of historical financial analysis"""
    symbol: str
    analysis_period: str
    profitability_analysis: Dict[str, Any]
    dividend_analysis: Dict[str, Any]
    debt_analysis: Dict[str, Any]
    peer_comparison: Dict[str, Any]
    overall_assessment: str
    red_flags: List[str]
    strengths: List[str]
    timestamp: datetime

class HistoricalFinancialAnalyzer:
    """
    Analyzes 5-10 years of financial performance
    Implements comprehensive fundamental analysis as specified
    """
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None):
        self.api_client = api_client or UnifiedAPIClient()
        
        # Analysis thresholds
        self.profitability_thresholds = {
            'roe_excellent': 0.15,     # 15%+ ROE
            'roe_good': 0.10,          # 10%+ ROE
            'margin_excellent': 0.20,   # 20%+ net margin
            'margin_good': 0.10        # 10%+ net margin
        }
        
        self.debt_thresholds = {
            'de_low': 0.3,            # D/E < 30%
            'de_moderate': 0.6,       # D/E < 60%
            'de_high': 1.0,           # D/E < 100%
            'interest_coverage_safe': 5.0,  # 5x+ coverage
            'interest_coverage_adequate': 2.5  # 2.5x+ coverage
        }
        
        self.valuation_thresholds = {
            'pe_cheap': 15,           # P/E < 15
            'pe_reasonable': 25,      # P/E < 25
            'pb_cheap': 1.5,          # P/B < 1.5
            'pb_reasonable': 3.0      # P/B < 3.0
        }
    
    @monitor_performance
    def analyze_historical_performance(self, symbol: str, years: int = 10) -> HistoricalAnalysisResult:
        """
        Comprehensive 5-10 year historical analysis
        
        Args:
            symbol: Stock symbol
            years: Number of years to analyze (5-10)
        """
        try:
            logger.info(f"Starting {years}-year historical analysis for {symbol}")
            
            # Get historical financial data
            historical_data = self._get_historical_financial_data(symbol, years)
            
            # 1. Profitability Analysis
            profitability_analysis = self._analyze_profitability(historical_data, years)
            
            # 2. Dividend Consistency Analysis
            dividend_analysis = self._analyze_dividend_consistency(symbol, historical_data, years)
            
            # 3. Debt Burden Analysis
            debt_analysis = self._analyze_debt_burden(symbol, historical_data)
            
            # 4. Peer Valuation Comparison
            peer_comparison = self._analyze_peer_comparison(symbol, historical_data)
            
            # Generate overall assessment
            overall_assessment = self._generate_overall_assessment(
                profitability_analysis, dividend_analysis, debt_analysis, peer_comparison
            )
            
            # Identify red flags and strengths
            red_flags = self._identify_red_flags(profitability_analysis, dividend_analysis, debt_analysis)
            strengths = self._identify_strengths(profitability_analysis, dividend_analysis, debt_analysis)
            
            result = HistoricalAnalysisResult(
                symbol=symbol,
                analysis_period=f"{years} years",
                profitability_analysis=profitability_analysis,
                dividend_analysis=dividend_analysis,
                debt_analysis=debt_analysis,
                peer_comparison=peer_comparison,
                overall_assessment=overall_assessment,
                red_flags=red_flags,
                strengths=strengths,
                timestamp=datetime.now()
            )
            
            # Record analysis
            metrics_collector.record_feature_usage('historical_analysis')
            
            logger.info(f"Historical analysis completed for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Historical analysis failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e), years)
    
    def _get_historical_financial_data(self, symbol: str, years: int) -> Dict[str, List[float]]:
        """Get historical financial data for the specified period"""
        try:
            # In production, this would pull actual historical data from APIs
            # For now, generate realistic mock data
            
            # Generate years of data
            years_range = list(range(2024 - years, 2024))
            
            # Mock financial metrics with realistic trends
            np.random.seed(hash(symbol) % 2**32)  # Consistent data for same symbol
            
            # Base values
            base_revenue = 1000000000  # $1B base revenue
            base_earnings = 100000000  # $100M base earnings
            
            # Generate realistic financial data
            data = {
                'years': years_range,
                'revenue': self._generate_realistic_series(base_revenue, years, growth_rate=0.05, volatility=0.15),
                'net_income': self._generate_realistic_series(base_earnings, years, growth_rate=0.07, volatility=0.25),
                'total_assets': self._generate_realistic_series(base_revenue * 2, years, growth_rate=0.04, volatility=0.10),
                'total_debt': self._generate_realistic_series(base_revenue * 0.3, years, growth_rate=0.03, volatility=0.20),
                'shareholders_equity': self._generate_realistic_series(base_revenue * 0.5, years, growth_rate=0.06, volatility=0.15),
                'dividends_paid': self._generate_realistic_series(base_earnings * 0.4, years, growth_rate=0.05, volatility=0.30),
                'interest_expense': self._generate_realistic_series(base_revenue * 0.02, years, growth_rate=0.02, volatility=0.25),
                'shares_outstanding': [1000000000] * years,  # Constant for simplicity
                'market_cap': self._generate_realistic_series(base_revenue * 5, years, growth_rate=0.08, volatility=0.30)
            }
            
            # Calculate derived metrics
            data['roe'] = [ni / se if se > 0 else 0 for ni, se in zip(data['net_income'], data['shareholders_equity'])]
            data['roa'] = [ni / ta if ta > 0 else 0 for ni, ta in zip(data['net_income'], data['total_assets'])]
            data['debt_to_equity'] = [td / se if se > 0 else 0 for td, se in zip(data['total_debt'], data['shareholders_equity'])]
            data['net_margin'] = [ni / rev if rev > 0 else 0 for ni, rev in zip(data['net_income'], data['revenue'])]
            data['pe_ratio'] = [mc / ni if ni > 0 else 0 for mc, ni in zip(data['market_cap'], data['net_income'])]
            data['pb_ratio'] = [mc / se if se > 0 else 0 for mc, se in zip(data['market_cap'], data['shareholders_equity'])]
            data['interest_coverage'] = [(ni + ie) / ie if ie > 0 else 0 for ni, ie in zip(data['net_income'], data['interest_expense'])]
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return {}
    
    def _generate_realistic_series(self, base_value: float, years: int, 
                                  growth_rate: float = 0.05, volatility: float = 0.15) -> List[float]:
        """Generate realistic financial time series"""
        values = [base_value]
        
        for year in range(1, years):
            # Add trend growth
            trend_growth = growth_rate
            
            # Add some volatility
            random_factor = np.random.normal(0, volatility)
            
            # Calculate new value
            new_value = values[-1] * (1 + trend_growth + random_factor)
            values.append(max(new_value, 0))  # Ensure non-negative
        
        return values
    
    def _analyze_profitability(self, data: Dict[str, List], years: int) -> Dict[str, Any]:
        """
        Analyze profitability over the specified period
        Question: Is the company profitable over the past 5-10 years?
        """
        try:
            net_income = data.get('net_income', [])
            roe = data.get('roe', [])
            roa = data.get('roa', [])
            net_margin = data.get('net_margin', [])
            revenue = data.get('revenue', [])
            
            if not net_income:
                return {'error': 'Insufficient profitability data'}
            
            # Calculate profitability metrics
            profitable_years = sum(1 for ni in net_income if ni > 0)
            total_years = len(net_income)
            profitability_rate = profitable_years / total_years if total_years > 0 else 0
            
            # Calculate averages
            avg_roe = np.mean([r for r in roe if r > 0]) if roe else 0
            avg_roa = np.mean([r for r in roa if r > 0]) if roa else 0
            avg_margin = np.mean([m for m in net_margin if m > 0]) if net_margin else 0
            
            # Determine trend
            profitability_trend = self._determine_profitability_trend(net_income)
            
            # Revenue growth analysis
            revenue_growth = self._calculate_cagr(revenue) if len(revenue) >= 2 else 0
            
            # Assessment
            assessment = self._assess_profitability(
                profitability_rate, avg_roe, avg_roa, avg_margin, profitability_trend
            )
            
            return {
                'profitable_years': profitable_years,
                'total_years': total_years,
                'profitability_rate': profitability_rate,
                'avg_roe': avg_roe,
                'avg_roa': avg_roa,
                'avg_net_margin': avg_margin,
                'revenue_cagr': revenue_growth,
                'trend': profitability_trend.value,
                'assessment': assessment,
                'historical_roe': roe,
                'historical_net_income': net_income,
                'years_analyzed': data.get('years', [])
            }
            
        except Exception as e:
            logger.error(f"Profitability analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_dividend_consistency(self, symbol: str, data: Dict[str, List], years: int) -> Dict[str, Any]:
        """
        Analyze dividend consistency
        Question: Does it pay dividends consistently?
        """
        try:
            dividends = data.get('dividends_paid', [])
            net_income = data.get('net_income', [])
            
            if not dividends:
                return {
                    'consistency': DividendConsistency.NO_DIVIDENDS.value,
                    'assessment': 'No dividend history',
                    'years_with_dividends': 0,
                    'total_years': years
                }
            
            # Count years with dividends
            years_with_dividends = sum(1 for div in dividends if div > 0)
            
            # Calculate dividend metrics
            dividend_consistency = self._assess_dividend_consistency(years_with_dividends, years)
            
            # Calculate payout ratio
            payout_ratios = []
            for i, (div, ni) in enumerate(zip(dividends, net_income)):
                if ni > 0 and div > 0:
                    payout_ratios.append(div / ni)
            
            avg_payout_ratio = np.mean(payout_ratios) if payout_ratios else 0
            
            # Dividend growth analysis
            dividend_growth = self._calculate_cagr(dividends) if len(dividends) >= 2 else 0
            
            # Sustainability analysis
            sustainability = self._assess_dividend_sustainability(avg_payout_ratio, payout_ratios)
            
            return {
                'years_with_dividends': years_with_dividends,
                'total_years': years,
                'consistency': dividend_consistency.value,
                'avg_payout_ratio': avg_payout_ratio,
                'dividend_cagr': dividend_growth,
                'sustainability': sustainability,
                'historical_dividends': dividends,
                'historical_payout_ratios': payout_ratios,
                'assessment': self._generate_dividend_assessment(dividend_consistency, sustainability)
            }
            
        except Exception as e:
            logger.error(f"Dividend analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_debt_burden(self, symbol: str, data: Dict[str, List]) -> Dict[str, Any]:
        """
        Analyze debt burden
        Question: Is it burdened with debt? Low D/E ratio or interest coverage better than industry average?
        """
        try:
            debt_to_equity = data.get('debt_to_equity', [])
            interest_coverage = data.get('interest_coverage', [])
            total_debt = data.get('total_debt', [])
            
            if not debt_to_equity:
                return {'error': 'Insufficient debt data'}
            
            # Calculate debt metrics
            avg_de_ratio = np.mean([de for de in debt_to_equity if de >= 0])
            avg_interest_coverage = np.mean([ic for ic in interest_coverage if ic > 0])
            
            # Assess debt level
            debt_level = self._assess_debt_level(avg_de_ratio, avg_interest_coverage)
            
            # Debt trend analysis
            debt_trend = self._analyze_debt_trend(debt_to_equity, total_debt)
            
            # Industry comparison (mock - in production, get real industry data)
            industry_avg_de = 0.5  # Mock industry average
            industry_avg_coverage = 6.0  # Mock industry average
            
            vs_industry = {
                'de_vs_industry': 'Better' if avg_de_ratio < industry_avg_de else 'Worse',
                'coverage_vs_industry': 'Better' if avg_interest_coverage > industry_avg_coverage else 'Worse'
            }
            
            return {
                'avg_debt_to_equity': avg_de_ratio,
                'avg_interest_coverage': avg_interest_coverage,
                'debt_level': debt_level.value,
                'debt_trend': debt_trend,
                'vs_industry': vs_industry,
                'industry_benchmarks': {
                    'industry_avg_de': industry_avg_de,
                    'industry_avg_coverage': industry_avg_coverage
                },
                'historical_de_ratio': debt_to_equity,
                'historical_interest_coverage': interest_coverage,
                'assessment': self._generate_debt_assessment(debt_level, vs_industry)
            }
            
        except Exception as e:
            logger.error(f"Debt analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_peer_comparison(self, symbol: str, data: Dict[str, List]) -> Dict[str, Any]:
        """
        Peer valuation comparison
        Question: Is its valuation (P/E, P/B) reasonable compared to peers in the industry?
        """
        try:
            pe_ratios = data.get('pe_ratio', [])
            pb_ratios = data.get('pb_ratio', [])
            
            if not pe_ratios or not pb_ratios:
                return {'error': 'Insufficient valuation data'}
            
            # Calculate current/recent valuation metrics
            current_pe = pe_ratios[-1] if pe_ratios else 0
            current_pb = pb_ratios[-1] if pb_ratios else 0
            
            # Historical averages
            avg_pe = np.mean([pe for pe in pe_ratios if pe > 0])
            avg_pb = np.mean([pb for pb in pb_ratios if pb > 0])
            
            # Mock peer/industry data (in production, get real peer data)
            industry_metrics = self._get_mock_industry_metrics(symbol)
            
            # Valuation assessment
            pe_assessment = self._assess_pe_valuation(current_pe, avg_pe, industry_metrics['pe'])
            pb_assessment = self._assess_pb_valuation(current_pb, avg_pb, industry_metrics['pb'])
            
            return {
                'current_pe': current_pe,
                'current_pb': current_pb,
                'historical_avg_pe': avg_pe,
                'historical_avg_pb': avg_pb,
                'industry_pe': industry_metrics['pe'],
                'industry_pb': industry_metrics['pb'],
                'pe_vs_industry': 'Cheaper' if current_pe < industry_metrics['pe'] else 'More Expensive',
                'pb_vs_industry': 'Cheaper' if current_pb < industry_metrics['pb'] else 'More Expensive',
                'pe_vs_history': 'Below Average' if current_pe < avg_pe else 'Above Average',
                'pb_vs_history': 'Below Average' if current_pb < avg_pb else 'Above Average',
                'pe_assessment': pe_assessment,
                'pb_assessment': pb_assessment,
                'peers': industry_metrics['peers'],
                'overall_valuation': self._assess_overall_valuation(pe_assessment, pb_assessment)
            }
            
        except Exception as e:
            logger.error(f"Peer comparison failed: {str(e)}")
            return {'error': str(e)}
    
    def _determine_profitability_trend(self, net_income: List[float]) -> ProfitabilityTrend:
        """Determine the trend in profitability"""
        if len(net_income) < 3:
            return ProfitabilityTrend.VOLATILE
        
        profitable_count = sum(1 for ni in net_income if ni > 0)
        total_count = len(net_income)
        
        # Check consistency
        if profitable_count == total_count:
            # All years profitable, check if improving
            recent_avg = np.mean(net_income[-3:])
            early_avg = np.mean(net_income[:3])
            
            if recent_avg > early_avg * 1.1:  # 10% improvement
                return ProfitabilityTrend.IMPROVING
            else:
                return ProfitabilityTrend.CONSISTENTLY_PROFITABLE
        
        elif profitable_count == 0:
            return ProfitabilityTrend.CONSISTENTLY_UNPROFITABLE
        
        elif profitable_count >= total_count * 0.7:  # 70%+ profitable
            # Check if trend is improving or declining
            recent_count = sum(1 for ni in net_income[-3:] if ni > 0)
            if recent_count >= 2:
                return ProfitabilityTrend.IMPROVING
            else:
                return ProfitabilityTrend.DECLINING
        
        else:
            return ProfitabilityTrend.VOLATILE
    
    def _assess_profitability(self, profitability_rate: float, avg_roe: float, 
                            avg_roa: float, avg_margin: float, trend: ProfitabilityTrend) -> str:
        """Generate profitability assessment"""
        
        if profitability_rate >= 0.9 and avg_roe >= self.profitability_thresholds['roe_excellent']:
            return "Excellent - Consistently profitable with strong returns"
        elif profitability_rate >= 0.8 and avg_roe >= self.profitability_thresholds['roe_good']:
            return "Good - Mostly profitable with decent returns"
        elif profitability_rate >= 0.6:
            return "Moderate - Reasonably profitable but some volatility"
        elif profitability_rate >= 0.4:
            return "Concerning - Limited profitability track record"
        else:
            return "Poor - Inconsistent or unprofitable performance"
    
    def _assess_dividend_consistency(self, years_with_dividends: int, total_years: int) -> DividendConsistency:
        """Assess dividend payment consistency"""
        consistency_rate = years_with_dividends / total_years if total_years > 0 else 0
        
        if years_with_dividends == 0:
            return DividendConsistency.NO_DIVIDENDS
        elif consistency_rate >= 0.9 and years_with_dividends >= 7:
            return DividendConsistency.EXCELLENT
        elif consistency_rate >= 0.8 and years_with_dividends >= 5:
            return DividendConsistency.GOOD
        elif consistency_rate >= 0.6:
            return DividendConsistency.MODERATE
        else:
            return DividendConsistency.POOR
    
    def _assess_dividend_sustainability(self, avg_payout_ratio: float, payout_ratios: List[float]) -> str:
        """Assess dividend sustainability"""
        if not payout_ratios or avg_payout_ratio == 0:
            return "N/A - No dividends"
        
        if avg_payout_ratio <= 0.4:
            return "Very Sustainable - Conservative payout ratio"
        elif avg_payout_ratio <= 0.6:
            return "Sustainable - Reasonable payout ratio"
        elif avg_payout_ratio <= 0.8:
            return "Moderate Risk - High payout ratio"
        else:
            return "High Risk - Very high payout ratio may not be sustainable"
    
    def _generate_dividend_assessment(self, consistency: DividendConsistency, sustainability: str) -> str:
        """Generate overall dividend assessment"""
        if consistency == DividendConsistency.NO_DIVIDENDS:
            return "No dividend history - Growth-focused company"
        
        consistency_desc = {
            DividendConsistency.EXCELLENT: "Excellent dividend track record",
            DividendConsistency.GOOD: "Good dividend consistency", 
            DividendConsistency.MODERATE: "Moderate dividend reliability",
            DividendConsistency.POOR: "Poor dividend consistency"
        }
        
        return f"{consistency_desc.get(consistency, 'Unknown')} - {sustainability}"
    
    def _assess_debt_level(self, avg_de_ratio: float, avg_interest_coverage: float) -> DebtLevel:
        """Assess overall debt level"""
        if (avg_de_ratio <= self.debt_thresholds['de_low'] and 
            avg_interest_coverage >= self.debt_thresholds['interest_coverage_safe']):
            return DebtLevel.LOW
        
        elif (avg_de_ratio <= self.debt_thresholds['de_moderate'] and 
              avg_interest_coverage >= self.debt_thresholds['interest_coverage_adequate']):
            return DebtLevel.MODERATE
        
        elif avg_de_ratio <= self.debt_thresholds['de_high']:
            return DebtLevel.HIGH
        
        else:
            return DebtLevel.EXCESSIVE
    
    def _analyze_debt_trend(self, debt_to_equity: List[float], total_debt: List[float]) -> str:
        """Analyze debt trend over time"""
        if len(debt_to_equity) < 2:
            return "Insufficient data"
        
        recent_avg = np.mean(debt_to_equity[-3:])
        early_avg = np.mean(debt_to_equity[:3])
        
        if recent_avg < early_avg * 0.9:  # 10% improvement
            return "Improving - Debt levels declining"
        elif recent_avg > early_avg * 1.1:  # 10% deterioration
            return "Worsening - Debt levels increasing"
        else:
            return "Stable - Debt levels relatively consistent"
    
    def _generate_debt_assessment(self, debt_level: DebtLevel, vs_industry: Dict[str, str]) -> str:
        """Generate debt assessment"""
        level_desc = {
            DebtLevel.LOW: "Low debt burden - Conservative capital structure",
            DebtLevel.MODERATE: "Moderate debt levels - Reasonable leverage",
            DebtLevel.HIGH: "High debt burden - Elevated financial risk",
            DebtLevel.EXCESSIVE: "Excessive debt - Significant financial risk"
        }
        
        industry_note = ""
        if vs_industry.get('de_vs_industry') == 'Better':
            industry_note = " - Better than industry average"
        elif vs_industry.get('de_vs_industry') == 'Worse':
            industry_note = " - Worse than industry average"
        
        return level_desc.get(debt_level, "Unknown") + industry_note
    
    def _get_mock_industry_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get mock industry metrics for comparison"""
        # In production, this would pull real industry/peer data
        return {
            'pe': 18.5,  # Industry average P/E
            'pb': 2.3,   # Industry average P/B
            'peers': ['PEER1', 'PEER2', 'PEER3']  # Mock peer companies
        }
    
    def _assess_pe_valuation(self, current_pe: float, historical_pe: float, industry_pe: float) -> str:
        """Assess P/E ratio valuation"""
        if current_pe <= 0:
            return "N/A - No earnings or negative earnings"
        
        if current_pe < self.valuation_thresholds['pe_cheap']:
            return "Cheap - P/E below 15"
        elif current_pe < self.valuation_thresholds['pe_reasonable']:
            return "Reasonable - P/E between 15-25"
        elif current_pe < 35:
            return "Expensive - P/E between 25-35"
        else:
            return "Very Expensive - P/E above 35"
    
    def _assess_pb_valuation(self, current_pb: float, historical_pb: float, industry_pb: float) -> str:
        """Assess P/B ratio valuation"""
        if current_pb <= 0:
            return "N/A - Invalid book value"
        
        if current_pb < self.valuation_thresholds['pb_cheap']:
            return "Cheap - P/B below 1.5"
        elif current_pb < self.valuation_thresholds['pb_reasonable']:
            return "Reasonable - P/B between 1.5-3.0"
        elif current_pb < 5:
            return "Expensive - P/B between 3.0-5.0"
        else:
            return "Very Expensive - P/B above 5.0"
    
    def _assess_overall_valuation(self, pe_assessment: str, pb_assessment: str) -> str:
        """Assess overall valuation based on multiple metrics"""
        pe_score = self._get_valuation_score(pe_assessment)
        pb_score = self._get_valuation_score(pb_assessment)
        
        avg_score = (pe_score + pb_score) / 2
        
        if avg_score <= 1.5:
            return "Undervalued - Attractive valuation on multiple metrics"
        elif avg_score <= 2.5:
            return "Fairly Valued - Reasonable valuation"
        elif avg_score <= 3.5:
            return "Overvalued - Expensive on most metrics"
        else:
            return "Significantly Overvalued - Very expensive"
    
    def _get_valuation_score(self, assessment: str) -> int:
        """Convert valuation assessment to numeric score"""
        if 'Cheap' in assessment:
            return 1
        elif 'Reasonable' in assessment:
            return 2
        elif 'Expensive' in assessment and 'Very' not in assessment:
            return 3
        else:
            return 4
    
    def _calculate_cagr(self, values: List[float]) -> float:
        """Calculate Compound Annual Growth Rate"""
        if len(values) < 2 or values[0] <= 0:
            return 0.0
        
        start_value = values[0]
        end_value = values[-1]
        years = len(values) - 1
        
        cagr = ((end_value / start_value) ** (1/years)) - 1
        return round(cagr, 4)
    
    def _generate_overall_assessment(self, profitability: Dict, dividends: Dict, 
                                   debt: Dict, peers: Dict) -> str:
        """Generate overall company assessment"""
        
        # Score each category
        profitability_score = self._score_profitability(profitability)
        dividend_score = self._score_dividends(dividends)
        debt_score = self._score_debt(debt)
        valuation_score = self._score_valuation(peers)
        
        overall_score = (profitability_score + dividend_score + debt_score + valuation_score) / 4
        
        if overall_score >= 4.0:
            return "Excellent - Strong fundamental profile across all metrics"
        elif overall_score >= 3.0:
            return "Good - Solid fundamentals with minor concerns"
        elif overall_score >= 2.0:
            return "Fair - Mixed fundamental profile with notable issues"
        else:
            return "Poor - Weak fundamentals across multiple areas"
    
    def _score_profitability(self, analysis: Dict) -> float:
        """Score profitability analysis (1-5 scale)"""
        if 'error' in analysis:
            return 1.0
        
        rate = analysis.get('profitability_rate', 0)
        roe = analysis.get('avg_roe', 0)
        
        if rate >= 0.9 and roe >= 0.15:
            return 5.0
        elif rate >= 0.8 and roe >= 0.10:
            return 4.0
        elif rate >= 0.6:
            return 3.0
        elif rate >= 0.4:
            return 2.0
        else:
            return 1.0
    
    def _score_dividends(self, analysis: Dict) -> float:
        """Score dividend analysis (1-5 scale)"""
        if 'error' in analysis:
            return 1.0
        
        consistency = analysis.get('consistency', 'no_dividends')
        
        score_map = {
            'excellent': 5.0,
            'good': 4.0,
            'moderate': 3.0,
            'poor': 2.0,
            'no_dividends': 3.0  # Neutral for growth companies
        }
        
        return score_map.get(consistency, 1.0)
    
    def _score_debt(self, analysis: Dict) -> float:
        """Score debt analysis (1-5 scale)"""
        if 'error' in analysis:
            return 1.0
        
        debt_level = analysis.get('debt_level', 'excessive')
        
        score_map = {
            'low': 5.0,
            'moderate': 4.0,
            'high': 2.0,
            'excessive': 1.0
        }
        
        return score_map.get(debt_level, 1.0)
    
    def _score_valuation(self, analysis: Dict) -> float:
        """Score valuation analysis (1-5 scale)"""
        if 'error' in analysis:
            return 1.0
        
        overall = analysis.get('overall_valuation', '')
        
        if 'Undervalued' in overall:
            return 5.0
        elif 'Fairly Valued' in overall:
            return 4.0
        elif 'Overvalued' in overall and 'Significantly' not in overall:
            return 2.0
        else:
            return 1.0
    
    def _identify_red_flags(self, profitability: Dict, dividends: Dict, debt: Dict) -> List[str]:
        """Identify red flags from the analysis"""
        red_flags = []
        
        # Profitability red flags
        if profitability.get('profitability_rate', 1) < 0.6:
            red_flags.append("Inconsistent profitability - Less than 60% of years profitable")
        
        if profitability.get('trend') == 'declining':
            red_flags.append("Declining profitability trend")
        
        # Dividend red flags
        if (dividends.get('consistency') == 'poor' and 
            'risk' in dividends.get('sustainability', '').lower()):
            red_flags.append("Unsustainable dividend payments")
        
        # Debt red flags
        if debt.get('debt_level') in ['high', 'excessive']:
            red_flags.append("High debt burden may limit financial flexibility")
        
        if debt.get('debt_trend') == 'Worsening':
            red_flags.append("Increasing debt levels over time")
        
        if debt.get('avg_interest_coverage', 10) < 2.5:
            red_flags.append("Low interest coverage ratio indicates financial stress")
        
        return red_flags
    
    def _identify_strengths(self, profitability: Dict, dividends: Dict, debt: Dict) -> List[str]:
        """Identify company strengths from the analysis"""
        strengths = []
        
        # Profitability strengths
        if profitability.get('profitability_rate', 0) >= 0.9:
            strengths.append("Consistent profitability across all analyzed years")
        
        if profitability.get('avg_roe', 0) >= 0.15:
            strengths.append("Strong return on equity (>15%)")
        
        if profitability.get('trend') == 'improving':
            strengths.append("Improving profitability trend")
        
        # Dividend strengths
        if dividends.get('consistency') in ['excellent', 'good']:
            strengths.append("Reliable dividend payments")
        
        if 'sustainable' in dividends.get('sustainability', '').lower():
            strengths.append("Sustainable dividend policy")
        
        # Debt strengths
        if debt.get('debt_level') == 'low':
            strengths.append("Conservative debt levels provide financial flexibility")
        
        if debt.get('vs_industry', {}).get('de_vs_industry') == 'Better':
            strengths.append("Debt levels better than industry average")
        
        if debt.get('avg_interest_coverage', 0) >= 5:
            strengths.append("Strong interest coverage provides financial safety")
        
        return strengths
    
    def _create_error_result(self, symbol: str, error_msg: str, years: int) -> HistoricalAnalysisResult:
        """Create error result for failed analysis"""
        return HistoricalAnalysisResult(
            symbol=symbol,
            analysis_period=f"{years} years",
            profitability_analysis={'error': error_msg},
            dividend_analysis={'error': error_msg},
            debt_analysis={'error': error_msg},
            peer_comparison={'error': error_msg},
            overall_assessment=f"Analysis failed: {error_msg}",
            red_flags=[f"Analysis error: {error_msg}"],
            strengths=[],
            timestamp=datetime.now()
        )