from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

def format_number(value, is_percentage=False):
    """Safely format numbers and percentages"""
    try:
        if isinstance(value, (int, float)):
            if is_percentage:
                return f"{value:.2f}%"
            else:
                return f"{value:.2f}"
        return str(value)
    except:
        return "N/A"

def analyze_stock(symbol: str):
    """Analyze a single stock"""
    print(f"\nAnalyzing {symbol}")
    print("=" * 60)
    
    analyzer = IntegratedAnalysis()
    
    try:
        results = analyzer.analyze_stock(symbol)
        
        if not results:
            print(f"Analysis failed for {symbol}")
            return
            
        # Company Type and Fundamental Analysis
        print("\n1. COMPANY PROFILE & FUNDAMENTALS")
        print("-" * 40)
        print(f"Company Type: {results['company_type'].upper()}")
        fund = results['fundamental_analysis']
        
        if results['company_type'] == 'value':
            rotc_data = fund['rotc_data']
            if rotc_data and isinstance(rotc_data, dict):
                print("\nROTC Analysis:")
                print(f"Current ROTC: {format_number(rotc_data.get('latest_rotc', 0), True)}")
                print(f"4Q Average ROTC: {format_number(rotc_data.get('avg_rotc', 0), True)}")
                print(f"ROTC Trend: {'Improving' if rotc_data.get('improving', False) else 'Declining'}")
        else:
            growth_data = fund['growth_data']
            if growth_data and isinstance(growth_data, dict):
                print("\nGrowth Metrics:")
                print(f"Revenue Growth: {format_number(growth_data.get('avg_revenue_growth', 0), True)}")
                print(f"Cash Flow Status: {'Positive' if growth_data.get('cash_flow_positive', False) else 'Negative'}")
                growth_trend = growth_data.get('revenue_growth_trend', 0)
                print(f"Growth Trend: {'Accelerating' if growth_trend > 0 else 'Decelerating'}")
        
        print(f"\nFundamental Score: {format_number(fund.get('score', 0))}/100")
        
        # Technical Analysis
        print("\n2. TECHNICAL ANALYSIS")
        print("-" * 40)
        tech = results['technical_analysis']
        price_metrics = tech.get('price_metrics', {})
        
        current_price = price_metrics.get('current_price', 0)
        predicted_price = price_metrics.get('predicted_price', 0)
        
        print(f"Current Price: ${format_number(current_price)}")
        print(f"Predicted Price: ${format_number(predicted_price)}")
        print(f"Expected Return: {format_number(tech.get('ml_prediction', 0), True)}")
        print(f"Model Confidence: {format_number(tech.get('confidence', 0), True)}")
        print(f"Technical Score: {format_number(tech.get('technical_score', 0))}/100")
        
        # Risk Assessment
        print("\n3. RISK ASSESSMENT")
        print("-" * 40)
        risk = results.get('risk_metrics', {})
        
        print(f"Annual Volatility: {format_number(risk.get('volatility', 0), True)}")
        print(f"Maximum Drawdown: {format_number(risk.get('max_drawdown', 0), True)}")
        print(f"Value at Risk (95%): {format_number(risk.get('var_95', 0), True)}")
        print(f"Current Volatility: {format_number(price_metrics.get('volatility', 0), True)}")
        
        # Final Assessment
        print("\n4. FINAL ASSESSMENT")
        print("-" * 40)
        print(f"Integrated Score: {format_number(results.get('integrated_score', 0))}/100")
        rec = results.get('recommendation', {})
        print(f"Recommendation: {rec.get('action', 'No recommendation')}")
        print(f"Reasoning: {rec.get('reasoning', 'No reasoning provided')}")
        
        # Investment Thesis
        print("\n5. INVESTMENT THESIS")
        print("-" * 40)
        if results['company_type'] == 'value':
            if rotc_data and isinstance(rotc_data, dict):
                print("Value Investment Case:")
                latest_rotc = rotc_data.get('latest_rotc', 0)
                print(f"- Company demonstrates capital efficiency with {format_number(latest_rotc, True)} ROTC")
                if rotc_data.get('improving', False):
                    print("- ROTC is improving, indicating better capital allocation")
                else:
                    print("- Monitor ROTC trend for potential deterioration")
        else:
            if growth_data and isinstance(growth_data, dict):
                print("Growth Investment Case:")
                avg_growth = growth_data.get('avg_revenue_growth', 0)
                print(f"- Revenue growing at {format_number(avg_growth, True)}")
                if growth_data.get('cash_flow_positive', False):
                    print("- Positive cash flow indicates sustainable growth")
                else:
                    print("- Monitor cash flow for path to profitability")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {str(e)}")
        import traceback
        print(traceback.format_exc())

def main():
    print("\nINVESTMENT BOT - COMPREHENSIVE STOCK ANALYSIS")
    print("=" * 60)
    
    # Test both value and growth companies
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        analyze_stock(symbol)
        if symbol != symbols[-1]:
            input("\nPress Enter to analyze next stock...")

if __name__ == "__main__":
    main()