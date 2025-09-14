"""
Financial Calculations Utility Module
Provides common financial calculations and ratios
"""

import math
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FinancialCalculations:
    """
    A comprehensive financial calculations utility class
    """
    
    def __init__(self):
        """Initialize financial calculations utility"""
        pass
    
    def calculate_ratio(self, numerator: float, denominator: float) -> float:
        """
        Calculate a ratio safely, handling division by zero
        
        Args:
            numerator: The top number in the ratio
            denominator: The bottom number in the ratio
            
        Returns:
            float: The calculated ratio or 0 if denominator is 0
        """
        try:
            return numerator / denominator if denominator != 0 else 0.0
        except (TypeError, ValueError):
            return 0.0
    
    def calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """
        Calculate percentage change between two values
        
        Args:
            old_value: The original value
            new_value: The new value
            
        Returns:
            float: Percentage change
        """
        if old_value == 0:
            return 0.0
        try:
            return ((new_value - old_value) / abs(old_value)) * 100
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0
    
    def calculate_compound_annual_growth_rate(self, beginning_value: float, ending_value: float, years: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR)
        
        Args:
            beginning_value: Starting value
            ending_value: Ending value  
            years: Number of years
            
        Returns:
            float: CAGR as a decimal (0.10 = 10%)
        """
        if beginning_value <= 0 or ending_value <= 0 or years <= 0:
            return 0.0
        try:
            return ((ending_value / beginning_value) ** (1/years)) - 1
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def calculate_average(self, values: List[float]) -> float:
        """
        Calculate arithmetic mean of a list of values
        
        Args:
            values: List of numerical values
            
        Returns:
            float: Average value
        """
        if not values:
            return 0.0
        try:
            return statistics.mean([v for v in values if v is not None])
        except (TypeError, ValueError, statistics.StatisticsError):
            return 0.0
    
    def calculate_median(self, values: List[float]) -> float:
        """
        Calculate median of a list of values
        
        Args:
            values: List of numerical values
            
        Returns:
            float: Median value
        """
        if not values:
            return 0.0
        try:
            clean_values = [v for v in values if v is not None]
            return statistics.median(clean_values) if clean_values else 0.0
        except (TypeError, ValueError, statistics.StatisticsError):
            return 0.0
    
    def calculate_volatility(self, returns: List[float], annualize: bool = True) -> float:
        """
        Calculate volatility (standard deviation) of returns
        
        Args:
            returns: List of return values
            annualize: Whether to annualize the volatility
            
        Returns:
            float: Volatility
        """
        if not returns or len(returns) < 2:
            return 0.0
        try:
            clean_returns = [r for r in returns if r is not None]
            if len(clean_returns) < 2:
                return 0.0
            
            vol = statistics.stdev(clean_returns)
            if annualize:
                vol = vol * math.sqrt(252)  # 252 trading days in a year
            return vol
        except (TypeError, ValueError, statistics.StatisticsError):
            return 0.0
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns: List of return values
            risk_free_rate: Risk-free rate (default 2%)
            
        Returns:
            float: Sharpe ratio
        """
        if not returns:
            return 0.0
        try:
            avg_return = self.calculate_average(returns)
            volatility = self.calculate_volatility(returns)
            
            if volatility == 0:
                return 0.0
                
            return (avg_return - risk_free_rate) / volatility
        except (TypeError, ValueError):
            return 0.0
    
    def calculate_beta(self, stock_returns: List[float], market_returns: List[float]) -> float:
        """
        Calculate beta (correlation with market)
        
        Args:
            stock_returns: List of stock return values
            market_returns: List of market return values
            
        Returns:
            float: Beta value
        """
        if not stock_returns or not market_returns or len(stock_returns) != len(market_returns):
            return 1.0  # Default beta
        
        try:
            # Calculate covariance and variance
            stock_mean = self.calculate_average(stock_returns)
            market_mean = self.calculate_average(market_returns)
            
            covariance = sum((s - stock_mean) * (m - market_mean) 
                           for s, m in zip(stock_returns, market_returns)) / len(stock_returns)
            
            market_variance = sum((m - market_mean) ** 2 for m in market_returns) / len(market_returns)
            
            if market_variance == 0:
                return 1.0
                
            return covariance / market_variance
        except (TypeError, ValueError, ZeroDivisionError):
            return 1.0
    
    def calculate_present_value(self, future_value: float, discount_rate: float, periods: int) -> float:
        """
        Calculate present value of future cash flow
        
        Args:
            future_value: Future cash flow
            discount_rate: Discount rate (as decimal)
            periods: Number of periods
            
        Returns:
            float: Present value
        """
        if periods <= 0 or discount_rate < -1:
            return future_value
        try:
            return future_value / ((1 + discount_rate) ** periods)
        except (TypeError, ValueError, ZeroDivisionError):
            return future_value
    
    def calculate_future_value(self, present_value: float, growth_rate: float, periods: int) -> float:
        """
        Calculate future value of present cash flow
        
        Args:
            present_value: Current value
            growth_rate: Growth rate (as decimal)
            periods: Number of periods
            
        Returns:
            float: Future value
        """
        if periods <= 0:
            return present_value
        try:
            return present_value * ((1 + growth_rate) ** periods)
        except (TypeError, ValueError):
            return present_value
    
    def calculate_npv(self, cash_flows: List[float], discount_rate: float) -> float:
        """
        Calculate Net Present Value
        
        Args:
            cash_flows: List of cash flows (first is initial investment, negative)
            discount_rate: Discount rate (as decimal)
            
        Returns:
            float: Net Present Value
        """
        if not cash_flows:
            return 0.0
        
        try:
            npv = 0.0
            for i, cf in enumerate(cash_flows):
                npv += self.calculate_present_value(cf, discount_rate, i)
            return npv
        except (TypeError, ValueError):
            return 0.0
    
    def calculate_irr(self, cash_flows: List[float], max_iterations: int = 100) -> float:
        """
        Calculate Internal Rate of Return using Newton-Raphson method
        
        Args:
            cash_flows: List of cash flows
            max_iterations: Maximum iterations for calculation
            
        Returns:
            float: IRR as decimal
        """
        if not cash_flows or len(cash_flows) < 2:
            return 0.0
        
        # Start with an initial guess
        rate = 0.1
        tolerance = 1e-6
        
        try:
            for _ in range(max_iterations):
                npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
                derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows) if i > 0)
                
                if abs(derivative) < tolerance:
                    break
                    
                new_rate = rate - npv / derivative
                if abs(new_rate - rate) < tolerance:
                    return new_rate
                rate = new_rate
                
            return rate
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0
    
    def safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        Safely divide two numbers with default fallback
        
        Args:
            numerator: Top number
            denominator: Bottom number
            default: Default value if division fails
            
        Returns:
            float: Result of division or default
        """
        try:
            if denominator == 0 or denominator is None:
                return default
            return numerator / denominator
        except (TypeError, ValueError):
            return default
    
    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 range
        
        Args:
            value: Value to normalize
            min_val: Minimum value in range
            max_val: Maximum value in range
            
        Returns:
            float: Normalized value (0-1)
        """
        if max_val == min_val:
            return 0.5  # Middle value if no range
        try:
            return (value - min_val) / (max_val - min_val)
        except (TypeError, ValueError):
            return 0.5
    
    def calculate_z_score(self, value: float, mean: float, std_dev: float) -> float:
        """
        Calculate Z-score (standard score)
        
        Args:
            value: Value to score
            mean: Mean of distribution
            std_dev: Standard deviation
            
        Returns:
            float: Z-score
        """
        if std_dev == 0:
            return 0.0
        try:
            return (value - mean) / std_dev
        except (TypeError, ValueError):
            return 0.0