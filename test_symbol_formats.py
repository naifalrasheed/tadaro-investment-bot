#!/usr/bin/env python3
"""
Test different Saudi stock symbol formats with TwelveData API
"""

import requests
import time

API_KEY = "71cdbb03b46645628e8416eeb4836c99"
BASE_URL = "https://api.twelvedata.com"

# Different symbol formats to test
SYMBOL_FORMATS = {
    "Saudi Aramco": [
        "2222.SAU",
        "2222.SR", 
        "2222.TADAWUL",
        "2222",
        "ARAMCO",
        "2222.RIYADH"
    ],
    "Al Rajhi Bank": [
        "1180.SAU",
        "1180.SR",
        "1180.TADAWUL", 
        "1180",
        "RJHI",
        "1180.RIYADH"
    ]
}

def test_symbol_format(company, symbol):
    """Test a specific symbol format"""
    try:
        url = f"{BASE_URL}/quote"
        params = {
            'symbol': symbol,
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'close' in data and data.get('close') is not None:
                return True, f"Price: {data['close']}"
            elif 'status' in data and data['status'] == 'error':
                return False, data.get('message', 'Unknown error')
            else:
                return False, f"Unexpected response: {list(data.keys())}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def main():
    print("🔍 SAUDI SYMBOL FORMAT TESTING")
    print("=" * 40)
    
    working_symbols = {}
    
    for company, symbols in SYMBOL_FORMATS.items():
        print(f"\n📊 Testing {company}:")
        print("-" * (len(company) + 10))
        
        for symbol in symbols:
            print(f"  🧪 {symbol:<15}", end=" -> ")
            
            success, message = test_symbol_format(company, symbol)
            
            if success:
                print(f"✅ {message}")
                working_symbols[company] = symbol
                break  # Found working format, move to next company
            else:
                print(f"❌ {message}")
            
            time.sleep(0.5)  # Rate limiting
        
        if company not in working_symbols:
            print(f"  ⚠️  No working format found for {company}")
    
    print("\n" + "=" * 40)
    print("🎯 WORKING SYMBOL FORMATS:")
    print("=" * 40)
    
    if working_symbols:
        for company, symbol in working_symbols.items():
            print(f"✅ {company}: {symbol}")
    else:
        print("❌ No working symbol formats found")
        
        # Try alternative approach - search for available symbols
        print("\n🔍 Searching for available Saudi market symbols...")
        try_alternative_search()

def try_alternative_search():
    """Try to find available symbols through symbol search"""
    try:
        # Test symbol search endpoint
        url = f"{BASE_URL}/symbol_search"
        params = {
            'symbol': 'ARAMCO',
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol search results:")
            
            if 'data' in data:
                for item in data['data'][:5]:  # Show first 5 results
                    symbol = item.get('symbol', 'N/A')
                    name = item.get('instrument_name', 'N/A')
                    exchange = item.get('exchange', 'N/A')
                    print(f"  📊 {symbol} - {name} ({exchange})")
            else:
                print(f"  📄 Response: {data}")
        else:
            print(f"❌ Symbol search failed: {response.status_code}")
            
        # Also try getting list of exchanges
        print(f"\n🏛️  Checking available exchanges...")
        url = f"{BASE_URL}/exchanges"
        params = {'apikey': API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for Saudi/Tadawul exchanges
            exchanges = data.get('data', []) if isinstance(data, dict) else data
            
            saudi_exchanges = []
            for exchange in exchanges:
                if isinstance(exchange, dict):
                    name = exchange.get('name', '').lower()
                    code = exchange.get('code', '').lower() 
                    
                    if 'saudi' in name or 'tadawul' in name or 'riyadh' in name:
                        saudi_exchanges.append(exchange)
            
            if saudi_exchanges:
                print(f"✅ Found Saudi exchanges:")
                for ex in saudi_exchanges:
                    print(f"  🏛️  {ex.get('name', 'N/A')} ({ex.get('code', 'N/A')})")
            else:
                print(f"⚠️  No Saudi exchanges found in list")
                print(f"📄 Sample exchanges: {[ex.get('name') for ex in exchanges[:3]]}")
        
    except Exception as e:
        print(f"❌ Alternative search failed: {str(e)}")

if __name__ == "__main__":
    main()