from analysis.stock_analyzer import StockAnalyzer
import pandas as pd
import logging
import os
from config import DevelopmentConfig as Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global MongoDB connection with timeout and availability flag
MONGO_AVAILABLE = False
db = None

try:
    # Only attempt MongoDB connection if configured
    if hasattr(Config, 'MONGODB_URI') and Config.MONGODB_URI:
        import pymongo
        client = pymongo.MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Test the connection
        client.admin.command('ping')
        db = client[Config.DATABASE_NAME]
        MONGO_AVAILABLE = True
        logger.info("MongoDB connection successful")
except ImportError:
    logger.warning("pymongo module not installed. MongoDB features disabled.")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {str(e)}. Feedback will not be saved.")

def save_user_feedback(feedback):
    """Save user feedback if MongoDB is available"""
    if MONGO_AVAILABLE and db is not None:
        try:
            collection_name = Config.COLLECTIONS.get('feedback', 'user_feedback')
            db[collection_name].insert_one(feedback)
            logger.info(f"Feedback saved for symbol {feedback.get('symbol')}")
            return True
        except Exception as e:
            logger.warning(f"Could not save feedback: {str(e)}")
    return False

def analyze_single_stock():
    """Interactive interface for single stock analysis"""
    analyzer = StockAnalyzer()
    
    while True:
        symbol = input("\nEnter stock symbol to analyze (or 'q' to quit): ").upper()
        if symbol == 'Q':
            break
            
        print(f"\nAnalyzing {symbol}...")
        results = analyzer.analyze_stock(symbol)
        
        if not results:
            print("Analysis failed. Please try another symbol.")
            continue
            
        # Print Analysis Results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Company: {results['company_name']} ({results['symbol']})")
        print(f"Sector: {results['sector']}")
        print(f"Industry: {results['industry']}")
        
        # Dividend Info
        div = results['dividend_metrics']
        print("\nDividend Analysis:")
        print(f"Yield: {div['dividend_yield']:.2f}%")
        print(f"Growth Rate: {div['dividend_growth']:.2f}%")
        print(f"Payout Ratio: {div['payout_ratio']:.2f}%")
        
        # Fundamental & Technical
        integrated = results['integrated_analysis']
        print("\nFundamental & Technical Analysis:")
        print(f"ROTC: {integrated['fundamental_analysis']['rotc_data']['latest_rotc']:.2f}%")
        print(f"Technical Score: {integrated['technical_analysis']['technical_score']:.2f}/100")
        
        # Portfolio Impact if available
        if results['portfolio_impact']:
            impact = results['portfolio_impact']['impact']
            print("\nPortfolio Impact (10% allocation):")
            print(f"Sharpe Ratio Change: {impact['sharpe_change']:.4f}")
            print(f"Volatility Change: {impact['volatility_change']:.4f}%")
        
        print("\nWould you like to:")
        print("1. See detailed metrics")
        print("2. Analyze another stock")
        print("3. Add to portfolio watchlist")
        print("4. Return to main menu")
        
        choice = input("Enter choice (1-4): ")
        if choice == '1':
            print_detailed_metrics(results)
        elif choice == '3':
            add_to_watchlist(results['symbol'])
            
        # Save analysis feedback
        if MONGO_AVAILABLE:
            try:
                feedback = {
                    "symbol": symbol,
                    "analysis_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "analysis_results": {
                        "technical_score": integrated['technical_analysis']['technical_score'],
                        "has_portfolio_impact": bool(results['portfolio_impact'])
                    }
                }
                save_user_feedback(feedback)
            except Exception as e:
                logger.error(f"Error saving feedback: {str(e)}")

def print_detailed_metrics(results: dict):
    """Print detailed metrics for a stock"""
    print("\n=== DETAILED METRICS ===")
    
    # Technical indicators
    tech = results['integrated_analysis']['technical_analysis']
    print("\nTechnical Indicators:")
    print(f"RSI (14-day): {tech.get('rsi', 0):.2f}")
    print(f"MACD: {tech.get('macd', 0):.4f}")
    print(f"Bollinger Band Position: {tech.get('bollinger_position', 0):.2f}")
    
    # Fundamental ratios
    fund = results['integrated_analysis']['fundamental_analysis']
    print("\nFundamental Ratios:")
    print(f"P/E Ratio: {fund.get('pe_ratio', 0):.2f}")
    print(f"EV/EBITDA: {fund.get('ev_ebitda', 0):.2f}")
    print(f"Debt to Equity: {fund.get('debt_to_equity', 0):.2f}")
    print(f"ROE: {fund.get('roe', 0):.2f}%")
    
    # Valuation metrics
    val = results.get('valuation', {})
    if val:
        print("\nValuation Metrics:")
        print(f"Intrinsic Value: ${val.get('intrinsic_value', 0):.2f}")
        print(f"Target Price: ${val.get('target_price', 0):.2f}")
        print(f"Upside Potential: {val.get('upside_potential', 0):.2f}%")
    
    input("\nPress Enter to continue...")

def add_to_watchlist(symbol: str):
    """Add stock to watchlist"""
    if MONGO_AVAILABLE and db is not None:
        try:
            collection_name = Config.COLLECTIONS.get('watchlist', 'stock_watchlist')
            watchlist_item = {
                "symbol": symbol,
                "added_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notes": ""
            }
            db[collection_name].insert_one(watchlist_item)
            print(f"\n{symbol} added to watchlist successfully!")
        except Exception as e:
            logger.error(f"Error adding to watchlist: {str(e)}")
            print("\nCould not add to watchlist. Please try again later.")
    else:
        # Save to local file if MongoDB not available
        watchlist_file = os.path.join(os.path.dirname(__file__), "watchlist.txt")
        try:
            with open(watchlist_file, "a") as f:
                f.write(f"{symbol},{pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
            print(f"\n{symbol} added to watchlist successfully!")
        except Exception as e:
            logger.error(f"Error adding to watchlist file: {str(e)}")
            print("\nCould not add to watchlist. Please try again later.")