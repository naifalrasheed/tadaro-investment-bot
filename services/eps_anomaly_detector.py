"""
EPS Anomaly Detection System
Advanced analysis as specified in user requirements:

EPS Analysis Enhancement:
- Use average EPS over multiple years (Graham prefers 5–10 years)
- If earnings jump higher than 40%, dig deeper and inform why
- Identify extraordinary items or non-recurring profit sources
- Analyze sustainability of earnings improvements
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from .api_client import UnifiedAPIClient
from monitoring.performance import monitor_performance, metrics_collector

logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """Types of EPS anomalies"""
    EXTRAORDINARY_GAIN = "extraordinary_gain"
    ONE_TIME_CHARGE = "one_time_charge"
    ASSET_SALE = "asset_sale"
    TAX_BENEFIT = "tax_benefit"
    ACCOUNTING_CHANGE = "accounting_change"
    RESTRUCTURING = "restructuring"
    ACQUISITION_IMPACT = "acquisition_impact"
    SEASONAL_EFFECT = "seasonal_effect"
    NORMAL_VOLATILITY = "normal_volatility"

class AnomalySeverity(Enum):
    """Severity levels for anomalies"""
    CRITICAL = "critical"      # >100% change
    HIGH = "high"             # 40-100% change
    MODERATE = "moderate"     # 20-40% change
    LOW = "low"              # <20% change

@dataclass
class EPSAnomalyResult:
    """Result of EPS anomaly analysis"""
    symbol: str
    analysis_period: str
    historical_eps: List[float]
    average_eps: float
    anomalies_detected: List[Dict[str, Any]]
    quality_adjusted_eps: List[float]
    sustainable_eps_trend: float
    earnings_quality_score: float
    recommendations: List[str]
    timestamp: datetime

class EPSAnomalyDetector:
    """
    Advanced EPS analysis system implementing Graham's principles
    Detects and analyzes earnings anomalies for better valuation accuracy
    """
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None):
        self.api_client = api_client or UnifiedAPIClient()
        
        # Anomaly detection thresholds
        self.thresholds = {
            'major_anomaly': 0.40,      # 40% as specified by user
            'moderate_anomaly': 0.20,   # 20% change
            'minor_anomaly': 0.15,      # 15% change
            'volatility_threshold': 0.30 # 30% std dev vs mean
        }
        
        # Quality scoring weights
        self.quality_weights = {
            'consistency': 0.30,        # Earnings consistency over time
            'recurring_quality': 0.25,  # Proportion of recurring earnings
            'growth_sustainability': 0.20, # Sustainable growth pattern
            'accounting_quality': 0.15, # Conservative accounting
            'anomaly_frequency': 0.10   # Frequency of anomalies
        }
        
        # Common extraordinary item indicators
        self.extraordinary_indicators = [
            'asset sale', 'disposal', 'discontinued', 'restructuring',
            'impairment', 'writedown', 'settlement', 'insurance',
            'litigation', 'tax benefit', 'foreign exchange', 'derivative',
            'acquisition', 'merger', 'spin-off', 'divestiture'
        ]
    
    @monitor_performance
    def analyze_eps_anomalies(self, symbol: str, years: int = 10) -> EPSAnomalyResult:
        """
        Comprehensive EPS anomaly analysis
        
        Args:
            symbol: Stock symbol to analyze
            years: Number of years of EPS data to analyze (5-10 as per Graham)
        """
        try:
            logger.info(f"Starting EPS anomaly analysis for {symbol} over {years} years")
            
            # Get historical EPS data
            historical_data = self._get_historical_eps_data(symbol, years)
            
            if not historical_data or len(historical_data['eps']) < 3:
                raise ValueError("Insufficient EPS data for analysis")
            
            eps_data = historical_data['eps']
            years_data = historical_data['years']
            
            # Calculate average EPS (Graham's approach)
            average_eps = self._calculate_quality_adjusted_average(eps_data)
            
            # Detect anomalies
            anomalies = self._detect_eps_anomalies(eps_data, years_data, historical_data)
            
            # Analyze each detected anomaly
            analyzed_anomalies = []
            for anomaly in anomalies:
                analysis = self._analyze_anomaly(anomaly, historical_data, symbol)
                analyzed_anomalies.append(analysis)
            
            # Calculate quality-adjusted EPS series
            quality_adjusted_eps = self._calculate_quality_adjusted_eps(eps_data, analyzed_anomalies)
            
            # Determine sustainable earnings trend
            sustainable_trend = self._calculate_sustainable_trend(quality_adjusted_eps)
            
            # Calculate earnings quality score
            quality_score = self._calculate_earnings_quality_score(
                eps_data, analyzed_anomalies, quality_adjusted_eps
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                eps_data, analyzed_anomalies, quality_score, sustainable_trend
            )
            
            result = EPSAnomalyResult(
                symbol=symbol,
                analysis_period=f"{years} years",
                historical_eps=eps_data,
                average_eps=average_eps,
                anomalies_detected=analyzed_anomalies,
                quality_adjusted_eps=quality_adjusted_eps,
                sustainable_eps_trend=sustainable_trend,
                earnings_quality_score=quality_score,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Record analysis
            metrics_collector.record_feature_usage('eps_anomaly_analysis')
            
            logger.info(f"EPS anomaly analysis completed for {symbol}. Found {len(analyzed_anomalies)} anomalies.")
            return result
            
        except Exception as e:
            logger.error(f"EPS anomaly analysis failed for {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e), years)
    
    def _get_historical_eps_data(self, symbol: str, years: int) -> Dict[str, Any]:
        """Get comprehensive historical EPS and earnings data"""
        try:
            # In production, this would pull detailed financial statement data
            # For now, generate realistic mock data with some anomalies
            
            np.random.seed(hash(symbol) % 2**32)  # Consistent data for same symbol
            
            years_range = list(range(2024 - years, 2024))
            
            # Generate base EPS trend with some growth
            base_eps = 2.50  # Starting EPS
            normal_growth = 0.05  # 5% annual growth
            
            eps_data = []
            revenues = []
            net_incomes = []
            special_items = []
            shares_outstanding = []
            
            for i, year in enumerate(years_range):
                # Normal EPS growth with some volatility
                normal_eps = base_eps * ((1 + normal_growth) ** i) * np.random.normal(1.0, 0.10)
                
                # Add occasional anomalies (30% chance per year)
                special_item = 0
                anomaly_factor = 1.0
                
                if np.random.random() < 0.30:  # 30% chance of anomaly
                    anomaly_type = np.random.choice([
                        'asset_sale', 'restructuring', 'tax_benefit', 
                        'acquisition', 'writedown', 'settlement'
                    ])
                    
                    if anomaly_type in ['asset_sale', 'tax_benefit', 'settlement']:
                        # Positive anomaly
                        anomaly_factor = np.random.uniform(1.2, 2.0)  # 20-100% boost
                        special_item = normal_eps * (anomaly_factor - 1)
                    else:
                        # Negative anomaly
                        anomaly_factor = np.random.uniform(0.3, 0.8)  # 20-70% reduction
                        special_item = normal_eps * (anomaly_factor - 1)
                
                final_eps = normal_eps * anomaly_factor
                eps_data.append(final_eps)
                
                # Generate supporting data
                revenues.append(base_eps * 100 * ((1 + 0.04) ** i))  # Revenue growth
                net_incomes.append(final_eps * 1000000)  # Net income (million shares assumed)
                special_items.append(special_item)
                shares_outstanding.append(1000000)  # 1M shares
            
            return {
                'years': years_range,
                'eps': eps_data,
                'revenues': revenues,
                'net_incomes': net_incomes,
                'special_items': special_items,
                'shares_outstanding': shares_outstanding,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error getting EPS data for {symbol}: {str(e)}")
            return {}
    
    def _calculate_quality_adjusted_average(self, eps_data: List[float]) -> float:
        """
        Calculate quality-adjusted average EPS following Graham's approach
        Removes or adjusts for extraordinary items
        """
        if not eps_data:
            return 0.0
        
        # Remove extreme outliers (beyond 3 standard deviations)
        eps_array = np.array(eps_data)
        mean_eps = np.mean(eps_array)
        std_eps = np.std(eps_array)
        
        # Filter out extreme outliers
        filtered_eps = eps_array[np.abs(eps_array - mean_eps) <= 3 * std_eps]
        
        # If we filtered out too much data, use all data
        if len(filtered_eps) < len(eps_data) * 0.6:  # Less than 60% remaining
            filtered_eps = eps_array
        
        return float(np.mean(filtered_eps))
    
    def _detect_eps_anomalies(self, eps_data: List[float], years_data: List[int], 
                            historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential EPS anomalies based on year-over-year changes"""
        anomalies = []
        
        for i in range(1, len(eps_data)):
            current_eps = eps_data[i]
            previous_eps = eps_data[i-1]
            current_year = years_data[i]
            
            if previous_eps == 0:
                continue  # Skip if previous year had zero/negative earnings
            
            # Calculate percentage change
            change_percent = (current_eps - previous_eps) / abs(previous_eps)
            
            # Determine anomaly severity
            severity = self._classify_anomaly_severity(change_percent)
            
            if abs(change_percent) >= self.thresholds['minor_anomaly']:
                anomaly = {
                    'year': current_year,
                    'year_index': i,
                    'current_eps': current_eps,
                    'previous_eps': previous_eps,
                    'change_percent': change_percent,
                    'change_absolute': current_eps - previous_eps,
                    'severity': severity,
                    'direction': 'positive' if change_percent > 0 else 'negative',
                    'requires_investigation': abs(change_percent) >= self.thresholds['major_anomaly']
                }
                anomalies.append(anomaly)
        
        return anomalies
    
    def _classify_anomaly_severity(self, change_percent: float) -> AnomalySeverity:
        """Classify the severity of an EPS anomaly"""
        abs_change = abs(change_percent)
        
        if abs_change >= 1.0:  # 100%+ change
            return AnomalySeverity.CRITICAL
        elif abs_change >= self.thresholds['major_anomaly']:  # 40%+ change
            return AnomalySeverity.HIGH
        elif abs_change >= self.thresholds['moderate_anomaly']:  # 20%+ change
            return AnomalySeverity.MODERATE
        else:
            return AnomalySeverity.LOW
    
    def _analyze_anomaly(self, anomaly: Dict[str, Any], historical_data: Dict[str, Any], 
                        symbol: str) -> Dict[str, Any]:
        """
        Deep analysis of detected anomaly to determine cause
        As specified: If earnings jump >40%, dig deeper and inform why
        """
        year_index = anomaly['year_index']
        change_percent = anomaly['change_percent']
        
        # Enhanced anomaly analysis
        enhanced_anomaly = anomaly.copy()
        
        # Analyze potential causes
        potential_causes = self._identify_potential_causes(anomaly, historical_data)
        
        # Determine most likely cause
        primary_cause = self._determine_primary_cause(potential_causes, change_percent)
        
        # Assess sustainability
        sustainability = self._assess_earnings_sustainability(
            anomaly, historical_data, primary_cause
        )
        
        # Generate explanation
        explanation = self._generate_anomaly_explanation(
            anomaly, primary_cause, sustainability
        )
        
        # Add investigation notes for major anomalies (>40% as specified)
        investigation_notes = []
        if abs(change_percent) >= self.thresholds['major_anomaly']:
            investigation_notes = self._generate_investigation_notes(
                anomaly, primary_cause, historical_data
            )
        
        # Update enhanced anomaly
        enhanced_anomaly.update({
            'potential_causes': potential_causes,
            'primary_cause': primary_cause,
            'sustainability_assessment': sustainability,
            'explanation': explanation,
            'investigation_notes': investigation_notes,
            'recurring_adjustment': self._calculate_recurring_adjustment(primary_cause, change_percent),
            'quality_impact': self._assess_quality_impact(primary_cause, change_percent)
        })
        
        return enhanced_anomaly
    
    def _identify_potential_causes(self, anomaly: Dict[str, Any], 
                                 historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential causes for the EPS anomaly"""
        causes = []
        year_index = anomaly['year_index']
        change_percent = anomaly['change_percent']
        
        # Check for special items
        special_items = historical_data.get('special_items', [])
        if year_index < len(special_items) and abs(special_items[year_index]) > 0:
            impact = special_items[year_index] / anomaly['current_eps'] if anomaly['current_eps'] != 0 else 0
            causes.append({
                'type': AnomalyType.EXTRAORDINARY_GAIN if special_items[year_index] > 0 else AnomalyType.ONE_TIME_CHARGE,
                'confidence': 0.8,
                'impact_percentage': impact * 100,
                'description': f"Special item of ${special_items[year_index]:.2f} detected"
            })
        
        # Revenue analysis
        revenues = historical_data.get('revenues', [])
        if len(revenues) > year_index > 0:
            revenue_change = (revenues[year_index] - revenues[year_index-1]) / revenues[year_index-1]
            
            if abs(revenue_change) > 0.15:  # Significant revenue change
                causes.append({
                    'type': AnomalyType.ACQUISITION_IMPACT if revenue_change > 0.30 else AnomalyType.NORMAL_VOLATILITY,
                    'confidence': 0.6,
                    'impact_percentage': revenue_change * 100,
                    'description': f"Revenue change of {revenue_change*100:.1f}%"
                })
        
        # Margin analysis (if EPS change differs significantly from revenue change)
        if len(revenues) > year_index > 0:
            revenue_change = (revenues[year_index] - revenues[year_index-1]) / revenues[year_index-1]
            eps_change = change_percent
            
            margin_effect = eps_change - revenue_change
            if abs(margin_effect) > 0.10:  # 10% difference suggests operational changes
                cause_type = AnomalyType.RESTRUCTURING if margin_effect > 0 else AnomalyType.ONE_TIME_CHARGE
                causes.append({
                    'type': cause_type,
                    'confidence': 0.5,
                    'impact_percentage': margin_effect * 100,
                    'description': f"Margin improvement/deterioration of {margin_effect*100:.1f}%"
                })
        
        # Tax analysis (simplified)
        if change_percent > 0.20 and len(causes) == 0:  # Unexplained positive anomaly
            causes.append({
                'type': AnomalyType.TAX_BENEFIT,
                'confidence': 0.4,
                'impact_percentage': change_percent * 30,  # Assume 30% tax impact
                'description': "Potential tax benefit or rate reduction"
            })
        
        # Default to normal volatility if no clear cause
        if not causes:
            causes.append({
                'type': AnomalyType.NORMAL_VOLATILITY,
                'confidence': 0.7,
                'impact_percentage': change_percent * 100,
                'description': "Normal business cycle volatility"
            })
        
        return causes
    
    def _determine_primary_cause(self, potential_causes: List[Dict[str, Any]], 
                                change_percent: float) -> Dict[str, Any]:
        """Determine the most likely primary cause of the anomaly"""
        if not potential_causes:
            return {
                'type': AnomalyType.NORMAL_VOLATILITY,
                'confidence': 0.3,
                'description': "Unknown cause"
            }
        
        # Sort by confidence and impact
        sorted_causes = sorted(potential_causes, 
                             key=lambda x: (x['confidence'], abs(x['impact_percentage'])), 
                             reverse=True)
        
        return sorted_causes[0]
    
    def _assess_earnings_sustainability(self, anomaly: Dict[str, Any], 
                                     historical_data: Dict[str, Any],
                                     primary_cause: Dict[str, Any]) -> Dict[str, Any]:
        """Assess sustainability of the earnings change"""
        
        cause_type = primary_cause['type']
        change_percent = anomaly['change_percent']
        
        # Sustainability based on cause type
        sustainability_map = {
            AnomalyType.NORMAL_VOLATILITY: {'sustainable': True, 'confidence': 0.7},
            AnomalyType.ACQUISITION_IMPACT: {'sustainable': True, 'confidence': 0.8},
            AnomalyType.RESTRUCTURING: {'sustainable': True, 'confidence': 0.6},
            AnomalyType.EXTRAORDINARY_GAIN: {'sustainable': False, 'confidence': 0.9},
            AnomalyType.ONE_TIME_CHARGE: {'sustainable': False, 'confidence': 0.9},
            AnomalyType.ASSET_SALE: {'sustainable': False, 'confidence': 0.95},
            AnomalyType.TAX_BENEFIT: {'sustainable': False, 'confidence': 0.8},
            AnomalyType.ACCOUNTING_CHANGE: {'sustainable': False, 'confidence': 0.7}
        }
        
        base_assessment = sustainability_map.get(cause_type, {'sustainable': False, 'confidence': 0.5})
        
        # Adjust based on magnitude
        if abs(change_percent) > 0.5:  # 50%+ changes are likely less sustainable
            base_assessment['confidence'] *= 0.8
            base_assessment['sustainable'] = False
        
        return {
            'is_sustainable': base_assessment['sustainable'],
            'confidence': base_assessment['confidence'],
            'rationale': self._get_sustainability_rationale(cause_type, change_percent),
            'recommended_adjustment': 1.0 - change_percent if not base_assessment['sustainable'] else 0.0
        }
    
    def _get_sustainability_rationale(self, cause_type: AnomalyType, change_percent: float) -> str:
        """Get rationale for sustainability assessment"""
        
        rationale_map = {
            AnomalyType.NORMAL_VOLATILITY: "Earnings change appears to be part of normal business cycle",
            AnomalyType.ACQUISITION_IMPACT: "Acquisition-related earnings likely sustainable if integration successful",
            AnomalyType.RESTRUCTURING: "Restructuring benefits may be sustainable but watch for future charges",
            AnomalyType.EXTRAORDINARY_GAIN: "One-time gain unlikely to repeat in future periods",
            AnomalyType.ONE_TIME_CHARGE: "One-time charge should not impact future earnings",
            AnomalyType.ASSET_SALE: "Asset sale proceeds are non-recurring and will not repeat",
            AnomalyType.TAX_BENEFIT: "Tax benefits may not be available in future periods",
            AnomalyType.ACCOUNTING_CHANGE: "Accounting changes may not reflect underlying business improvement"
        }
        
        base_rationale = rationale_map.get(cause_type, "Unknown cause makes sustainability difficult to assess")
        
        if abs(change_percent) > 0.5:
            base_rationale += f". Large magnitude ({change_percent*100:.0f}%) suggests non-recurring nature."
        
        return base_rationale
    
    def _generate_anomaly_explanation(self, anomaly: Dict[str, Any], 
                                    primary_cause: Dict[str, Any],
                                    sustainability: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the anomaly"""
        
        year = anomaly['year']
        change_percent = anomaly['change_percent']
        direction = "increased" if change_percent > 0 else "decreased"
        
        cause_desc = primary_cause.get('description', 'Unknown cause')
        cause_confidence = primary_cause.get('confidence', 0) * 100
        
        explanation = f"In {year}, EPS {direction} by {abs(change_percent)*100:.1f}%. "
        explanation += f"Primary cause appears to be: {cause_desc} "
        explanation += f"(confidence: {cause_confidence:.0f}%). "
        
        if sustainability['is_sustainable']:
            explanation += "This earnings change appears to be sustainable for future periods."
        else:
            explanation += "This earnings change is likely non-recurring and should be adjusted for valuation purposes."
        
        return explanation
    
    def _generate_investigation_notes(self, anomaly: Dict[str, Any], 
                                    primary_cause: Dict[str, Any],
                                    historical_data: Dict[str, Any]) -> List[str]:
        """
        Generate detailed investigation notes for major anomalies (>40% as specified)
        These help investors understand what happened and why
        """
        notes = []
        change_percent = anomaly['change_percent']
        year = anomaly['year']
        
        # Header note
        notes.append(f"🔍 DEEP DIVE ANALYSIS: {abs(change_percent)*100:.1f}% EPS change in {year}")
        
        # Cause analysis
        cause_type = primary_cause.get('type', AnomalyType.NORMAL_VOLATILITY)
        
        if cause_type == AnomalyType.EXTRAORDINARY_GAIN:
            notes.extend([
                "• Extraordinary gain detected - likely from asset sales or settlements",
                "• This gain should be excluded from normalized earnings calculations",
                "• Check financial statements for details on 'Other Income' or 'Non-operating Income'"
            ])
        
        elif cause_type == AnomalyType.ASSET_SALE:
            notes.extend([
                "• Probable asset sale or divestiture boosting earnings",
                "• These are one-time proceeds that won't repeat",
                "• Look for 'Gain on Sale of Assets' in income statement",
                "• Consider what assets were sold and impact on future earning power"
            ])
        
        elif cause_type == AnomalyType.TAX_BENEFIT:
            notes.extend([
                "• Potential tax benefit or rate reduction",
                "• May result from tax law changes, loss carryforwards, or settlements",
                "• Check effective tax rate vs historical average",
                "• Assess likelihood of similar benefits in future years"
            ])
        
        elif cause_type == AnomalyType.RESTRUCTURING:
            notes.extend([
                "• Restructuring or operational improvements detected",
                "• Could indicate cost reduction or efficiency gains", 
                "• Monitor whether benefits persist in subsequent quarters",
                "• Watch for future restructuring charges"
            ])
        
        elif cause_type == AnomalyType.ACQUISITION_IMPACT:
            notes.extend([
                "• Acquisition or merger likely impacting earnings",
                "• Assess whether acquired entity is profitable",
                "• Consider integration costs and synergies",
                "• Evaluate pro-forma earnings excluding acquisition effects"
            ])
        
        # Magnitude-specific notes
        if abs(change_percent) >= 1.0:  # 100%+ change
            notes.extend([
                "⚠️  EXTREME CHANGE: >100% earnings change is highly unusual",
                "• Such dramatic changes are rarely sustainable",
                "• Strong indication of non-recurring items",
                "• Use extreme caution in valuation models"
            ])
        
        # Investigation recommendations
        notes.extend([
            "",
            "📋 RECOMMENDED INVESTIGATION STEPS:",
            "• Review quarterly earnings reports for this period",
            "• Analyze cash flow statement for operating vs non-operating items",
            "• Compare adjusted/normalized earnings provided by management",
            "• Check analyst reports for explanations of earnings drivers",
            "• Monitor subsequent quarters to assess sustainability"
        ])
        
        return notes
    
    def _calculate_recurring_adjustment(self, primary_cause: Dict[str, Any], 
                                      change_percent: float) -> float:
        """Calculate adjustment factor to normalize for non-recurring items"""
        
        cause_type = primary_cause.get('type', AnomalyType.NORMAL_VOLATILITY)
        
        # Non-recurring items should be adjusted out
        non_recurring_types = [
            AnomalyType.EXTRAORDINARY_GAIN,
            AnomalyType.ASSET_SALE,
            AnomalyType.TAX_BENEFIT,
            AnomalyType.ONE_TIME_CHARGE
        ]
        
        if cause_type in non_recurring_types:
            # Adjust out the full impact
            return change_percent
        
        elif cause_type == AnomalyType.ACCOUNTING_CHANGE:
            # Adjust out 50% of accounting changes
            return change_percent * 0.5
        
        else:
            # No adjustment for recurring items
            return 0.0
    
    def _assess_quality_impact(self, primary_cause: Dict[str, Any], change_percent: float) -> float:
        """Assess impact on earnings quality (0-1 scale, 1 = highest quality)"""
        
        cause_type = primary_cause.get('type', AnomalyType.NORMAL_VOLATILITY)
        
        # Quality impact by cause type
        quality_impacts = {
            AnomalyType.NORMAL_VOLATILITY: 0.9,      # High quality
            AnomalyType.ACQUISITION_IMPACT: 0.7,     # Medium-high quality
            AnomalyType.RESTRUCTURING: 0.6,          # Medium quality
            AnomalyType.ACCOUNTING_CHANGE: 0.4,      # Low-medium quality
            AnomalyType.TAX_BENEFIT: 0.3,            # Low quality
            AnomalyType.EXTRAORDINARY_GAIN: 0.2,     # Very low quality
            AnomalyType.ASSET_SALE: 0.1,             # Lowest quality
            AnomalyType.ONE_TIME_CHARGE: 0.8         # One-time charges don't hurt future quality
        }
        
        base_quality = quality_impacts.get(cause_type, 0.5)
        
        # Adjust for magnitude - larger changes reduce quality
        magnitude_penalty = min(abs(change_percent) * 0.5, 0.3)  # Max 30% penalty
        
        return max(base_quality - magnitude_penalty, 0.1)  # Minimum 10% quality
    
    def _calculate_quality_adjusted_eps(self, original_eps: List[float], 
                                      anomalies: List[Dict[str, Any]]) -> List[float]:
        """Calculate quality-adjusted EPS series with non-recurring items removed"""
        
        adjusted_eps = original_eps.copy()
        
        for anomaly in anomalies:
            year_index = anomaly['year_index']
            adjustment = anomaly.get('recurring_adjustment', 0)
            
            if adjustment != 0 and year_index < len(adjusted_eps):
                # Remove the non-recurring component
                original_value = original_eps[year_index]
                adjusted_value = original_value / (1 + adjustment)
                adjusted_eps[year_index] = adjusted_value
        
        return adjusted_eps
    
    def _calculate_sustainable_trend(self, quality_adjusted_eps: List[float]) -> float:
        """Calculate sustainable earnings growth trend"""
        
        if len(quality_adjusted_eps) < 2:
            return 0.0
        
        # Calculate CAGR of quality-adjusted earnings
        start_value = quality_adjusted_eps[0]
        end_value = quality_adjusted_eps[-1]
        years = len(quality_adjusted_eps) - 1
        
        if start_value <= 0:
            return 0.0
        
        cagr = ((end_value / start_value) ** (1/years)) - 1
        
        # Cap at reasonable levels
        return max(min(cagr, 0.25), -0.15)  # Between -15% and 25%
    
    def _calculate_earnings_quality_score(self, original_eps: List[float], 
                                        anomalies: List[Dict[str, Any]],
                                        quality_adjusted_eps: List[float]) -> float:
        """Calculate overall earnings quality score (0-100 scale)"""
        
        scores = {}
        
        # 1. Consistency score (30% weight)
        eps_cv = np.std(original_eps) / np.mean(original_eps) if np.mean(original_eps) > 0 else 1
        consistency_score = max(0, 100 - (eps_cv * 100))  # Lower CV = higher score
        scores['consistency'] = consistency_score
        
        # 2. Recurring quality score (25% weight)
        total_anomaly_impact = sum(abs(a.get('recurring_adjustment', 0)) for a in anomalies)
        avg_anomaly_impact = total_anomaly_impact / len(original_eps) if original_eps else 0
        recurring_score = max(0, 100 - (avg_anomaly_impact * 200))  # Penalize non-recurring items
        scores['recurring_quality'] = recurring_score
        
        # 3. Growth sustainability score (20% weight)
        sustainable_trend = self._calculate_sustainable_trend(quality_adjusted_eps)
        if 0 <= sustainable_trend <= 0.15:  # Ideal growth range
            growth_score = 100
        elif sustainable_trend > 0.15:  # Too high growth
            growth_score = max(50, 100 - (sustainable_trend - 0.15) * 200)
        else:  # Negative growth
            growth_score = max(0, 50 + sustainable_trend * 200)
        scores['growth_sustainability'] = growth_score
        
        # 4. Accounting quality score (15% weight)
        # Simplified - penalize for accounting-related anomalies
        accounting_penalties = sum(1 for a in anomalies 
                                 if a.get('primary_cause', {}).get('type') == AnomalyType.ACCOUNTING_CHANGE)
        accounting_score = max(0, 100 - (accounting_penalties * 20))
        scores['accounting_quality'] = accounting_score
        
        # 5. Anomaly frequency score (10% weight)
        anomaly_rate = len(anomalies) / len(original_eps) if original_eps else 0
        frequency_score = max(0, 100 - (anomaly_rate * 100))
        scores['anomaly_frequency'] = frequency_score
        
        # Calculate weighted average
        weighted_score = sum(scores[category] * self.quality_weights[category] 
                           for category in scores)
        
        return round(weighted_score, 1)
    
    def _generate_recommendations(self, original_eps: List[float], 
                                anomalies: List[Dict[str, Any]],
                                quality_score: float,
                                sustainable_trend: float) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        # Quality-based recommendations
        if quality_score >= 80:
            recommendations.append("✅ High earnings quality - EPS data is reliable for valuation")
        elif quality_score >= 60:
            recommendations.append("⚠️ Moderate earnings quality - Use quality-adjusted EPS for analysis")
        else:
            recommendations.append("🔴 Low earnings quality - Exercise extreme caution in valuation")
        
        # Anomaly-specific recommendations
        major_anomalies = [a for a in anomalies if a['severity'] in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]]
        
        if major_anomalies:
            recommendations.append(f"🔍 {len(major_anomalies)} major earnings anomalies detected - Review investigation notes")
            
            # Check for recent anomalies
            recent_anomalies = [a for a in major_anomalies if a['year'] >= 2022]  # Last 2 years
            if recent_anomalies:
                recommendations.append("📊 Recent major anomalies detected - Use normalized earnings for current valuation")
        
        # Trend-based recommendations
        if sustainable_trend > 0.10:
            recommendations.append(f"📈 Strong sustainable growth trend ({sustainable_trend*100:.1f}%) - Consider growth premium")
        elif sustainable_trend < -0.05:
            recommendations.append(f"📉 Declining earnings trend ({sustainable_trend*100:.1f}%) - Apply valuation discount")
        else:
            recommendations.append("📊 Stable earnings trend - Use average EPS for conservative valuation")
        
        # Graham-specific recommendations
        avg_eps = np.mean(original_eps) if original_eps else 0
        if avg_eps > 0:
            recommendations.append(f"💡 Graham-style analysis: Use {avg_eps:.2f} as average EPS over {len(original_eps)} years")
        
        # Volatility recommendations
        eps_volatility = np.std(original_eps) / np.mean(original_eps) if np.mean(original_eps) > 0 else 0
        if eps_volatility > self.thresholds['volatility_threshold']:
            recommendations.append("⚡ High earnings volatility detected - Increase margin of safety requirement")
        
        return recommendations
    
    def _create_error_result(self, symbol: str, error_msg: str, years: int) -> EPSAnomalyResult:
        """Create error result for failed analysis"""
        return EPSAnomalyResult(
            symbol=symbol,
            analysis_period=f"{years} years",
            historical_eps=[],
            average_eps=0.0,
            anomalies_detected=[],
            quality_adjusted_eps=[],
            sustainable_eps_trend=0.0,
            earnings_quality_score=0.0,
            recommendations=[f"❌ Analysis failed: {error_msg}"],
            timestamp=datetime.now()
        )