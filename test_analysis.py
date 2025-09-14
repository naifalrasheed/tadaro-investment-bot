from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def format_metrics(value, is_percentage=False, decimals=2):
    """Format numerical output with better validation"""
    try:
        if value is None or pd.isna(value):
            return "N/A"
            
        if isinstance(value, (int, float, np.number)):
            # Handle price formatting
            if value >= 100 and not is_percentage:
                return f"${value:,.2f}"
            # Handle percentage formatting
            elif is_percentage:
                return f"{value:.2f}%"
            # Handle other numerical values
            else:
                return f"{value:.2f}"
        return str(value)
    except:
        return "N/A"

def get_fundamental_metrics(results):
    """Extract and format fundamental metrics"""
    fund = results['fundamental_analysis']
    metrics = []
    
    if results['company_type'] == 'value':
        rotc_data = fund.get('rotc_data', {})
        if rotc_data:
            metrics.extend([
                ("Current ROTC", rotc_data.get('latest_rotc')),
                ("4Q Average ROTC", rotc_data.get('avg_rotc')),
                ("ROTC Trend", "Improving" if rotc_data.get('improving') else "Declining"),
            ])
    else:
        growth_data = fund.get('growth_data', {})
        if growth_data:
            metrics.extend([
                ("Revenue Growth", growth_data.get('avg_revenue_growth')),
                ("Cash Flow Status", "Positive" if growth_data.get('cash_flow_positive') else "Negative"),
                ("Growth Trend", "Accelerating" if growth_data.get('revenue_growth_trend', 0) > 0 else "Decelerating")
            ])
    
    metrics.append(("Fundamental Score", fund.get('score')))
    return metrics

def get_technical_metrics(results):
    """Extract and format technical metrics"""
    tech = results.get('technical_analysis', {})
    price_metrics = tech.get('price_metrics', {})
    
    return [
        ("Current Price", price_metrics.get('current_price')),
        ("Predicted Price", price_metrics.get('predicted_price')),
        ("Expected Return", tech.get('ml_prediction')),
        ("Model Confidence", tech.get('confidence')),
        ("Technical Score", tech.get('technical_score'))
    ]

def get_risk_metrics(results):
    """Extract and format risk metrics"""
    risk = results.get('risk_metrics', {})
    
    return [
        ("Annual Volatility", risk.get('volatility')),
        ("Maximum Drawdown", risk.get('max_drawdown')),
        ("Value at Risk (95%)", risk.get('var_95')),
        ("Sharpe Ratio", risk.get('sharpe_ratio')),
        ("Risk Level", risk.get('risk_level', 'N/A'))
    ]

def get_final_assessment(results):
    """Extract and format final assessment"""
    rec = results.get('recommendation', {})
    
    return [
        ("Integrated Score", results.get('integrated_score')),
        ("Recommendation", rec.get('action', 'N/A')),
        ("Reasoning", rec.get('reasoning', 'N/A')),
        ("Risk Context", rec.get('risk_context', 'N/A'))
    ]

def analyze_stock_detailed(symbol: str):
    """Perform detailed analysis of a stock"""
    print(f"\nDetailed Analysis for {symbol}")
    print("=" * 60)
    
    analyzer = IntegratedAnalysis()
    
    try:
        print(f"\nFetching and analyzing {symbol}...")
        results = analyzer.analyze_stock(symbol)
        
        if not results:
            print(f"Analysis failed for {symbol}")
            return
            
        # Display sections with validation
        sections = {
            "1. COMPANY PROFILE": [
                ("Company Type", results['company_type'].upper()),
            ],
            "2. FUNDAMENTAL ANALYSIS": get_fundamental_metrics(results),
            "3. TECHNICAL ANALYSIS": get_technical_metrics(results),
            "4. RISK ASSESSMENT": get_risk_metrics(results),
            "5. FINAL ASSESSMENT": get_final_assessment(results)
        }
        
        for section_title, metrics in sections.items():
            print(f"\n{section_title}")
            print("-" * 40)
            for label, value in metrics:
                if isinstance(value, bool):
                    print(f"{label}: {'Yes' if value else 'No'}")
                elif "Trend" in label or "Status" in label or "Level" in label or "Context" in label:
                    print(f"{label}: {value}")
                elif "Reasoning" in label or "Recommendation" in label:
                    print(f"{label}: {value}")
                else:
                    is_percentage = any(term in label.lower() for term in 
                                     ['return', 'growth', 'rotc', 'volatility', 'drawdown', 'var'])
                    print(f"{label}: {format_metrics(value, is_percentage)}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {str(e)}")
        import traceback
        print(traceback.format_exc())

def main():
    print("\nINVESTMENT BOT - COMPREHENSIVE STOCK ANALYSIS")
    print("=" * 60)
    
    # Test different types of companies
    symbols = [
        "AAPL",    # Value company with high ROTC
        "MSFT",    # Value company with strong metrics
        "GOOGL"    # Growth/Value hybrid
    ]
    
    for symbol in symbols:
        analyze_stock_detailed(symbol)
        if symbol != symbols[-1]:
            input("\nPress Enter to analyze next stock...")

if __name__ == "__main__":
    main()