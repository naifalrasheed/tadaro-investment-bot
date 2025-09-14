# src/portfolio/portfolio_management.py

from portfolio.portfolio_optimization import PortfolioOptimizer
from portfolio.file_import import PortfolioFileImporter, FileImportException
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from data.saudi_market_api import SaudiMarketAPI
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta

class PortfolioManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimizer = PortfolioOptimizer()
        self.analyzer = EnhancedStockAnalyzer()
        self.file_importer = PortfolioFileImporter()
        self.saudi_market_api = SaudiMarketAPI()
        self.current_portfolio = {}
        self.profile_constraints = None
        self.portfolio_history = []
        
        # Create cache directory for portfolio files
        os.makedirs("./cache/portfolios", exist_ok=True)
    
    def import_portfolio_from_file(self, file_path: str) -> Dict:
        """
        Import portfolio data from a file (Excel, CSV, or PDF)
        
        Args:
            file_path: Path to the portfolio file
            
        Returns:
            Dict with portfolio data and import status
            
        Raises:
            FileImportException: If file import fails with validation errors
        """
        self.logger.info(f"Importing portfolio from {file_path}")
        
        try:
            # Use the file importer to parse and validate the file
            portfolio_data = self.file_importer.import_file(file_path)
            
            # Store as current portfolio
            self.current_portfolio = portfolio_data
            
            # Return success result with portfolio summary
            return {
                'success': True,
                'message': f"Successfully imported portfolio with {portfolio_data['positions_count']} positions",
                'data': portfolio_data,
                'file_path': file_path
            }
            
        except FileImportException as e:
            # Return error result with validation errors
            self.logger.error(f"Portfolio import failed: {e.message}")
            return {
                'success': False,
                'message': e.message,
                'validation_errors': e.validation_errors,
                'file_path': file_path
            }
        except Exception as e:
            # Return generic error result
            self.logger.error(f"Portfolio import failed with unexpected error: {str(e)}")
            return {
                'success': False,
                'message': f"Import failed: {str(e)}",
                'file_path': file_path
            }
    
    def save_portfolio(self, portfolio_name: str, user_id: Optional[int] = None) -> Dict:
        """
        Save the current portfolio with a name
        
        Args:
            portfolio_name: Name to save the portfolio as
            user_id: Optional user ID to associate with the portfolio
            
        Returns:
            Dict with save status
        """
        if not self.current_portfolio:
            return {
                'success': False,
                'message': "No portfolio data to save"
            }
        
        try:
            # Add metadata to the portfolio
            portfolio_to_save = self.current_portfolio.copy()
            portfolio_to_save['name'] = portfolio_name
            portfolio_to_save['user_id'] = user_id
            portfolio_to_save['save_date'] = datetime.now().isoformat()
            
            # Create a filename based on name and date
            filename = f"{portfolio_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join("./cache/portfolios", filename)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(portfolio_to_save, f, indent=2)
            
            self.logger.info(f"Saved portfolio '{portfolio_name}' to {file_path}")
            
            return {
                'success': True,
                'message': f"Portfolio '{portfolio_name}' saved successfully",
                'file_path': file_path
            }
            
        except Exception as e:
            self.logger.error(f"Error saving portfolio: {str(e)}")
            return {
                'success': False,
                'message': f"Error saving portfolio: {str(e)}"
            }
    
    def load_portfolio(self, file_path: str) -> Dict:
        """
        Load a saved portfolio from file
        
        Args:
            file_path: Path to the saved portfolio file
            
        Returns:
            Dict with load status and portfolio data
        """
        try:
            with open(file_path, 'r') as f:
                portfolio_data = json.load(f)
            
            self.current_portfolio = portfolio_data
            
            self.logger.info(f"Loaded portfolio '{portfolio_data.get('name')}' from {file_path}")
            
            return {
                'success': True,
                'message': f"Portfolio '{portfolio_data.get('name')}' loaded successfully",
                'data': portfolio_data
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'message': f"Portfolio file not found: {file_path}"
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'message': f"Invalid portfolio file format: {file_path}"
            }
        except Exception as e:
            self.logger.error(f"Error loading portfolio: {str(e)}")
            return {
                'success': False,
                'message': f"Error loading portfolio: {str(e)}"
            }
    
    def analyze_portfolio(self, portfolio_data: Optional[Dict] = None) -> Dict:
        """
        Analyze the portfolio composition, risk, and returns
        
        Args:
            portfolio_data: Optional portfolio data to analyze (uses current_portfolio if None)
            
        Returns:
            Dict with portfolio analysis results
        """
        # Use provided portfolio data or current portfolio
        portfolio = portfolio_data or self.current_portfolio
        
        if not portfolio:
            return {
                'success': False,
                'message': "No portfolio data to analyze"
            }
        
        try:
            # Get holdings from the portfolio
            holdings = portfolio.get('holdings', [])
            
            if not holdings:
                return {
                    'success': False,
                    'message': "Portfolio has no holdings to analyze"
                }
            
            # Calculate core metrics
            total_value = sum(holding.get('position_value', 0) for holding in holdings)
            total_cost = sum(holding.get('cost_basis', 0) for holding in holdings)
            
            # Calculate asset allocation
            asset_allocation = {}
            for holding in holdings:
                asset_class = holding.get('asset_class', 'Unknown')
                weight = (holding.get('position_value', 0) / total_value) * 100 if total_value else 0
                
                if asset_class not in asset_allocation:
                    asset_allocation[asset_class] = 0
                
                asset_allocation[asset_class] += weight
            
            # Calculate sector exposure
            sector_exposure = {}
            for holding in holdings:
                sector = holding.get('sector', 'Unknown')
                weight = (holding.get('position_value', 0) / total_value) * 100 if total_value else 0
                
                if sector not in sector_exposure:
                    sector_exposure[sector] = 0
                
                sector_exposure[sector] += weight
            
            # Calculate concentration metrics
            sorted_holdings = sorted(holdings, key=lambda h: h.get('position_value', 0), reverse=True)
            top_holdings = sorted_holdings[:5]
            top_concentration = sum(h.get('position_value', 0) for h in top_holdings) / total_value if total_value else 0
            
            # Calculate portfolio risk metrics (simple approximation)
            # For more accurate risk calculation, we would need historical data
            # This is a simplification for demonstration purposes
            volatility_estimate = 0
            for holding in holdings:
                symbol = holding.get('symbol')
                weight = holding.get('weight', 0)
                
                try:
                    # Get stock info for volatility approximation
                    stock_data = self.analyzer.analyze_stock(symbol)
                    if stock_data and 'volatility' in stock_data:
                        volatility_estimate += weight * stock_data['volatility']
                except Exception as e:
                    self.logger.warning(f"Error getting volatility for {symbol}: {str(e)}")
            
            # Prepare analysis results
            analysis_results = {
                'success': True,
                'portfolio_summary': {
                    'total_value': total_value,
                    'total_cost': total_cost,
                    'total_gain_loss': total_value - total_cost,
                    'total_gain_loss_pct': ((total_value - total_cost) / total_cost) * 100 if total_cost else 0,
                    'positions_count': len(holdings),
                    'top_concentration': top_concentration * 100,  # as percentage
                    'volatility_estimate': volatility_estimate
                },
                'asset_allocation': asset_allocation,
                'sector_exposure': sector_exposure,
                'top_holdings': [
                    {
                        'symbol': h.get('symbol'),
                        'weight': h.get('weight', 0) * 100,  # as percentage
                        'position_value': h.get('position_value', 0),
                        'gain_loss_pct': h.get('gain_loss_pct', 0) * 100  # as percentage
                    }
                    for h in top_holdings
                ],
                'alignment': self._check_portfolio_alignment(portfolio)
            }
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio: {str(e)}")
            return {
                'success': False,
                'message': f"Error analyzing portfolio: {str(e)}"
            }
    
    def _check_portfolio_alignment(self, portfolio: Dict) -> Dict:
        """
        Check portfolio alignment with target profile
        
        Args:
            portfolio: Portfolio data to check
            
        Returns:
            Dict with alignment check results
        """
        # Default target values if no profile constraints
        default_targets = {
            'target_return': 8.0,  # 8% annual return
            'max_risk': 15.0,      # 15% max volatility
            'target_allocation': {
                'Equity': 60,
                'Fixed Income': 25,
                'Cash': 10,
                'Alternative': 5
            }
        }
        
        # Use profile constraints if available, otherwise use defaults
        targets = self.profile_constraints or default_targets
        
        # Get current portfolio metrics
        holdings = portfolio.get('holdings', [])
        asset_allocation = {}
        
        for holding in holdings:
            asset_class = holding.get('asset_class', 'Unknown')
            weight = holding.get('weight', 0) * 100  # as percentage
            
            if asset_class not in asset_allocation:
                asset_allocation[asset_class] = 0
            
            asset_allocation[asset_class] += weight
        
        # Check allocation alignment
        allocation_misalignments = []
        target_allocation = targets.get('target_allocation', {})
        
        for asset_class, target_weight in target_allocation.items():
            current_weight = asset_allocation.get(asset_class, 0)
            difference = abs(current_weight - target_weight)
            
            if difference > 15:  # More than 15% deviation
                allocation_misalignments.append({
                    'asset_class': asset_class,
                    'target_weight': target_weight,
                    'current_weight': current_weight,
                    'difference': difference,
                    'explanation': f"{asset_class} allocation is {'above' if current_weight > target_weight else 'below'} target by {difference:.1f}%"
                })
        
        # Check risk alignment (simplified)
        risk_misalignment = None
        current_risk = portfolio.get('portfolio_summary', {}).get('volatility_estimate', 0)
        max_risk = targets.get('max_risk', 15.0)
        
        if current_risk > max_risk * 1.1:  # More than 10% above target
            risk_misalignment = {
                'target_risk': max_risk,
                'current_risk': current_risk,
                'difference': current_risk - max_risk,
                'explanation': f"Portfolio risk ({current_risk:.1f}%) exceeds target ({max_risk:.1f}%) by {(current_risk - max_risk):.1f}%"
            }
        
        # Check return alignment (simplified)
        return_misalignment = None
        current_return = portfolio.get('portfolio_summary', {}).get('expected_return', 0)
        target_return = targets.get('target_return', 8.0)
        
        if current_return < target_return * 0.8:  # More than 20% below target
            return_misalignment = {
                'target_return': target_return,
                'current_return': current_return,
                'difference': target_return - current_return,
                'explanation': f"Expected return ({current_return:.1f}%) is below target ({target_return:.1f}%) by {(target_return - current_return):.1f}%"
            }
        
        # Compile alignment results
        alignment_results = {
            'allocation_aligned': len(allocation_misalignments) == 0,
            'risk_aligned': risk_misalignment is None,
            'return_aligned': return_misalignment is None,
            'allocation_misalignments': allocation_misalignments,
            'risk_misalignment': risk_misalignment,
            'return_misalignment': return_misalignment
        }
        
        return alignment_results
    
    def get_rebalancing_suggestions(self, portfolio_data: Optional[Dict] = None, max_trades: int = 5) -> Dict:
        """
        Generate rebalancing suggestions to align portfolio with targets
        
        Args:
            portfolio_data: Optional portfolio data to analyze (uses current_portfolio if None)
            max_trades: Maximum number of trades to suggest
            
        Returns:
            Dict with rebalancing suggestions
        """
        # Use provided portfolio data or current portfolio
        portfolio = portfolio_data or self.current_portfolio
        
        if not portfolio:
            return {
                'success': False,
                'message': "No portfolio data to analyze"
            }
        
        try:
            # Get alignment status
            alignment = self._check_portfolio_alignment(portfolio)
            
            # If everything is aligned, no suggestions needed
            if alignment.get('allocation_aligned') and alignment.get('risk_aligned') and alignment.get('return_aligned'):
                return {
                    'success': True,
                    'message': "Portfolio is well-aligned with targets. No rebalancing needed.",
                    'suggestions': []
                }
            
            # Get holdings from the portfolio
            holdings = portfolio.get('holdings', [])
            total_value = sum(holding.get('position_value', 0) for holding in holdings)
            
            suggestions = []
            
            # Address allocation misalignments
            for misalignment in alignment.get('allocation_misalignments', []):
                asset_class = misalignment.get('asset_class')
                target_weight = misalignment.get('target_weight', 0)
                current_weight = misalignment.get('current_weight', 0)
                
                if current_weight > target_weight:
                    # Need to reduce this asset class
                    excess_weight = current_weight - target_weight
                    asset_holdings = [h for h in holdings if h.get('asset_class') == asset_class]
                    
                    # Sort by performance (sell worst performers first)
                    asset_holdings.sort(key=lambda h: h.get('gain_loss_pct', 0))
                    
                    for holding in asset_holdings:
                        if len(suggestions) >= max_trades:
                            break
                            
                        holding_weight = holding.get('weight', 0) * 100
                        symbol = holding.get('symbol')
                        quantity = holding.get('quantity', 0)
                        current_price = holding.get('current_price', 0)
                        
                        # Calculate what portion to sell (at most the entire position)
                        weight_to_reduce = min(holding_weight, excess_weight)
                        value_to_reduce = (weight_to_reduce / 100) * total_value
                        shares_to_sell = int(value_to_reduce / current_price)
                        
                        if shares_to_sell > 0:
                            suggestions.append({
                                'action': 'SELL',
                                'symbol': symbol,
                                'quantity': shares_to_sell,
                                'current_quantity': quantity,
                                'estimated_value': shares_to_sell * current_price,
                                'explanation': f"Sell {shares_to_sell} shares of {symbol} to reduce {asset_class} exposure by {weight_to_reduce:.1f}%"
                            })
                            
                            excess_weight -= weight_to_reduce
                            if excess_weight <= 0.5:  # Threshold to consider it resolved
                                break
                
                elif current_weight < target_weight:
                    # Need to increase this asset class
                    deficit_weight = target_weight - current_weight
                    value_to_add = (deficit_weight / 100) * total_value
                    
                    # Find best candidates to add from this asset class (not currently in portfolio)
                    if asset_class == 'Equity':
                        # For equities, suggest high-quality stocks
                        suggestions.append({
                            'action': 'BUY',
                            'symbol': 'VTI',  # Total stock market ETF
                            'quantity': int(value_to_add / 200),  # Approximate price of VTI
                            'estimated_value': int(value_to_add / 200) * 200,
                            'explanation': f"Buy VTI to increase {asset_class} exposure by {deficit_weight:.1f}%"
                        })
                    elif asset_class == 'Fixed Income':
                        suggestions.append({
                            'action': 'BUY',
                            'symbol': 'BND',  # Total bond market ETF
                            'quantity': int(value_to_add / 80),  # Approximate price of BND
                            'estimated_value': int(value_to_add / 80) * 80,
                            'explanation': f"Buy BND to increase {asset_class} exposure by {deficit_weight:.1f}%"
                        })
                    elif asset_class == 'Cash':
                        suggestions.append({
                            'action': 'ADD_CASH',
                            'amount': value_to_add,
                            'explanation': f"Add ${value_to_add:.0f} in cash to increase {asset_class} exposure by {deficit_weight:.1f}%"
                        })
                    else:
                        suggestions.append({
                            'action': 'BUY',
                            'symbol': 'REIT',  # Placeholder for alternative investments
                            'quantity': int(value_to_add / 100),  # Approximate price
                            'estimated_value': int(value_to_add / 100) * 100,
                            'explanation': f"Buy alternative assets to increase {asset_class} exposure by {deficit_weight:.1f}%"
                        })
                    
                    if len(suggestions) >= max_trades:
                        break
            
            # Address risk/return misalignments if we haven't reached max trades
            if len(suggestions) < max_trades:
                # Risk misalignment logic
                if not alignment.get('risk_aligned'):
                    high_risk_holdings = sorted(holdings, key=lambda h: h.get('volatility', 0), reverse=True)
                    
                    for holding in high_risk_holdings[:2]:  # Look at top 2 high-risk holdings
                        if len(suggestions) >= max_trades:
                            break
                            
                        symbol = holding.get('symbol')
                        quantity = holding.get('quantity', 0)
                        current_price = holding.get('current_price', 0)
                        
                        # Suggest selling some of the position
                        shares_to_sell = max(1, int(quantity * 0.25))  # Sell 25% of position
                        
                        if shares_to_sell > 0:
                            suggestions.append({
                                'action': 'SELL',
                                'symbol': symbol,
                                'quantity': shares_to_sell,
                                'current_quantity': quantity,
                                'estimated_value': shares_to_sell * current_price,
                                'explanation': f"Sell {shares_to_sell} shares of {symbol} to reduce portfolio risk"
                            })
                
                # Return misalignment logic
                if not alignment.get('return_aligned') and len(suggestions) < max_trades:
                    suggestions.append({
                        'action': 'BUY',
                        'symbol': 'VOO',  # S&P 500 ETF
                        'quantity': int((total_value * 0.05) / 400),  # 5% of portfolio at approx. price of VOO
                        'estimated_value': int((total_value * 0.05) / 400) * 400,
                        'explanation': "Buy VOO to increase expected returns"
                    })
            
            return {
                'success': True,
                'message': f"Generated {len(suggestions)} rebalancing suggestions",
                'suggestions': suggestions[:max_trades]  # Limit to max_trades
            }
            
        except Exception as e:
            self.logger.error(f"Error generating rebalancing suggestions: {str(e)}")
            return {
                'success': False,
                'message': f"Error generating rebalancing suggestions: {str(e)}"
            }
    
    def optimize_portfolio(self, profile_constraints: Dict = None) -> Dict:
        """Interactive portfolio optimization with optional profile constraints"""
        self.logger.info("Starting portfolio optimization")
        
        if profile_constraints:
            self.logger.info(f"Using profile constraints: {profile_constraints}")
            self.profile_constraints = profile_constraints
        
        # Get optimization parameters
        objective = 'sharpe'  # Default objective
        target_return = None
        target_risk = None
        target_dividend = None
        
        # Extract symbols from current portfolio if available
        symbols = []
        if self.current_portfolio and 'holdings' in self.current_portfolio:
            symbols = [holding.get('symbol') for holding in self.current_portfolio.get('holdings', [])]
            self.logger.info(f"Using {len(symbols)} symbols from current portfolio")
        
        # Add profile constraints
        if self.profile_constraints:
            target_return = self.profile_constraints.get('min_return')
            target_risk = self.profile_constraints.get('max_risk')
        
        # Run optimization
        self.logger.info(f"Running optimization with objective={objective}, target_return={target_return}, target_risk={target_risk}")
        
        result = self.optimizer.optimize_portfolio(
            symbols,
            objective=objective,
            target_return=target_return,
            target_risk=target_risk,
            target_dividend_yield=target_dividend,
            profile_constraints=self.profile_constraints
        )
        
        if result:
            self.logger.info("Optimization successful")
            
            # Create a properly formatted portfolio from optimization results
            optimized_portfolio = {
                'holdings': [],
                'total_value': 0
            }
            
            # Assume a $100,000 portfolio for demonstration
            total_value = 100000
            
            for symbol, weight in result['weights'].items():
                # Get stock info
                try:
                    stock_info = self.analyzer.get_stock_info(symbol)
                    current_price = stock_info.get('price', 0) if stock_info else 0
                    
                    if current_price > 0:
                        position_value = total_value * (weight / 100)
                        quantity = position_value / current_price
                        
                        optimized_portfolio['holdings'].append({
                            'symbol': symbol,
                            'quantity': int(quantity),  # Round down to whole shares
                            'current_price': current_price,
                            'position_value': position_value,
                            'weight': weight / 100,
                            'sector': stock_info.get('sector', '') if stock_info else '',
                            'asset_class': 'Equity'  # Default to equity
                        })
                except Exception as e:
                    self.logger.warning(f"Error getting stock info for {symbol}: {str(e)}")
            
            # Set as current portfolio
            if optimized_portfolio['holdings']:
                self.current_portfolio = optimized_portfolio
                self.current_portfolio['expected_return'] = result['expected_return']
                self.current_portfolio['risk'] = result['risk']
                self.current_portfolio['sharpe_ratio'] = result['sharpe_ratio']
                self.current_portfolio['dividend_yield'] = result['dividend_yield']
                self.current_portfolio['optimization_date'] = datetime.now().isoformat()
                
            return {
                'success': True,
                'message': "Portfolio optimization completed successfully",
                'portfolio': self.current_portfolio,
                'optimization_result': result
            }
        else:
            self.logger.warning("Optimization failed")
            return {
                'success': False,
                'message': "Optimization failed. Please try different parameters."
            }

    def _filter_symbols_by_sector(self, symbols: List[str]) -> List[str]:
        """Filter symbols based on sector preferences"""
        if not self.profile_constraints:
            return symbols
            
        filtered_symbols = []
        preferred_sectors = self.profile_constraints.get('preferred_sectors', [])
        excluded_sectors = self.profile_constraints.get('excluded_sectors', [])
        
        for symbol in symbols:
            try:
                info = self.analyzer.get_stock_info(symbol)
                sector = info.get('sector', '')
                if sector:
                    if (not preferred_sectors or sector in preferred_sectors) and \
                    (not excluded_sectors or sector not in excluded_sectors):
                        filtered_symbols.append(symbol)
            except Exception as e:
                self.logger.error(f"Error getting sector for {symbol}: {str(e)}")
                filtered_symbols.append(symbol)  # Include symbol if sector check fails
        
        return filtered_symbols
        
    def monitor_portfolio_performance(self, days: int = 30) -> Dict:
        """
        Monitor daily portfolio performance over the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with performance metrics
        """
        if not self.current_portfolio or 'holdings' not in self.current_portfolio:
            return {
                'success': False,
                'message': "No portfolio data available for monitoring"
            }
        
        try:
            self.logger.info(f"Monitoring portfolio performance over {days} days")
            
            # Get holdings
            holdings = self.current_portfolio.get('holdings', [])
            
            # Get historical data for each holding
            historical_data = {}
            for holding in holdings:
                symbol = holding.get('symbol')
                weight = holding.get('weight', 0)
                
                try:
                    # Get historical prices
                    stock_data = self.analyzer.get_historical_prices(symbol, days=days)
                    if stock_data is not None:
                        historical_data[symbol] = {
                            'prices': stock_data,
                            'weight': weight
                        }
                except Exception as e:
                    self.logger.warning(f"Error getting historical data for {symbol}: {str(e)}")
            
            if not historical_data:
                return {
                    'success': False,
                    'message': "Could not get historical data for any holdings"
                }
            
            # Create a date index for all dates in the period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
            
            # Create portfolio performance dataframe
            portfolio_df = pd.DataFrame(index=date_range)
            portfolio_df['Portfolio'] = 0
            
            # Add each stock's contribution to the portfolio
            for symbol, data in historical_data.items():
                prices = data['prices']
                weight = data['weight']
                
                # Convert stock data to Series
                if isinstance(prices, list):
                    # Convert list of dicts to Series
                    stock_series = pd.Series(index=date_range)
                    for price_data in prices:
                        date = pd.to_datetime(price_data.get('date'))
                        if date in stock_series.index:
                            stock_series[date] = price_data.get('close', 0)
                    
                    # Forward fill missing values
                    stock_series = stock_series.fillna(method='ffill')
                elif isinstance(prices, pd.Series):
                    stock_series = prices
                else:
                    continue
                
                # Calculate daily returns
                stock_returns = stock_series.pct_change().fillna(0)
                
                # Add weighted contribution to portfolio
                portfolio_df[symbol] = stock_returns * weight
                portfolio_df['Portfolio'] += portfolio_df[symbol]
            
            # Calculate cumulative returns
            portfolio_df['Cumulative'] = (1 + portfolio_df['Portfolio']).cumprod()
            
            # Calculate rolling metrics
            portfolio_df['Rolling_Volatility'] = portfolio_df['Portfolio'].rolling(window=20).std() * np.sqrt(252)
            portfolio_df['Rolling_Sharpe'] = (portfolio_df['Portfolio'].rolling(window=20).mean() * 252) / portfolio_df['Rolling_Volatility']
            
            # Get benchmark data (S&P 500)
            try:
                benchmark_data = self.analyzer.get_historical_prices('^GSPC', days=days)
                if benchmark_data is not None:
                    # Convert to Series
                    if isinstance(benchmark_data, list):
                        benchmark_series = pd.Series(index=date_range)
                        for price_data in benchmark_data:
                            date = pd.to_datetime(price_data.get('date'))
                            if date in benchmark_series.index:
                                benchmark_series[date] = price_data.get('close', 0)
                        
                        benchmark_series = benchmark_series.fillna(method='ffill')
                    elif isinstance(benchmark_data, pd.Series):
                        benchmark_series = benchmark_data
                    
                    # Calculate benchmark returns
                    benchmark_returns = benchmark_series.pct_change().fillna(0)
                    portfolio_df['Benchmark'] = benchmark_returns
                    portfolio_df['Benchmark_Cumulative'] = (1 + portfolio_df['Benchmark']).cumprod()
            except Exception as e:
                self.logger.warning(f"Error getting benchmark data: {str(e)}")
            
            # Calculate performance metrics
            performance_metrics = {
                'total_return': (portfolio_df['Cumulative'].iloc[-1] - 1) * 100 if len(portfolio_df) > 0 else 0,
                'annualized_return': portfolio_df['Portfolio'].mean() * 252 * 100,
                'annualized_volatility': portfolio_df['Portfolio'].std() * np.sqrt(252) * 100,
                'sharpe_ratio': (portfolio_df['Portfolio'].mean() * 252) / (portfolio_df['Portfolio'].std() * np.sqrt(252)) if portfolio_df['Portfolio'].std() > 0 else 0
            }
            
            # Calculate benchmark comparison if available
            if 'Benchmark' in portfolio_df.columns:
                benchmark_metrics = {
                    'benchmark_return': (portfolio_df['Benchmark_Cumulative'].iloc[-1] - 1) * 100 if len(portfolio_df) > 0 else 0,
                    'benchmark_volatility': portfolio_df['Benchmark'].std() * np.sqrt(252) * 100,
                    'excess_return': performance_metrics['total_return'] - ((portfolio_df['Benchmark_Cumulative'].iloc[-1] - 1) * 100 if len(portfolio_df) > 0 else 0)
                }
                performance_metrics.update(benchmark_metrics)
            
            # Format results
            result = {
                'success': True,
                'performance_metrics': performance_metrics,
                'daily_returns': portfolio_df['Portfolio'].tail(min(days, len(portfolio_df))).to_dict(),
                'cumulative_returns': portfolio_df['Cumulative'].tail(min(days, len(portfolio_df))).to_dict(),
                'rolling_volatility': portfolio_df['Rolling_Volatility'].tail(min(days, len(portfolio_df))).to_dict(),
                'rolling_sharpe': portfolio_df['Rolling_Sharpe'].tail(min(days, len(portfolio_df))).to_dict()
            }
            
            if 'Benchmark' in portfolio_df.columns:
                result['benchmark_returns'] = portfolio_df['Benchmark_Cumulative'].tail(min(days, len(portfolio_df))).to_dict()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error monitoring portfolio: {str(e)}")
            return {
                'success': False,
                'message': f"Error monitoring portfolio: {str(e)}"
            }
            
    def _get_symbols(self) -> List[str]:
        """Get list of symbols and their minimum allocations from user"""
        symbols = []
        min_allocations = {}
        print("\nEnter stock symbols and minimum allocations (optional):")
        print("Format: SYMBOL [MIN%] (e.g., 'AAPL 5' for 5% minimum, or just 'AAPL' for no minimum)")
        print("Enter blank line to finish")
        
        while True:
            entry = input().strip().upper()
            if not entry:
                break
                
            parts = entry.split()
            symbol = parts[0]
            
            if len(parts) > 1:
                try:
                    min_alloc = float(parts[1])
                    if 0 <= min_alloc <= 100:
                        self.optimizer.set_minimum_allocation(symbol, min_alloc)
                    else:
                        print(f"Invalid minimum allocation for {symbol}. Using default.")
                except ValueError:
                    print(f"Invalid minimum allocation for {symbol}. Using default.")
            
            symbols.append(symbol)
        
        return symbols

    def _display_optimization_results(self, results: Dict):
        if not results:
            print("\nOptimization failed. Please try different parameters.")
            return
            
        print("\n=== Optimization Results ===")
        print("\nPortfolio Allocation:")
        
        # Sort allocations by weight
        sorted_weights = sorted(results['weights'].items(), key=lambda x: x[1], reverse=True)
        
        # Display only positions with significant weights
        active_positions = 0
        for symbol, weight in sorted_weights:
            if weight > 1.0:  # Only show positions > 1%
                print(f"{symbol}: {weight:.2f}%")
                active_positions += 1
        
        # Calculate diversification metrics
        total_positions = len(sorted_weights)
        concentration = sum(weight for _, weight in sorted_weights[:3])  # Top 3 concentration
        
        print("\nDiversification Metrics:")
        print(f"Active Positions: {active_positions} of {total_positions}")
        print(f"Top 3 Concentration: {concentration:.1f}%")
        
        print("\nPortfolio Metrics:")
        print(f"Expected Annual Return: {results['expected_return']:.2f}%")
        print(f"Annual Volatility: {results['risk']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Dividend Yield: {results['dividend_yield']:.2f}%")
        
        print("\nPortfolio Analysis:")
        if results['sharpe_ratio'] > 2:
            print("✓ Excellent risk-adjusted return potential")
        elif results['sharpe_ratio'] > 1:
            print("✓ Good risk-adjusted return potential")
        
        if results['risk'] < 15:
            print("✓ Low volatility level")
        elif results['risk'] < 20:
            print("✓ Moderate volatility level")
        else:
            print("! High volatility level")
            
        if results['dividend_yield'] > 3:
            print("✓ Strong dividend income potential")
        elif results['dividend_yield'] > 2:
            print("✓ Moderate dividend income potential")
            
        if concentration > 60:
            print("! High portfolio concentration")
        elif concentration < 40:
            print("✓ Well diversified portfolio")