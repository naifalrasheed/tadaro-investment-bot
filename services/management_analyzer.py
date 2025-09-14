"""
Management Quality Analyzer
Comprehensive management assessment as specified in user requirements:

1. Management behavior analysis and turnover tracking
2. Balance sheet trends and consistency monitoring  
3. Historical statement vs delivery tracking (promises made vs kept)
4. Negative news sentiment analysis on leadership
5. CEO/leadership previous statements verification
6. Performance delivery analysis with failure reasons

Focuses on management credibility, consistency, and shareholder value creation
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import requests
import re
from .api_client import UnifiedAPIClient
from monitoring.performance import monitor_performance, metrics_collector

logger = logging.getLogger(__name__)

class ManagementRating(Enum):
    """Overall management quality rating"""
    EXCELLENT = "excellent"      # Top-tier management
    GOOD = "good"               # Solid management team
    AVERAGE = "average"         # Typical management
    BELOW_AVERAGE = "below_average"  # Concerning issues
    POOR = "poor"               # Significant problems

class TurnoverLevel(Enum):
    """Employee turnover assessment"""
    LOW = "low"                 # <10% annual turnover
    MODERATE = "moderate"       # 10-20% annual turnover
    HIGH = "high"               # 20-30% annual turnover
    EXCESSIVE = "excessive"     # >30% annual turnover

class PromiseKeeping(Enum):
    """Management promise delivery track record"""
    EXCELLENT = "excellent"     # >90% promises kept
    GOOD = "good"              # 75-90% promises kept
    MODERATE = "moderate"      # 60-75% promises kept
    POOR = "poor"              # <60% promises kept

@dataclass
class ManagementAnalysisResult:
    """Result of comprehensive management analysis"""
    symbol: str
    company_name: str
    analysis_period: str
    overall_rating: ManagementRating
    
    # Core analysis components
    turnover_analysis: Dict[str, Any]
    balance_sheet_consistency: Dict[str, Any]
    promise_tracking: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    performance_delivery: Dict[str, Any]
    
    # Summary assessments
    strengths: List[str]
    concerns: List[str]
    red_flags: List[str]
    recommendations: List[str]
    
    timestamp: datetime

class ManagementQualityAnalyzer:
    """
    Analyzes management quality and governance practices
    Implements comprehensive leadership assessment framework
    """
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None):
        self.api_client = api_client or UnifiedAPIClient()
        
        # Analysis parameters
        self.analysis_years = 5  # Default analysis period
        
        # Quality thresholds
        self.thresholds = {
            'turnover_low': 0.10,           # 10% annual turnover
            'turnover_moderate': 0.20,       # 20% annual turnover
            'turnover_high': 0.30,          # 30% annual turnover
            'promise_excellent': 0.90,       # 90% promise keeping
            'promise_good': 0.75,           # 75% promise keeping
            'promise_moderate': 0.60,        # 60% promise keeping
            'sentiment_negative_threshold': -0.3,  # Negative sentiment threshold
            'performance_variance_threshold': 0.15  # 15% variance tolerance
        }
        
        # Key management metrics to track
        self.key_metrics = [
            'revenue_growth', 'margin_improvement', 'debt_reduction',
            'market_share', 'operational_efficiency', 'cost_control',
            'capital_allocation', 'shareholder_returns'
        ]
        
        # News sentiment keywords
        self.negative_keywords = [
            'scandal', 'fraud', 'investigation', 'lawsuit', 'misconduct',
            'resignation', 'fired', 'criminal', 'sec investigation',
            'whistleblower', 'corruption', 'embezzlement', 'insider trading'
        ]
        
        self.positive_keywords = [
            'innovation', 'leadership', 'award', 'recognition', 'achievement',
            'growth', 'expansion', 'strategic', 'visionary', 'successful'
        ]
    
    @monitor_performance
    def analyze_management_quality(self, symbol: str, company_name: str = None) -> ManagementAnalysisResult:
        """
        Comprehensive management quality analysis
        
        Args:
            symbol: Stock symbol
            company_name: Company name (optional)
        """
        try:
            logger.info(f"Starting management quality analysis for {symbol}")
            
            if not company_name:
                company_name = self._get_company_name(symbol)
            
            # Get historical data for analysis
            historical_data = self._get_management_data(symbol, self.analysis_years)
            
            # 1. Analyze employee turnover
            turnover_analysis = self._analyze_employee_turnover(symbol, historical_data)
            
            # 2. Analyze balance sheet trends and consistency
            balance_sheet_analysis = self._analyze_balance_sheet_consistency(symbol, historical_data)
            
            # 3. Track management promises vs delivery
            promise_analysis = self._analyze_promise_keeping(symbol, company_name, historical_data)
            
            # 4. Analyze sentiment on leadership
            sentiment_analysis = self._analyze_management_sentiment(symbol, company_name)
            
            # 5. Analyze performance delivery
            performance_analysis = self._analyze_performance_delivery(symbol, historical_data)
            
            # Generate overall assessment
            overall_rating = self._calculate_overall_rating(
                turnover_analysis, balance_sheet_analysis, promise_analysis, 
                sentiment_analysis, performance_analysis
            )
            
            # Identify strengths, concerns, and red flags
            strengths = self._identify_strengths(
                turnover_analysis, balance_sheet_analysis, promise_analysis, 
                sentiment_analysis, performance_analysis
            )
            
            concerns = self._identify_concerns(
                turnover_analysis, balance_sheet_analysis, promise_analysis, 
                sentiment_analysis, performance_analysis
            )
            
            red_flags = self._identify_red_flags(
                turnover_analysis, balance_sheet_analysis, promise_analysis, 
                sentiment_analysis, performance_analysis
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall_rating, strengths, concerns, red_flags
            )
            
            result = ManagementAnalysisResult(
                symbol=symbol,
                company_name=company_name,
                analysis_period=f"{self.analysis_years} years",
                overall_rating=overall_rating,
                turnover_analysis=turnover_analysis,
                balance_sheet_consistency=balance_sheet_analysis,
                promise_tracking=promise_analysis,
                sentiment_analysis=sentiment_analysis,
                performance_delivery=performance_analysis,
                strengths=strengths,
                concerns=concerns,
                red_flags=red_flags,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Record analysis
            metrics_collector.record_feature_usage('management_analysis')
            
            logger.info(f"Management analysis completed for {symbol}: {overall_rating.value}")
            return result
            
        except Exception as e:
            logger.error(f"Management analysis failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e))
    
    def _get_company_name(self, symbol: str) -> str:
        """Get company name from symbol"""
        try:
            # This would typically use the API to get company info
            # For now, return a placeholder
            return f"Company {symbol}"
        except Exception:
            return symbol
    
    def _get_management_data(self, symbol: str, years: int) -> Dict[str, Any]:
        """Gather comprehensive management-related data"""
        try:
            # In production, this would gather data from multiple sources:
            # - SEC filings (proxy statements, 10-K, 10-Q)
            # - News sources
            # - Earnings call transcripts
            # - Employee review sites (Glassdoor, etc.)
            # - Financial statements
            
            # Generate mock data for demonstration
            np.random.seed(hash(symbol) % 2**32)  # Consistent data
            
            years_range = list(range(2024 - years, 2024))
            
            # Mock financial performance data
            base_revenue = 1000000000  # $1B
            base_margin = 0.15  # 15%
            
            financial_data = {
                'years': years_range,
                'revenue': [base_revenue * ((1.05) ** i) * np.random.normal(1.0, 0.10) 
                           for i in range(years)],
                'net_margin': [base_margin * np.random.normal(1.0, 0.20) for _ in range(years)],
                'debt_to_equity': [0.4 * np.random.normal(1.0, 0.15) for _ in range(years)],
                'roe': [0.12 * np.random.normal(1.0, 0.25) for _ in range(years)]
            }
            
            # Mock management promises and delivery data
            promises_data = self._generate_mock_promises_data(symbol, years)
            
            # Mock turnover data
            turnover_data = {
                'annual_turnover_rate': [np.random.uniform(0.08, 0.25) for _ in range(years)],
                'executive_changes': [np.random.choice([0, 1, 2]) for _ in range(years)],
                'key_departures': [np.random.choice([0, 0, 1]) for _ in range(years)]
            }
            
            # Mock news sentiment data
            sentiment_data = {
                'quarterly_sentiment': [np.random.uniform(-0.5, 0.5) for _ in range(years * 4)],
                'major_news_events': self._generate_mock_news_events(symbol, years)
            }
            
            return {
                'financial_data': financial_data,
                'promises_data': promises_data,
                'turnover_data': turnover_data,
                'sentiment_data': sentiment_data,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error getting management data for {symbol}: {str(e)}")
            return {}
    
    def _generate_mock_promises_data(self, symbol: str, years: int) -> Dict[str, Any]:
        """Generate mock management promises and delivery data"""
        promises = []
        
        promise_types = [
            'Revenue Growth', 'Margin Improvement', 'Cost Reduction',
            'Market Share Gain', 'New Product Launch', 'International Expansion',
            'Debt Reduction', 'Dividend Increase', 'Share Buyback'
        ]
        
        for year in range(2024 - years, 2024):
            num_promises = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
            
            for i in range(num_promises):
                promise_type = np.random.choice(promise_types)
                target_value = np.random.uniform(5, 20)  # 5-20% targets
                actual_delivery = np.random.uniform(0, target_value * 1.2)  # Some variation
                
                promise = {
                    'year': year,
                    'promise_type': promise_type,
                    'target_value': target_value,
                    'actual_delivery': actual_delivery,
                    'delivery_rate': min(actual_delivery / target_value, 1.5) if target_value > 0 else 0,
                    'kept': actual_delivery >= target_value * 0.8,  # 80% threshold for "kept"
                    'source': 'Annual Guidance' if i == 0 else 'Earnings Call'
                }
                promises.append(promise)
        
        return {
            'promises': promises,
            'total_promises': len(promises),
            'promises_kept': sum(1 for p in promises if p['kept']),
            'keeping_rate': sum(1 for p in promises if p['kept']) / len(promises) if promises else 0
        }
    
    def _generate_mock_news_events(self, symbol: str, years: int) -> List[Dict[str, Any]]:
        """Generate mock news events for sentiment analysis"""
        events = []
        
        event_types = [
            ('CEO Appointment', 0.3), ('Strategic Initiative', 0.2), ('Earnings Beat', 0.4),
            ('Product Launch', 0.3), ('Acquisition', 0.1), ('Legal Issue', -0.4),
            ('Executive Departure', -0.2), ('Regulatory Issue', -0.3)
        ]
        
        for year in range(2024 - years, 2024):
            num_events = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
            
            for _ in range(num_events):
                event_type, base_sentiment = np.random.choice(event_types, p=[0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1])
                
                event = {
                    'year': year,
                    'month': np.random.randint(1, 13),
                    'event_type': event_type,
                    'sentiment_score': base_sentiment + np.random.normal(0, 0.1),
                    'impact_magnitude': np.random.uniform(0.1, 0.8)
                }
                events.append(event)
        
        return events
    
    def _analyze_employee_turnover(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze employee turnover patterns
        Question: Look at management behavior, turnover in employees historically
        """
        try:
            turnover_data = data.get('turnover_data', {})
            annual_rates = turnover_data.get('annual_turnover_rate', [])
            executive_changes = turnover_data.get('executive_changes', [])
            key_departures = turnover_data.get('key_departures', [])
            
            if not annual_rates:
                return {'error': 'Insufficient turnover data'}
            
            # Calculate turnover metrics
            avg_turnover_rate = np.mean(annual_rates)
            turnover_trend = self._calculate_trend(annual_rates)
            turnover_volatility = np.std(annual_rates)
            
            # Assess turnover level
            turnover_level = self._assess_turnover_level(avg_turnover_rate)
            
            # Executive stability analysis
            total_executive_changes = sum(executive_changes)
            avg_executive_changes = total_executive_changes / len(executive_changes) if executive_changes else 0
            
            # Key departure analysis
            total_key_departures = sum(key_departures)
            departure_rate = total_key_departures / len(key_departures) if key_departures else 0
            
            # Overall assessment
            assessment = self._assess_turnover_quality(
                turnover_level, turnover_trend, avg_executive_changes, departure_rate
            )
            
            return {
                'avg_annual_turnover_rate': avg_turnover_rate,
                'turnover_level': turnover_level.value,
                'turnover_trend': turnover_trend,
                'turnover_volatility': turnover_volatility,
                'total_executive_changes': total_executive_changes,
                'avg_annual_executive_changes': avg_executive_changes,
                'key_departures': total_key_departures,
                'departure_rate': departure_rate,
                'assessment': assessment,
                'historical_rates': annual_rates
            }
            
        except Exception as e:
            logger.error(f"Turnover analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _assess_turnover_level(self, avg_rate: float) -> TurnoverLevel:
        """Assess turnover level based on average rate"""
        if avg_rate <= self.thresholds['turnover_low']:
            return TurnoverLevel.LOW
        elif avg_rate <= self.thresholds['turnover_moderate']:
            return TurnoverLevel.MODERATE
        elif avg_rate <= self.thresholds['turnover_high']:
            return TurnoverLevel.HIGH
        else:
            return TurnoverLevel.EXCESSIVE
    
    def _assess_turnover_quality(self, level: TurnoverLevel, trend: str, 
                               exec_changes: float, departure_rate: float) -> str:
        """Generate turnover quality assessment"""
        
        if level == TurnoverLevel.LOW and trend != 'Increasing':
            return "Excellent - Low, stable turnover indicates strong employee satisfaction"
        elif level == TurnoverLevel.MODERATE and exec_changes < 0.5:
            return "Good - Moderate turnover with stable executive team"
        elif level == TurnoverLevel.HIGH:
            return "Concerning - High turnover may indicate management or culture issues"
        else:
            return "Poor - Excessive turnover suggests significant organizational problems"
    
    def _analyze_balance_sheet_consistency(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze balance sheet trends and consistency
        Question: Balance sheet trends, and consistency
        """
        try:
            financial_data = data.get('financial_data', {})
            
            debt_to_equity = financial_data.get('debt_to_equity', [])
            roe = financial_data.get('roe', [])
            revenue = financial_data.get('revenue', [])
            net_margin = financial_data.get('net_margin', [])
            years = financial_data.get('years', [])
            
            if not debt_to_equity or not roe:
                return {'error': 'Insufficient balance sheet data'}
            
            # Trend analysis
            de_trend = self._calculate_trend(debt_to_equity)
            roe_trend = self._calculate_trend(roe)
            margin_trend = self._calculate_trend(net_margin) if net_margin else 'Stable'
            
            # Consistency analysis
            de_consistency = self._assess_consistency(debt_to_equity)
            roe_consistency = self._assess_consistency(roe)
            margin_consistency = self._assess_consistency(net_margin) if net_margin else 'Moderate'
            
            # Quality scores
            financial_discipline = self._assess_financial_discipline(debt_to_equity, de_trend)
            profitability_management = self._assess_profitability_management(roe, margin_trend)
            
            # Overall balance sheet management assessment
            overall_assessment = self._assess_balance_sheet_management(
                de_trend, roe_trend, de_consistency, roe_consistency
            )
            
            return {
                'debt_equity_trend': de_trend,
                'roe_trend': roe_trend,
                'margin_trend': margin_trend,
                'debt_equity_consistency': de_consistency,
                'roe_consistency': roe_consistency,
                'margin_consistency': margin_consistency,
                'financial_discipline_score': financial_discipline,
                'profitability_management_score': profitability_management,
                'overall_assessment': overall_assessment,
                'historical_metrics': {
                    'debt_to_equity': debt_to_equity,
                    'roe': roe,
                    'net_margin': net_margin,
                    'years': years
                }
            }
            
        except Exception as e:
            logger.error(f"Balance sheet analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _assess_consistency(self, values: List[float]) -> str:
        """Assess consistency of financial metrics"""
        if not values:
            return 'Unknown'
        
        cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1
        
        if cv <= 0.15:
            return 'Very Consistent'
        elif cv <= 0.25:
            return 'Consistent'
        elif cv <= 0.35:
            return 'Moderate'
        else:
            return 'Inconsistent'
    
    def _assess_financial_discipline(self, debt_ratios: List[float], trend: str) -> float:
        """Assess management's financial discipline (0-100 score)"""
        avg_debt = np.mean(debt_ratios) if debt_ratios else 0.5
        
        # Base score based on debt level
        if avg_debt <= 0.3:
            base_score = 90
        elif avg_debt <= 0.5:
            base_score = 70
        elif avg_debt <= 0.7:
            base_score = 50
        else:
            base_score = 30
        
        # Adjust for trend
        if trend == 'Improving':
            base_score += 10
        elif trend == 'Deteriorating':
            base_score -= 15
        
        return max(min(base_score, 100), 0)
    
    def _assess_profitability_management(self, roe_values: List[float], margin_trend: str) -> float:
        """Assess management's profitability management (0-100 score)"""
        avg_roe = np.mean(roe_values) if roe_values else 0.08
        
        # Base score based on ROE level
        if avg_roe >= 0.15:
            base_score = 90
        elif avg_roe >= 0.12:
            base_score = 75
        elif avg_roe >= 0.08:
            base_score = 60
        else:
            base_score = 40
        
        # Adjust for margin trend
        if margin_trend == 'Improving':
            base_score += 10
        elif margin_trend == 'Deteriorating':
            base_score -= 10
        
        return max(min(base_score, 100), 0)
    
    def _assess_balance_sheet_management(self, de_trend: str, roe_trend: str, 
                                       de_consistency: str, roe_consistency: str) -> str:
        """Generate overall balance sheet management assessment"""
        
        positive_factors = 0
        negative_factors = 0
        
        # Trend factors
        if de_trend == 'Improving':
            positive_factors += 2
        elif de_trend == 'Deteriorating':
            negative_factors += 2
        
        if roe_trend == 'Improving':
            positive_factors += 2
        elif roe_trend == 'Deteriorating':
            negative_factors += 2
        
        # Consistency factors
        if de_consistency in ['Very Consistent', 'Consistent']:
            positive_factors += 1
        elif de_consistency == 'Inconsistent':
            negative_factors += 1
        
        if roe_consistency in ['Very Consistent', 'Consistent']:
            positive_factors += 1
        elif roe_consistency == 'Inconsistent':
            negative_factors += 1
        
        # Generate assessment
        net_score = positive_factors - negative_factors
        
        if net_score >= 3:
            return "Excellent - Strong, consistent balance sheet management"
        elif net_score >= 1:
            return "Good - Generally sound financial management"
        elif net_score >= -1:
            return "Average - Mixed financial management track record"
        else:
            return "Poor - Concerning balance sheet management patterns"
    
    def _analyze_promise_keeping(self, symbol: str, company_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze management promise keeping track record
        Questions: CEO or leadership previous statements on company business or profitability? 
                  Did they deliver on them? If no, what reasons they gave?
        """
        try:
            promises_data = data.get('promises_data', {})
            promises = promises_data.get('promises', [])
            
            if not promises:
                return {'error': 'No promise tracking data available'}
            
            # Calculate promise keeping metrics
            total_promises = len(promises)
            promises_kept = sum(1 for p in promises if p['kept'])
            overall_keeping_rate = promises_kept / total_promises if total_promises > 0 else 0
            
            # Analyze by promise type
            promise_type_analysis = self._analyze_promises_by_type(promises)
            
            # Analyze delivery patterns over time
            yearly_performance = self._analyze_yearly_promise_performance(promises)
            
            # Assess promise keeping quality
            keeping_assessment = self._assess_promise_keeping_quality(overall_keeping_rate)
            
            # Analyze reasons for failures
            failure_analysis = self._analyze_promise_failures(promises)
            
            # Recent performance analysis
            recent_promises = [p for p in promises if p['year'] >= 2022]
            recent_keeping_rate = (sum(1 for p in recent_promises if p['kept']) / 
                                 len(recent_promises) if recent_promises else 0)
            
            return {
                'total_promises_tracked': total_promises,
                'promises_kept': promises_kept,
                'overall_keeping_rate': overall_keeping_rate,
                'recent_keeping_rate': recent_keeping_rate,
                'keeping_assessment': keeping_assessment.value,
                'promise_type_analysis': promise_type_analysis,
                'yearly_performance': yearly_performance,
                'failure_analysis': failure_analysis,
                'trend': 'Improving' if recent_keeping_rate > overall_keeping_rate else 'Declining',
                'detailed_promises': promises[-10:]  # Last 10 promises for review
            }
            
        except Exception as e:
            logger.error(f"Promise keeping analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_promises_by_type(self, promises: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze promise keeping by promise type"""
        type_analysis = {}
        
        for promise in promises:
            promise_type = promise['promise_type']
            
            if promise_type not in type_analysis:
                type_analysis[promise_type] = {
                    'total': 0,
                    'kept': 0,
                    'avg_delivery_rate': 0,
                    'delivery_rates': []
                }
            
            type_analysis[promise_type]['total'] += 1
            if promise['kept']:
                type_analysis[promise_type]['kept'] += 1
            
            type_analysis[promise_type]['delivery_rates'].append(promise['delivery_rate'])
        
        # Calculate keeping rates and average delivery
        for promise_type in type_analysis:
            analysis = type_analysis[promise_type]
            analysis['keeping_rate'] = analysis['kept'] / analysis['total'] if analysis['total'] > 0 else 0
            analysis['avg_delivery_rate'] = np.mean(analysis['delivery_rates'])
            del analysis['delivery_rates']  # Remove detailed data
        
        return type_analysis
    
    def _analyze_yearly_promise_performance(self, promises: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze promise keeping performance by year"""
        yearly_performance = {}
        
        for promise in promises:
            year = promise['year']
            
            if year not in yearly_performance:
                yearly_performance[year] = {
                    'total': 0,
                    'kept': 0,
                    'avg_delivery_rate': 0,
                    'delivery_rates': []
                }
            
            yearly_performance[year]['total'] += 1
            if promise['kept']:
                yearly_performance[year]['kept'] += 1
            
            yearly_performance[year]['delivery_rates'].append(promise['delivery_rate'])
        
        # Calculate metrics
        for year in yearly_performance:
            perf = yearly_performance[year]
            perf['keeping_rate'] = perf['kept'] / perf['total'] if perf['total'] > 0 else 0
            perf['avg_delivery_rate'] = np.mean(perf['delivery_rates'])
            del perf['delivery_rates']
        
        return yearly_performance
    
    def _assess_promise_keeping_quality(self, keeping_rate: float) -> PromiseKeeping:
        """Assess promise keeping quality based on rate"""
        if keeping_rate >= self.thresholds['promise_excellent']:
            return PromiseKeeping.EXCELLENT
        elif keeping_rate >= self.thresholds['promise_good']:
            return PromiseKeeping.GOOD
        elif keeping_rate >= self.thresholds['promise_moderate']:
            return PromiseKeeping.MODERATE
        else:
            return PromiseKeeping.POOR
    
    def _analyze_promise_failures(self, promises: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in promise failures"""
        failures = [p for p in promises if not p['kept']]
        
        if not failures:
            return {
                'total_failures': 0,
                'common_failure_types': [],
                'avg_shortfall': 0
            }
        
        # Common failure types
        failure_types = {}
        shortfalls = []
        
        for failure in failures:
            failure_type = failure['promise_type']
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
            
            # Calculate shortfall
            if failure['target_value'] > 0:
                shortfall = (failure['target_value'] - failure['actual_delivery']) / failure['target_value']
                shortfalls.append(shortfall)
        
        # Sort failure types by frequency
        common_failures = sorted(failure_types.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_failures': len(failures),
            'failure_rate': len(failures) / len(promises) if promises else 0,
            'common_failure_types': common_failures[:3],  # Top 3
            'avg_shortfall': np.mean(shortfalls) if shortfalls else 0,
            'typical_reasons': self._generate_failure_reasons(common_failures)
        }
    
    def _generate_failure_reasons(self, common_failures: List[Tuple[str, int]]) -> List[str]:
        """Generate typical reasons for promise failures"""
        reason_map = {
            'Revenue Growth': 'Market conditions, competitive pressure, or overoptimistic projections',
            'Margin Improvement': 'Cost inflation, operational challenges, or investment requirements',
            'Cost Reduction': 'Implementation delays, employee resistance, or one-time charges',
            'Market Share Gain': 'Competitive response, product delays, or market dynamics',
            'New Product Launch': 'Development delays, regulatory issues, or market readiness',
            'International Expansion': 'Regulatory hurdles, cultural challenges, or market conditions',
            'Debt Reduction': 'Cash flow issues, acquisition opportunities, or strategic priorities',
            'Dividend Increase': 'Cash flow constraints, investment needs, or economic uncertainty'
        }
        
        return [reason_map.get(failure_type, 'Execution challenges or external factors') 
                for failure_type, _ in common_failures]
    
    def _analyze_management_sentiment(self, symbol: str, company_name: str) -> Dict[str, Any]:
        """
        Analyze sentiment on management and leadership
        Question: Monitor negative news on management
        """
        try:
            # In production, this would analyze:
            # - News articles about management
            # - Social media sentiment
            # - Analyst reports on management
            # - Employee reviews and ratings
            
            # For now, use mock sentiment data
            sentiment_data = self._get_mock_sentiment_data(symbol)
            
            # Analyze sentiment trends
            overall_sentiment = np.mean(sentiment_data['scores'])
            recent_sentiment = np.mean(sentiment_data['scores'][-4:])  # Last year
            sentiment_trend = self._calculate_trend(sentiment_data['scores'])
            
            # Identify negative events
            negative_events = [event for event in sentiment_data['events'] 
                             if event['sentiment'] < self.thresholds['sentiment_negative_threshold']]
            
            # Assess sentiment quality
            sentiment_assessment = self._assess_sentiment_quality(overall_sentiment, recent_sentiment)
            
            # Risk assessment
            reputation_risk = self._assess_reputation_risk(negative_events, overall_sentiment)
            
            return {
                'overall_sentiment_score': overall_sentiment,
                'recent_sentiment_score': recent_sentiment,
                'sentiment_trend': sentiment_trend,
                'sentiment_assessment': sentiment_assessment,
                'negative_events_count': len(negative_events),
                'major_negative_events': [e for e in negative_events if abs(e['sentiment']) > 0.5],
                'reputation_risk_level': reputation_risk,
                'monitoring_period': '5 years',
                'recent_events': sentiment_data['events'][-5:]  # Last 5 events
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _get_mock_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock sentiment data for analysis"""
        np.random.seed(hash(symbol) % 2**32)
        
        # Generate quarterly sentiment scores
        scores = [np.random.normal(0.1, 0.3) for _ in range(20)]  # 5 years quarterly
        
        # Generate specific events
        events = [
            {'date': '2023-Q4', 'event': 'CEO Strategic Vision', 'sentiment': 0.4},
            {'date': '2023-Q3', 'event': 'Earnings Call Performance', 'sentiment': 0.2},
            {'date': '2023-Q1', 'event': 'Product Launch Execution', 'sentiment': 0.3},
            {'date': '2022-Q4', 'event': 'Cost Management Initiative', 'sentiment': -0.1},
            {'date': '2022-Q2', 'event': 'Executive Team Changes', 'sentiment': -0.2}
        ]
        
        return {
            'scores': scores,
            'events': events
        }
    
    def _assess_sentiment_quality(self, overall: float, recent: float) -> str:
        """Assess management sentiment quality"""
        if overall >= 0.2 and recent >= 0.1:
            return "Positive - Strong management reputation"
        elif overall >= 0.0 and recent >= -0.1:
            return "Neutral - Mixed but acceptable sentiment"
        elif overall >= -0.2:
            return "Concerning - Some negative sentiment issues"
        else:
            return "Poor - Significant negative sentiment"
    
    def _assess_reputation_risk(self, negative_events: List[Dict], overall_sentiment: float) -> str:
        """Assess reputation risk level"""
        if len(negative_events) == 0 and overall_sentiment > 0:
            return "Low"
        elif len(negative_events) <= 2 and overall_sentiment >= -0.1:
            return "Moderate"
        elif len(negative_events) <= 4:
            return "High"
        else:
            return "Very High"
    
    def _analyze_performance_delivery(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze actual performance vs expectations/guidance
        Focus on consistency and reliability of management forecasts
        """
        try:
            financial_data = data.get('financial_data', {})
            promises_data = data.get('promises_data', {})
            
            # Analyze financial performance consistency
            revenue_consistency = self._assess_consistency(financial_data.get('revenue', []))
            margin_consistency = self._assess_consistency(financial_data.get('net_margin', []))
            
            # Analyze guidance accuracy
            guidance_accuracy = self._analyze_guidance_accuracy(promises_data)
            
            # Performance volatility
            revenue_volatility = (np.std(financial_data.get('revenue', [])) / 
                                np.mean(financial_data.get('revenue', [])) 
                                if financial_data.get('revenue') else 0)
            
            # Overall performance reliability
            reliability_score = self._calculate_reliability_score(
                revenue_consistency, margin_consistency, guidance_accuracy
            )
            
            return {
                'revenue_consistency': revenue_consistency,
                'margin_consistency': margin_consistency,
                'revenue_volatility': revenue_volatility,
                'guidance_accuracy': guidance_accuracy,
                'reliability_score': reliability_score,
                'assessment': self._assess_performance_delivery(reliability_score)
            }
            
        except Exception as e:
            logger.error(f"Performance delivery analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_guidance_accuracy(self, promises_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze accuracy of management guidance"""
        promises = promises_data.get('promises', [])
        
        if not promises:
            return {'accuracy_rate': 0, 'avg_variance': 0, 'assessment': 'No data'}
        
        # Calculate accuracy metrics
        accurate_guidance = sum(1 for p in promises if abs(1 - p['delivery_rate']) <= 0.1)  # Within 10%
        accuracy_rate = accurate_guidance / len(promises)
        
        # Calculate average variance
        variances = [abs(1 - p['delivery_rate']) for p in promises]
        avg_variance = np.mean(variances)
        
        return {
            'total_guidance_items': len(promises),
            'accurate_guidance': accurate_guidance,
            'accuracy_rate': accuracy_rate,
            'avg_variance': avg_variance,
            'assessment': self._assess_guidance_accuracy(accuracy_rate, avg_variance)
        }
    
    def _assess_guidance_accuracy(self, accuracy_rate: float, avg_variance: float) -> str:
        """Assess guidance accuracy quality"""
        if accuracy_rate >= 0.8 and avg_variance <= 0.15:
            return "Excellent - Highly reliable guidance"
        elif accuracy_rate >= 0.6 and avg_variance <= 0.25:
            return "Good - Generally reliable guidance"
        elif accuracy_rate >= 0.4:
            return "Moderate - Somewhat reliable guidance"
        else:
            return "Poor - Unreliable guidance"
    
    def _calculate_reliability_score(self, revenue_consistency: str, margin_consistency: str, 
                                   guidance_accuracy: Dict[str, Any]) -> float:
        """Calculate overall performance reliability score (0-100)"""
        score = 0
        
        # Revenue consistency score
        consistency_scores = {
            'Very Consistent': 25, 'Consistent': 20, 'Moderate': 15, 'Inconsistent': 5
        }
        score += consistency_scores.get(revenue_consistency, 10)
        
        # Margin consistency score
        score += consistency_scores.get(margin_consistency, 10)
        
        # Guidance accuracy score (50 points total)
        accuracy_rate = guidance_accuracy.get('accuracy_rate', 0)
        score += accuracy_rate * 50
        
        return min(score, 100)
    
    def _assess_performance_delivery(self, reliability_score: float) -> str:
        """Assess overall performance delivery quality"""
        if reliability_score >= 85:
            return "Excellent - Highly reliable performance delivery"
        elif reliability_score >= 70:
            return "Good - Generally reliable performance"
        elif reliability_score >= 55:
            return "Average - Mixed performance delivery"
        else:
            return "Poor - Unreliable performance delivery"
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return 'Stable'
        
        # Simple linear regression to determine trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.05:  # 5% threshold
            return 'Improving'
        elif slope < -0.05:
            return 'Deteriorating'
        else:
            return 'Stable'
    
    def _calculate_overall_rating(self, turnover: Dict, balance_sheet: Dict, 
                                promises: Dict, sentiment: Dict, performance: Dict) -> ManagementRating:
        """Calculate overall management rating"""
        score = 0
        
        # Turnover analysis (20 points)
        if turnover.get('turnover_level') == 'low':
            score += 20
        elif turnover.get('turnover_level') == 'moderate':
            score += 15
        elif turnover.get('turnover_level') == 'high':
            score += 8
        
        # Balance sheet management (20 points)
        if 'Excellent' in balance_sheet.get('overall_assessment', ''):
            score += 20
        elif 'Good' in balance_sheet.get('overall_assessment', ''):
            score += 15
        elif 'Average' in balance_sheet.get('overall_assessment', ''):
            score += 10
        else:
            score += 5
        
        # Promise keeping (25 points)
        keeping_rate = promises.get('overall_keeping_rate', 0)
        score += keeping_rate * 25
        
        # Sentiment analysis (15 points)
        sentiment_score = sentiment.get('overall_sentiment_score', 0)
        score += max(0, min(15, (sentiment_score + 0.5) * 15))  # Normalize to 0-15
        
        # Performance delivery (20 points)
        reliability = performance.get('reliability_score', 50) / 100  # Normalize to 0-1
        score += reliability * 20
        
        # Convert to rating
        if score >= 85:
            return ManagementRating.EXCELLENT
        elif score >= 70:
            return ManagementRating.GOOD
        elif score >= 55:
            return ManagementRating.AVERAGE
        elif score >= 40:
            return ManagementRating.BELOW_AVERAGE
        else:
            return ManagementRating.POOR
    
    def _identify_strengths(self, *analyses) -> List[str]:
        """Identify management strengths from all analyses"""
        strengths = []
        
        turnover, balance_sheet, promises, sentiment, performance = analyses
        
        # Turnover strengths
        if turnover.get('turnover_level') == 'low':
            strengths.append("Low employee turnover indicates strong workplace culture")
        
        if turnover.get('turnover_trend') == 'Improving':
            strengths.append("Employee retention improving over time")
        
        # Balance sheet strengths
        if 'Excellent' in balance_sheet.get('overall_assessment', ''):
            strengths.append("Excellent balance sheet management and financial discipline")
        
        if balance_sheet.get('financial_discipline_score', 0) >= 80:
            strengths.append("Strong financial discipline with conservative debt management")
        
        # Promise keeping strengths
        if promises.get('overall_keeping_rate', 0) >= 0.8:
            strengths.append("Excellent track record of delivering on management promises")
        
        if promises.get('trend') == 'Improving':
            strengths.append("Improving promise delivery performance")
        
        # Sentiment strengths
        if sentiment.get('overall_sentiment_score', 0) >= 0.2:
            strengths.append("Positive market sentiment and management reputation")
        
        # Performance strengths
        if performance.get('reliability_score', 0) >= 80:
            strengths.append("Highly reliable performance delivery and guidance accuracy")
        
        return strengths
    
    def _identify_concerns(self, *analyses) -> List[str]:
        """Identify management concerns from all analyses"""
        concerns = []
        
        turnover, balance_sheet, promises, sentiment, performance = analyses
        
        # Turnover concerns
        if turnover.get('turnover_level') == 'high':
            concerns.append("High employee turnover may indicate management or culture issues")
        
        if turnover.get('avg_annual_executive_changes', 0) >= 1:
            concerns.append("Frequent executive changes suggest leadership instability")
        
        # Balance sheet concerns
        if 'Poor' in balance_sheet.get('overall_assessment', ''):
            concerns.append("Poor balance sheet management patterns")
        
        # Promise keeping concerns
        if promises.get('overall_keeping_rate', 0) < 0.7:
            concerns.append("Below-average promise keeping track record")
        
        # Sentiment concerns
        if sentiment.get('negative_events_count', 0) >= 3:
            concerns.append("Multiple negative news events about management")
        
        # Performance concerns
        if performance.get('reliability_score', 0) < 60:
            concerns.append("Inconsistent performance delivery and guidance accuracy")
        
        return concerns
    
    def _identify_red_flags(self, *analyses) -> List[str]:
        """Identify serious red flags from all analyses"""
        red_flags = []
        
        turnover, balance_sheet, promises, sentiment, performance = analyses
        
        # Critical turnover issues
        if turnover.get('turnover_level') == 'excessive':
            red_flags.append("🚩 EXCESSIVE employee turnover - major organizational problems")
        
        if turnover.get('key_departures', 0) >= 3:
            red_flags.append("🚩 Multiple key management departures in recent years")
        
        # Critical financial management issues
        if balance_sheet.get('financial_discipline_score', 100) < 40:
            red_flags.append("🚩 Poor financial discipline - concerning debt management")
        
        # Critical promise keeping issues
        if promises.get('overall_keeping_rate', 1) < 0.5:
            red_flags.append("🚩 Majority of management promises not delivered")
        
        # Critical sentiment issues
        if sentiment.get('overall_sentiment_score', 0) < -0.3:
            red_flags.append("🚩 Significant negative sentiment about management")
        
        if len(sentiment.get('major_negative_events', [])) >= 2:
            red_flags.append("🚩 Multiple major negative events involving management")
        
        # Critical performance issues
        if performance.get('reliability_score', 100) < 40:
            red_flags.append("🚩 Highly unreliable performance delivery and guidance")
        
        return red_flags
    
    def _generate_recommendations(self, overall_rating: ManagementRating, 
                                strengths: List[str], concerns: List[str], 
                                red_flags: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Overall rating recommendations
        if overall_rating == ManagementRating.EXCELLENT:
            recommendations.append("✅ Excellent management team - suitable for long-term investment")
        elif overall_rating == ManagementRating.GOOD:
            recommendations.append("👍 Good management team - generally reliable for investment")
        elif overall_rating == ManagementRating.AVERAGE:
            recommendations.append("⚠️ Average management - monitor closely and require higher margin of safety")
        elif overall_rating == ManagementRating.BELOW_AVERAGE:
            recommendations.append("⚡ Below-average management - consider avoiding or require significant discount")
        else:
            recommendations.append("❌ Poor management - likely unsuitable for quality-focused investment")
        
        # Red flag recommendations
        if red_flags:
            recommendations.append(f"🚨 {len(red_flags)} critical red flags detected - exercise extreme caution")
            recommendations.append("📋 Recommend detailed due diligence on management before investing")
        
        # Concern-based recommendations
        if len(concerns) >= 3:
            recommendations.append("⚠️ Multiple management concerns - increase margin of safety requirement")
        
        # Strength-based recommendations
        if len(strengths) >= 4:
            recommendations.append("💪 Strong management profile supports premium valuation")
        
        # Monitoring recommendations
        recommendations.extend([
            "📊 Monitor quarterly earnings calls for management communication quality",
            "📰 Set up news alerts to track management-related developments",
            "💼 Review proxy statements annually for compensation and governance changes"
        ])
        
        return recommendations
    
    def _create_error_result(self, symbol: str, error_msg: str) -> ManagementAnalysisResult:
        """Create error result for failed analysis"""
        return ManagementAnalysisResult(
            symbol=symbol,
            company_name=symbol,
            analysis_period="N/A",
            overall_rating=ManagementRating.POOR,
            turnover_analysis={'error': error_msg},
            balance_sheet_consistency={'error': error_msg},
            promise_tracking={'error': error_msg},
            sentiment_analysis={'error': error_msg},
            performance_delivery={'error': error_msg},
            strengths=[],
            concerns=[],
            red_flags=[f"Analysis failed: {error_msg}"],
            recommendations=[f"❌ Unable to assess management quality: {error_msg}"],
            timestamp=datetime.now()
        )