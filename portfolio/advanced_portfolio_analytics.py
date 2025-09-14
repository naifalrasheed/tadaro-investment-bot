"""
Advanced Portfolio Analytics Module

This module implements CFA-level portfolio analytics including factor analysis,
performance attribution, and advanced risk metrics.
"""

import numpy as np
import pandas as pd
import scipy.optimize as sco
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import logging
import json

class AdvancedPortfolioAnalytics:
    """
    Advanced portfolio analytics based on CFA curriculum methodologies.
    """
    
    def __init__(self):
        """Initialize the advanced portfolio analytics module."""
        self.logger = logging.getLogger(__name__)
        # Factor returns data would typically be loaded from a database or external source
        self._factor_returns = self._initialize_factor_returns()
    
    def calculate_factor_exposures(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate portfolio exposure to common factors.
        
        Args:
            portfolio: Portfolio data including holdings
            
        Returns:
            Dictionary of factor exposures
        """
        if not portfolio or "holdings" not in portfolio:
            return {}
            
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return {}
            
        # Calculate total portfolio value
        total_value = sum(holding.get("current_value", 0) for holding in holdings)
        if total_value == 0:
            return {}
            
        # Initialize factor exposures
        exposures = {
            "size": 0,
            "value": 0,
            "momentum": 0,
            "quality": 0,
            "volatility": 0,
            "yield": 0,
            "growth": 0
        }
        
        # Calculate weighted factor exposures
        for holding in holdings:
            weight = holding.get("current_value", 0) / total_value
            symbol = holding.get("symbol", "")
            
            # Get stock factor data
            stock_factors = self._get_stock_factor_data(symbol)
            
            # Add weighted factor exposures
            for factor in exposures:
                if factor in stock_factors:
                    exposures[factor] += weight * stock_factors[factor]
        
        return exposures
    
    def perform_style_analysis(self, portfolio: Dict[str, Any], returns_history: pd.DataFrame) -> Dict[str, float]:
        """
        Perform returns-based style analysis.
        
        Args:
            portfolio: Portfolio data
            returns_history: Portfolio returns history
            
        Returns:
            Dictionary of style exposures
        """
        if not isinstance(returns_history, pd.DataFrame) or returns_history.empty:
            return {}
            
        # Ensure returns_history has a datetime index
        if not isinstance(returns_history.index, pd.DatetimeIndex):
            try:
                returns_history.index = pd.to_datetime(returns_history.index)
            except:
                self.logger.error("Returns history index could not be converted to datetime")
                return {}
        
        # Get factor returns for the same period
        factor_returns = self._get_factor_returns_for_period(
            start_date=returns_history.index.min(),
            end_date=returns_history.index.max()
        )
        
        # Check if we have matching factor returns
        if factor_returns.empty:
            self.logger.error("No factor returns available for the period")
            return {}
            
        # Ensure the indices match
        common_dates = returns_history.index.intersection(factor_returns.index)
        if len(common_dates) < 12:  # Need at least 12 data points for meaningful analysis
            self.logger.error(f"Insufficient common dates for style analysis: {len(common_dates)}")
            return {}
            
        # Prepare data for regression
        portfolio_returns = returns_history.loc[common_dates, 'portfolio_return']
        factor_returns_aligned = factor_returns.loc[common_dates]
        
        # Perform constrained regression (weights sum to 1, all weights >= 0)
        try:
            # Initial guess - equal weights
            n_factors = factor_returns_aligned.shape[1]
            initial_weights = np.ones(n_factors) / n_factors
            
            # Constraints: weights sum to 1, all weights >= 0
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_factors))
            
            # Objective function to minimize: sum of squared errors
            def objective(weights):
                return np.sum((portfolio_returns - np.dot(factor_returns_aligned, weights)) ** 2)
            
            # Run optimization
            result = sco.minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                # Create style exposures dictionary
                style_exposures = dict(zip(factor_returns_aligned.columns, result.x))
                # Filter out insignificant exposures (< 1%)
                style_exposures = {k: v for k, v in style_exposures.items() if v > 0.01}
                return style_exposures
            else:
                self.logger.error(f"Style analysis optimization failed: {result.message}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error performing style analysis: {str(e)}")
            return {}
    
    def calculate_risk_metrics(self, portfolio: Dict[str, Any], returns_history: pd.DataFrame, risk_free_rate: float = 0.03) -> Dict[str, float]:
        """
        Calculate advanced risk metrics.
        
        Args:
            portfolio: Portfolio data
            returns_history: Portfolio returns history
            risk_free_rate: Risk-free rate (annual)
            
        Returns:
            Dictionary of risk metrics
        """
        if not isinstance(returns_history, pd.DataFrame) or returns_history.empty:
            return {}
            
        try:
            # Make sure we have necessary columns
            if 'portfolio_return' not in returns_history.columns:
                self.logger.error("Returns history missing 'portfolio_return' column")
                return {}
                
            # Convert annual risk-free rate to match returns frequency
            if 'date' in returns_history.columns:
                returns_history.set_index('date', inplace=True)
                
            # Determine frequency of returns (daily, monthly, etc.)
            if isinstance(returns_history.index, pd.DatetimeIndex):
                # Calculate average days between observations
                avg_days = (returns_history.index[-1] - returns_history.index[0]).days / (len(returns_history) - 1)
                
                # Adjust risk-free rate to match return frequency
                if avg_days < 5:  # Daily returns
                    period_rf = (1 + risk_free_rate) ** (1/252) - 1
                elif avg_days < 45:  # Monthly returns
                    period_rf = (1 + risk_free_rate) ** (1/12) - 1
                else:  # Quarterly or less frequent
                    period_rf = (1 + risk_free_rate) ** (1/4) - 1
            else:
                # Default to assuming monthly returns
                period_rf = (1 + risk_free_rate) ** (1/12) - 1
            
            # Extract returns series
            returns = returns_history['portfolio_return']
            
            # Calculate basic statistics
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Calculate downside deviation (returns below zero)
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() if not downside_returns.empty else 0
            
            # Calculate Sharpe Ratio
            excess_return = mean_return - period_rf
            sharpe_ratio = excess_return / std_return if std_return > 0 else 0
            
            # Calculate Sortino Ratio
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
            
            # Calculate maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns / running_max) - 1
            max_drawdown = drawdown.min()
            
            # Calculate VaR (95% confidence)
            var_95 = np.percentile(returns, 5)
            
            # Calculate Expected Shortfall (CVaR)
            cvar_95 = returns[returns <= var_95].mean()
            
            # Check if benchmark returns are available for beta calculation
            beta = None
            tracking_error = None
            information_ratio = None
            treynor_ratio = None
            
            if 'benchmark_return' in returns_history.columns:
                benchmark_returns = returns_history['benchmark_return']
                
                # Calculate beta (covariance with benchmark / variance of benchmark)
                covariance = np.cov(returns, benchmark_returns)[0, 1]
                benchmark_variance = benchmark_returns.var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 1
                
                # Calculate tracking error (standard deviation of return differences)
                tracking_error = (returns - benchmark_returns).std()
                
                # Calculate Information Ratio
                active_return = returns.mean() - benchmark_returns.mean()
                information_ratio = active_return / tracking_error if tracking_error > 0 else 0
                
                # Calculate Treynor Ratio
                treynor_ratio = excess_return / beta if beta > 0 else 0
            
            # Assemble metrics dictionary
            metrics = {
                "mean_return": mean_return,
                "std_deviation": std_return,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown": max_drawdown,
                "var_95": var_95,
                "cvar_95": cvar_95,
                "downside_deviation": downside_deviation
            }
            
            # Add metrics that require benchmark
            if beta is not None:
                metrics["beta"] = beta
            if tracking_error is not None:
                metrics["tracking_error"] = tracking_error
            if information_ratio is not None:
                metrics["information_ratio"] = information_ratio
            if treynor_ratio is not None:
                metrics["treynor_ratio"] = treynor_ratio
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}
    
    def perform_attribution_analysis(self, 
                                    portfolio: Dict[str, Any], 
                                    benchmark: Dict[str, Any], 
                                    returns_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform Brinson-Fachler performance attribution analysis.
        
        Args:
            portfolio: Portfolio data
            benchmark: Benchmark data
            returns_data: Dictionary containing returns for portfolio and benchmark components
            
        Returns:
            Dictionary with attribution effects
        """
        if not portfolio or not benchmark or not returns_data:
            return {}
            
        try:
            # Initialize attribution effects
            attribution = {
                "allocation_effect": {},
                "selection_effect": {},
                "interaction_effect": {},
                "total_effects": {},
                "total_active_return": 0
            }
            
            # Get portfolio and benchmark sector weights and returns
            portfolio_data = self._get_sector_weights_and_returns(portfolio, returns_data)
            benchmark_data = self._get_sector_weights_and_returns(benchmark, returns_data)
            
            # Calculate total returns
            portfolio_total_return = sum(data["weight"] * data["return"] for data in portfolio_data.values())
            benchmark_total_return = sum(data["weight"] * data["return"] for data in benchmark_data.values())
            
            # Calculate total active return
            attribution["total_active_return"] = portfolio_total_return - benchmark_total_return
            
            # Calculate attribution effects by sector
            for sector in benchmark_data:
                if sector in portfolio_data:
                    p_weight = portfolio_data[sector]["weight"]
                    b_weight = benchmark_data[sector]["weight"]
                    p_return = portfolio_data[sector]["return"]
                    b_return = benchmark_data[sector]["return"]
                    
                    # Calculate effects
                    allocation_effect = (p_weight - b_weight) * (b_return - benchmark_total_return)
                    selection_effect = b_weight * (p_return - b_return)
                    interaction_effect = (p_weight - b_weight) * (p_return - b_return)
                    total_effect = allocation_effect + selection_effect + interaction_effect
                    
                    attribution["allocation_effect"][sector] = allocation_effect
                    attribution["selection_effect"][sector] = selection_effect
                    attribution["interaction_effect"][sector] = interaction_effect
                    attribution["total_effects"][sector] = total_effect
            
            # Calculate sums of effects
            attribution["allocation_effect_total"] = sum(attribution["allocation_effect"].values())
            attribution["selection_effect_total"] = sum(attribution["selection_effect"].values())
            attribution["interaction_effect_total"] = sum(attribution["interaction_effect"].values())
            
            return attribution
            
        except Exception as e:
            self.logger.error(f"Error performing attribution analysis: {str(e)}")
            return {}
    
    def generate_efficient_frontier(self, 
                                   returns_data: pd.DataFrame, 
                                   risk_free_rate: float = 0.03, 
                                   num_portfolios: int = 50) -> List[Dict[str, Any]]:
        """
        Generate the efficient frontier for a set of assets.
        
        Args:
            returns_data: DataFrame of asset returns (assets in columns)
            risk_free_rate: Annual risk-free rate
            num_portfolios: Number of portfolios to generate
            
        Returns:
            List of efficient frontier portfolios
        """
        if not isinstance(returns_data, pd.DataFrame) or returns_data.empty:
            return []
            
        try:
            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean()
            cov_matrix = returns_data.cov()
            
            # Number of assets
            num_assets = len(expected_returns)
            
            # Generate random portfolios
            all_weights = np.zeros((num_portfolios, num_assets))
            returns_array = np.zeros(num_portfolios)
            volatility_array = np.zeros(num_portfolios)
            sharpe_array = np.zeros(num_portfolios)
            
            for i in range(num_portfolios):
                # Generate random weights
                weights = np.random.random(num_assets)
                weights /= np.sum(weights)
                all_weights[i, :] = weights
                
                # Calculate portfolio return
                returns_array[i] = np.sum(expected_returns * weights)
                
                # Calculate portfolio volatility
                volatility_array[i] = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                # Calculate Sharpe Ratio
                sharpe_array[i] = (returns_array[i] - risk_free_rate) / volatility_array[i]
            
            # Create results array
            results = np.column_stack((returns_array, volatility_array, sharpe_array))
            
            # Convert to DataFrame
            results_df = pd.DataFrame(results, columns=['Return', 'Volatility', 'Sharpe'])
            
            # Add weight columns
            for j in range(num_assets):
                results_df[f'Weight_{j}'] = all_weights[:, j]
            
            # Find portfolio with maximum Sharpe ratio
            max_sharpe_idx = results_df['Sharpe'].idxmax()
            max_sharpe_return = results_df.loc[max_sharpe_idx, 'Return']
            max_sharpe_volatility = results_df.loc[max_sharpe_idx, 'Volatility']
            
            # Find portfolio with minimum volatility
            min_vol_idx = results_df['Volatility'].idxmin()
            min_vol_return = results_df.loc[min_vol_idx, 'Return']
            min_vol_volatility = results_df.loc[min_vol_idx, 'Volatility']
            
            # Create efficient frontier portfolios
            frontier_portfolios = []
            
            # Add minimum volatility portfolio
            min_vol_weights = {}
            for j in range(num_assets):
                min_vol_weights[returns_data.columns[j]] = results_df.loc[min_vol_idx, f'Weight_{j}']
                
            frontier_portfolios.append({
                "return": min_vol_return,
                "risk": min_vol_volatility,
                "sharpe": results_df.loc[min_vol_idx, 'Sharpe'],
                "weights": min_vol_weights,
                "type": "Minimum Volatility"
            })
            
            # Add maximum Sharpe ratio portfolio
            max_sharpe_weights = {}
            for j in range(num_assets):
                max_sharpe_weights[returns_data.columns[j]] = results_df.loc[max_sharpe_idx, f'Weight_{j}']
                
            frontier_portfolios.append({
                "return": max_sharpe_return,
                "risk": max_sharpe_volatility,
                "sharpe": results_df.loc[max_sharpe_idx, 'Sharpe'],
                "weights": max_sharpe_weights,
                "type": "Maximum Sharpe"
            })
            
            # Sort results by volatility to get efficient frontier
            results_df = results_df.sort_values('Volatility')
            
            # Add efficient frontier portfolios
            for i in range(0, len(results_df), len(results_df) // 10):  # Select ~10 points along frontier
                if i != min_vol_idx and i != max_sharpe_idx:  # Skip if already added
                    weights = {}
                    for j in range(num_assets):
                        weights[returns_data.columns[j]] = results_df.iloc[i][f'Weight_{j}']
                        
                    frontier_portfolios.append({
                        "return": results_df.iloc[i]['Return'],
                        "risk": results_df.iloc[i]['Volatility'],
                        "sharpe": results_df.iloc[i]['Sharpe'],
                        "weights": weights,
                        "type": "Efficient Frontier"
                    })
            
            # Sort by risk
            frontier_portfolios.sort(key=lambda x: x["risk"])
            
            return frontier_portfolios
            
        except Exception as e:
            self.logger.error(f"Error generating efficient frontier: {str(e)}")
            return []
    
    def optimize_for_maximum_sharpe(self, 
                                   returns_data: pd.DataFrame, 
                                   risk_free_rate: float = 0.03,
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize portfolio for maximum Sharpe ratio.
        
        Args:
            returns_data: DataFrame of asset returns (assets in columns)
            risk_free_rate: Annual risk-free rate
            constraints: Optional constraints on optimization
            
        Returns:
            Dictionary with optimal portfolio weights and metrics
        """
        if not isinstance(returns_data, pd.DataFrame) or returns_data.empty:
            return {}
            
        try:
            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean()
            cov_matrix = returns_data.cov()
            
            # Number of assets
            num_assets = len(expected_returns)
            
            # Initial weights (equal weighted)
            initial_weights = np.ones(num_assets) / num_assets
            
            # Constraints: weights sum to 1
            constraints_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
            # Add custom constraints if provided
            if constraints:
                # Minimum weight constraints
                if 'min_weights' in constraints:
                    min_weights = constraints['min_weights']
                    for i, asset in enumerate(returns_data.columns):
                        if asset in min_weights:
                            constraints_list.append({
                                'type': 'ineq',
                                'fun': lambda x, idx=i, min_w=min_weights[asset]: x[idx] - min_w
                            })
                
                # Maximum weight constraints
                if 'max_weights' in constraints:
                    max_weights = constraints['max_weights']
                    for i, asset in enumerate(returns_data.columns):
                        if asset in max_weights:
                            constraints_list.append({
                                'type': 'ineq',
                                'fun': lambda x, idx=i, max_w=max_weights[asset]: max_w - x[idx]
                            })
                
                # Sector constraints
                if 'sector_constraints' in constraints and 'asset_sectors' in constraints:
                    sector_constraints = constraints['sector_constraints']
                    asset_sectors = constraints['asset_sectors']
                    
                    # Group assets by sector
                    sector_assets = {}
                    for asset, sector in asset_sectors.items():
                        if sector not in sector_assets:
                            sector_assets[sector] = []
                        sector_assets[sector].append(asset)
                    
                    # Add sector constraints
                    for sector, limits in sector_constraints.items():
                        if sector in sector_assets:
                            # Get indices of assets in this sector
                            sector_indices = [i for i, asset in enumerate(returns_data.columns) if asset in sector_assets[sector]]
                            
                            # Minimum sector weight
                            if 'min' in limits:
                                constraints_list.append({
                                    'type': 'ineq',
                                    'fun': lambda x, indices=sector_indices, min_w=limits['min']: sum(x[i] for i in indices) - min_w
                                })
                            
                            # Maximum sector weight
                            if 'max' in limits:
                                constraints_list.append({
                                    'type': 'ineq',
                                    'fun': lambda x, indices=sector_indices, max_w=limits['max']: max_w - sum(x[i] for i in indices)
                                })
            
            # Bounds for weights (default is 0 to 1 for each asset)
            if constraints and 'min_weights' in constraints and 'max_weights' in constraints:
                bounds = []
                for asset in returns_data.columns:
                    min_w = constraints['min_weights'].get(asset, 0)
                    max_w = constraints['max_weights'].get(asset, 1)
                    bounds.append((min_w, max_w))
            else:
                bounds = tuple((0, 1) for _ in range(num_assets))
            
            # Objective function to minimize (negative Sharpe Ratio)
            def neg_sharpe_ratio(weights):
                portfolio_return = np.sum(expected_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
                return -sharpe
            
            # Run optimization
            result = sco.minimize(
                neg_sharpe_ratio,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list
            )
            
            if result.success:
                # Get optimal weights
                optimal_weights = result.x
                
                # Calculate portfolio metrics
                optimal_return = np.sum(expected_returns * optimal_weights)
                optimal_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                optimal_sharpe = (optimal_return - risk_free_rate) / optimal_volatility
                
                # Create weights dictionary
                weights_dict = dict(zip(returns_data.columns, optimal_weights))
                
                # Filter out insignificant weights (< 0.1%)
                weights_dict = {k: v for k, v in weights_dict.items() if v > 0.001}
                
                # Calculate sector weights if asset_sectors provided
                sector_weights = {}
                if constraints and 'asset_sectors' in constraints:
                    for asset, weight in weights_dict.items():
                        if asset in constraints['asset_sectors']:
                            sector = constraints['asset_sectors'][asset]
                            if sector not in sector_weights:
                                sector_weights[sector] = 0
                            sector_weights[sector] += weight
                
                return {
                    "weights": weights_dict,
                    "return": optimal_return,
                    "risk": optimal_volatility,
                    "sharpe": optimal_sharpe,
                    "sector_weights": sector_weights if sector_weights else None
                }
            else:
                self.logger.error(f"Optimization failed: {result.message}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error optimizing for maximum Sharpe ratio: {str(e)}")
            return {}
    
    def optimize_with_risk_constraints(self, 
                                      returns_data: pd.DataFrame, 
                                      max_risk: Optional[float] = None, 
                                      target_return: Optional[float] = None,
                                      current_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Optimize portfolio with risk constraints.
        
        Args:
            returns_data: DataFrame of asset returns (assets in columns)
            max_risk: Maximum portfolio volatility
            target_return: Target portfolio return
            current_weights: Current portfolio weights (for comparison)
            
        Returns:
            Dictionary with optimized portfolio weights and metrics
        """
        if not isinstance(returns_data, pd.DataFrame) or returns_data.empty:
            return {}
            
        try:
            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean()
            cov_matrix = returns_data.cov()
            
            # Number of assets
            num_assets = len(expected_returns)
            
            # Initial weights (equal weighted)
            initial_weights = np.ones(num_assets) / num_assets
            
            # Constraints: weights sum to 1
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
            # Add risk constraint if provided
            if max_risk is not None:
                def risk_constraint(weights):
                    return max_risk - np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                constraints.append({'type': 'ineq', 'fun': risk_constraint})
            
            # Add return constraint if provided
            if target_return is not None:
                def return_constraint(weights):
                    return np.sum(expected_returns * weights) - target_return
                
                constraints.append({'type': 'eq', 'fun': return_constraint})
            
            # Bounds for weights (0 to 1 for each asset)
            bounds = tuple((0, 1) for _ in range(num_assets))
            
            # Objective function depends on what constraints are provided
            if max_risk is not None and target_return is None:
                # Maximize return subject to risk constraint
                def objective(weights):
                    return -np.sum(expected_returns * weights)
                
            elif max_risk is None and target_return is not None:
                # Minimize risk subject to return constraint
                def objective(weights):
                    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
            else:
                # Maximize Sharpe ratio
                def objective(weights):
                    portfolio_return = np.sum(expected_returns * weights)
                    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    return -portfolio_return / portfolio_volatility
            
            # Run optimization
            result = sco.minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                # Get optimal weights
                optimal_weights = result.x
                
                # Calculate portfolio metrics
                optimal_return = np.sum(expected_returns * optimal_weights)
                optimal_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                
                # Create weights dictionary
                weights_dict = dict(zip(returns_data.columns, optimal_weights))
                
                # Filter out insignificant weights (< 0.1%)
                weights_dict = {k: v for k, v in weights_dict.items() if v > 0.001}
                
                # Calculate metrics for current portfolio if provided
                current_portfolio_metrics = None
                if current_weights:
                    # Convert current weights to array in the same order as returns_data
                    current_weights_array = np.zeros(num_assets)
                    for i, asset in enumerate(returns_data.columns):
                        if asset in current_weights:
                            current_weights_array[i] = current_weights[asset]
                    
                    # Normalize weights to sum to 1
                    current_weights_array /= np.sum(current_weights_array)
                    
                    # Calculate current portfolio metrics
                    current_return = np.sum(expected_returns * current_weights_array)
                    current_volatility = np.sqrt(np.dot(current_weights_array.T, np.dot(cov_matrix, current_weights_array)))
                    
                    current_portfolio_metrics = {
                        "return": current_return,
                        "risk": current_volatility
                    }
                
                return {
                    "weights": weights_dict,
                    "return": optimal_return,
                    "risk": optimal_volatility,
                    "current_portfolio": current_portfolio_metrics
                }
            else:
                self.logger.error(f"Optimization failed: {result.message}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error optimizing with risk constraints: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _get_stock_factor_data(self, symbol: str) -> Dict[str, float]:
        """Get factor data for a stock"""
        # In a real implementation, this would fetch real factor data from a database
        # For now, return sample data
        
        # Sample factor data for common stocks
        factor_data = {
            "AAPL": {"size": 1.0, "value": -0.5, "momentum": 0.8, "quality": 0.9, "volatility": -0.3, "yield": -0.4, "growth": 0.8},
            "MSFT": {"size": 1.0, "value": -0.4, "momentum": 0.7, "quality": 0.9, "volatility": -0.4, "yield": -0.2, "growth": 0.8},
            "AMZN": {"size": 1.0, "value": -0.8, "momentum": 0.5, "quality": 0.7, "volatility": 0.3, "yield": -1.0, "growth": 0.9},
            "GOOGL": {"size": 1.0, "value": -0.3, "momentum": 0.6, "quality": 0.8, "volatility": -0.2, "yield": -1.0, "growth": 0.7},
            "META": {"size": 0.9, "value": 0.2, "momentum": 0.9, "quality": 0.6, "volatility": 0.2, "yield": -1.0, "growth": 0.7},
            "TSLA": {"size": 0.9, "value": -1.0, "momentum": 0.7, "quality": 0.3, "volatility": 1.0, "yield": -1.0, "growth": 0.9},
            "NVDA": {"size": 0.9, "value": -0.9, "momentum": 1.0, "quality": 0.8, "volatility": 0.7, "yield": -0.7, "growth": 1.0},
            "JPM": {"size": 0.9, "value": 0.6, "momentum": 0.3, "quality": 0.7, "volatility": -0.1, "yield": 0.6, "growth": 0.3},
            "V": {"size": 0.9, "value": -0.2, "momentum": 0.5, "quality": 0.9, "volatility": -0.3, "yield": 0.2, "growth": 0.6},
            "JNJ": {"size": 0.9, "value": 0.3, "momentum": 0.1, "quality": 0.8, "volatility": -0.8, "yield": 0.5, "growth": 0.2},
            "PG": {"size": 0.9, "value": 0.1, "momentum": 0.2, "quality": 0.9, "volatility": -0.9, "yield": 0.5, "growth": 0.3},
            "XOM": {"size": 0.8, "value": 0.7, "momentum": 0.4, "quality": 0.5, "volatility": 0.0, "yield": 0.8, "growth": 0.1},
            "BAC": {"size": 0.8, "value": 0.8, "momentum": 0.2, "quality": 0.6, "volatility": 0.2, "yield": 0.7, "growth": 0.2},
            "HD": {"size": 0.8, "value": -0.1, "momentum": 0.3, "quality": 0.8, "volatility": -0.5, "yield": 0.4, "growth": 0.5},
            "DIS": {"size": 0.8, "value": 0.2, "momentum": 0.3, "quality": 0.7, "volatility": 0.1, "yield": 0.1, "growth": 0.4},
            "NFLX": {"size": 0.8, "value": -0.7, "momentum": 0.6, "quality": 0.6, "volatility": 0.5, "yield": -1.0, "growth": 0.8},
            "INTC": {"size": 0.7, "value": 0.9, "momentum": -0.3, "quality": 0.6, "volatility": 0.0, "yield": 0.6, "growth": -0.1}
        }
        
        # Return factor data for the requested symbol, or default data if not found
        default_data = {"size": 0.5, "value": 0.0, "momentum": 0.0, "quality": 0.5, "volatility": 0.0, "yield": 0.0, "growth": 0.5}
        return factor_data.get(symbol, default_data)
    
    def _initialize_factor_returns(self) -> pd.DataFrame:
        """Initialize historical factor returns data"""
        # In a real implementation, this would load actual factor returns from a database
        # For now, generate sample data
        
        # Create date range
        start_date = datetime(2020, 1, 1)
        end_date = datetime.now()
        date_range = pd.date_range(start=start_date, end=end_date, freq='M')
        
        # Create factors
        factors = ['Market', 'Size', 'Value', 'Momentum', 'Quality', 'Volatility', 'Yield', 'Growth']
        
        # Generate random returns for each factor
        np.random.seed(42)  # For reproducibility
        data = {}
        
        for factor in factors:
            # Generate returns with different characteristics for each factor
            if factor == 'Market':
                mean_return = 0.008  # ~10% annually
                volatility = 0.04
            elif factor == 'Size':
                mean_return = 0.002
                volatility = 0.03
            elif factor == 'Value':
                mean_return = 0.001
                volatility = 0.02
            elif factor == 'Momentum':
                mean_return = 0.003
                volatility = 0.025
            elif factor == 'Quality':
                mean_return = 0.001
                volatility = 0.015
            elif factor == 'Volatility':
                mean_return = -0.001
                volatility = 0.02
            elif factor == 'Yield':
                mean_return = 0.001
                volatility = 0.01
            else:  # Growth
                mean_return = 0.002
                volatility = 0.03
                
            # Generate returns
            returns = np.random.normal(mean_return, volatility, len(date_range))
            data[factor] = returns
        
        # Create DataFrame
        factor_returns = pd.DataFrame(data, index=date_range)
        
        return factor_returns
    
    def _get_factor_returns_for_period(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get factor returns for a specific period"""
        # Filter factor returns for the specified period
        mask = (self._factor_returns.index >= start_date) & (self._factor_returns.index <= end_date)
        return self._factor_returns.loc[mask]
    
    def _get_sector_weights_and_returns(self, 
                                       portfolio: Dict[str, Any], 
                                       returns_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Calculate sector weights and returns.
        
        Args:
            portfolio: Portfolio data with holdings
            returns_data: Return data for portfolio holdings
            
        Returns:
            Dictionary mapping sectors to weights and returns
        """
        if not portfolio or "holdings" not in portfolio:
            return {}
            
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return {}
            
        # Calculate total portfolio value
        total_value = sum(holding.get("current_value", 0) for holding in holdings)
        if total_value == 0:
            return {}
            
        # Group holdings by sector
        sector_data = {}
        
        for holding in holdings:
            sector = holding.get("sector", "Unknown")
            symbol = holding.get("symbol", "")
            weight = holding.get("current_value", 0) / total_value
            
            # Get return for this holding
            if returns_data and symbol in returns_data:
                ret = returns_data[symbol]
            else:
                ret = 0
                
            # Add to sector data
            if sector not in sector_data:
                sector_data[sector] = {"weight": 0, "weighted_return": 0}
                
            sector_data[sector]["weight"] += weight
            sector_data[sector]["weighted_return"] += weight * ret
        
        # Calculate sector returns
        for sector in sector_data:
            if sector_data[sector]["weight"] > 0:
                sector_data[sector]["return"] = sector_data[sector]["weighted_return"] / sector_data[sector]["weight"]
            else:
                sector_data[sector]["return"] = 0
                
            # Remove weighted_return as it's no longer needed
            sector_data[sector].pop("weighted_return")
        
        return sector_data


class EnhancedPortfolioOptimizer:
    """
    Enhanced portfolio optimization using CFA curriculum methodologies.
    """
    
    def __init__(self):
        """Initialize the enhanced portfolio optimizer."""
        self.logger = logging.getLogger(__name__)
        self.analytics = AdvancedPortfolioAnalytics()
    
    def generate_efficient_frontier(self, 
                                   portfolio: Dict[str, Any], 
                                   risk_free_rate: float = 0.03,
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate the efficient frontier for a portfolio.
        
        Args:
            portfolio: Portfolio data with holdings
            risk_free_rate: Annual risk-free rate
            constraints: Optional optimization constraints
            
        Returns:
            Dictionary with efficient frontier data
        """
        if not portfolio or "holdings" not in portfolio:
            return {}
            
        try:
            # Extract symbols from portfolio
            symbols = [holding.get("symbol") for holding in portfolio.get("holdings", [])]
            symbols = [s for s in symbols if s]  # Remove any None values
            
            if not symbols:
                return {}
                
            # Get historical returns for these symbols
            returns_data = self._get_historical_returns(symbols)
            
            if returns_data.empty:
                self.logger.error("Failed to retrieve historical returns data")
                return {}
                
            # Get current portfolio weights
            total_value = sum(holding.get("current_value", 0) for holding in portfolio.get("holdings", []))
            current_weights = {}
            for holding in portfolio.get("holdings", []):
                symbol = holding.get("symbol")
                if symbol and total_value > 0:
                    current_weights[symbol] = holding.get("current_value", 0) / total_value
            
            # Generate efficient frontier
            frontier_portfolios = self.analytics.generate_efficient_frontier(
                returns_data=returns_data,
                risk_free_rate=risk_free_rate,
                num_portfolios=50
            )
            
            if not frontier_portfolios:
                return {}
                
            # Calculate current portfolio metrics
            current_return = None
            current_risk = None
            
            if current_weights:
                # Convert to array in the right order
                weights_array = np.zeros(len(returns_data.columns))
                for i, symbol in enumerate(returns_data.columns):
                    if symbol in current_weights:
                        weights_array[i] = current_weights[symbol]
                
                # Normalize
                if np.sum(weights_array) > 0:
                    weights_array = weights_array / np.sum(weights_array)
                    
                    # Calculate metrics
                    expected_returns = returns_data.mean()
                    cov_matrix = returns_data.cov()
                    
                    current_return = np.sum(expected_returns * weights_array)
                    current_risk = np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array)))
            
            # Extract frontier points
            frontier_points = [
                {
                    "return": p["return"],
                    "risk": p["risk"],
                    "sharpe": p["sharpe"],
                    "type": p["type"]
                }
                for p in frontier_portfolios
            ]
            
            # Extract key portfolios
            max_sharpe_portfolio = next((p for p in frontier_portfolios if p["type"] == "Maximum Sharpe"), None)
            min_vol_portfolio = next((p for p in frontier_portfolios if p["type"] == "Minimum Volatility"), None)
            
            # Prepare result
            result = {
                "frontier_points": frontier_points,
                "max_sharpe_portfolio": max_sharpe_portfolio,
                "min_vol_portfolio": min_vol_portfolio
            }
            
            # Add current portfolio if metrics available
            if current_return is not None and current_risk is not None:
                current_sharpe = (current_return - risk_free_rate) / current_risk if current_risk > 0 else 0
                result["current_portfolio"] = {
                    "return": current_return,
                    "risk": current_risk,
                    "sharpe": current_sharpe,
                    "weights": current_weights
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating efficient frontier: {str(e)}")
            return {}
    
    def optimize_for_target_return(self, 
                                  portfolio: Dict[str, Any], 
                                  target_return: float,
                                  constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize a portfolio for a target return with minimum risk.
        
        Args:
            portfolio: Portfolio data with holdings
            target_return: Target annualized return
            constraints: Optional optimization constraints
            
        Returns:
            Dictionary with optimized portfolio data
        """
        if not portfolio or "holdings" not in portfolio:
            return {}
            
        try:
            # Extract symbols from portfolio
            symbols = [holding.get("symbol") for holding in portfolio.get("holdings", [])]
            symbols = [s for s in symbols if s]  # Remove any None values
            
            if not symbols:
                return {}
                
            # Get historical returns for these symbols
            returns_data = self._get_historical_returns(symbols)
            
            if returns_data.empty:
                self.logger.error("Failed to retrieve historical returns data")
                return {}
                
            # Get current portfolio weights
            total_value = sum(holding.get("current_value", 0) for holding in portfolio.get("holdings", []))
            current_weights = {}
            for holding in portfolio.get("holdings", []):
                symbol = holding.get("symbol")
                if symbol and total_value > 0:
                    current_weights[symbol] = holding.get("current_value", 0) / total_value
            
            # Optimize portfolio
            result = self.analytics.optimize_with_risk_constraints(
                returns_data=returns_data,
                target_return=target_return,
                current_weights=current_weights
            )
            
            if not result:
                return {}
                
            # Add trade recommendations
            if current_weights and "weights" in result:
                trades = []
                for symbol, weight in result["weights"].items():
                    current_weight = current_weights.get(symbol, 0)
                    weight_diff = weight - current_weight
                    
                    if abs(weight_diff) > 0.01:  # Only include significant trades (>1%)
                        trades.append({
                            "symbol": symbol,
                            "action": "Buy" if weight_diff > 0 else "Sell",
                            "current_weight": current_weight,
                            "target_weight": weight,
                            "weight_difference": weight_diff,
                            "dollar_amount": weight_diff * total_value
                        })
                
                result["trades"] = sorted(trades, key=lambda x: abs(x["weight_difference"]), reverse=True)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error optimizing for target return: {str(e)}")
            return {}
    
    def optimize_for_risk_budget(self, 
                               portfolio: Dict[str, Any], 
                               risk_budget: Dict[str, float],
                               constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize a portfolio to match a specified risk budget.
        
        Args:
            portfolio: Portfolio data with holdings
            risk_budget: Dictionary mapping assets/sectors to target risk contribution percentages
            constraints: Optional optimization constraints
            
        Returns:
            Dictionary with optimized portfolio data
        """
        if not portfolio or "holdings" not in portfolio or not risk_budget:
            return {}
            
        try:
            # Extract symbols from portfolio
            symbols = [holding.get("symbol") for holding in portfolio.get("holdings", [])]
            symbols = [s for s in symbols if s]  # Remove any None values
            
            if not symbols:
                return {}
                
            # Get historical returns for these symbols
            returns_data = self._get_historical_returns(symbols)
            
            if returns_data.empty:
                self.logger.error("Failed to retrieve historical returns data")
                return {}
                
            # Calculate covariance matrix
            cov_matrix = returns_data.cov()
            
            # Initial weights (equal weighted)
            num_assets = len(symbols)
            initial_weights = np.ones(num_assets) / num_assets
            
            # Convert risk budget to array in the same order as returns_data columns
            risk_budget_array = np.zeros(num_assets)
            
            # Check if risk budget is specified by symbol or sector
            if all(rb in symbols for rb in risk_budget):
                # Risk budget by symbol
                for i, symbol in enumerate(returns_data.columns):
                    if symbol in risk_budget:
                        risk_budget_array[i] = risk_budget[symbol]
            else:
                # Risk budget by sector
                # Get sector for each symbol
                symbol_sectors = {}
                for holding in portfolio.get("holdings", []):
                    symbol = holding.get("symbol")
                    sector = holding.get("sector")
                    if symbol and sector:
                        symbol_sectors[symbol] = sector
                
                for i, symbol in enumerate(returns_data.columns):
                    if symbol in symbol_sectors:
                        sector = symbol_sectors[symbol]
                        if sector in risk_budget:
                            # If multiple symbols in same sector, divide risk budget equally
                            sector_symbols = sum(1 for s, sec in symbol_sectors.items() if sec == sector)
                            risk_budget_array[i] = risk_budget[sector] / sector_symbols
            
            # Normalize risk budget to sum to 1
            if np.sum(risk_budget_array) > 0:
                risk_budget_array = risk_budget_array / np.sum(risk_budget_array)
            else:
                risk_budget_array = np.ones(num_assets) / num_assets
            
            # Objective function: minimize risk budget deviation
            def objective(weights):
                portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                risk_contributions = []
                
                for i in range(len(weights)):
                    marginal_contrib = np.dot(cov_matrix[i], weights)
                    risk_contrib = weights[i] * marginal_contrib / portfolio_risk
                    risk_contributions.append(risk_contrib)
                
                risk_contributions = np.array(risk_contributions)
                target_risk_contributions = risk_budget_array * portfolio_risk
                
                return np.sum((risk_contributions - target_risk_contributions) ** 2)
            
            # Constraints: weights sum to 1
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
            # Bounds for weights (0 to 1 for each asset)
            bounds = tuple((0, 1) for _ in range(num_assets))
            
            # Run optimization
            result = sco.minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if not result.success:
                self.logger.error(f"Optimization failed: {result.message}")
                return {}
                
            # Get optimal weights
            optimal_weights = result.x
            
            # Calculate portfolio metrics
            expected_returns = returns_data.mean()
            portfolio_return = np.sum(expected_returns * optimal_weights)
            portfolio_risk = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
            
            # Calculate risk contributions
            risk_contributions = []
            for i in range(len(optimal_weights)):
                marginal_contrib = np.dot(cov_matrix[i], optimal_weights)
                risk_contrib = optimal_weights[i] * marginal_contrib / portfolio_risk
                risk_contributions.append(risk_contrib / portfolio_risk * 100)  # As percentage
            
            # Create weights dictionary
            weights_dict = dict(zip(returns_data.columns, optimal_weights))
            risk_contrib_dict = dict(zip(returns_data.columns, risk_contributions))
            
            # Filter out insignificant weights (< 0.1%)
            weights_dict = {k: v for k, v in weights_dict.items() if v > 0.001}
            risk_contrib_dict = {k: v for k, v in risk_contrib_dict.items() if weights_dict.get(k, 0) > 0.001}
            
            # Get current portfolio weights
            total_value = sum(holding.get("current_value", 0) for holding in portfolio.get("holdings", []))
            current_weights = {}
            for holding in portfolio.get("holdings", []):
                symbol = holding.get("symbol")
                if symbol and total_value > 0:
                    current_weights[symbol] = holding.get("current_value", 0) / total_value
            
            # Add trade recommendations
            trades = []
            if current_weights:
                for symbol, weight in weights_dict.items():
                    current_weight = current_weights.get(symbol, 0)
                    weight_diff = weight - current_weight
                    
                    if abs(weight_diff) > 0.01:  # Only include significant trades (>1%)
                        trades.append({
                            "symbol": symbol,
                            "action": "Buy" if weight_diff > 0 else "Sell",
                            "current_weight": current_weight,
                            "target_weight": weight,
                            "weight_difference": weight_diff,
                            "dollar_amount": weight_diff * total_value,
                            "risk_contribution": risk_contrib_dict.get(symbol, 0)
                        })
            
            return {
                "weights": weights_dict,
                "return": portfolio_return,
                "risk": portfolio_risk,
                "risk_contributions": risk_contrib_dict,
                "trades": sorted(trades, key=lambda x: abs(x["weight_difference"]), reverse=True)
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing for risk budget: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _get_historical_returns(self, symbols: List[str]) -> pd.DataFrame:
        """Get historical returns for a list of symbols"""
        # In a real implementation, this would fetch actual historical returns
        # For now, generate sample returns data
        
        # Generate 250 days (approx. 1 year) of returns
        index = pd.date_range(end=datetime.now(), periods=250, freq='B')
        
        # Create returns DataFrame
        np.random.seed(42)  # For reproducibility
        data = {}
        
        # Generate correlated returns for all symbols
        # Base correlation matrix
        base_corr = np.array([
            [1.0, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1],
            [0.5, 1.0, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
            [0.4, 0.5, 1.0, 0.5, 0.4, 0.3, 0.2, 0.1],
            [0.3, 0.4, 0.5, 1.0, 0.5, 0.4, 0.3, 0.2],
            [0.2, 0.3, 0.4, 0.5, 1.0, 0.5, 0.4, 0.3],
            [0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 0.5, 0.4],
            [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 0.5],
            [-0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
        ])
        
        # If we have more than 8 symbols, extend the correlation matrix
        n = len(symbols)
        if n > 8:
            # Create larger correlation matrix
            larger_corr = np.zeros((n, n))
            # Fill the top-left corner with the base correlation matrix
            larger_corr[:8, :8] = base_corr
            # Fill the rest with 0.2 + small random values
            for i in range(n):
                for j in range(n):
                    if i >= 8 or j >= 8:
                        if i == j:
                            larger_corr[i, j] = 1.0
                        else:
                            larger_corr[i, j] = 0.2 + np.random.uniform(-0.1, 0.1)
            base_corr = larger_corr
        elif n < 8:
            # Use a subset of the base correlation matrix
            base_corr = base_corr[:n, :n]
        
        # Generate means and standard deviations for each symbol
        means = np.random.uniform(0.0005, 0.0015, n)  # Daily returns between 0.05% and 0.15%
        stds = np.random.uniform(0.01, 0.03, n)       # Daily volatility between 1% and 3%
        
        # Create the covariance matrix
        D = np.diag(stds)
        cov = D @ base_corr @ D
        
        # Generate multivariate normal returns
        returns = np.random.multivariate_normal(means, cov, len(index))
        
        # Create DataFrame
        returns_df = pd.DataFrame(returns, index=index, columns=symbols)
        
        return returns_df