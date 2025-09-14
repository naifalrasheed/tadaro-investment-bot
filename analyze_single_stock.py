from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def analyze_single_stock(symbol: str):
    """Perform detailed analysis of a single stock"""
    print(f"\nDETAILED ANALYSIS FOR {symbol}")
    print("=" * 60)
    
    analyzer = IntegratedAnalysis()
    
    try:
        # Get analysis
        print(f"\nFetching and analyzing {symbol} data...")
        results = analyzer.analyze_stock(symbol)
        
        if not results:
            print(f"Analysis failed for {symbol}")
            return
        
        # 1. Company Overview
        print("\n1. COMPANY OVERVIEW")
        print("-" * 40)
        print(f"Analysis Date: {results['analysis_date']}")
        print(f"Company Type: {results['company_type'].upper()}")
        
        # 2. Fundamental Analysis
        print("\n2. FUNDAMENTAL METRICS")
        print("-" * 40)
        fund = results['fundamental_analysis']
        
        if results['company_type'] == 'value':
            rotc_data = fund.get('rotc_data', {})
            if rotc_data:
                print("Value Metrics:")
                print(f"• Current ROTC: {rotc_data.get('latest_rotc', 0):.2f}%")
                print(f"• 4Q Average ROTC: {rotc_data.get('avg_rotc', 0):.2f}%")
                print(f"• ROTC Trend: {'Improving' if rotc_data.get('improving') else 'Declining'}")
        else:
            growth_data = fund.get('growth_data', {})
            if growth_data:
                print("Growth Metrics:")
                print(f"• Revenue Growth: {growth_data.get('avg_revenue_growth', 0):.2f}%")
                print(f"• Cash Flow Status: {'Positive' if growth_data.get('cash_flow_positive') else 'Negative'}")
                trend = growth_data.get('revenue_growth_trend', 0)
                print(f"• Growth Trend: {'Accelerating' if trend > 0 else 'Decelerating'}")
        
        # 3. Technical Analysis
        print("\n3. TECHNICAL ANALYSIS")
        print("-" * 40)
        tech = results['technical_analysis']
        price_metrics = tech.get('price_metrics', {})
        
        print("Price Metrics:")
        print(f"• Current Price: ${price_metrics.get('current_price', 0):.2f}")
        print(f"• Predicted Price: ${price_metrics.get('predicted_price', 0):.2f}")
        print(f"• Expected Return: {tech.get('ml_prediction', 0):.2f}%")
        print(f"• Model Confidence: {tech.get('confidence', 0):.2f}%")
        
        # 4. Risk Assessment
        print("\n4. RISK ASSESSMENT")
        print("-" * 40)
        risk = results['risk_metrics']
        
        print("Risk Metrics:")
        print(f"• Annual Volatility: {risk.get('volatility', 0):.2f}%")
        print(f"• Maximum Drawdown: {risk.get('max_drawdown', 0):.2f}%")
        print(f"• Value at Risk (95%): {risk.get('var_95', 0):.2f}%")
        print(f"• Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}")
        print(f"• Risk Level: {risk.get('risk_level', 'N/A')}")
        
        # 5. Investment Summary
        print("\n5. INVESTMENT SUMMARY")
        print("-" * 40)
        print(f"Integrated Score: {results.get('integrated_score', 0):.2f}/100")
        
        rec = results['recommendation']
        print(f"Recommendation: {rec.get('action', 'N/A')}")
        print(f"Reasoning: {rec.get('reasoning', 'N/A')}")
        print(f"Risk Context: {rec.get('risk_context', 'N/A')}")
        
        # 6. Investment Thesis
        print("\n6. INVESTMENT THESIS")
        print("-" * 40)
        
        # Generate investment thesis based on company type
        if results['company_type'] == 'value':
            rotc = rotc_data.get('latest_rotc', 0)
            rotc_trend = rotc_data.get('improving', False)
            
            print("Value Investment Case:")
            if rotc > 10:
                print("• Strong capital efficiency with high ROTC")
            elif rotc > 5:
                print("• Moderate capital efficiency")
            else:
                print("• Below average capital efficiency")
                
            if rotc_trend:
                print("• Improving capital allocation trend")
            else:
                print("• Monitor declining ROTC trend")
        else:
            growth = growth_data.get('avg_revenue_growth', 0)
            cash_positive = growth_data.get('cash_flow_positive', False)
            
            print("Growth Investment Case:")
            if growth > 30:
                print("• Strong revenue growth momentum")
            elif growth > 15:
                print("• Moderate revenue growth")
            else:
                print("• Slowing growth rates")
                
            if cash_positive:
                print("• Sustainable growth with positive cash flow")
            else:
                print("• Monitor path to profitability")
        
        # Add risk-based considerations
        volatility = risk.get('volatility', 0)
        if volatility > 30:
            print("• High volatility requires active risk management")
        elif volatility > 20:
            print("• Moderate volatility suggests normal market risk")
        else:
            print("• Low volatility indicates stability")
            
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        import traceback
        print(traceback.format_exc())

def main():
    # Get stock symbol from user
    symbol = input("\nEnter stock symbol to analyze (e.g., AAPL): ").upper()
    analyze_single_stock(symbol)

if __name__ == "__main__":
    main()