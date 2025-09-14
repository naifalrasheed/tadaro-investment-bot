from ml_components.integrated_analysis import IntegratedAnalysis
import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

def analyze_different_stock_types():
    analyzer = IntegratedAnalysis()
    
    # Different types of stocks to test
    stocks = {
        "Value Stocks (High ROTC)": [
            "AAPL",  # Apple: High ROTC, stable
            "MSFT",  # Microsoft: High ROTC, growing
        ],
        "Growth Stocks": [
            "TSLA",  # Tesla: High growth, negative ROTC
            "NVDA",  # NVIDIA: High growth, positive ROTC
        ],
        "Dividend Stocks": [
            "JNJ",   # Johnson & Johnson: Stable, high dividend
            "PG",    # Procter & Gamble: Stable, consistent dividend
        ],
        "Technology Sector": [
            "GOOGL", # Alphabet: Mixed growth/value
            "AMD",   # AMD: High growth, cyclical
        ]
    }
    
    print("\nCOMPREHENSIVE STOCK TYPE ANALYSIS")
    print("=" * 60)
    
    for category, stock_list in stocks.items():
        print(f"\n{category.upper()}")
        print("-" * 60)
        
        for symbol in stock_list:
            try:
                print(f"\nAnalyzing {symbol}...")
                results = analyzer.analyze_stock(symbol)
                
                if not results:
                    print(f"Analysis failed for {symbol}")
                    continue
                
                # Display company type and fundamental metrics
                print(f"\nCompany Profile:")
                print(f"Type: {results['company_type']}")
                
                # Display fundamental analysis
                fund = results['fundamental_analysis']
                print("\nFundamental Analysis:")
                if results['company_type'] == 'value':
                    rotc_data = fund.get('rotc_data', {})
                    if rotc_data:
                        print(f"ROTC: {rotc_data.get('latest_rotc', 0):.2f}%")
                        print(f"ROTC Trend: {'Improving' if rotc_data.get('improving') else 'Declining'}")
                else:
                    growth_data = fund.get('growth_data', {})
                    if growth_data:
                        print(f"Revenue Growth: {growth_data.get('avg_revenue_growth', 0):.2f}%")
                        print(f"Cash Flow: {'Positive' if growth_data.get('cash_flow_positive') else 'Negative'}")
                
                # Display technical analysis
                tech = results['technical_analysis']
                price_metrics = tech.get('price_metrics', {})
                print("\nTechnical Analysis:")
                print(f"Current Price: ${price_metrics.get('current_price', 0):.2f}")
                print(f"Predicted Price: ${price_metrics.get('predicted_price', 0):.2f}")
                print(f"Expected Return: {tech.get('ml_prediction', 0):.2f}%")
                
                # Display risk metrics
                risk = results['risk_metrics']
                print("\nRisk Profile:")
                print(f"Volatility: {risk.get('volatility', 0):.2f}%")
                print(f"Max Drawdown: {risk.get('max_drawdown', 0):.2f}%")
                print(f"Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}")
                
                # Display final assessment
                print("\nFinal Assessment:")
                print(f"Integrated Score: {results.get('integrated_score', 0):.2f}/100")
                rec = results['recommendation']
                print(f"Recommendation: {rec.get('action', 'N/A')}")
                print(f"Reasoning: {rec.get('reasoning', 'N/A')}")
                
                print("-" * 40)
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    analyze_different_stock_types()