# ml_components/naif_alrasheed_model.py
"""
Naif Al-Rasheed Investment Model

A comprehensive multi-market investment model that implements Naif Al-Rasheed's
investment philosophy for both Saudi and US markets. The model follows a 
disciplined approach to identify high-quality companies with strong fundamentals,
excellent management, and attractive valuations.

The model implements a multi-stage screening process:
1. Macro-economic analysis and growth indicators assessment
2. Sector-level growth analysis and ranking
3. Company fundamental screening (ROTC, revenue growth, EBITDA, FCF)
4. Management quality assessment
5. Portfolio construction with diversification (12-18 companies)
6. Monte Carlo simulation with Brownian motion
7. Portfolio optimization based on user risk profile
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
import io
import base64
from typing import List, Dict, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
import os
import json
import random
import math
from scipy import stats
from sklearn.preprocessing import StandardScaler
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm

# Import necessary components
from data.saudi_market_api import SaudiMarketAPI
from data.data_fetcher import DataFetcher
from analysis.enhanced_stock_analyzer import EnhancedStockAnalyzer
from portfolio.portfolio_management import PortfolioManager
from portfolio.portfolio_optimization import PortfolioOptimizer
from user_profiling.risk_profiler import RiskProfiler


class NaifAlRasheedModel:
    """
    Implements the Naif Al-Rasheed investment philosophy for both US and Saudi markets.
    
    The model follows a systematic approach to identify high-quality companies with:
    - Strong return on tangible capital (ROTC > 15%)
    - High revenue growth potential
    - Positive EBITDA and/or free cash flow
    - Strong management teams
    - Fair valuations with margin of safety
    
    The model also integrates sector and macro-economic analysis to align investments
    with long-term economic growth trends.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.saudi_api = SaudiMarketAPI()
        self.data_fetcher = DataFetcher()
        self.stock_analyzer = EnhancedStockAnalyzer()
        self.portfolio_manager = PortfolioManager()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_profiler = RiskProfiler()
        
        # Pipeline stages and their weights
        self.pipeline_stages = {
            'macro_analysis': 0.1,
            'sector_ranking': 0.15,
            'fundamental_screening': 0.3,
            'management_quality': 0.15,
            'valuation_analysis': 0.2,
            'technical_indicators': 0.1
        }
        
        # Investment criteria
        self.investment_criteria = {
            'us': {
                'min_rotc': 15.0,                # Min 15% ROTC
                'min_revenue_growth': 5.0,       # Min 5% revenue growth
                'min_market_cap': 1_000_000_000, # Min $1B market cap
                'positive_ebitda': True,         # Must have positive EBITDA or...
                'positive_fcf': True,            # ...positive free cash flow
                'max_pe_ratio': 25.0,            # Max P/E ratio
                'min_dividend_yield': 1.0,       # Min dividend yield (optional)
                'min_management_score': 60.0     # Min management quality score
            },
            'saudi': {
                'min_rotc': 12.0,                # Min 12% ROTC
                'min_revenue_growth': 5.0,       # Min 5% revenue growth
                'min_market_cap': 500_000_000,   # Min 500M SAR market cap
                'positive_ebitda': True,         # Must have positive EBITDA or...
                'positive_fcf': True,            # ...positive free cash flow
                'max_pe_ratio': 20.0,            # Max P/E ratio
                'min_dividend_yield': 2.0,       # Min dividend yield (higher in Saudi)
                'min_management_score': 60.0     # Min management quality score
            }
        }
        
        # Portfolio construction parameters
        self.portfolio_params = {
            'min_stocks': 12,              # Minimum stocks in portfolio
            'max_stocks': 18,              # Maximum stocks in portfolio
            'min_sectors': 5,              # Minimum number of sectors
            'max_sector_weight': 0.25,     # Maximum weight for any sector
            'cash_allocation': 0.05,       # 5% cash position
            'simulation_runs': 5000,       # Number of Monte Carlo simulations (limited for testing, should be 10000 for production)
            'time_horizon': 5,             # 5-year investment horizon
            'benchmark': {
                'us': 'SPY',               # S&P 500 ETF for US
                'saudi': '^TASI'           # Tadawul All Share Index for Saudi
            }
        }
        
        # Create cache directories
        os.makedirs("./cache/naif_model", exist_ok=True)
        os.makedirs("./cache/naif_model/us", exist_ok=True)
        os.makedirs("./cache/naif_model/saudi", exist_ok=True)
        os.makedirs("./cache/naif_model/simulations", exist_ok=True)
    
    def run_full_screening(self, market: str = 'us', 
                          custom_params: Optional[Dict] = None, 
                          risk_profile: Optional[Dict] = None,
                          existing_portfolio: Optional[Dict] = None) -> Dict:
        """
        Run the complete multi-stage screening process for either US or Saudi market
        
        Args:
            market: Market to analyze ('us' or 'saudi')
            custom_params: Optional custom screening parameters
            risk_profile: Optional user risk profile information
            existing_portfolio: Optional existing portfolio to optimize from
            
        Returns:
            Dict with screening results and portfolio recommendations
        """
        market = market.lower()
        if market not in ['us', 'saudi']:
            self.logger.error(f"Invalid market specified: {market}")
            return {
                'success': False,
                'message': f"Invalid market: {market}. Use 'us' or 'saudi'."
            }
            
        self.logger.info(f"Starting Naif Al-Rasheed investment model screening for {market.upper()} market")
        
        # Update criteria if custom parameters provided
        criteria = self.investment_criteria[market].copy()
        if custom_params:
            criteria.update(custom_params)
            self.logger.info(f"Using custom parameters: {custom_params}")
        
        try:
            # Stage 1: Analyze macro-economic conditions
            self.logger.info("Stage 1: Analyzing macro-economic conditions")
            macro_analysis = self._analyze_macro_conditions(market)
            
            # Stage 2: Sector ranking and selection
            self.logger.info("Stage 2: Ranking market sectors")
            sector_scores = self._rank_sectors(market, macro_analysis)
            top_sectors = self._select_top_sectors(sector_scores, market)
            
            # Stage 3: Get companies in top sectors
            self.logger.info(f"Stage 3: Getting companies in {len(top_sectors)} top sectors")
            companies = self._get_companies_in_sectors(top_sectors, market)
            
            # Stage 4: Fundamental screening
            self.logger.info(f"Stage 4: Running fundamental screening on {len(companies)} companies")
            screened_companies = self._run_fundamental_screening(companies, criteria, market)
            
            # Stage 5: Management quality assessment
            self.logger.info(f"Stage 5: Analyzing management quality for {len(screened_companies)} companies")
            quality_companies = self._analyze_management_quality(screened_companies, criteria, market)
            
            # Stage 6: Valuation analysis
            self.logger.info(f"Stage 6: Running valuation analysis on {len(quality_companies)} companies")
            valuated_companies = self._run_valuation_analysis(quality_companies, criteria, market)
            
            # Stage 7: Final ranking and selection
            self.logger.info("Stage 7: Final ranking and selection")
            ranked_companies = self._rank_companies(valuated_companies, market)
            selected_companies = self._select_final_candidates(ranked_companies, market)
            
            # Stage 8: Generate portfolio
            self.logger.info("Stage 8: Constructing portfolio")
            portfolio = self._construct_portfolio(selected_companies, risk_profile, existing_portfolio, market)
            
            # Stage 9: Run Monte Carlo simulation
            self.logger.info("Stage 9: Running Monte Carlo simulation")
            simulation_results = self._run_monte_carlo_simulation(portfolio, market)
            
            # Stage 10: Prepare final output with visualizations
            self.logger.info("Stage 10: Preparing final output with visualizations")
            visualizations = self._generate_visualizations(portfolio, simulation_results, market)
            
            return {
                'success': True,
                'analysis_date': datetime.now().isoformat(),
                'market': market.upper(),
                'parameters': criteria,
                'macro_analysis': macro_analysis,
                'sector_scores': sector_scores,
                'selected_sectors': top_sectors,
                'screened_companies': [c['symbol'] for c in screened_companies],
                'quality_companies': [c['symbol'] for c in quality_companies],
                'valuated_companies': [c['symbol'] for c in valuated_companies],
                'selected_companies': [c['symbol'] for c in selected_companies],
                'portfolio': portfolio,
                'simulation_results': simulation_results,
                'visualizations': visualizations,
                'recommendations': self._generate_recommendations(portfolio, simulation_results, market)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Naif Al-Rasheed screening: {str(e)}")
            return {
                'success': False,
                'market': market.upper(),
                'message': f"Screening failed: {str(e)}"
            }
    
    def _analyze_macro_conditions(self, market: str) -> Dict:
        """
        Analyze macro-economic conditions to assess growth outlook and favorable sectors
        
        Args:
            market: The market to analyze ('us' or 'saudi')
            
        Returns:
            Dict with macro-economic indicators and analysis
        """
        self.logger.info(f"Analyzing macro-economic conditions for {market.upper()} market")
        
        # Get key macro-economic indicators
        indicators = {}
        growth_outlook = 0.0
        
        try:
            if market == 'us':
                # For US market - in a real implementation, these would come from API calls
                # to economic data providers or calculated from market data
                gdp_growth = self.data_fetcher.get_macro_data('gdp_growth') or 2.0
                inflation = self.data_fetcher.get_macro_data('inflation_rate') or 3.0
                interest_rate = self.data_fetcher.get_macro_data('interest_rate') or 3.5
                unemployment = self.data_fetcher.get_macro_data('unemployment_rate') or 3.7
                consumer_confidence = self.data_fetcher.get_macro_data('consumer_confidence') or 105.0
                
                indicators = {
                    'gdp_growth': gdp_growth,
                    'inflation': inflation,
                    'interest_rate': interest_rate,
                    'unemployment': unemployment,
                    'consumer_confidence': consumer_confidence
                }
                
                # Calculate growth outlook (simplified)
                # Positive factors: GDP growth, consumer confidence
                # Negative factors: high inflation, high interest rates, high unemployment
                growth_outlook = (
                    gdp_growth * 3.0 + 
                    (consumer_confidence / 100.0) * 2.0 - 
                    (inflation - 2.0) * 2.0 if inflation > 2.0 else 0 -  # Penalize inflation above 2%
                    (interest_rate - 3.0) * 1.5 if interest_rate > 3.0 else 0 -  # Penalize interest rates above 3%
                    (unemployment - 4.0) * 2.0 if unemployment > 4.0 else 0  # Penalize unemployment above 4%
                )
                
            elif market == 'saudi':
                # For Saudi market - would typically come from Saudi economic indicators
                # Using placeholder values for demonstration
                gdp_growth = 2.5  # Example value
                oil_price = 75.0  # Example: Current oil price
                inflation = 3.0   # Example value
                interest_rate = 4.0  # Example value
                vision_2030_progress = 65.0  # Example: Progress on Vision 2030 goals (0-100)
                
                indicators = {
                    'gdp_growth': gdp_growth,
                    'oil_price': oil_price,
                    'inflation': inflation,
                    'interest_rate': interest_rate,
                    'vision_2030_progress': vision_2030_progress
                }
                
                # Calculate growth outlook for Saudi market
                # Include oil price as a key factor for Saudi economy
                growth_outlook = (
                    gdp_growth * 3.0 - 
                    (inflation - 2.0) * 2.0 if inflation > 2.0 else 0 -
                    (interest_rate - 3.0) * 1.5 if interest_rate > 3.0 else 0 +
                    (oil_price - 65.0) * 0.1 if oil_price > 65.0 else (oil_price - 65.0) * 0.2 +  # Oil price impact
                    (vision_2030_progress - 50.0) * 0.05  # Vision 2030 impact
                )
            
            # Normalize growth outlook to a 0-100 scale
            normalized_outlook = min(max(50.0 + growth_outlook * 5.0, 0.0), 100.0)
            
            # Determine growth regime
            if normalized_outlook >= 70:
                growth_regime = "Strong Growth"
            elif normalized_outlook >= 55:
                growth_regime = "Moderate Growth"
            elif normalized_outlook >= 45:
                growth_regime = "Stable"
            elif normalized_outlook >= 30:
                growth_regime = "Slow Growth"
            else:
                growth_regime = "Contraction"
                
            # Identify sectors likely to perform well in the current regime
            favorable_sectors = self._identify_favorable_sectors(indicators, growth_regime, market)
                
            # Generate narrative explanation
            explanation = self._generate_macro_explanation(indicators, normalized_outlook, growth_regime, market)
            
            return {
                'market': market.upper(),
                'indicators': indicators,
                'growth_outlook_score': normalized_outlook,
                'growth_regime': growth_regime,
                'favorable_sectors': favorable_sectors,
                'explanation': explanation,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in macro-economic analysis: {str(e)}")
            # Return a default conservative analysis if error occurs
            return {
                'market': market.upper(),
                'indicators': {},
                'growth_outlook_score': 50.0,  # Neutral outlook
                'growth_regime': "Uncertain",
                'favorable_sectors': ["Technology", "Healthcare", "Consumer Staples"],
                'explanation': "Unable to complete full macro-economic analysis. Using default conservative outlook.",
                'analysis_date': datetime.now().isoformat()
            }
    
    def _identify_favorable_sectors(self, indicators: Dict, growth_regime: str, market: str) -> List[str]:
        """
        Identify sectors likely to perform well in the current macro environment
        
        Args:
            indicators: Dict of economic indicators
            growth_regime: Current growth regime classification
            market: Market being analyzed
            
        Returns:
            List of favorable sectors
        """
        # Base case - moderate conditions favor these sectors
        favorable_sectors = ["Technology", "Healthcare", "Financials"]
        
        if market == 'us':
            gdp_growth = indicators.get('gdp_growth', 0)
            inflation = indicators.get('inflation', 0)
            interest_rate = indicators.get('interest_rate', 0)
            
            if growth_regime == "Strong Growth":
                favorable_sectors = ["Technology", "Consumer Discretionary", "Industrials", "Communication Services"]
            elif growth_regime == "Moderate Growth":
                favorable_sectors = ["Technology", "Healthcare", "Financials", "Consumer Discretionary"]
            elif growth_regime == "Stable":
                favorable_sectors = ["Healthcare", "Utilities", "Consumer Staples", "Financials"]
            elif growth_regime == "Slow Growth":
                favorable_sectors = ["Utilities", "Consumer Staples", "Healthcare", "Real Estate"]
            else:  # Contraction
                favorable_sectors = ["Consumer Staples", "Utilities", "Healthcare", "Telecommunications"]
                
            # Adjust for high inflation
            if inflation > 4.0:
                if "Energy" not in favorable_sectors:
                    favorable_sectors.append("Energy")
                if "Materials" not in favorable_sectors:
                    favorable_sectors.append("Materials")
                
            # Adjust for high interest rates
            if interest_rate > 4.0:
                if "Financials" not in favorable_sectors:
                    favorable_sectors.append("Financials")
                
        elif market == 'saudi':
            oil_price = indicators.get('oil_price', 0)
            vision_2030_progress = indicators.get('vision_2030_progress', 50)
            
            if growth_regime == "Strong Growth":
                favorable_sectors = ["Banking", "Petrochemicals", "Retail", "Real Estate"]
            elif growth_regime == "Moderate Growth":
                favorable_sectors = ["Banking", "Insurance", "Retail", "Petrochemicals"]
            elif growth_regime == "Stable":
                favorable_sectors = ["Banking", "Telecommunications", "Food & Agriculture", "Utilities"]
            elif growth_regime == "Slow Growth":
                favorable_sectors = ["Telecommunications", "Food & Agriculture", "Utilities", "Banking"]
            else:  # Contraction
                favorable_sectors = ["Food & Agriculture", "Utilities", "Telecommunications", "Healthcare"]
                
            # Adjust for oil price
            if oil_price > 80:
                if "Petrochemicals" not in favorable_sectors:
                    favorable_sectors.append("Petrochemicals")
                if "Energy" not in favorable_sectors:
                    favorable_sectors.append("Energy")
            
            # Adjust for Vision 2030 progress
            if vision_2030_progress > 60:
                if "Tourism" not in favorable_sectors:
                    favorable_sectors.append("Tourism")
                if "Entertainment" not in favorable_sectors:
                    favorable_sectors.append("Entertainment")
        
        return favorable_sectors
    
    def _generate_macro_explanation(self, indicators: Dict, outlook: float, regime: str, market: str) -> str:
        """Generate explanatory narrative for macro conditions"""
        
        explanation = f"The {market.upper()} economy is currently in a {regime.lower()} phase "
        
        # Add details specific to each market
        if market == 'us':
            gdp = indicators.get('gdp_growth', 0)
            inflation = indicators.get('inflation', 0)
            interest = indicators.get('interest_rate', 0)
            
            explanation += f"with GDP growth at {gdp:.1f}%. "
            
            if inflation > 4:
                explanation += f"Inflation is elevated at {inflation:.1f}%, "
            else:
                explanation += f"Inflation is moderate at {inflation:.1f}%, "
                
            explanation += f"and interest rates are at {interest:.1f}%. "
            
            if outlook >= 70:
                explanation += "These conditions suggest a favorable environment for equity investments, "
                explanation += "particularly in growth-oriented sectors. "
            elif outlook >= 55:
                explanation += "These conditions are conducive to balanced equity investments "
                explanation += "with a mix of growth and value stocks. "
            elif outlook >= 45:
                explanation += "This indicates a neutral environment that favors quality companies "
                explanation += "with strong balance sheets and sustainable competitive advantages. "
            else:
                explanation += "This suggests a more defensive approach, focusing on companies "
                explanation += "with stable cash flows and less cyclical business models. "
                
        elif market == 'saudi':
            gdp = indicators.get('gdp_growth', 0)
            oil_price = indicators.get('oil_price', 0)
            
            explanation += f"with GDP growth at {gdp:.1f}%. "
            explanation += f"The oil price at ${oil_price:.2f} is a key factor, "
            
            if oil_price > 80:
                explanation += "which is highly supportive of government spending and economic activity. "
            elif oil_price > 65:
                explanation += "which provides moderate support for government initiatives. "
            else:
                explanation += "which may constrain government spending and economic growth. "
                
            if outlook >= 60:
                explanation += "The Saudi Vision 2030 initiatives continue to diversify the economy, "
                explanation += "creating opportunities in non-oil sectors."
            else:
                explanation += "Focus should be on companies that will benefit from economic transformation "
                explanation += "efforts and those with minimal reliance on government spending."
        
        return explanation
    
    def _rank_sectors(self, market: str, macro_analysis: Dict) -> Dict[str, float]:
        """
        Rank sectors based on growth, momentum, profitability, and alignment with macro outlook
        
        Args:
            market: Market to analyze ('us' or 'saudi')
            macro_analysis: Results from macro-economic analysis
            
        Returns:
            Dict mapping sector names to their scores
        """
        self.logger.info(f"Ranking sectors for {market.upper()} market")
        
        sector_scores = {}
        favorable_sectors = macro_analysis.get('favorable_sectors', [])
        
        try:
            if market == 'us':
                # Get all S&P 500 sectors
                sp500_sectors = self.data_fetcher.get_sp500_sector_stocks()
                
                for sector, stocks in sp500_sectors.items():
                    # Calculate sector metrics
                    growth_score = self._calculate_sector_growth(stocks, market)
                    momentum_score = self._calculate_sector_momentum(stocks, market)
                    profitability_score = self._calculate_sector_profitability(stocks, market)
                    valuation_score = self._calculate_sector_valuation(stocks, market)
                    
                    # Add bonus for sectors identified as favorable in macro analysis
                    macro_alignment = 15.0 if sector in favorable_sectors else 0.0
                    
                    # Combine scores with appropriate weights
                    sector_scores[sector] = (
                        growth_score * 0.35 +
                        momentum_score * 0.20 +
                        profitability_score * 0.25 +
                        (100 - valuation_score) * 0.15 +  # Invert valuation (lower is better)
                        macro_alignment
                    )
                    
                    self.logger.debug(f"US Sector: {sector}, Score: {sector_scores[sector]:.2f}")
                    
            elif market == 'saudi':
                # Get all Saudi market sectors
                all_symbols = self.saudi_api.get_symbols()
                sectors = set(symbol.get('sector', 'Unknown') for symbol in all_symbols)
                
                for sector in sectors:
                    if sector == 'Unknown':
                        continue
                        
                    # Get sector companies
                    sector_companies = [s for s in all_symbols if s.get('sector') == sector]
                    
                    if not sector_companies:
                        continue
                    
                    # Calculate sector metrics
                    growth_score = self._calculate_sector_growth(sector_companies, market)
                    momentum_score = self._calculate_sector_momentum(sector_companies, market)
                    profitability_score = self._calculate_sector_profitability(sector_companies, market)
                    valuation_score = self._calculate_sector_valuation(sector_companies, market)
                    
                    # Add bonus for sectors identified as favorable in macro analysis
                    macro_alignment = 15.0 if sector in favorable_sectors else 0.0
                    
                    # Combine scores with appropriate weights
                    sector_scores[sector] = (
                        growth_score * 0.35 +
                        momentum_score * 0.20 +
                        profitability_score * 0.25 +
                        (100 - valuation_score) * 0.15 +  # Invert valuation (lower is better)
                        macro_alignment
                    )
                    
                    self.logger.debug(f"Saudi Sector: {sector}, Score: {sector_scores[sector]:.2f}")
        
        except Exception as e:
            self.logger.error(f"Error ranking sectors: {str(e)}")
        
        return sector_scores
    
    def _calculate_sector_growth(self, companies: List, market: str) -> float:
        """
        Calculate sector growth score based on revenue and profit growth
        
        Args:
            companies: List of companies in the sector
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Growth score (0-100)
        """
        if not companies:
            return 0
            
        growth_scores = []
        
        # Different approach based on market
        if market == 'us':
            # For US market, we receive a list of symbols
            for symbol in companies:
                try:
                    # Get growth metrics from data fetcher
                    growth_metrics = self.data_fetcher.get_growth_metrics(symbol)
                    
                    if growth_metrics:
                        revenue_growth = growth_metrics.get('revenue_growth', 0)
                        
                        # Get earnings growth from stock analyzer
                        stock_data = self.stock_analyzer.analyze_stock(symbol)
                        if stock_data and 'earnings_growth' in stock_data:
                            earnings_growth = stock_data.get('earnings_growth', 0)
                        else:
                            earnings_growth = revenue_growth * 0.8  # Estimate if not available
                        
                        # Combine revenue and earnings growth
                        company_score = (revenue_growth * 0.6 + earnings_growth * 0.4)
                        growth_scores.append(company_score)
                except Exception as e:
                    self.logger.debug(f"Error calculating growth for US stock {symbol}: {str(e)}")
        
        elif market == 'saudi':
            # For Saudi market, we receive company dictionaries
            for company in companies:
                try:
                    symbol = company.get('symbol')
                    info = self.saudi_api.get_symbol_info(symbol)
                    
                    # Use mock data or calculate from info
                    revenue_growth = info.get('revenue_growth', 0)
                    profit_growth = info.get('profit_growth', 0)
                    
                    company_score = (revenue_growth * 0.6 + profit_growth * 0.4)
                    growth_scores.append(company_score)
                except Exception as e:
                    self.logger.debug(f"Error calculating growth for Saudi stock {company.get('symbol')}: {str(e)}")
        
        # Return average, or 0 if no scores
        if growth_scores:
            # Normalize to 0-100 scale
            avg_growth = sum(growth_scores) / len(growth_scores)
            return min(max(50 + avg_growth * 2.5, 0), 100)  # Scale and clamp to 0-100
        return 50  # Default moderate score
    
    def _calculate_sector_momentum(self, companies: List, market: str) -> float:
        """
        Calculate sector momentum score based on price performance over different timeframes
        
        Args:
            companies: List of companies in the sector
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Momentum score (0-100)
        """
        if not companies:
            return 0
            
        momentum_scores = []
        
        if market == 'us':
            # For US market
            for symbol in companies:
                try:
                    # Get historical data for 6 months
                    hist_data = self.stock_analyzer.get_historical_prices(symbol, days=180)
                    
                    if hist_data is None or len(hist_data) < 60:  # Need sufficient history
                        continue
                    
                    # Extract closing prices
                    closing_prices = hist_data['Close'].values
                    
                    # Calculate returns for different periods
                    latest_price = closing_prices[-1]
                    week_ago_idx = max(0, len(closing_prices) - 5)  # ~1 week
                    month_ago_idx = max(0, len(closing_prices) - 21)  # ~1 month
                    three_month_idx = max(0, len(closing_prices) - 63)  # ~3 months
                    six_month_idx = 0  # Beginning of the period
                    
                    week_return = (latest_price / closing_prices[week_ago_idx] - 1) * 100
                    month_return = (latest_price / closing_prices[month_ago_idx] - 1) * 100
                    three_month_return = (latest_price / closing_prices[three_month_idx] - 1) * 100
                    six_month_return = (latest_price / closing_prices[six_month_idx] - 1) * 100
                    
                    # Weight recent performance more heavily
                    momentum_score = (
                        week_return * 0.3 +
                        month_return * 0.3 +
                        three_month_return * 0.25 +
                        six_month_return * 0.15
                    )
                    
                    momentum_scores.append(momentum_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating momentum for US stock {symbol}: {str(e)}")
        
        elif market == 'saudi':
            # For Saudi market
            for company in companies:
                try:
                    symbol = company.get('symbol')
                    
                    # Get historical data for 6 months
                    historical = self.saudi_api.get_historical_data(symbol, period='6m')
                    
                    if not historical or 'data' not in historical:
                        continue
                        
                    data = historical['data']
                    
                    # Check if we have enough data
                    if len(data) < 20:  # Need at least a month of data
                        continue
                    
                    # Calculate returns for different periods
                    latest_price = data[-1]['close']
                    week_ago_idx = max(0, len(data) - 5)  # ~1 week
                    month_ago_idx = max(0, len(data) - 20)  # ~1 month
                    three_month_idx = max(0, len(data) - 60)  # ~3 months
                    six_month_idx = 0  # Beginning of the period
                    
                    # Calculate returns (handle case when indices are the same)
                    week_return = (latest_price / data[week_ago_idx]['close'] - 1) * 100 if week_ago_idx != len(data) - 1 else 0
                    month_return = (latest_price / data[month_ago_idx]['close'] - 1) * 100 if month_ago_idx != len(data) - 1 else 0
                    three_month_return = (latest_price / data[three_month_idx]['close'] - 1) * 100 if three_month_idx != len(data) - 1 else 0
                    six_month_return = (latest_price / data[six_month_idx]['close'] - 1) * 100 if six_month_idx != len(data) - 1 else 0
                    
                    # Weight recent performance more heavily
                    momentum_score = (
                        week_return * 0.3 +
                        month_return * 0.3 +
                        three_month_return * 0.25 +
                        six_month_return * 0.15
                    )
                    
                    momentum_scores.append(momentum_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating momentum for Saudi stock {symbol}: {str(e)}")
        
        # Return average, or 0 if no scores
        if momentum_scores:
            avg_momentum = sum(momentum_scores) / len(momentum_scores)
            # Normalize to 0-100 scale
            return min(max(50 + avg_momentum * 2.5, 0), 100)  # Center at 50, scale and clamp
        return 50  # Default moderate score
    
    def _calculate_sector_profitability(self, companies: List, market: str) -> float:
        """
        Calculate sector profitability based on ROE, margins, ROTC, and other metrics
        
        Args:
            companies: List of companies in the sector
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Profitability score (0-100)
        """
        if not companies:
            return 0
            
        profitability_scores = []
        
        if market == 'us':
            # For US market
            for symbol in companies:
                try:
                    # Get ROTC data
                    rotc_data = self.data_fetcher.calculate_rotc(symbol)
                    rotc = rotc_data.get('rotc', 0) if rotc_data else 0
                    
                    # Get other profitability metrics
                    stock_info = self.stock_analyzer.get_stock_info(symbol)
                    
                    if stock_info:
                        # Extract metrics (handling potential None values)
                        roe = stock_info.get('returnOnEquity', 0)
                        if roe is not None:
                            roe = roe * 100  # Convert to percentage
                        else:
                            roe = 0
                            
                        profit_margin = stock_info.get('profitMargin', 0)
                        if profit_margin is not None:
                            profit_margin = profit_margin * 100  # Convert to percentage
                        else:
                            profit_margin = 0
                        
                        # Calculate weighted profitability score
                        profitability_score = (
                            (rotc if rotc is not None else 0) * 0.4 +
                            roe * 0.3 +
                            profit_margin * 0.3
                        )
                        
                        profitability_scores.append(profitability_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating profitability for US stock {symbol}: {str(e)}")
        
        elif market == 'saudi':
            # For Saudi market
            for company in companies:
                try:
                    symbol = company.get('symbol')
                    info = self.saudi_api.get_symbol_info(symbol)
                    
                    # Get profitability metrics
                    roe = info.get('roe', 0)  # Return on Equity
                    profit_margin = info.get('profit_margin', 0)
                    roic = info.get('roic', 0)  # Return on Invested Capital
                    
                    # Calculate weighted profitability score
                    profitability_score = (
                        roe * 0.4 +
                        profit_margin * 0.3 +
                        roic * 0.3
                    )
                    
                    profitability_scores.append(profitability_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating profitability for Saudi stock {symbol}: {str(e)}")
        
        # Return average, or 0 if no scores
        if profitability_scores:
            avg_profitability = sum(profitability_scores) / len(profitability_scores)
            # Normalize to 0-100 scale
            return min(max(avg_profitability * 5, 0), 100)  # Scale and clamp
        return 50  # Default moderate score
    
    def _calculate_sector_valuation(self, companies: List, market: str) -> float:
        """
        Calculate sector valuation based on P/E, P/B, and EV/EBITDA
        Lower score is better (cheaper valuation)
        
        Args:
            companies: List of companies in the sector
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Valuation score (0-100, lower is better)
        """
        if not companies:
            return 50  # Default moderate valuation
            
        valuation_scores = []
        
        if market == 'us':
            # For US market
            for symbol in companies:
                try:
                    # Get valuation metrics
                    stock_info = self.stock_analyzer.get_stock_info(symbol)
                    
                    if stock_info:
                        # Extract metrics (handling potential None values)
                        pe_ratio = stock_info.get('trailingPE', 0)
                        if pe_ratio is None or pe_ratio <= 0 or pe_ratio > 200:
                            pe_ratio = 20  # Default if not available or unreasonable
                            
                        pb_ratio = stock_info.get('priceToBook', 0)
                        if pb_ratio is None or pb_ratio <= 0 or pb_ratio > 50:
                            pb_ratio = 3  # Default if not available or unreasonable
                            
                        ev_ebitda = stock_info.get('enterpriseToEbitda', 0)
                        if ev_ebitda is None or ev_ebitda <= 0 or ev_ebitda > 100:
                            ev_ebitda = 15  # Default if not available or unreasonable
                        
                        # Calculate valuation score components (lower is better)
                        pe_score = min(max(pe_ratio * 2, 0), 100)  # PE of 50+ = 100 (expensive)
                        pb_score = min(max(pb_ratio * 10, 0), 100)  # PB of 10+ = 100 (expensive)
                        ev_ebitda_score = min(max(ev_ebitda * 4, 0), 100)  # EV/EBITDA of 25+ = 100 (expensive)
                        
                        # Combined valuation score (lower is better)
                        valuation_score = (
                            pe_score * 0.4 +
                            pb_score * 0.3 +
                            ev_ebitda_score * 0.3
                        )
                        
                        valuation_scores.append(valuation_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating valuation for US stock {symbol}: {str(e)}")
        
        elif market == 'saudi':
            # For Saudi market
            for company in companies:
                try:
                    symbol = company.get('symbol')
                    info = self.saudi_api.get_symbol_info(symbol)
                    
                    # Get valuation metrics
                    pe_ratio = info.get('pe_ratio', 0)
                    pb_ratio = info.get('pb_ratio', 0)
                    ev_ebitda = info.get('ev_ebitda', 0)
                    
                    if pe_ratio <= 0 or pe_ratio > 200:
                        pe_ratio = 15  # Default for Saudi market
                    
                    if pb_ratio <= 0 or pb_ratio > 50:
                        pb_ratio = 2  # Default for Saudi market
                        
                    if ev_ebitda <= 0 or ev_ebitda > 100:
                        ev_ebitda = 12  # Default for Saudi market
                    
                    # Calculate valuation score components (lower is better)
                    pe_score = min(max(pe_ratio * 2.5, 0), 100)  # PE of 40+ = 100 (expensive)
                    pb_score = min(max(pb_ratio * 15, 0), 100)  # PB of 6.7+ = 100 (expensive)
                    ev_ebitda_score = min(max(ev_ebitda * 5, 0), 100)  # EV/EBITDA of 20+ = 100 (expensive)
                    
                    # Combined valuation score (lower is better)
                    valuation_score = (
                        pe_score * 0.4 +
                        pb_score * 0.3 +
                        ev_ebitda_score * 0.3
                    )
                    
                    valuation_scores.append(valuation_score)
                    
                except Exception as e:
                    self.logger.debug(f"Error calculating valuation for Saudi stock {symbol}: {str(e)}")
        
        # Return average, or default if no scores
        if valuation_scores:
            avg_valuation = sum(valuation_scores) / len(valuation_scores)
            return avg_valuation  # Already normalized (0-100)
        return 50  # Default moderate valuation
    
    def _select_top_sectors(self, sector_scores: Dict[str, float], market: str) -> List[Dict]:
        """
        Select top-performing sectors with the highest growth potential
        
        Args:
            sector_scores: Dict mapping sector names to scores
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            List of top sector dictionaries with name and score
        """
        # Sort sectors by score
        sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Select top sectors with good potential (score > 50)
        # For long-term growth strategy, select at least 5 sectors if possible
        top_sectors = []
        
        # First add sectors with strong potential
        for sector, score in sorted_sectors:
            if score >= 65:  # Strong growth potential
                top_sectors.append({
                    'name': sector,
                    'score': score,
                    'tier': 'top',
                    'description': f"Strong growth potential in {sector} sector with score {score:.1f}/100"
                })
        
        # Then add sectors with solid potential
        for sector, score in sorted_sectors:
            if 50 <= score < 65 and len(top_sectors) < 8:  # Solid growth potential
                top_sectors.append({
                    'name': sector,
                    'score': score,
                    'tier': 'solid',
                    'description': f"Solid growth potential in {sector} sector with score {score:.1f}/100"
                })
        
        # Ensure we have at least 5 sectors for diversification
        if len(top_sectors) < 5:
            # Add more sectors to reach minimum required
            for sector, score in sorted_sectors:
                if score < 50 and {'name': sector} not in top_sectors and len(top_sectors) < 5:
                    top_sectors.append({
                        'name': sector,
                        'score': score,
                        'tier': 'additional',
                        'description': f"Additional diversification from {sector} sector with score {score:.1f}/100"
                    })
        
        # For US market specifically
        if market == 'us':
            # Add Technology sector if not already in top sectors (for long-term growth)
            if not any(s['name'] == 'Technology' for s in top_sectors) and 'Technology' in sector_scores:
                tech_score = sector_scores['Technology']
                top_sectors.append({
                    'name': 'Technology',
                    'score': tech_score,
                    'tier': 'strategic',
                    'description': "Strategic addition of Technology sector for long-term growth potential"
                })
                
            # Add Healthcare sector if not already in top sectors (for defensive growth)
            if not any(s['name'] == 'Healthcare' for s in top_sectors) and 'Healthcare' in sector_scores:
                health_score = sector_scores['Healthcare']
                top_sectors.append({
                    'name': 'Healthcare',
                    'score': health_score,
                    'tier': 'strategic',
                    'description': "Strategic addition of Healthcare sector for defensive growth potential"
                })
        
        # For Saudi market specifically
        elif market == 'saudi':
            # Add Banking sector if not already in top sectors (important in Saudi economy)
            if not any(s['name'] == 'Banking' for s in top_sectors) and 'Banking' in sector_scores:
                banking_score = sector_scores['Banking']
                top_sectors.append({
                    'name': 'Banking',
                    'score': banking_score,
                    'tier': 'strategic',
                    'description': "Strategic addition of Banking sector for financial exposure in Saudi market"
                })
                
            # Add Petrochemicals or Energy if not already in top sectors (key Saudi sectors)
            if not any(s['name'] in ['Petrochemicals', 'Energy'] for s in top_sectors):
                if 'Petrochemicals' in sector_scores:
                    petrochem_score = sector_scores['Petrochemicals']
                    top_sectors.append({
                        'name': 'Petrochemicals',
                        'score': petrochem_score,
                        'tier': 'strategic',
                        'description': "Strategic addition of Petrochemicals sector for key Saudi market exposure"
                    })
                elif 'Energy' in sector_scores:
                    energy_score = sector_scores['Energy']
                    top_sectors.append({
                        'name': 'Energy',
                        'score': energy_score,
                        'tier': 'strategic',
                        'description': "Strategic addition of Energy sector for key Saudi market exposure"
                    })
        
        return top_sectors
    
    def _get_companies_in_sectors(self, sectors: List[Dict], market: str, max_companies_per_sector: int = 40) -> List:
        """
        Get companies in the selected sectors
        
        Args:
            sectors: List of sector dictionaries from _select_top_sectors
            market: Market being analyzed ('us' or 'saudi')
            max_companies_per_sector: Maximum number of companies to include per sector (for testing)
            
        Returns:
            List of companies (format depends on market)
        """
        sector_names = [sector['name'] for sector in sectors]
        self.logger.info(f"Getting companies for {len(sector_names)} sectors in {market.upper()} market (max {max_companies_per_sector} per sector)")
        
        if market == 'us':
            # Get SP500 stocks by sector
            sp500_sectors = self.data_fetcher.get_sp500_sector_stocks()
            
            companies = []
            for sector in sector_names:
                if sector in sp500_sectors:
                    sector_stocks = sp500_sectors[sector]
                    # Limit number of companies per sector for testing
                    if max_companies_per_sector > 0:
                        sector_stocks = sector_stocks[:max_companies_per_sector]
                    # Add sector info to each stock
                    companies.extend([{
                        'symbol': symbol,
                        'sector': sector,
                        'sector_score': next((s['score'] for s in sectors if s['name'] == sector), 0)
                    } for symbol in sector_stocks])
            
            self.logger.info(f"Found {len(companies)} US companies in selected sectors")
            return companies
            
        elif market == 'saudi':
            # Get Saudi market stocks
            all_symbols = self.saudi_api.get_symbols()
            
            # Filter by sector and limit
            sector_counts = {sector: 0 for sector in sector_names}
            companies = []
            
            for symbol in all_symbols:
                sector = symbol.get('sector')
                if sector in sector_names:
                    # Check if we've reached the limit for this sector
                    if max_companies_per_sector > 0 and sector_counts[sector] >= max_companies_per_sector:
                        continue
                        
                    # Add sector score to company data
                    company = symbol.copy()
                    company['sector_score'] = next((s['score'] for s in sectors if s['name'] == sector), 0)
                    companies.append(company)
                    
                    # Increment counter
                    sector_counts[sector] += 1
            
            self.logger.info(f"Found {len(companies)} Saudi companies in selected sectors")
            return companies
    
    def _run_fundamental_screening(self, companies: List, criteria: Dict, market: str) -> List[Dict]:
        """
        Apply fundamental screening criteria to companies, focusing on ROTC, revenue growth,
        EBITDA positivity, and free cash flow
        
        Args:
            companies: List of company data dictionaries
            criteria: Investment criteria to apply
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Filtered list of companies that pass screening with fundamental metrics
        """
        self.logger.info(f"Screening {len(companies)} companies for {market.upper()} market")
        screened_companies = []
        
        # Extract screening criteria
        min_rotc = criteria.get('min_rotc', 15.0)
        min_revenue_growth = criteria.get('min_revenue_growth', 5.0)
        min_market_cap = criteria.get('min_market_cap', 1_000_000_000)
        positive_ebitda = criteria.get('positive_ebitda', True)
        positive_fcf = criteria.get('positive_fcf', True)
        
        for company in companies:
            try:
                # Different approach based on market
                if market == 'us':
                    # Get symbol as string
                    if isinstance(company, dict):
                        symbol = company.get('symbol', '')
                    else:
                        symbol = company
                    
                    # Get ROTC (Return on Tangible Capital)
                    # Make sure we have a string symbol
                    if isinstance(symbol, dict):
                        symbol_str = symbol.get('symbol', '')
                    else:
                        symbol_str = symbol
                        
                    rotc_data = self.data_fetcher.calculate_rotc(symbol_str)
                    rotc = rotc_data.get('rotc', 0) if rotc_data else 0
                    
                    # Get growth metrics
                    growth_metrics = self.data_fetcher.get_growth_metrics(symbol_str)
                    revenue_growth = growth_metrics.get('revenue_growth', 0) if growth_metrics else 0
                    
                    # Get additional fundamental data
                    stock_info = self.stock_analyzer.get_stock_info(symbol_str)
                    
                    if not stock_info:
                        continue
                        
                    # Extract key metrics
                    market_cap = stock_info.get('marketCap', 0)
                    ebitda = stock_info.get('ebitda', 0)
                    free_cash_flow = stock_info.get('freeCashflow', 0)
                    
                    # Calculate debt metrics
                    total_debt = stock_info.get('totalDebt', 0)
                    total_equity = stock_info.get('totalStockholderEquity', 1)  # Use 1 to avoid division by zero
                    debt_to_equity = total_debt / total_equity if total_equity else float('inf')
                    
                    # Extract profitability metrics
                    roe = stock_info.get('returnOnEquity', 0)
                    if roe is not None:
                        roe = roe * 100  # Convert to percentage
                    else:
                        roe = 0
                        
                    profit_margin = stock_info.get('profitMargin', 0)
                    if profit_margin is not None:
                        profit_margin = profit_margin * 100  # Convert to percentage
                    else:
                        profit_margin = 0
                    
                    # Check if company passes key criteria
                    passes_criteria = (
                        market_cap >= min_market_cap and 
                        rotc is not None and rotc >= min_rotc and
                        revenue_growth is not None and revenue_growth >= min_revenue_growth and
                        (not positive_ebitda or (ebitda is not None and ebitda > 0)) and
                        (not positive_fcf or (free_cash_flow is not None and free_cash_flow > 0))
                    )
                    
                    if passes_criteria:
                        # Prepare company data with all relevant metrics
                        company_with_scores = company.copy()
                        company_with_scores.update({
                            'name': stock_info.get('longName', symbol),
                            'market_cap': market_cap,
                            'rotc': rotc,
                            'revenue_growth': revenue_growth,
                            'ebitda': ebitda,
                            'free_cash_flow': free_cash_flow,
                            'debt_to_equity': debt_to_equity,
                            'roe': roe,
                            'profit_margin': profit_margin,
                            'pe_ratio': stock_info.get('trailingPE', 0),
                            'pb_ratio': stock_info.get('priceToBook', 0),
                            'dividend_yield': stock_info.get('dividendYield', 0) * 100 if stock_info.get('dividendYield') else 0,
                            'price': stock_info.get('regularMarketPrice', 0),
                            'high_52w': stock_info.get('fiftyTwoWeekHigh', 0),
                            'low_52w': stock_info.get('fiftyTwoWeekLow', 0),
                            'market': 'US'
                        })
                        
                        # Calculate fundamental score (0-100 scale)
                        rotc_score = min(rotc / min_rotc, 3) * 25  # Up to 75 points for 3x minimum ROTC
                        growth_score = min(revenue_growth / min_revenue_growth, 4) * 15  # Up to 60 points for 4x minimum growth
                        margin_score = min(profit_margin / 10, 2) * 10  # Up to 20 points for 20% margin
                        
                        # Cash flow/EBITDA positive bonus
                        ebitda_bonus = 10 if ebitda > 0 else 0
                        fcf_bonus = 15 if free_cash_flow > 0 else 0
                        
                        # Penalty for high debt
                        debt_penalty = min(debt_to_equity * 10, 25) if debt_to_equity > 1 else 0
                        
                        fundamental_score = min(
                            rotc_score + growth_score + margin_score + ebitda_bonus + fcf_bonus - debt_penalty,
                            100
                        )
                        
                        company_with_scores['fundamental_score'] = fundamental_score
                        screened_companies.append(company_with_scores)
                
                elif market == 'saudi':
                    # Get symbol as string
                    if isinstance(company, dict):
                        symbol = company.get('symbol', '')
                    else:
                        symbol = company
                    info = self.saudi_api.get_symbol_info(symbol)
                    
                    # Extract metrics
                    market_cap = info.get('market_cap', 0)
                    roic = info.get('roic', 0)  # Use ROIC as proxy for ROTC
                    revenue_growth = info.get('revenue_growth', 0)
                    ebitda = info.get('ebitda', 0)
                    free_cash_flow = info.get('free_cash_flow', 0)
                    profit_margin = info.get('profit_margin', 0)
                    roe = info.get('roe', 0)
                    debt_to_equity = info.get('debt_to_equity', 0)
                    
                    # Check if company passes key criteria
                    passes_criteria = (
                        market_cap >= min_market_cap and 
                        roic >= min_rotc and  # Using ROIC as proxy for ROTC
                        revenue_growth >= min_revenue_growth and
                        (not positive_ebitda or ebitda > 0) and
                        (not positive_fcf or free_cash_flow > 0)
                    )
                    
                    if passes_criteria:
                        # Add fundamental scores to company data
                        company_with_scores = company.copy()
                        company_with_scores.update({
                            'market_cap': market_cap,
                            'rotc': roic,  # Using ROIC as proxy for ROTC
                            'revenue_growth': revenue_growth,
                            'ebitda': ebitda,
                            'free_cash_flow': free_cash_flow,
                            'roe': roe,
                            'profit_margin': profit_margin,
                            'debt_to_equity': debt_to_equity,
                            'pe_ratio': info.get('pe_ratio', 0),
                            'pb_ratio': info.get('pb_ratio', 0),
                            'dividend_yield': info.get('dividend_yield', 0),
                            'price': info.get('price', 0),
                            'high_52w': info.get('high_52w', 0),
                            'low_52w': info.get('low_52w', 0),
                            'market': 'Saudi'
                        })
                        
                        # Calculate fundamental score (0-100 scale)
                        rotc_score = min(roic / min_rotc, 3) * 25  # Up to 75 points for 3x minimum ROTC
                        growth_score = min(revenue_growth / min_revenue_growth, 4) * 15  # Up to 60 points for 4x minimum growth
                        margin_score = min(profit_margin / 10, 2) * 10  # Up to 20 points for 20% margin
                        
                        # Cash flow/EBITDA positive bonus
                        ebitda_bonus = 10 if ebitda > 0 else 0
                        fcf_bonus = 15 if free_cash_flow > 0 else 0
                        
                        # Penalty for high debt
                        debt_penalty = min(debt_to_equity * 10, 25) if debt_to_equity > 1 else 0
                        
                        fundamental_score = min(
                            rotc_score + growth_score + margin_score + ebitda_bonus + fcf_bonus - debt_penalty,
                            100
                        )
                        
                        company_with_scores['fundamental_score'] = fundamental_score
                        screened_companies.append(company_with_scores)
                    
            except Exception as e:
                self.logger.debug(f"Error screening {company.get('symbol', 'unknown')}: {str(e)}")
        
        # Sort by fundamental score
        screened_companies.sort(key=lambda x: x.get('fundamental_score', 0), reverse=True)
        
        self.logger.info(f"Fundamental screening passed {len(screened_companies)} companies out of {len(companies)}")
        return screened_companies
    
    def _analyze_management_quality(self, companies: List[Dict], criteria: Dict, market: str) -> List[Dict]:
        """
        Analyze management quality based on historical performance consistency, capital allocation,
        and statement delivery compared to promises
        
        Args:
            companies: List of company data dictionaries that passed fundamental screening
            criteria: Investment criteria to apply
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            List of companies that pass management quality assessment with quality scores
        """
        self.logger.info(f"Analyzing management quality for {len(companies)} companies")
        
        min_management_score = criteria.get('min_management_score', 60.0)
        quality_companies = []
        
        for company in companies:
            try:
                symbol = company.get('symbol')
                
                # Assess management quality (implementation varies by market)
                if market == 'us':
                    # For US stocks, analyze earnings beats, capital allocation, and business consistency
                    
                    # In a real implementation, this would analyze:
                    # 1. SEC filings for promises vs. delivery
                    # 2. Conference call transcripts
                    # 3. Capital allocation decisions
                    # 4. Business consistency metrics
                    
                    # For this implementation, we'll use a simplified proxy approach
                    stock_data = self.stock_analyzer.analyze_stock(symbol) or {}
                    
                    # Get earnings history (beats vs. misses) as one proxy for management quality
                    earnings_beats = 0
                    earnings_misses = 0
                    
                    # In a real implementation, this would come from actual earnings data
                    # For now, estimate based on available info or use default moderate values
                    if 'earnings_history' in stock_data:
                        earnings_history = stock_data.get('earnings_history', [])
                        if earnings_history:
                            for quarter in earnings_history:
                                if quarter.get('surprise', 0) > 0:
                                    earnings_beats += 1
                                else:
                                    earnings_misses += 1
                    else:
                        # Default moderate values for demo
                        earnings_beats = 3
                        earnings_misses = 1
                    
                    # Get financial consistency metrics
                    revenue_consistency = stock_data.get('revenue_consistency', 70)  # 0-100 scale
                    margin_consistency = stock_data.get('margin_consistency', 65)    # 0-100 scale
                    
                    # Get capital allocation metrics
                    shares_buyback = stock_data.get('shares_buyback', False)
                    dividend_growth = stock_data.get('dividend_growth', 0)
                    
                    # Evaluate management quality
                    earnings_score = 70 + (earnings_beats - earnings_misses) * 5  # Base 70, adjust by beats/misses
                    consistency_score = (revenue_consistency + margin_consistency) / 2
                    capital_score = 60 + (15 if shares_buyback else 0) + min(dividend_growth * 2, 15)
                    
                    # Overall management quality score (0-100)
                    management_score = (
                        earnings_score * 0.35 +
                        consistency_score * 0.40 +
                        capital_score * 0.25
                    )
                    
                    # Cap at range 0-100
                    management_score = min(max(management_score, 0), 100)
                    
                    # Determine strengths and concerns
                    strengths = []
                    concerns = []
                    
                    if earnings_beats > earnings_misses + 1:
                        strengths.append("Consistent earnings beats")
                    elif earnings_misses > earnings_beats:
                        concerns.append("History of earnings misses")
                    
                    if consistency_score >= 75:
                        strengths.append("Strong business consistency")
                    elif consistency_score < 50:
                        concerns.append("Inconsistent business performance")
                    
                    if shares_buyback and dividend_growth > 0:
                        strengths.append("Effective capital allocation via buybacks and dividend growth")
                    elif not shares_buyback and dividend_growth <= 0:
                        concerns.append("Limited shareholder returns via buybacks or dividends")
                    
                elif market == 'saudi':
                    # For Saudi stocks, use simpler metrics due to data limitations
                    # In a real implementation, this would use Saudi market-specific data
                    
                    # Default values for demonstration
                    management_score = 70  # Base score
                    
                    # Adjust based on profitability trend (proxy for management execution)
                    profit_margin = company.get('profit_margin', 0)
                    roe = company.get('roe', 0)
                    
                    if profit_margin > 15 and roe > 15:
                        management_score += 15
                        strengths = ["Strong profit margins and ROE indicate effective management"]
                    elif profit_margin > 10 and roe > 10:
                        management_score += 10
                        strengths = ["Solid profit margins and ROE suggest capable management"]
                    else:
                        strengths = ["Management team maintains market position"]
                    
                    # Adjust based on dividend consistency (proxy for financial discipline)
                    dividend_yield = company.get('dividend_yield', 0)
                    if dividend_yield > 3:
                        management_score += 10
                        strengths.append("Consistent dividend payments indicate financial discipline")
                    
                    # Concerns
                    if profit_margin < 5:
                        management_score -= 10
                        concerns = ["Below-average profit margins"]
                    else:
                        concerns = []
                
                # Only include companies with sufficient management quality
                if management_score >= min_management_score:
                    company_with_quality = company.copy()
                    company_with_quality['management_quality'] = {
                        'score': management_score,
                        'strengths': strengths,
                        'concerns': concerns,
                        'rating': self._get_management_rating(management_score)
                    }
                    quality_companies.append(company_with_quality)
            
            except Exception as e:
                self.logger.debug(f"Error analyzing management for {company.get('symbol', 'unknown')}: {str(e)}")
        
        self.logger.info(f"Management quality assessment passed {len(quality_companies)} out of {len(companies)} companies")
        return quality_companies
    
    def _get_management_rating(self, score: float) -> str:
        """Convert management quality score to rating"""
        if score >= 85:
            return 'Excellent'
        elif score >= 70:
            return 'Good'
        elif score >= 60:
            return 'Acceptable'
        elif score >= 40:
            return 'Questionable'
        else:
            return 'Poor'
    
    def _run_valuation_analysis(self, companies: List[Dict], criteria: Dict, market: str) -> List[Dict]:
        """
        Apply valuation analysis to companies that passed management quality assessment
        
        Args:
            companies: List of company data dictionaries that passed management quality assessment
            criteria: Investment criteria to apply
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            List of companies with valuation scores
        """
        self.logger.info(f"Running valuation analysis for {len(companies)} companies")
        
        max_pe_ratio = criteria.get('max_pe_ratio', 25.0)
        valuated_companies = []
        
        for company in companies:
            try:
                symbol = company.get('symbol')
                current_price = company.get('price', 0)
                pe_ratio = company.get('pe_ratio', 0)
                
                # Different valuation approach based on market
                if market == 'us':
                    # Get more valuation metrics if needed
                    stock_info = self.stock_analyzer.get_stock_info(symbol)
                    
                    if not stock_info:
                        continue
                    
                    # Calculate intrinsic value (Discounted Cash Flow method)
                    intrinsic_value = self._calculate_intrinsic_value(company, market)
                    
                    # Calculate margin of safety
                    margin_of_safety = ((intrinsic_value / current_price) - 1) * 100 if current_price > 0 else 0
                    
                    # Check if meets valuation criteria
                    # Allow higher PE for high-growth companies
                    growth_adjusted_pe_max = max_pe_ratio * (1 + (company.get('revenue_growth', 0) / 20))
                    
                    if pe_ratio <= 0 or pe_ratio > 200:  # Invalid PE ratio, use other metrics
                        meets_valuation = margin_of_safety > 0
                    else:
                        meets_valuation = pe_ratio <= growth_adjusted_pe_max or margin_of_safety > 10
                    
                    if meets_valuation:
                        # Add valuation data to company
                        company_with_valuation = company.copy()
                        company_with_valuation.update({
                            'intrinsic_value': intrinsic_value,
                            'margin_of_safety': margin_of_safety,
                            'price_to_value': current_price / intrinsic_value if intrinsic_value > 0 else float('inf'),
                        })
                        
                        # Calculate valuation score (0-100)
                        if pe_ratio > 0 and pe_ratio < 200:
                            pe_score = min(max(100 - (pe_ratio / growth_adjusted_pe_max) * 100, 0), 100)
                        else:
                            pe_score = 50  # Neutral score for invalid PE
                            
                        mos_score = min(max(margin_of_safety * 2, 0), 100)  # 50% margin of safety = 100 points
                        
                        valuation_score = pe_score * 0.4 + mos_score * 0.6
                        
                        company_with_valuation['valuation_score'] = valuation_score
                        valuated_companies.append(company_with_valuation)
                
                elif market == 'saudi':
                    # Get valuation metrics
                    info = self.saudi_api.get_symbol_info(symbol)
                    
                    # Calculate intrinsic value
                    intrinsic_value = self._calculate_intrinsic_value(company, market)
                    
                    # Calculate margin of safety
                    margin_of_safety = ((intrinsic_value / current_price) - 1) * 100 if current_price > 0 else 0
                    
                    # Check if meets valuation criteria
                    growth_adjusted_pe_max = max_pe_ratio * (1 + (company.get('revenue_growth', 0) / 20))
                    
                    if pe_ratio <= 0 or pe_ratio > 100:  # Invalid PE ratio, use other metrics
                        meets_valuation = margin_of_safety > 0
                    else:
                        meets_valuation = pe_ratio <= growth_adjusted_pe_max or margin_of_safety > 10
                    
                    if meets_valuation:
                        # Add valuation scores to company data
                        company_with_valuation = company.copy()
                        company_with_valuation.update({
                            'intrinsic_value': intrinsic_value,
                            'margin_of_safety': margin_of_safety,
                            'price_to_value': current_price / intrinsic_value if intrinsic_value > 0 else float('inf'),
                        })
                        
                        # Calculate valuation score (0-100)
                        if pe_ratio > 0 and pe_ratio < 100:
                            pe_score = min(max(100 - (pe_ratio / growth_adjusted_pe_max) * 100, 0), 100)
                        else:
                            pe_score = 50  # Neutral score for invalid PE
                            
                        mos_score = min(max(margin_of_safety * 2, 0), 100)  # 50% margin of safety = 100 points
                        
                        valuation_score = pe_score * 0.4 + mos_score * 0.6
                        
                        company_with_valuation['valuation_score'] = valuation_score
                        valuated_companies.append(company_with_valuation)
                    
            except Exception as e:
                self.logger.debug(f"Error in valuation for {company.get('symbol', 'unknown')}: {str(e)}")
        
        # Sort by valuation score
        valuated_companies.sort(key=lambda x: x.get('valuation_score', 0), reverse=True)
        
        self.logger.info(f"Valuation analysis passed {len(valuated_companies)} out of {len(companies)} companies")
        return valuated_companies
    
    def _calculate_intrinsic_value(self, company: Dict, market: str) -> float:
        """
        Calculate intrinsic value using a Discounted Cash Flow (DCF) model
        
        Args:
            company: Company data dictionary
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Estimated intrinsic value per share
        """
        try:
            # Extract symbol as string
            if isinstance(company, dict):
                symbol = company.get('symbol', '')
            else:
                symbol = company
            
            # Different approach based on market
            if market == 'us':
                # Get financial data for US stock
                stock_info = self.stock_analyzer.get_stock_info(symbol)
                
                if not stock_info:
                    return company.get('price', 0) * 1.1  # Default to 10% above current price
                
                # Get earnings per share and growth metrics
                eps = stock_info.get('trailingEPS', 0)
                if eps is None or eps <= 0:
                    eps = stock_info.get('forwardEPS', 0)
                
                if eps is None or eps <= 0:
                    # If no EPS data, estimate from revenue and profit margin
                    revenue_per_share = stock_info.get('revenuePerShare', 0)
                    profit_margin = stock_info.get('profitMargin', 0.1)
                    eps = revenue_per_share * profit_margin if revenue_per_share and profit_margin else 0
                
                # Get growth rate from company data or estimate from revenue growth
                growth_rate = company.get('revenue_growth', 10) / 100  # Convert to decimal
                
                # Use conservative growth rate
                growth_rate = min(growth_rate, 0.20)  # Cap at 20%
                
                # DCF calculation parameters
                discount_rate = 0.10  # 10% discount rate
                terminal_growth_rate = 0.03  # 3% terminal growth
                forecast_years = 5  # 5-year forecast
                
                # Project earnings for forecast period
                projected_earnings = []
                for year in range(1, forecast_years + 1):
                    # Gradually decrease growth rate over time for conservatism
                    adjusted_growth = growth_rate * (1 - (year - 1) / (forecast_years * 2))
                    year_earnings = eps * (1 + adjusted_growth) ** year
                    projected_earnings.append(year_earnings)
                
                # Calculate present value of projected earnings
                present_value = sum(
                    earnings / ((1 + discount_rate) ** year)
                    for year, earnings in enumerate(projected_earnings, 1)
                )
                
                # Calculate terminal value using perpetuity method
                terminal_value = (projected_earnings[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
                present_value_terminal = terminal_value / ((1 + discount_rate) ** forecast_years)
                
                # Total intrinsic value per share
                intrinsic_value = present_value + present_value_terminal
                
                # Apply margin of safety to our estimate (being conservative)
                intrinsic_value = intrinsic_value * 0.9  # 10% safety margin
                
                return max(intrinsic_value, 0)  # Ensure non-negative
                
            elif market == 'saudi':
                # Get financial data for Saudi stock
                info = self.saudi_api.get_symbol_info(symbol)
                
                # Get necessary financial data
                eps = info.get('eps', 0)  # Earnings per share
                growth_rate = company.get('revenue_growth', 8) / 100  # Convert to decimal
                
                # Use conservative growth rate
                growth_rate = min(growth_rate, 0.15)  # Cap at 15%
                
                # DCF calculation
                discount_rate = 0.11  # 11% discount rate (higher for Saudi market)
                terminal_growth_rate = 0.03  # 3% terminal growth
                forecast_years = 5
                
                # Project earnings for forecast period
                projected_earnings = []
                for year in range(1, forecast_years + 1):
                    # Gradually decrease growth rate over time for conservatism
                    adjusted_growth = growth_rate * (1 - (year - 1) / (forecast_years * 2))
                    year_earnings = eps * (1 + adjusted_growth) ** year
                    projected_earnings.append(year_earnings)
                
                # Calculate present value of projected earnings
                present_value = sum(
                    earnings / ((1 + discount_rate) ** year)
                    for year, earnings in enumerate(projected_earnings, 1)
                )
                
                # Calculate terminal value
                terminal_value = (projected_earnings[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
                present_value_terminal = terminal_value / ((1 + discount_rate) ** forecast_years)
                
                # Total intrinsic value per share
                intrinsic_value = present_value + present_value_terminal
                
                # Apply margin of safety to our estimate (being conservative)
                intrinsic_value = intrinsic_value * 0.9  # 10% safety margin
                
                return max(intrinsic_value, 0)  # Ensure non-negative
            
        except Exception as e:
            self.logger.debug(f"Error calculating intrinsic value for {company.get('symbol', 'unknown')}: {str(e)}")
            return company.get('price', 0) * 1.05  # Default to 5% above current price as fallback
    
    def _rank_companies(self, companies: List[Dict], market: str) -> List[Dict]:
        """
        Rank companies based on combined scores from all analysis stages
        
        Args:
            companies: List of company data dictionaries with all analysis scores
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            List of companies sorted by combined score
        """
        self.logger.info(f"Ranking {len(companies)} companies based on combined metrics")
        
        for company in companies:
            # Extract component scores
            fundamental_score = company.get('fundamental_score', 0)
            management_score = company.get('management_quality', {}).get('score', 60)
            valuation_score = company.get('valuation_score', 0)
            sector_score = company.get('sector_score', 0)
            
            # Get technical score (price momentum, etc.)
            try:
                symbol = company.get('symbol')
                technical_score = self._calculate_technical_score(symbol, market)
            except Exception as e:
                self.logger.debug(f"Error calculating technical score for {symbol}: {str(e)}")
                technical_score = 50  # Neutral score as fallback
            
            # Store technical score
            company['technical_score'] = technical_score
            
            # Calculate combined score with weightings from pipeline stages
            combined_score = (
                fundamental_score * self.pipeline_stages['fundamental_screening'] +
                management_score * self.pipeline_stages['management_quality'] +
                valuation_score * self.pipeline_stages['valuation_analysis'] +
                technical_score * self.pipeline_stages['technical_indicators'] +
                sector_score * 0.05  # Small bonus for being in a top sector
            )
            
            # Store combined score
            company['combined_score'] = combined_score
            
            # Generate investment thesis
            company['investment_thesis'] = self._generate_investment_thesis(company)
        
        # Sort by combined score
        ranked_companies = sorted(companies, key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return ranked_companies
    
    def _calculate_technical_score(self, symbol: str, market: str) -> float:
        """
        Calculate technical score based on price momentum, volume, and chart patterns
        
        Args:
            symbol: Stock symbol (string or dict)
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Technical score (0-100)
        """
        """
        Calculate technical score based on price momentum, volume, and chart patterns
        
        Args:
            symbol: Stock symbol
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Technical score (0-100)
        """
        try:
            if market == 'us':
                # Get historical data for US stock
                hist_data = self.stock_analyzer.get_historical_prices(symbol, days=180)
                
                if hist_data is None or len(hist_data) < 50:  # Need sufficient history
                    return 50  # Neutral score if insufficient data
                
                # Extract closing prices and volume
                prices = hist_data['Close'].values
                volumes = hist_data['Volume'].values
                
                # 1. Price momentum (recent performance)
                latest_price = prices[-1]
                week_ago_idx = max(0, len(prices) - 5)  # ~1 week
                month_ago_idx = max(0, len(prices) - 21)  # ~1 month
                three_month_idx = max(0, len(prices) - 63)  # ~3 months
                
                week_change = (latest_price / prices[week_ago_idx] - 1) * 100
                month_change = (latest_price / prices[month_ago_idx] - 1) * 100
                three_month_change = (latest_price / prices[three_month_idx] - 1) * 100
                
                momentum_score = (
                    week_change * 0.3 +
                    month_change * 0.4 +
                    three_month_change * 0.3
                )
                momentum_score = min(max(50 + momentum_score * 2, 0), 100)  # Scale and clamp to 0-100
                
                # 2. Volume trend
                recent_volumes = volumes[-20:]
                older_volumes = volumes[-40:-20]
                
                avg_recent_volume = np.mean(recent_volumes) if len(recent_volumes) > 0 else 0
                avg_older_volume = np.mean(older_volumes) if len(older_volumes) > 0 else avg_recent_volume
                
                volume_trend = (avg_recent_volume / avg_older_volume - 0.8) * 100 if avg_older_volume > 0 else 50
                volume_score = min(max(volume_trend, 0), 100)  # Clamp to 0-100
                
                # 3. Moving average analysis
                # Calculate moving averages
                ma20 = np.mean(prices[-20:]) if len(prices) >= 20 else latest_price
                ma50 = np.mean(prices[-50:]) if len(prices) >= 50 else latest_price
                ma200 = np.mean(prices[-200:]) if len(prices) >= 200 else latest_price
                
                # Score based on price relative to MAs
                ma_score = 0
                
                # Uptrend conditions
                if latest_price > ma20 and ma20 > ma50 and ma50 > ma200:
                    ma_score = 100  # Strong uptrend
                elif latest_price > ma20 and ma20 > ma50:
                    ma_score = 80  # Moderate uptrend
                elif latest_price > ma50 and ma50 > ma200:
                    ma_score = 70  # Long-term uptrend
                elif latest_price > ma20:
                    ma_score = 60  # Above short-term MA
                
                # Downtrend conditions
                elif latest_price < ma20 and ma20 < ma50 and ma50 < ma200:
                    ma_score = 0  # Strong downtrend
                elif latest_price < ma20 and ma20 < ma50:
                    ma_score = 20  # Moderate downtrend
                elif latest_price < ma50 and ma50 < ma200:
                    ma_score = 30  # Long-term downtrend
                
                # Neutral conditions
                else:
                    ma_score = 50  # Neutral MA configuration
                
                # Combined technical score
                technical_score = (
                    momentum_score * 0.4 +
                    volume_score * 0.2 +
                    ma_score * 0.4
                )
                
                return technical_score
            
            elif market == 'saudi':
                # Get historical data for Saudi stock
                historical = self.saudi_api.get_historical_data(symbol, period='6m')
                
                if not historical or 'data' not in historical:
                    return 50  # Neutral score if no data
                    
                data = historical['data']
                
                if len(data) < 20:  # Need sufficient data
                    return 50
                
                # Extract prices and volumes from historical data
                prices = [day['close'] for day in data]
                volumes = [day.get('volume', 0) for day in data]
                
                latest_price = prices[-1]
                
                # Calculate moving averages
                ma_short = np.mean(prices[-10:]) if len(prices) >= 10 else latest_price
                ma_medium = np.mean(prices[-30:]) if len(prices) >= 30 else latest_price
                ma_long = np.mean(prices[-90:]) if len(prices) >= 90 else latest_price
                
                # Price momentum analysis
                short_term_return = (latest_price / prices[-10]) - 1 if len(prices) >= 10 else 0
                medium_term_return = (latest_price / prices[-30]) - 1 if len(prices) >= 30 else 0
                long_term_return = (latest_price / prices[-90]) - 1 if len(prices) >= 90 else 0
                
                momentum_score = (
                    short_term_return * 100 * 0.3 +
                    medium_term_return * 100 * 0.4 +
                    long_term_return * 100 * 0.3
                )
                momentum_score = min(max(50 + momentum_score * 2, 0), 100)  # Scale and clamp
                
                # Moving average analysis
                ma_score = 0
                
                if latest_price > ma_short and ma_short > ma_medium and ma_medium > ma_long:
                    ma_score = 100  # Strong uptrend
                elif latest_price > ma_short and ma_short > ma_medium:
                    ma_score = 80  # Moderate uptrend
                elif latest_price > ma_medium:
                    ma_score = 60  # Above medium-term MA
                elif latest_price < ma_short and ma_short < ma_medium and ma_medium < ma_long:
                    ma_score = 0  # Strong downtrend
                elif latest_price < ma_short and ma_short < ma_medium:
                    ma_score = 20  # Moderate downtrend
                else:
                    ma_score = 50  # Neutral
                
                # Volume analysis (simplified for Saudi market)
                recent_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else 0
                older_volume = np.mean(volumes[-30:-10]) if len(volumes) >= 30 else recent_volume
                
                volume_score = 50  # Default neutral
                if recent_volume > older_volume * 1.2:
                    volume_score = 80  # Increasing volume (bullish)
                elif recent_volume < older_volume * 0.8:
                    volume_score = 30  # Decreasing volume (bearish)
                
                # Combined technical score
                technical_score = (
                    momentum_score * 0.4 +
                    ma_score * 0.4 +
                    volume_score * 0.2
                )
                
                return technical_score
                
        except Exception as e:
            self.logger.debug(f"Error in technical analysis for {symbol}: {str(e)}")
            return 50  # Neutral score on error
    
    def _generate_investment_thesis(self, company: Dict) -> str:
        """
        Generate an investment thesis explanation for the company
        
        Args:
            company: Company data dictionary with all analysis results
            
        Returns:
            Investment thesis text
        """
        symbol = company.get('symbol', '')
        name = company.get('name', symbol)
        sector = company.get('sector', 'Unknown')
        
        # Get key metrics
        rotc = company.get('rotc', 0)
        revenue_growth = company.get('revenue_growth', 0)
        margin_of_safety = company.get('margin_of_safety', 0)
        management_rating = company.get('management_quality', {}).get('rating', 'Average')
        
        # Build investment thesis
        thesis = f"{name} ({symbol}) is a compelling investment opportunity in the {sector} sector. "
        
        # Add details about return on capital
        if rotc >= 20:
            thesis += f"The company demonstrates exceptional capital efficiency with a {rotc:.1f}% return on tangible capital, "
        elif rotc >= 15:
            thesis += f"The company shows strong capital efficiency with a {rotc:.1f}% return on tangible capital, "
        else:
            thesis += f"The company maintains solid capital efficiency with a {rotc:.1f}% return on tangible capital, "
        
        # Add details about growth
        if revenue_growth >= 15:
            thesis += f"paired with exceptional revenue growth of {revenue_growth:.1f}%. "
        elif revenue_growth >= 8:
            thesis += f"coupled with strong revenue growth of {revenue_growth:.1f}%. "
        else:
            thesis += f"along with steady revenue growth of {revenue_growth:.1f}%. "
        
        # Add details about management
        thesis += f"Management quality is rated as {management_rating}, "
        if management_rating in ['Excellent', 'Good']:
            thesis += "demonstrating effective capital allocation and consistent performance. "
        else:
            thesis += "with room for improvement in capital allocation. "
        
        # Add valuation perspective
        if margin_of_safety >= 20:
            thesis += f"Current valuation offers a significant margin of safety of {margin_of_safety:.1f}%, "
            thesis += "suggesting the stock is substantially undervalued."
        elif margin_of_safety >= 10:
            thesis += f"Current valuation offers a reasonable margin of safety of {margin_of_safety:.1f}%, "
            thesis += "indicating the stock is moderately undervalued."
        else:
            thesis += f"Current valuation offers a margin of safety of {margin_of_safety:.1f}%, "
            thesis += "suggesting fair valuation with potential for long-term appreciation."
        
        return thesis
    
    def _select_final_candidates(self, ranked_companies: List[Dict], market: str) -> List[Dict]:
        """
        Select final investment candidates to build portfolio
        
        Args:
            ranked_companies: List of ranked company data dictionaries
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            List of final selected companies
        """
        self.logger.info(f"Selecting final investment candidates from {len(ranked_companies)} companies")
        
        # Minimum required portfolio metrics
        min_stocks = self.portfolio_params['min_stocks']
        max_stocks = self.portfolio_params['max_stocks']
        min_sectors = self.portfolio_params['min_sectors']
        
        # Select top candidates with high scores (80+)
        top_tier = [c for c in ranked_companies if c.get('combined_score', 0) >= 80]
        
        # Select mid-tier candidates (65-80)
        mid_tier = [c for c in ranked_companies if 65 <= c.get('combined_score', 0) < 80]
        
        # Select acceptable candidates (score 50-65)
        acceptable_tier = [c for c in ranked_companies if 50 <= c.get('combined_score', 0) < 65]
        
        # Start with top tier
        selected = top_tier.copy()
        
        # If we need more stocks, add from mid tier
        if len(selected) < min_stocks:
            # Add mid tier stocks to reach minimum
            needed = min_stocks - len(selected)
            selected.extend(mid_tier[:needed])
        
        # If still insufficient, add from acceptable tier
        if len(selected) < min_stocks:
            needed = min_stocks - len(selected)
            selected.extend(acceptable_tier[:needed])
        
        # If we have too many stocks, trim to maximum
        if len(selected) > max_stocks:
            selected = selected[:max_stocks]
        
        # Check sector diversification
        selected_sectors = set(c.get('sector', 'Unknown') for c in selected)
        
        # If we don't have enough sectors, add more stocks from different sectors
        if len(selected_sectors) < min_sectors:
            # Identify sectors we're missing
            remaining_companies = [c for c in ranked_companies if c not in selected]
            
            # Sort by score within each new sector
            for company in sorted(remaining_companies, key=lambda x: x.get('combined_score', 0), reverse=True):
                sector = company.get('sector', 'Unknown')
                if sector not in selected_sectors and company.get('combined_score', 0) >= 45:
                    selected.append(company)
                    selected_sectors.add(sector)
                    
                    if len(selected_sectors) >= min_sectors:
                        break
        
        # If we still don't have minimum stocks, add more top remaining candidates
        if len(selected) < min_stocks:
            remaining = [c for c in ranked_companies if c not in selected]
            needed = min_stocks - len(selected)
            selected.extend(remaining[:needed])
        
        # Final sort by combined score
        selected.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        self.logger.info(f"Selected {len(selected)} final candidates from {len(selected_sectors)} sectors")
        return selected
    
    def _calculate_technical_score(self, symbol: str, market: str = 'saudi') -> float:
        """
        Calculate technical score based on price momentum, volume, and chart patterns
        
        Args:
            symbol: Stock symbol
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Technical score (0-100)
        """
        try:
            if market == 'us':
                # Ensure symbol is a string
                symbol_str = symbol.get('symbol', symbol) if isinstance(symbol, dict) else symbol
                
                # Get historical data for US stock
                historical_prices = self.stock_analyzer.get_historical_prices(symbol_str, days=180)
                
                if historical_prices is None or len(historical_prices) < 50:  # Need sufficient history
                    return 50  # Neutral score if insufficient data
                
                # Extract data
                prices = historical_prices['Close'].values
                volumes = historical_prices['Volume'].values if 'Volume' in historical_prices else np.zeros(len(prices))
                
                # Calculate price momentum scores
                latest_price = prices[-1]
                week_ago_idx = max(0, len(prices) - 5)  # ~1 week
                month_ago_idx = max(0, len(prices) - 21)  # ~1 month
                
                week_change = (latest_price / prices[week_ago_idx] - 1) * 100
                month_change = (latest_price / prices[month_ago_idx] - 1) * 100
                
                momentum_score = (week_change * 0.4 + month_change * 0.6 + 10) * 2.5
                momentum_score = min(max(momentum_score, 0), 100)  # Clamp to 0-100
                
                # Volume trend
                recent_volumes = volumes[-20:]
                older_volumes = volumes[-40:-20]
                
                avg_recent_volume = np.mean(recent_volumes) if len(recent_volumes) > 0 else 0
                avg_older_volume = np.mean(older_volumes) if len(older_volumes) > 0 else avg_recent_volume
                
                volume_trend = (avg_recent_volume / avg_older_volume - 0.8) * 50 if avg_older_volume > 0 else 50
                volume_score = min(max(volume_trend, 0), 100)  # Clamp to 0-100
                
                # Moving average analysis
                ma20 = np.mean(prices[-20:])
                ma50 = np.mean(prices[-50:])
                
                # Score based on price relative to MAs
                ma_score = 0
                if latest_price > ma20 and ma20 > ma50:
                    ma_score = 100  # Strong uptrend
                elif latest_price > ma20:
                    ma_score = 75  # Above short-term MA
                elif latest_price > ma50:
                    ma_score = 50  # Above long-term MA
                elif ma20 > ma50:
                    ma_score = 25  # MAs in positive configuration but price below
                
                # Combined technical score
                technical_score = (
                    momentum_score * 0.4 +
                    volume_score * 0.3 +
                    ma_score * 0.3
                )
                
                return technical_score
                
            else:  # market == 'saudi'
                # Ensure symbol is a string
                symbol_str = symbol.get('symbol', symbol) if isinstance(symbol, dict) else symbol
                
                # Get historical data for Saudi stock
                historical = self.saudi_api.get_historical_data(symbol_str, period='6m')
                
                if not historical or 'data' not in historical:
                    return 50  # Return neutral score
                    
                data = historical['data']
                
                if len(data) < 50:  # Need enough data for analysis
                    return 50  # Return neutral score
                
                # 1. Price momentum (recent performance)
                latest_price = data[-1]['close']
                week_ago_idx = max(0, len(data) - 5)  # ~1 week (5 trading days)
                month_ago_idx = max(0, len(data) - 20)  # ~1 month (20 trading days)
                
                week_change = (latest_price / data[week_ago_idx]['close'] - 1) * 100
                month_change = (latest_price / data[month_ago_idx]['close'] - 1) * 100
                
                momentum_score = (week_change * 0.4 + month_change * 0.6 + 10) * 2.5
                momentum_score = min(max(momentum_score, 0), 100)  # Clamp to 0-100
                
                # 2. Volume trend
                recent_volumes = [day['volume'] for day in data[-20:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                
                older_volumes = [day['volume'] for day in data[-40:-20]]
                older_avg_volume = sum(older_volumes) / len(older_volumes) if older_volumes else avg_volume
                
                volume_trend = (avg_volume / older_avg_volume - 0.8) * 50 if older_avg_volume > 0 else 50
                volume_score = min(max(volume_trend, 0), 100)  # Clamp to 0-100
                
                # 3. Moving average analysis
                prices = [day['close'] for day in data]
                
                # Calculate moving averages
                ma20 = sum(prices[-20:]) / 20
                ma50 = sum(prices[-50:]) / 50
                
                # Score based on price relative to MAs
                ma_score = 0
                if latest_price > ma20 and ma20 > ma50:
                    ma_score = 100  # Strong uptrend
                elif latest_price > ma20:
                    ma_score = 75  # Above short-term MA
                elif latest_price > ma50:
                    ma_score = 50  # Above long-term MA
                elif ma20 > ma50:
                    ma_score = 25  # MAs in positive configuration but price below
                
                # Combined technical score
                technical_score = (
                    momentum_score * 0.4 +
                    volume_score * 0.3 +
                    ma_score * 0.3
                )
                
                return technical_score
            
        except Exception as e:
            self.logger.debug(f"Error in technical analysis for {symbol} in {market} market: {str(e)}")
            return 50  # Return neutral score on error
    
    def _generate_technical_signal(self, symbol: str, technical_score: float, market: str) -> str:
        """
        Generate a technical analysis signal summary for a stock
        
        Args:
            symbol: Stock symbol
            technical_score: Technical score from calculation
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Signal summary text
        """
        # Generate signal based on technical score
        if technical_score >= 75:
            signal = f"Strong technical signals indicate positive momentum for {symbol}. The stock is trading above key moving averages with strong volume support, suggesting continued upward movement."
        elif technical_score >= 60:
            signal = f"{symbol} shows favorable technical indicators with positive price action. The stock is trending above important moving averages, suggesting continued strength."
        elif technical_score >= 50:
            signal = f"{symbol} displays mixed technical signals but maintains a positive bias. While some indicators suggest caution, the overall momentum remains supportive."
        elif technical_score >= 40:
            signal = f"Technical indicators for {symbol} show some caution signals. The stock is experiencing mixed momentum and may consolidate before establishing a clearer direction."
        elif technical_score >= 25:
            signal = f"{symbol} exhibits weakening technical indicators. Price action has been declining, suggesting potential continued weakness in the near term."
        else:
            signal = f"Technical analysis for {symbol} indicates bearish signals. The stock is trading below key moving averages with negative momentum, suggesting continued downward pressure."
        
        # Add market-specific context
        if market == 'us':
            signal += f" Relative to the broader {market.upper()} market, {symbol} is {'outperforming' if technical_score > 60 else 'underperforming' if technical_score < 40 else 'performing in line with'} the S&P 500 index."
        else:  # saudi
            signal += f" Relative to the broader {market.upper()} market, {symbol} is {'outperforming' if technical_score > 60 else 'underperforming' if technical_score < 40 else 'performing in line with'} the TASI index."
        
        return signal
    
    def _construct_portfolio(self, selected_companies: List[Dict], risk_profile: Optional[Dict], 
                            existing_portfolio: Optional[Dict], market: str) -> Dict:
        """
        Construct an optimized portfolio from selected companies based on user's risk profile
        
        Args:
            selected_companies: List of final selected companies
            risk_profile: Optional user risk profile information
            existing_portfolio: Optional existing portfolio to make incremental adjustments
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Portfolio allocation dictionary
        """
        self.logger.info(f"Constructing portfolio from {len(selected_companies)} selected companies")
        
        if not selected_companies:
            return {
                'holdings': [],
                'total_value': 0,
                'positions_count': 0,
                'market': market.upper(),
                'cash_allocation': self.portfolio_params['cash_allocation'],
                'creation_date': datetime.now().isoformat()
            }
        
        # Calculate initial weights based on combined scores
        total_score = sum(company.get('combined_score', 0) for company in selected_companies)
        
        # Initialize holdings with base weights
        holdings = []
        for company in selected_companies:
            symbol = company.get('symbol')
            score = company.get('combined_score', 0)
            
            # Calculate initial weight based on score
            initial_weight = (score / total_score) if total_score > 0 else (1.0 / len(selected_companies))
            
            # Get current price based on market
            try:
                if market == 'us':
                    price = company.get('price', 0)
                    if price <= 0:
                        stock_info = self.stock_analyzer.get_stock_info(symbol)
                        price = stock_info.get('regularMarketPrice', 0) if stock_info else 0
                else:  # saudi
                    info = self.saudi_api.get_symbol_info(symbol)
                    price = info.get('price', 0)
                
                # Add to holdings
                holdings.append({
                    'symbol': symbol,
                    'name': company.get('name', symbol),
                    'sector': company.get('sector', 'Unknown'),
                    'initial_weight': initial_weight,  # Store initial weight for reference
                    'weight': initial_weight,  # This will be adjusted during optimization
                    'price': price,
                    'rotc': company.get('rotc', 0),
                    'revenue_growth': company.get('revenue_growth', 0),
                    'pe_ratio': company.get('pe_ratio', 0),
                    'pb_ratio': company.get('pb_ratio', 0),
                    'dividend_yield': company.get('dividend_yield', 0),
                    'margin_of_safety': company.get('margin_of_safety', 0),
                    'management_quality': company.get('management_quality', {}).get('rating', 'Average'),
                    'fundamental_score': company.get('fundamental_score', 0),
                    'valuation_score': company.get('valuation_score', 0),
                    'technical_score': company.get('technical_score', 0),
                    'combined_score': score,
                    'investment_thesis': company.get('investment_thesis', ''),
                    'market': market.upper()
                })
            except Exception as e:
                self.logger.debug(f"Error adding {symbol} to portfolio: {str(e)}")
        
        # If we're adjusting an existing portfolio, incorporate those positions
        if existing_portfolio and 'holdings' in existing_portfolio:
            holdings = self._adjust_for_existing_portfolio(holdings, existing_portfolio.get('holdings', []))
        
        # Apply portfolio optimization based on risk profile
        if risk_profile:
            holdings = self._optimize_with_risk_profile(holdings, risk_profile, market)
        else:
            # Default optimization to improve diversification
            holdings = self._optimize_default(holdings, market)
        
        # Set aside cash allocation
        cash_allocation = self.portfolio_params['cash_allocation']
        equity_allocation = 1.0 - cash_allocation
        
        # Adjust weights for cash allocation
        for holding in holdings:
            holding['weight'] = holding['weight'] * equity_allocation
        
        # Add cash position
        risk_free_rate = 0.04 if market == 'us' else 0.05  # 4% for US, 5% for Saudi (example values)
        
        cash_position = {
            'symbol': 'CASH',
            'name': 'Cash Reserve',
            'sector': 'Cash',
            'weight': cash_allocation,
            'price': 1.0,
            'yield': risk_free_rate * 100,  # Convert to percentage
            'asset_class': 'Cash',
            'market': market.upper()
        }
        
        # Calculate sector allocations
        sector_allocations = {}
        for holding in holdings:
            sector = holding.get('sector', 'Unknown')
            if sector not in sector_allocations:
                sector_allocations[sector] = 0
            sector_allocations[sector] += holding.get('weight', 0)
        
        # Add cash to sector allocations
        sector_allocations['Cash'] = cash_allocation
        
        # Calculate sample position quantities for a $1 million / 1 million SAR portfolio
        total_value = 1_000_000  # 1 million in local currency
        
        # Calculate position values and quantities
        for holding in holdings:
            price = holding.get('price', 0)
            weight = holding.get('weight', 0)
            
            if price > 0:
                # Calculate position value and quantity
                position_value = total_value * weight
                quantity = int(position_value / price)  # Round down to whole shares
                
                holding.update({
                    'position_value': position_value,
                    'quantity': quantity,
                    'asset_class': 'Equity'  # All stocks are equity
                })
        
        # Add cash position with calculated value
        cash_position['position_value'] = total_value * cash_allocation
        cash_position['quantity'] = cash_position['position_value']  # Cash has 1:1 price-to-quantity
        
        # Add cash to holdings
        holdings.append(cash_position)
        
        # Create portfolio structure
        portfolio = {
            'holdings': holdings,
            'sector_allocations': sector_allocations,
            'total_value': total_value,
            'equity_allocation': equity_allocation,
            'cash_allocation': cash_allocation,
            'positions_count': len(holdings) - 1,  # Not counting cash
            'creation_date': datetime.now().isoformat(),
            'market': market.upper(),
            'model': 'Naif Al-Rasheed Investment Model',
            'min_stocks': self.portfolio_params['min_stocks'],
            'max_stocks': self.portfolio_params['max_stocks'],
            'min_sectors': self.portfolio_params['min_sectors']
        }
        
        return portfolio
    
    def _adjust_for_existing_portfolio(self, new_holdings: List[Dict], existing_holdings: List[Dict]) -> List[Dict]:
        """
        Adjust new portfolio to minimize changes from existing holdings
        
        Args:
            new_holdings: New portfolio holdings
            existing_holdings: Current portfolio holdings
            
        Returns:
            Adjusted holdings list
        """
        self.logger.info("Adjusting for existing portfolio to minimize changes")
        
        # Create dictionaries for fast lookup
        new_holdings_dict = {h['symbol']: h for h in new_holdings}
        existing_holdings_dict = {h['symbol']: h for h in existing_holdings}
        
        # Identify common holdings between existing and new portfolios
        common_symbols = set(new_holdings_dict.keys()).intersection(set(existing_holdings_dict.keys()))
        
        # For common holdings, adjust weights to transition gradually (70% existing, 30% new)
        for symbol in common_symbols:
            existing_weight = existing_holdings_dict[symbol].get('weight', 0)
            new_weight = new_holdings_dict[symbol].get('weight', 0)
            
            # Blend weights (70% existing, 30% new)
            adjusted_weight = existing_weight * 0.7 + new_weight * 0.3
            
            # Update weight in new holdings
            new_holdings_dict[symbol]['weight'] = adjusted_weight
            new_holdings_dict[symbol]['adjusted_from_existing'] = True
            new_holdings_dict[symbol]['previous_weight'] = existing_weight
        
        # For existing holdings not in new portfolio, consider keeping at reduced weight
        for symbol, holding in existing_holdings_dict.items():
            if symbol not in new_holdings_dict and holding.get('weight', 0) >= 0.03:
                # Keep at 50% of original weight if it's significant
                reduced_holding = holding.copy()
                reduced_holding['weight'] = holding.get('weight', 0) * 0.5
                reduced_holding['phasing_out'] = True
                reduced_holding['initial_weight'] = 0  # Not in new portfolio
                
                # Add to new holdings
                new_holdings.append(reduced_holding)
        
        # Normalize weights to ensure they sum to 1.0
        total_weight = sum(h.get('weight', 0) for h in new_holdings)
        
        if total_weight > 0:
            for holding in new_holdings:
                holding['weight'] = holding.get('weight', 0) / total_weight
        
        return new_holdings
    
    def _optimize_with_risk_profile(self, holdings: List[Dict], risk_profile: Dict, market: str) -> List[Dict]:
        """
        Optimize portfolio weights based on user's risk profile
        
        Args:
            holdings: Initial portfolio holdings
            risk_profile: User risk profile information
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Optimized holdings list
        """
        self.logger.info("Optimizing portfolio based on user risk profile")
        
        # Extract risk tolerance from profile (0-100 scale)
        risk_tolerance = risk_profile.get('risk_scores', {}).get('risk_tolerance', 50)
        
        # Convert to risk profile category
        if risk_tolerance >= 70:
            risk_category = 'aggressive'
        elif risk_tolerance >= 40:
            risk_category = 'moderate'
        else:
            risk_category = 'conservative'
            
        self.logger.info(f"User risk profile: {risk_category.upper()} (score: {risk_tolerance})")
        
        # Adjust sector allocation targets based on risk profile
        sector_targets = {}
        
        if risk_category == 'conservative':
            # Conservative profile: Focus on defensive sectors
            sector_targets = {
                'Consumer Staples': (0.15, 0.25),  # (min, max) allocation
                'Utilities': (0.10, 0.20),
                'Healthcare': (0.15, 0.25),
                'Telecommunications': (0.05, 0.15),
                'Financials': (0.05, 0.15),
                # Limit higher-risk sectors
                'Technology': (0.0, 0.10),
                'Consumer Discretionary': (0.0, 0.10),
                'Industrials': (0.0, 0.10),
                'Materials': (0.0, 0.05),
                'Energy': (0.0, 0.05)
            }
            
            # Saudi market specifics
            if market == 'saudi':
                sector_targets = {
                    'Banking': (0.15, 0.25),
                    'Food & Agriculture': (0.10, 0.20),
                    'Telecommunications': (0.10, 0.20),
                    'Utilities': (0.10, 0.20),
                    'Insurance': (0.05, 0.15),
                    # Limit higher-risk sectors
                    'Petrochemicals': (0.0, 0.10),
                    'Real Estate': (0.0, 0.10),
                    'Retail': (0.0, 0.10)
                }
        
        elif risk_category == 'moderate':
            # Moderate profile: Balanced allocation
            sector_targets = {
                'Technology': (0.10, 0.20),
                'Healthcare': (0.10, 0.20),
                'Financials': (0.10, 0.20),
                'Consumer Staples': (0.05, 0.15),
                'Consumer Discretionary': (0.05, 0.15),
                'Industrials': (0.05, 0.15),
                'Utilities': (0.05, 0.10),
                'Materials': (0.0, 0.10),
                'Energy': (0.0, 0.10),
                'Telecommunications': (0.0, 0.10)
            }
            
            # Saudi market specifics
            if market == 'saudi':
                sector_targets = {
                    'Banking': (0.10, 0.20),
                    'Petrochemicals': (0.10, 0.20),
                    'Telecommunications': (0.05, 0.15),
                    'Retail': (0.05, 0.15),
                    'Food & Agriculture': (0.05, 0.15),
                    'Insurance': (0.05, 0.15),
                    'Real Estate': (0.05, 0.15),
                    'Utilities': (0.0, 0.10)
                }
        
        else:  # aggressive
            # Aggressive profile: Focus on growth sectors
            sector_targets = {
                'Technology': (0.15, 0.30),
                'Consumer Discretionary': (0.10, 0.20),
                'Communication Services': (0.10, 0.20),
                'Industrials': (0.05, 0.15),
                'Healthcare': (0.05, 0.15),
                'Financials': (0.05, 0.15),
                'Energy': (0.0, 0.10),
                'Materials': (0.0, 0.10),
                'Consumer Staples': (0.0, 0.10),
                'Utilities': (0.0, 0.05)
            }
            
            # Saudi market specifics
            if market == 'saudi':
                sector_targets = {
                    'Petrochemicals': (0.15, 0.30),
                    'Banking': (0.10, 0.20),
                    'Real Estate': (0.10, 0.20),
                    'Retail': (0.10, 0.20),
                    'Insurance': (0.05, 0.15),
                    'Telecommunications': (0.0, 0.10),
                    'Food & Agriculture': (0.0, 0.10),
                    'Utilities': (0.0, 0.05)
                }
        
        # Apply sector targets to adjust weights
        return self._optimize_sector_weights(holdings, sector_targets)
    
    def _optimize_default(self, holdings: List[Dict], market: str) -> List[Dict]:
        """
        Apply default portfolio optimization (balanced approach)
        
        Args:
            holdings: Initial portfolio holdings
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Optimized holdings list
        """
        self.logger.info("Applying default portfolio optimization")
        
        # Default sector targets (balanced)
        sector_targets = {}
        
        if market == 'us':
            sector_targets = {
                'Technology': (0.10, 0.20),
                'Healthcare': (0.10, 0.20),
                'Financials': (0.10, 0.20),
                'Consumer Discretionary': (0.05, 0.15),
                'Consumer Staples': (0.05, 0.15),
                'Industrials': (0.05, 0.15),
                'Communication Services': (0.05, 0.15),
                'Utilities': (0.0, 0.10),
                'Materials': (0.0, 0.10),
                'Energy': (0.0, 0.10),
                'Real Estate': (0.0, 0.10)
            }
        else:  # saudi
            sector_targets = {
                'Banking': (0.10, 0.20),
                'Petrochemicals': (0.10, 0.20),
                'Telecommunications': (0.05, 0.15),
                'Retail': (0.05, 0.15),
                'Food & Agriculture': (0.05, 0.15),
                'Insurance': (0.05, 0.15),
                'Real Estate': (0.05, 0.15),
                'Utilities': (0.0, 0.10)
            }
        
        # Apply sector targets for balanced diversification
        return self._optimize_sector_weights(holdings, sector_targets)
    
    def _optimize_sector_weights(self, holdings: List[Dict], sector_targets: Dict) -> List[Dict]:
        """
        Optimize portfolio weights based on sector targets and holding quality
        
        Args:
            holdings: Initial portfolio holdings
            sector_targets: Target allocation ranges for each sector
            
        Returns:
            Optimized holdings list
        """
        # Group holdings by sector
        sectors = {}
        for holding in holdings:
            sector = holding.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(holding)
        
        # Sort holdings within each sector by combined score
        for sector, sector_holdings in sectors.items():
            sectors[sector] = sorted(sector_holdings, key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Calculate target sector weights based on sector_targets
        sector_weights = {}
        for sector in sectors:
            # Use target if available, otherwise use flexible approach
            if sector in sector_targets:
                min_weight, max_weight = sector_targets[sector]
                # Set initial target at midpoint of range
                sector_weights[sector] = (min_weight + max_weight) / 2
            else:
                # For sectors not in targets, set modest default
                sector_weights[sector] = 0.05
        
        # Normalize sector weights to sum to 1.0
        total_sector_weight = sum(sector_weights.values())
        for sector in sector_weights:
            sector_weights[sector] = sector_weights[sector] / total_sector_weight
        
        # Distribute sector weights among holdings within each sector
        optimized_holdings = []
        for sector, sector_holdings in sectors.items():
            sector_weight = sector_weights.get(sector, 0)
            sector_total_score = sum(h.get('combined_score', 0) for h in sector_holdings)
            
            # Distribute sector weight proportionally to combined scores
            for holding in sector_holdings:
                score = holding.get('combined_score', 0)
                if sector_total_score > 0:
                    holding_weight = sector_weight * (score / sector_total_score)
                else:
                    holding_weight = sector_weight / len(sector_holdings)
                
                # Update holding weight
                holding['weight'] = holding_weight
                optimized_holdings.append(holding)
        
        # Ensure weights sum to 1.0 (accounting for floating point precision)
        total_weight = sum(h.get('weight', 0) for h in optimized_holdings)
        if total_weight > 0:
            adjustment_factor = 1.0 / total_weight
            for holding in optimized_holdings:
                holding['weight'] = holding['weight'] * adjustment_factor
        
        return optimized_holdings
    
    def _run_monte_carlo_simulation(self, portfolio: Dict, market: str) -> Dict:
        """
        Run Monte Carlo simulation to assess portfolio risk and return
        
        Args:
            portfolio: Constructed portfolio
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Simulation results
        """
        self.logger.info("Running Monte Carlo simulation for portfolio risk analysis")
        
        try:
            # Extract portfolio holdings (excluding cash)
            holdings = [h for h in portfolio.get('holdings', []) if h.get('asset_class', '') == 'Equity']
            
            if not holdings:
                return {
                    'success': False,
                    'message': "No equity holdings to simulate"
                }
            
            # Extract symbols and weights
            symbols = [h.get('symbol', '') for h in holdings]
            weights = [h.get('weight', 0) / (1 - portfolio.get('cash_allocation', 0)) for h in holdings]
            
            # Get historical price data
            historical_prices = {}
            returns_data = {}
            
            # Different approach based on market
            if market == 'us':
                # Get 3 years of monthly returns for US stocks
                for symbol in symbols:
                    hist_data = self.stock_analyzer.get_historical_prices(symbol, days=1095)  # ~3 years
                    
                    if hist_data is not None and not hist_data.empty:
                        monthly_prices = hist_data['Close'].resample('M').last()
                        monthly_returns = monthly_prices.pct_change().dropna()
                        returns_data[symbol] = monthly_returns.values
            
            else:  # Saudi market
                # Get historical data for Saudi stocks
                for symbol in symbols:
                    historical = self.saudi_api.get_historical_data(symbol, period='1y')
                    
                    if historical and 'data' in historical:
                        # Extract prices and dates
                        prices = [d['close'] for d in historical['data']]
                        dates = [d['date'] for d in historical['data']]
                        
                        # Convert to returns
                        returns = []
                        for i in range(1, len(prices)):
                            if prices[i-1] > 0:
                                ret = (prices[i] / prices[i-1]) - 1
                                returns.append(ret)
                        
                        if returns:
                            returns_data[symbol] = np.array(returns)
            
            # Check if we have sufficient data
            if len(returns_data) < len(symbols) * 0.5:
                # Not enough historical data, use synthetic data with brownian motion
                self.logger.warning("Insufficient historical data, using synthetic data with Brownian motion")
                
                # Parameters for synthetic data
                if market == 'us':
                    mean_return = 0.007  # ~8.7% annual return
                    volatility = 0.045   # ~15.6% annual volatility
                else:  # Saudi
                    mean_return = 0.006  # ~7.4% annual return
                    volatility = 0.055   # ~19% annual volatility
                
                # Generate synthetic returns for all symbols
                returns_data = {}
                for symbol in symbols:
                    # Generate 36 months of returns (3 years)
                    synthetic_returns = np.random.normal(mean_return, volatility, 36)
                    returns_data[symbol] = synthetic_returns
            
            # Convert returns to DataFrame for correlation analysis
            returns_df = pd.DataFrame(returns_data)
            
            # If still missing data, fill with market average plus random variation
            if returns_df.shape[1] < len(symbols):
                self.logger.warning(f"Some symbols missing data, filling with estimated returns")
                
                # Calculate average returns across available symbols
                available_returns = np.mean(returns_df.values, axis=1)
                
                # Fill missing symbols with average plus random variation
                for symbol in symbols:
                    if symbol not in returns_df.columns:
                        # Add random variation to average returns
                        variation = np.random.normal(0, 0.02, size=len(available_returns))
                        synthetic_returns = available_returns + variation
                        returns_df[symbol] = synthetic_returns
            
            # Calculate mean returns and covariance matrix
            mean_returns = returns_df.mean().values
            cov_matrix = returns_df.cov().values
            
            # Monte Carlo simulation parameters
            num_simulations = self.portfolio_params['simulation_runs']
            time_horizon = self.portfolio_params['time_horizon']
            num_periods = time_horizon * 12  # Monthly periods
            
            # Create initial investment array (all starting at 1.0)
            initial_investment = np.ones(num_simulations)
            
            # Calculate portfolio expected return and volatility
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            # Generate correlated random returns for each period
            all_simulations = []
            
            # Run simulations
            for i in range(num_simulations):
                # Initialize cumulative return
                cumulative_return = initial_investment[i]
                simulation_path = [cumulative_return]
                
                for j in range(num_periods):
                    # Generate random return from normal distribution with portfolio mean and volatility
                    period_return = np.random.normal(portfolio_return, portfolio_volatility)
                    
                    # Update cumulative return
                    cumulative_return = cumulative_return * (1 + period_return)
                    simulation_path.append(cumulative_return)
                
                all_simulations.append(simulation_path)
            
            # Convert to numpy array for easier analysis
            all_simulations = np.array(all_simulations)
            
            # Calculate final values for each simulation
            final_values = all_simulations[:, -1]
            
            # Calculate percentiles
            percentiles = {
                '5%': np.percentile(final_values, 5),
                '25%': np.percentile(final_values, 25),
                '50%': np.percentile(final_values, 50),  # Median
                '75%': np.percentile(final_values, 75),
                '95%': np.percentile(final_values, 95)
            }
            
            # Calculate other statistics
            mean_final_value = np.mean(final_values)
            median_final_value = np.median(final_values)
            min_final_value = np.min(final_values)
            max_final_value = np.max(final_values)
            
            # Calculate probability of loss
            loss_probability = np.mean(final_values < 1.0) * 100
            
            # Calculate expected annual return
            expected_annual_return = (mean_final_value ** (1/time_horizon) - 1) * 100
            
            # Calculate value at risk (VaR) at 95% confidence
            var_95 = (1 - np.percentile(final_values, 5)) * 100
            
            # Add cash effect to final results 
            cash_allocation = portfolio.get('cash_allocation', 0)
            risk_free_rate = 0.04 if market == 'us' else 0.05  # 4% for US, 5% for Saudi
            
            # Adjust expected return for cash allocation
            adjusted_return = expected_annual_return * (1 - cash_allocation) + (risk_free_rate * 100 * cash_allocation)
            
            # Adjust risk (VaR) for cash allocation
            adjusted_var = var_95 * (1 - cash_allocation)
            
            # Create simulation results
            simulation_results = {
                'success': True,
                'market': market.upper(),
                'time_horizon_years': time_horizon,
                'num_simulations': num_simulations,
                'expected_annual_return': expected_annual_return,
                'adjusted_annual_return': adjusted_return,
                'portfolio_volatility': portfolio_volatility * np.sqrt(12) * 100,  # Annualized
                'value_at_risk_95': var_95,
                'adjusted_var_95': adjusted_var,
                'loss_probability': loss_probability,
                'final_value_statistics': {
                    'mean': mean_final_value,
                    'median': median_final_value,
                    'min': min_final_value,
                    'max': max_final_value
                },
                'percentiles': percentiles,
                'simulation_summary': {
                    'starting_value': 1.0,
                    'mean_ending_value': mean_final_value,
                    'worst_case': percentiles['5%'],
                    'best_case': percentiles['95%']
                }
            }
            
            return simulation_results
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo simulation: {str(e)}")
            return {
                'success': False,
                'message': f"Simulation failed: {str(e)}"
            }
    
    def _generate_visualizations(self, portfolio: Dict, simulation_results: Dict, market: str) -> Dict:
        """
        Generate visualization data for portfolio and simulation results
        
        Args:
            portfolio: The constructed portfolio
            simulation_results: Results from Monte Carlo simulation
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Dict with visualization data encoded as base64 strings
        """
        self.logger.info("Generating portfolio visualizations")
        
        visualizations = {}
        
        try:
            # 1. Sector Allocation Pie Chart
            sector_allocations = portfolio.get('sector_allocations', {})
            if sector_allocations:
                fig, ax = plt.subplots(figsize=(10, 7))
                
                # Sort sectors by allocation (descending)
                sorted_sectors = sorted(sector_allocations.items(), key=lambda x: x[1], reverse=True)
                labels = [f"{s[0]} ({s[1]*100:.1f}%)" for s in sorted_sectors]
                sizes = [s[1] for s in sorted_sectors]
                
                # Use a colorful palette
                colors = plt.cm.tab20(np.arange(len(labels)))
                
                # Plot pie chart with shadow
                wedges, texts, autotexts = ax.pie(
                    sizes, 
                    labels=None,  # We'll add a legend instead
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=True
                )
                
                # Customize text properties
                plt.setp(autotexts, weight="bold", size=10)
                
                # Add legend
                ax.legend(
                    wedges, 
                    labels,
                    title="Sectors",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1)
                )
                
                plt.axis('equal')
                plt.title(f'Portfolio Sector Allocation - {market.upper()} Market', fontsize=14, fontweight='bold')
                
                # Save to buffer
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64 for embedding in HTML
                sector_pie_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                visualizations['sector_allocation_pie'] = sector_pie_b64
                plt.close(fig)
                
            # 2. Top Holdings Bar Chart
            holdings = portfolio.get('holdings', [])
            equity_holdings = [h for h in holdings if h.get('asset_class', '') == 'Equity']
            
            if equity_holdings:
                # Sort holdings by weight (descending)
                sorted_holdings = sorted(equity_holdings, key=lambda x: x.get('weight', 0), reverse=True)
                
                # Select top 10 holdings
                top_holdings = sorted_holdings[:10]
                
                # Create bar chart
                fig, ax = plt.subplots(figsize=(10, 7))
                
                symbols = [h.get('symbol', '') for h in top_holdings]
                weights = [h.get('weight', 0) * 100 for h in top_holdings]  # Convert to percentage
                
                # Use colorful bars
                bars = ax.bar(symbols, weights, color=plt.cm.tab10(np.arange(len(symbols))))
                
                # Add data labels
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                # Customize appearance
                ax.set_ylabel('Allocation (%)')
                ax.set_title(f'Top 10 Holdings - {market.upper()} Portfolio', fontsize=14, fontweight='bold')
                ax.set_ylim(0, max(weights) * 1.15)  # Add some space for labels
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                # Save to buffer
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64
                holdings_bar_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                visualizations['top_holdings_bar'] = holdings_bar_b64
                plt.close(fig)
                
            # 3. Monte Carlo Simulation Paths
            if simulation_results.get('success', False):
                # We need to re-run a smaller version of the simulation to plot the paths
                # (not ideal, but we didn't store the paths in the simulation results)
                
                # Extract portfolio data
                equity_holdings = [h for h in portfolio.get('holdings', []) if h.get('asset_class', '') == 'Equity']
                symbols = [h.get('symbol', '') for h in equity_holdings]
                weights = [h.get('weight', 0) / (1 - portfolio.get('cash_allocation', 0)) for h in equity_holdings]
                
                # Use simulation parameters
                portfolio_return = simulation_results.get('expected_annual_return', 8) / 100 / 12  # Monthly return
                portfolio_volatility = simulation_results.get('portfolio_volatility', 15) / 100 / np.sqrt(12)  # Monthly volatility
                
                # Generate a smaller set of simulation paths for visualization
                num_paths = 100  # Use fewer paths for visualization
                time_horizon = simulation_results.get('time_horizon_years', 5)
                num_periods = time_horizon * 12
                
                # Create time points (months)
                time_points = np.arange(0, num_periods + 1)
                
                # Run simulations
                all_simulations = []
                for i in range(num_paths):
                    # Initialize cumulative return
                    cumulative_return = 1.0
                    simulation_path = [cumulative_return]
                    
                    for j in range(num_periods):
                        # Generate random return
                        period_return = np.random.normal(portfolio_return, portfolio_volatility)
                        
                        # Update cumulative return
                        cumulative_return = cumulative_return * (1 + period_return)
                        simulation_path.append(cumulative_return)
                    
                    all_simulations.append(simulation_path)
                
                # Convert to numpy array
                all_simulations = np.array(all_simulations)
                
                # Plot simulation paths
                fig, ax = plt.subplots(figsize=(10, 7))
                
                # Plot all simulation paths with transparency
                for i in range(len(all_simulations)):
                    ax.plot(time_points, all_simulations[i], 'b-', alpha=0.1)
                
                # Plot percentile lines
                percentiles = [5, 25, 50, 75, 95]
                colors = ['red', 'orange', 'green', 'orange', 'red']
                
                for p, color in zip(percentiles, colors):
                    percentile_values = [np.percentile(all_simulations[:, j], p) for j in range(num_periods + 1)]
                    ax.plot(time_points, percentile_values, color=color, linewidth=2, 
                          label=f'{p}th Percentile')
                
                # Add annotations for final percentiles
                for p, color in zip(percentiles, colors):
                    final_percentile = np.percentile(all_simulations[:, -1], p)
                    ax.annotate(f'{p}th: ${final_percentile:.2f}',
                               xy=(num_periods, final_percentile),
                               xytext=(5, 0),
                               textcoords="offset points",
                               ha='left', va='center',
                               color=color, fontweight='bold')
                
                # Customize plot
                ax.set_xlabel('Months')
                ax.set_ylabel('Portfolio Value (Initial = $1.00)')
                ax.set_title(f'Monte Carlo Simulation - {time_horizon} Year Projection', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Add a legend
                ax.legend(loc='upper left')
                
                # Save to buffer
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64
                simulation_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                visualizations['monte_carlo_simulation'] = simulation_b64
                plt.close(fig)
                
            # 4. Risk-Return Scatter Plot (if we had sufficient data)
            if len(equity_holdings) >= 5:
                fig, ax = plt.subplots(figsize=(10, 7))
                
                # Extract expected returns and risk data
                returns = [h.get('expected_return', h.get('dividend_yield', 0) / 100 + 0.05) for h in equity_holdings]
                risks = [h.get('risk', (h.get('combined_score', 50) / 50) * 0.15) for h in equity_holdings]
                symbols = [h.get('symbol', '') for h in equity_holdings]
                
                # Create scatter plot
                scatter = ax.scatter(risks, returns, s=100, c=range(len(equity_holdings)), cmap='viridis', alpha=0.7)
                
                # Add labels to points
                for i, symbol in enumerate(symbols):
                    ax.annotate(symbol,
                               (risks[i], returns[i]),
                               xytext=(5, 5),
                               textcoords="offset points")
                
                # Add portfolio point (larger)
                portfolio_return = simulation_results.get('expected_annual_return', 8) / 100
                portfolio_risk = simulation_results.get('portfolio_volatility', 15) / 100
                
                ax.scatter(portfolio_risk, portfolio_return, s=300, c='red', 
                         marker='*', label='Portfolio')
                
                ax.annotate('Portfolio',
                          (portfolio_risk, portfolio_return),
                          xytext=(10, 10),
                          textcoords="offset points",
                          fontweight='bold')
                
                # Customize plot
                ax.set_xlabel('Risk (Annualized Volatility)')
                ax.set_ylabel('Expected Annual Return')
                ax.set_title('Risk-Return Profile', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Format axes as percentages
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
                
                # Save to buffer
                buffer = BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                
                # Convert to base64
                risk_return_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                visualizations['risk_return_scatter'] = risk_return_b64
                plt.close(fig)
                
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {str(e)}")
            return {
                'error': f"Visualization generation failed: {str(e)}"
            }
    
    def _generate_recommendations(self, portfolio: Dict, simulation_results: Dict, market: str) -> Dict:
        """
        Generate investment recommendations based on portfolio and simulation results
        
        Args:
            portfolio: The constructed portfolio
            simulation_results: Results from Monte Carlo simulation
            market: Market being analyzed ('us' or 'saudi')
            
        Returns:
            Dict with recommendations and explanations
        """
        self.logger.info("Generating investment recommendations")
        
        try:
            # Extract key metrics
            holdings = portfolio.get('holdings', [])
            equity_holdings = [h for h in holdings if h.get('asset_class', '') == 'Equity']
            
            # Sort holdings by combined score (descending)
            sorted_holdings = sorted(equity_holdings, key=lambda x: x.get('combined_score', 0), reverse=True)
            
            # Get top 5 holdings
            top_holdings = sorted_holdings[:5]
            
            # Get simulation metrics
            expected_return = simulation_results.get('adjusted_annual_return', 0)
            risk = simulation_results.get('adjusted_var_95', 0)
            loss_probability = simulation_results.get('loss_probability', 0)
            
            # Prepare explanations
            explanations = []
            
            # Overall strategy explanation
            strategy_explanation = (
                f"Based on the Naif Al-Rasheed investment philosophy, this portfolio focuses on "
                f"companies with high return on tangible capital (ROTC > 15%), strong revenue growth, "
                f"and positive cash flow generation. The portfolio is diversified across {len(set(h.get('sector', '') for h in equity_holdings))} "
                f"sectors to reduce non-systematic risk. A {portfolio.get('cash_allocation', 0)*100:.1f}% cash allocation "
                f"provides liquidity and reduces overall portfolio volatility."
            )
            
            # Performance expectations
            performance_explanation = (
                f"The portfolio has an expected annual return of {expected_return:.1f}% with a "
                f"95% Value-at-Risk (VaR) of {risk:.1f}%. This means there is a 95% probability "
                f"that the portfolio will not lose more than {risk:.1f}% of its value in a given year. "
                f"The probability of any loss over the {simulation_results.get('time_horizon_years', 5)}-year "
                f"investment horizon is {loss_probability:.1f}%."
            )
            
            # Top holdings explanation
            top_holdings_explanation = "The top holdings in the portfolio include:"
            
            for i, holding in enumerate(top_holdings, 1):
                symbol = holding.get('symbol', '')
                name = holding.get('name', symbol)
                weight = holding.get('weight', 0) * 100
                sector = holding.get('sector', 'Unknown')
                rotc = holding.get('rotc', 0)
                growth = holding.get('revenue_growth', 0)
                
                holding_text = (
                    f"{i}. {name} ({symbol}, {sector}): {weight:.1f}% allocation. "
                    f"This company shows {rotc:.1f}% ROTC and {growth:.1f}% revenue growth. "
                )
                
                # Add special comments for top companies
                if i <= 3:
                    thesis = holding.get('investment_thesis', '').split('. ')[1:3]
                    if thesis:
                        holding_text += " ".join(thesis)
                
                top_holdings_explanation += "\n" + holding_text
            
            # Investment horizon recommendation
            horizon_recommendation = (
                f"Based on the Monte Carlo simulation, this portfolio is designed for a {simulation_results.get('time_horizon_years', 5)}-year "
                f"investment horizon. While shorter-term volatility may occur, the portfolio has a "
                f"{100-loss_probability:.1f}% probability of positive returns over the full investment period."
            )
            
            # Market-specific recommendations
            market_specific = ""
            if market == 'us':
                market_specific = (
                    f"This US-focused portfolio is benchmarked against the S&P 500 index. "
                    f"The portfolio emphasizes companies with sustainable competitive advantages "
                    f"and strong management quality, which are key factors in the Naif Al-Rasheed "
                    f"investment approach."
                )
            else:  # saudi
                market_specific = (
                    f"This Saudi market portfolio is benchmarked against the TASI index. "
                    f"The portfolio takes into account specific characteristics of the Saudi market, "
                    f"including Vision 2030 initiatives and economic diversification efforts. "
                    f"Companies with strong governance and resilience to oil price fluctuations "
                    f"are prioritized."
                )
            
            # Consolidate explanations
            explanations = [
                strategy_explanation,
                performance_explanation,
                top_holdings_explanation,
                horizon_recommendation,
                market_specific
            ]
            
            # Generate recommendations
            recommendations = {
                'strategy': strategy_explanation,
                'performance_expectations': performance_explanation,
                'top_holdings': top_holdings_explanation,
                'investment_horizon': horizon_recommendation,
                'market_specific': market_specific,
                'summary': "\n\n".join(explanations)
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return {
                'error': f"Recommendation generation failed: {str(e)}",
                'summary': "Unable to generate detailed recommendations. Please review the portfolio data directly."
            }