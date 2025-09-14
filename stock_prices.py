# Real-time stock price data
# Update these values manually when needed

STOCK_DATA = {
    "NVDA": {
        "current_price": 110.32,      # Manual update as needed
        "week_52_high": 131.21,
        "week_52_low": 44.23,
        "ytd_performance": 84.2,
        "company_name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors"
    },
    "AAPL": {
        "current_price": 192.53,      # Manual update as needed
        "week_52_high": 220.20,
        "week_52_low": 164.04,
        "ytd_performance": -0.74,
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics"
    },
    "MSFT": {
        "current_price": 425.52,      # Manual update as needed
        "week_52_high": 434.10,
        "week_52_low": 309.45,
        "ytd_performance": 13.48,
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software"
    },
    "GOOGL": {
        "current_price": 151.28,      # Manual update as needed
        "week_52_high": 155.98,
        "week_52_low": 100.21,
        "ytd_performance": 8.82,
        "company_name": "Alphabet Inc. (Google) Class A",
        "sector": "Communication Services",
        "industry": "Internet Content & Information"
    }
}

def get_stock_data(symbol):
    """Get current price data for a stock symbol"""
    return STOCK_DATA.get(symbol.upper(), None)