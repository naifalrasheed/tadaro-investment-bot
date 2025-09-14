#!/usr/bin/env python
"""
Test script for Naif Al-Rasheed Investment Model Performance Limits

This script tests the Naif Al-Rasheed investment model with both testing performance limits
and production settings, comparing results and execution time.
"""

import sys
import time
import os
from datetime import datetime
import logging

# Set up path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the model
from ml_components.naif_alrasheed_model import NaifAlRasheedModel

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_naif_model_performance(market='us'):
    """Test Naif Al-Rasheed model with different performance settings"""
    
    logger.info(f"=== Starting Naif Al-Rasheed Model Performance Test for {market.upper()} market ===")
    
    # 1. Test with default testing limits
    logger.info("Running test with DEFAULT TEST LIMITS:")
    test_model = NaifAlRasheedModel()
    
    # Log current settings
    logger.info(f"- Max companies per sector: 40 (test limit)")
    logger.info(f"- Monte Carlo simulations: {test_model.portfolio_params['simulation_runs']} (test limit)")
    
    # Track execution time
    start_time = time.time()
    
    # Run full screening with default test settings
    test_results = test_model.run_full_screening(market=market)
    
    test_execution_time = time.time() - start_time
    logger.info(f"Test run completed in {test_execution_time:.2f} seconds")
    
    # 2. Test with production settings
    logger.info("\nRunning test with PRODUCTION SETTINGS:")
    prod_model = NaifAlRasheedModel()
    
    # Update to production settings
    prod_model.portfolio_params['simulation_runs'] = 10000  # 10,000 runs for production
    logger.info(f"- Max companies per sector: 0 (unlimited)")
    logger.info(f"- Monte Carlo simulations: {prod_model.portfolio_params['simulation_runs']} (production setting)")
    
    # Track execution time
    start_time = time.time()
    
    # Run with production settings (no company limit)
    production_results = prod_model.run_full_screening(
        market=market, 
        custom_params={
            'max_companies_per_sector': 0  # No limit
        }
    )
    
    prod_execution_time = time.time() - start_time
    logger.info(f"Production run completed in {prod_execution_time:.2f} seconds")
    
    # 3. Compare results
    logger.info("\n=== PERFORMANCE COMPARISON ===")
    
    # Compare execution time
    time_difference = prod_execution_time - test_execution_time
    time_ratio = prod_execution_time / test_execution_time if test_execution_time > 0 else float('inf')
    logger.info(f"Execution time: Test={test_execution_time:.2f}s vs Production={prod_execution_time:.2f}s")
    logger.info(f"Production took {time_difference:.2f}s longer ({time_ratio:.2f}x slower)")
    
    # Compare number of companies analyzed
    test_companies = len(test_results.get('screened_companies', []))
    prod_companies = len(production_results.get('screened_companies', []))
    logger.info(f"Companies analyzed: Test={test_companies} vs Production={prod_companies}")
    
    # Compare portfolio metrics
    if test_results.get('success') and production_results.get('success'):
        test_return = test_results.get('simulation_results', {}).get('expected_annual_return', 0)
        prod_return = production_results.get('simulation_results', {}).get('expected_annual_return', 0)
        
        test_risk = test_results.get('simulation_results', {}).get('value_at_risk_95', 0)
        prod_risk = production_results.get('simulation_results', {}).get('value_at_risk_95', 0)
        
        logger.info(f"Expected return: Test={test_return:.2f}% vs Production={prod_return:.2f}%")
        logger.info(f"Risk (VaR 95%): Test={test_risk:.2f}% vs Production={prod_risk:.2f}%")
        logger.info(f"Return difference: {abs(prod_return - test_return):.2f}% points")
        logger.info(f"Risk difference: {abs(prod_risk - test_risk):.2f}% points")
    
    # Provide recommendation based on results
    logger.info("\n=== RECOMMENDATION ===")
    if time_ratio > 3:
        logger.info("The production settings are significantly slower than test settings.")
        logger.info("For development and testing, continue using the test limits.")
        logger.info("For production use, ensure server capacity is adequate for the increased computational load.")
    else:
        logger.info("Performance difference is acceptable. Production settings can be used if needed.")
    
    # Return both results for further analysis if needed
    return {
        'test_results': test_results,
        'production_results': production_results,
        'test_execution_time': test_execution_time,
        'production_execution_time': prod_execution_time
    }

if __name__ == "__main__":
    # Get market from command line argument or use default
    market = sys.argv[1] if len(sys.argv) > 1 else 'us'
    result = test_naif_model_performance(market=market)
    
    # Save results summary to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"naif_model_performance_test_{market}_{timestamp}.log", "w") as f:
        f.write(f"=== Naif Al-Rasheed Model Performance Test Results ({market.upper()}) ===\n")
        f.write(f"Test execution time: {result['test_execution_time']:.2f} seconds\n")
        f.write(f"Production execution time: {result['production_execution_time']:.2f} seconds\n")
        
        if result['test_results'].get('success') and result['production_results'].get('success'):
            test_return = result['test_results'].get('simulation_results', {}).get('expected_annual_return', 0)
            prod_return = result['production_results'].get('simulation_results', {}).get('expected_annual_return', 0)
            
            test_risk = result['test_results'].get('simulation_results', {}).get('value_at_risk_95', 0)
            prod_risk = result['production_results'].get('simulation_results', {}).get('value_at_risk_95', 0)
            
            f.write(f"Expected return: Test={test_return:.2f}% vs Production={prod_return:.2f}%\n")
            f.write(f"Risk (VaR 95%): Test={test_risk:.2f}% vs Production={prod_risk:.2f}%\n")
            
            # Calculate difference in portfolio composition
            test_companies = set(result['test_results'].get('selected_companies', []))
            prod_companies = set(result['production_results'].get('selected_companies', []))
            
            common = test_companies.intersection(prod_companies)
            only_test = test_companies - prod_companies
            only_prod = prod_companies - test_companies
            
            f.write(f"\nPortfolio Composition Comparison:\n")
            f.write(f"Common companies: {len(common)}\n")
            f.write(f"Only in test portfolio: {len(only_test)}\n")
            f.write(f"Only in production portfolio: {len(only_prod)}\n")