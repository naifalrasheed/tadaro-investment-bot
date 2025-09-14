from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
from datetime import datetime

def run_stock_analysis(symbols: list):
    analyzer = IntegratedAnalysis()
    
    for symbol in symbols:
        print(f"\nDetailed Analysis for {symbol}")
        print("=" * 50)
        
        results = analyzer.analyze_stock(symbol)
        
        if results:
            # Company Classification
            print(f"\n1. Company Classification:")
            print(f"Type: {results['company_type'].upper()}")
            
            # Fundamental Analysis
            print(f"\n2. Fundamental Analysis:")
            fund = results['fundamental_analysis']
            if results['company_type'] == 'value':
                rotc_data = fund['rotc_data']
                print(f"ROTC Analysis:")
                print(f"- Current ROTC: {rotc_data.get('latest_rotc', 0):.2%}")
                print(f"- ROTC Trend: {'Improving' if rotc_data.get('improving', False) else 'Declining'}")
                print(f"- 4Q Average ROTC: {rotc_data.get('avg_rotc', 0):.2%}")
            else:
                growth_data = fund['growth_data']
                print(f"Growth Analysis:")
                print(f"- Revenue Growth: {growth_data.get('avg_revenue_growth', 0):.2%}")
                print(f"- Cash Flow Status: {'Positive' if growth_data.get('cash_flow_positive', False) else 'Negative'}")
                print(f"- Growth Trend: {'Accelerating' if growth_data.get('revenue_growth_trend', 0) > 0 else 'Decelerating'}")
            
            print(f"\nFundamental Score: {fund['score']:.2f}/100")
            
            # Technical Analysis
            print(f"\n3. Technical Analysis:")
            tech = results['technical_analysis']
            print(f"ML Predictions:")
            print(f"- Expected Return: {tech['ml_prediction']:.2%}")
            print(f"- Confidence Level: {tech['confidence']:.2%}")
            print(f"- Technical Score: {tech['technical_score']:.2f}/100")
            
            # Price Metrics
            price_metrics = tech['price_metrics']
            print(f"\nPrice Information:")
            print(f"- Current Price: ${price_metrics['current_price']:.2f}")
            print(f"- Predicted Price: ${price_metrics['predicted_price']:.2f}")
            print(f"- Volatility: {price_metrics['volatility']:.2%}")
            
            # Risk Analysis
            print(f"\n4. Risk Assessment:")
            risk = results['risk_metrics']
            print(f"- Annual Volatility: {risk['volatility']:.2f}%")
            print(f"- Maximum Drawdown: {risk['max_drawdown']:.2f}%")
            print(f"- Value at Risk (95%): {risk['var_95']:.2f}%")
            
            # Final Results
            print(f"\n5. Integrated Results:")
            print(f"Final Score: {results['integrated_score']:.2f}/100")
            rec = results['recommendation']
            print(f"Recommendation: {rec['action']}")
            print(f"Reasoning: {rec['reasoning']}")
            
            print("\n" + "="*50)
        else:
            print(f"Analysis failed for {symbol}")
        
        input("\nPress Enter to analyze next stock...")

if __name__ == "__main__":
    # Test different types of companies
    companies = [
        "AAPL",    # Value company with high ROTC
        "AMZN",    # Growth company with strong revenue growth
        "MSFT",    # Value company with improving ROTC
        "TSLA"     # Growth company with volatile metrics
    ]
    
    print("Starting Comprehensive Stock Analysis")
    print("=" * 50)
    run_stock_analysis(companies)