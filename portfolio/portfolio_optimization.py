# src/portfolio/portfolio_optimizer.py

import numpy as np
import pandas as pd
import warnings
from scipy.optimize import minimize
from typing import Dict, List, Tuple
import yfinance as yf

class PortfolioOptimizer:
    def __init__(self):
        self.risk_free_rate = 0.02
        self.min_weight = 0.03
        self.max_weight = 0.25
        self.user_min_weights = {}  # Add this to store user-specified minimums

    def get_historical_data(self, symbols: List[str], period: str = '1y') -> pd.DataFrame:
        """Fetch historical data for multiple symbols"""
        data = pd.DataFrame()
        valid_symbols = []

        for symbol in symbols:
            try:
                # Skip crypto symbols
                if symbol.upper() in ['BTC', 'GBTC']:
                    print(f"Skipping {symbol} - cryptocurrency not supported in optimization")
                    continue
                    
                stock = yf.Ticker(symbol)
                hist = stock.history(period=period)
                if not hist.empty:
                    data[symbol] = hist['Close']
                    valid_symbols.append(symbol)
                else:
                    print(f"No data available for {symbol}")
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
                
        # Return both the data and valid symbols list to ensure consistent symbols throughout
        return data[valid_symbols]  # Only keep columns for valid symbols

    def get_dividend_yields(self, symbols: List[str]) -> Dict[str, float]:
        """Get current dividend yields for symbols"""
        yields = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                yields[symbol] = info.get('dividendYield', 0) or 0
            except Exception as e:
                print(f"Error fetching dividend yield for {symbol}: {str(e)}")
                yields[symbol] = 0
        return yields

    def calculate_portfolio_return(self, returns: pd.DataFrame, weights: np.array) -> float:
        """Calculate annualized portfolio return"""
        try:
            return np.sum(returns.mean() * weights) * 252
        except Exception as e:
            print(f"Error calculating portfolio return: {str(e)}")
            return 0.0

    def calculate_portfolio_risk(self, returns: pd.DataFrame, weights: np.array) -> float:
        """Calculate annualized portfolio risk"""
        try:
            return np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        except Exception as e:
            print(f"Error calculating portfolio risk: {str(e)}")
            return 0.0

    def calculate_sharpe_ratio(self, returns: pd.DataFrame, weights: np.array) -> float:
        """Calculate portfolio Sharpe ratio"""
        port_return = self.calculate_portfolio_return(returns, weights)
        port_risk = self.calculate_portfolio_risk(returns, weights)
        if port_risk == 0:
            return 0.0
        return (port_return - self.risk_free_rate) / port_risk

    def calculate_portfolio_dividend_yield(self, yields: Dict[str, float], weights: np.array) -> float:
        """Calculate weighted average dividend yield"""
        return sum(yields[symbol] * weight for symbol, weight in zip(yields.keys(), weights))

    def set_minimum_allocation(self, symbol: str, min_percentage: float):
        """Set minimum allocation for a specific symbol"""
        if 0 <= min_percentage <= 100:
            self.user_min_weights[symbol] = min_percentage / 100

    def optimize_portfolio(self, symbols: List[str], objective: str = 'sharpe', 
                      target_return: float = None, target_risk: float = None,
                      target_dividend_yield: float = None, profile_constraints: Dict = None) -> Dict:
        try:
            # Filter out invalid symbols
            valid_symbols = [s for s in symbols if s.upper() not in ['BTC', 'GBTC']]
            print(f"\nOptimizing portfolio with {len(valid_symbols)} assets...")
            
            # Get historical data (now returns filtered data)
            data = self.get_historical_data(valid_symbols)
            if data.empty:
                raise ValueError("No valid data available")
            
            # Update valid_symbols to match actual available data
            valid_symbols = list(data.columns)
            if len(valid_symbols) < 3:  # Minimum diversification requirement
                raise ValueError("Need at least 3 valid stocks for optimization")
                
            print(f"Proceeding with {len(valid_symbols)} valid assets: {', '.join(valid_symbols)}")
            
            # Use profile constraints if provided
            if profile_constraints:
                if target_return is None:
                    target_return = profile_constraints.get('min_return')
                if target_risk is None:
                    target_risk = profile_constraints.get('max_risk')

            # Calculate returns more safely
            returns = data.pct_change(fill_method=None).dropna()
            if len(returns) < 100:  # Ensure sufficient data points
                raise ValueError("Insufficient historical data")
                
            # Initial weights - equal distribution
            num_assets = len(valid_symbols)
            init_weights = np.array([1/num_assets] * num_assets)
            
            # Base constraints and target processing moved here
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
            ]
            
            # Individual minimum weight constraints
            for i, symbol in enumerate(valid_symbols):
                min_weight = max(self.user_min_weights.get(symbol, self.min_weight), self.min_weight)
                constraints.append(
                    {'type': 'ineq', 'fun': lambda x, idx=i: x[idx] - min_weight}
                )
            
            # Return constraints (single definition with target conversion)
            if target_return is not None:
                target_return = target_return / 100  # Convert to decimal once
                constraints.extend([
                    {'type': 'ineq', 'fun': lambda x: self.calculate_portfolio_return(returns, x) - target_return * 0.95},  # Within 5% below target
                    {'type': 'ineq', 'fun': lambda x: target_return * 1.05 - self.calculate_portfolio_return(returns, x)}   # Within 5% above target
                ])
                
            # Risk constraints (single definition with target conversion)
            if target_risk is not None:
                target_risk = target_risk / 100  # Convert to decimal once
                constraints.append(
                    {'type': 'ineq', 'fun': lambda x: target_risk * 1.2 - self.calculate_portfolio_risk(returns, x)}
                )

            # Single bounds definition
            bounds = tuple((0.05, 0.20) for _ in range(num_assets))  # Min 5%, Max 20%
            
            # Diversification constraint
            constraints.append(
                {'type': 'ineq', 'fun': lambda x: 0.50 - sum(sorted(x, reverse=True)[:3])}  # Top 3 positions < 50%
            )
            
            # Define objective function with better error handling
            def objective_function(weights):
                try:
                    if objective == 'sharpe':
                        return -self.calculate_sharpe_ratio(returns, weights)
                    elif objective == 'min_risk':
                        return self.calculate_portfolio_risk(returns, weights)
                    else:
                        return -self.calculate_portfolio_return(returns, weights)
                except Exception as e:
                    print(f"Error in objective function: {str(e)}")
                    return float('inf')

            # Multiple optimization attempts with different initial weights
            best_result = None
            best_score = float('inf')
            
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                
                for attempt in range(10):  # Increased attempts
                    try:
                        result = minimize(
                            objective_function,
                            init_weights,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints,
                            options={
                                'maxiter': 2000,
                                'ftol': 1e-8,  # Increased precision
                                'disp': False
                            }
                        )
                        
                        if result.success:
                            portfolio_return = self.calculate_portfolio_return(returns, result.x)
                            portfolio_risk = self.calculate_portfolio_risk(returns, result.x)
                            
                            # More relaxed conditions for accepting a result
                            conditions_met = True
                            if target_return is not None:
                                conditions_met = conditions_met and (portfolio_return >= target_return * 0.8)
                            if target_risk is not None:
                                conditions_met = conditions_met and (portfolio_risk <= target_risk * 1.2)
                            
                            if conditions_met and result.fun < best_score:
                                best_result = result
                                best_score = result.fun
                        
                        # Generate new starting weights for next attempt
                        init_weights = np.random.random(num_assets)
                        init_weights /= init_weights.sum()
                        
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed: {str(e)}")
                        continue
            
            if best_result is None:
                print("\nTrying optimization with relaxed constraints...")
                try:
                    # Minimal constraints for last attempt
                    basic_constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                    result = minimize(
                        objective_function,
                        init_weights,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=basic_constraints,
                        options={'maxiter': 3000, 'ftol': 1e-6}
                    )
                    if result.success:
                        best_result = result
                except Exception as e:
                    print(f"\nFinal optimization attempt failed: {str(e)}")
            
            if best_result is None:
                raise ValueError("No successful optimization found")
            
            # Calculate portfolio metrics
            optimized_weights = best_result.x
            portfolio_return = self.calculate_portfolio_return(returns, optimized_weights) * 100
            portfolio_risk = self.calculate_portfolio_risk(returns, optimized_weights) * 100
            
            # Check targets and concentration
            if target_return and portfolio_return < target_return * 90:
                print("\nWarning: Achieved return significantly below target")
            if target_risk and portfolio_risk > target_risk * 110:
                print("\nWarning: Portfolio risk exceeds target")
                
            concentration = sum(sorted(optimized_weights, reverse=True)[:3])
            if concentration > 0.6:
                print("\nWarning: High portfolio concentration")
            
            # Format results
            portfolio_metrics = {
                'weights': {symbol: round(weight * 100, 2) for symbol, weight 
                        in zip(valid_symbols, optimized_weights)},
                'expected_return': round(portfolio_return, 2),
                'risk': round(portfolio_risk, 2),
                'sharpe_ratio': round(self.calculate_sharpe_ratio(returns, optimized_weights), 2),
                'dividend_yield': round(self.calculate_portfolio_dividend_yield(
                    self.get_dividend_yields(valid_symbols), optimized_weights) * 100, 2)
            }
            
            return portfolio_metrics
            
        except Exception as e:
            print(f"\nError in portfolio optimization: {str(e)}")
            return {}