#!/usr/bin/env python3
"""
Real Saudi Market API Testing
Tests TwelveData API integration with actual Saudi stock market data
"""

import requests
import json
import time
from datetime import datetime, timedelta

print("🇸🇦 REAL SAUDI MARKET API TESTING")
print("=" * 50)

# TwelveData API configuration
API_KEY = "71cdbb03b46645628e8416eeb4836c99"
BASE_URL = "https://api.twelvedata.com"

# Popular Saudi stocks for testing
SAUDI_STOCKS = {
    '2222.SAU': 'Saudi Aramco',
    '1180.SAU': 'Al Rajhi Bank', 
    '2030.SAU': 'SABIC',
    '1120.SAU': 'Saudi National Bank',
    '2010.SAU': 'Saudi Basic Industries Corp'
}

def test_api_connection():
    """Test basic API connectivity"""
    print("\n🔌 Test 1: API Connection")
    print("-" * 25)
    
    try:
        # Test with simple quote endpoint
        symbol = '2222.SAU'  # Saudi Aramco
        url = f"{BASE_URL}/quote"
        
        params = {
            'symbol': symbol,
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received for {SAUDI_STOCKS[symbol]}")
            
            if 'symbol' in data:
                print(f"  📊 Symbol: {data.get('symbol', 'N/A')}")
                print(f"  💰 Price: {data.get('close', 'N/A')} SAR")
                print(f"  📈 Change: {data.get('change', 'N/A')}")
                return True, data
            else:
                print(f"  ⚠️  Unexpected response structure: {data}")
                return False, data
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False, None

def test_multiple_stocks():
    """Test multiple Saudi stocks"""
    print("\n📊 Test 2: Multiple Saudi Stocks")
    print("-" * 32)
    
    successful_calls = 0
    
    for symbol, name in SAUDI_STOCKS.items():
        try:
            print(f"🔍 Testing {name} ({symbol})...")
            
            url = f"{BASE_URL}/quote"
            params = {
                'symbol': symbol,
                'apikey': API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'close' in data:
                    price = data.get('close', 'N/A')
                    change = data.get('change', 'N/A')
                    print(f"  ✅ Price: {price} SAR, Change: {change}")
                    successful_calls += 1
                else:
                    print(f"  ⚠️  Data structure: {list(data.keys())}")
            else:
                print(f"  ❌ Failed: {response.status_code}")
            
            # Rate limiting - wait between calls
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print(f"\n📈 Results: {successful_calls}/{len(SAUDI_STOCKS)} stocks retrieved")
    return successful_calls > 0

def test_historical_data():
    """Test historical data retrieval"""
    print("\n📅 Test 3: Historical Data")
    print("-" * 25)
    
    try:
        symbol = '2222.SAU'  # Saudi Aramco
        print(f"📊 Getting historical data for {SAUDI_STOCKS[symbol]}...")
        
        url = f"{BASE_URL}/time_series"
        params = {
            'symbol': symbol,
            'interval': '1day',
            'outputsize': 10,  # Last 10 days
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'values' in data:
                values = data['values']
                print(f"✅ Retrieved {len(values)} historical data points")
                
                if len(values) > 0:
                    latest = values[0]
                    print(f"  📅 Latest Date: {latest.get('datetime', 'N/A')}")
                    print(f"  💰 Close Price: {latest.get('close', 'N/A')} SAR")
                    print(f"  📊 Volume: {latest.get('volume', 'N/A')}")
                    
                    # Calculate simple metrics
                    if len(values) >= 2:
                        prev_close = float(values[1].get('close', 0))
                        curr_close = float(values[0].get('close', 0))
                        if prev_close > 0:
                            daily_change = ((curr_close - prev_close) / prev_close) * 100
                            print(f"  📈 Daily Change: {daily_change:.2f}%")
                
                return True
            else:
                print(f"  ⚠️  Response structure: {list(data.keys())}")
                print(f"  📄 Response sample: {str(data)[:200]}...")
                return False
        else:
            print(f"❌ Historical data failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Historical data error: {str(e)}")
        return False

def test_company_profile():
    """Test company profile data"""
    print("\n🏢 Test 4: Company Profiles")
    print("-" * 26)
    
    try:
        symbol = '2222.SAU'  # Saudi Aramco
        print(f"🔍 Getting profile for {SAUDI_STOCKS[symbol]}...")
        
        url = f"{BASE_URL}/profile"
        params = {
            'symbol': symbol,
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Company profile retrieved")
            
            # Display available information
            profile_fields = [
                ('name', 'Company Name'),
                ('sector', 'Sector'),
                ('industry', 'Industry'), 
                ('market_cap', 'Market Cap'),
                ('employees', 'Employees'),
                ('description', 'Description')
            ]
            
            for field, label in profile_fields:
                if field in data:
                    value = data[field]
                    if field == 'description' and len(str(value)) > 100:
                        value = str(value)[:100] + "..."
                    print(f"  📋 {label}: {value}")
            
            return True
        else:
            print(f"❌ Profile failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Profile error: {str(e)}")
        return False

def test_market_stats():
    """Test market statistics"""
    print("\n📊 Test 5: Market Statistics")
    print("-" * 27)
    
    try:
        # Test statistics for Saudi Aramco
        symbol = '2222.SAU'
        print(f"📈 Getting statistics for {SAUDI_STOCKS[symbol]}...")
        
        url = f"{BASE_URL}/statistics"
        params = {
            'symbol': symbol,
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics retrieved")
            
            # Display key statistics
            stats_fields = [
                ('52_week_high', '52-Week High'),
                ('52_week_low', '52-Week Low'),
                ('market_cap', 'Market Cap'),
                ('pe_ratio', 'P/E Ratio'),
                ('dividend_yield', 'Dividend Yield'),
                ('beta', 'Beta')
            ]
            
            for field, label in stats_fields:
                if field in data:
                    print(f"  📊 {label}: {data[field]}")
            
            return True
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            # Try alternative endpoint
            print("  🔄 Trying alternative approach...")
            return test_alternative_stats(symbol)
            
    except Exception as e:
        print(f"❌ Statistics error: {str(e)}")
        return False

def test_alternative_stats(symbol):
    """Test alternative statistics approach"""
    try:
        # Use quote endpoint which sometimes includes additional data
        url = f"{BASE_URL}/quote"
        params = {
            'symbol': symbol,
            'apikey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Alternative data retrieved")
            
            # Show all available fields
            print(f"  📋 Available fields: {list(data.keys())}")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ❌ Alternative approach failed: {str(e)}")
        return False

def test_api_limits():
    """Test API rate limits and quotas"""
    print("\n⚡ Test 6: API Limits & Performance")
    print("-" * 34)
    
    print("🔍 Testing API performance...")
    
    start_time = time.time()
    successful_calls = 0
    
    # Test 5 rapid calls
    for i in range(5):
        try:
            symbol = list(SAUDI_STOCKS.keys())[i % len(SAUDI_STOCKS)]
            
            url = f"{BASE_URL}/quote"
            params = {
                'symbol': symbol,
                'apikey': API_KEY
            }
            
            call_start = time.time()
            response = requests.get(url, params=params, timeout=10)
            call_time = time.time() - call_start
            
            if response.status_code == 200:
                successful_calls += 1
                print(f"  ✅ Call {i+1}: {call_time:.2f}s")
            else:
                print(f"  ❌ Call {i+1}: Failed ({response.status_code})")
            
            # Small delay to respect rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Call {i+1}: Error - {str(e)}")
    
    total_time = time.time() - start_time
    
    print(f"\n📊 Performance Results:")
    print(f"  • Successful calls: {successful_calls}/5")
    print(f"  • Total time: {total_time:.2f}s")
    print(f"  • Average per call: {total_time/5:.2f}s")
    
    if successful_calls >= 4:
        print(f"  🎉 Performance: EXCELLENT")
    elif successful_calls >= 2:
        print(f"  ✅ Performance: GOOD")
    else:
        print(f"  ⚠️  Performance: NEEDS IMPROVEMENT")
    
    return successful_calls >= 2

# Run all tests
def main():
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: ...{API_KEY[-8:]}")  # Show last 8 characters only
    
    test_results = []
    
    # Run all tests
    test_results.append(("API Connection", test_api_connection()[0]))
    test_results.append(("Multiple Stocks", test_multiple_stocks()))
    test_results.append(("Historical Data", test_historical_data()))
    test_results.append(("Company Profiles", test_company_profile()))
    test_results.append(("Market Statistics", test_market_stats()))
    test_results.append(("API Performance", test_api_limits()))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏆 SAUDI MARKET API TEST SUMMARY")
    print("=" * 50)
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if passed:
            passed_tests += 1
    
    success_rate = (passed_tests / len(test_results)) * 100
    print(f"\n📊 Success Rate: {passed_tests}/{len(test_results)} tests ({success_rate:.0f}%)")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT! Saudi market API is ready for production")
    elif success_rate >= 60:
        print("✅ GOOD! Saudi market API is functional with minor issues")
    elif success_rate >= 40:
        print("⚠️  FAIR! Saudi market API needs optimization")
    else:
        print("❌ POOR! Saudi market API requires significant fixes")
    
    print("\n🚀 Next Steps:")
    if success_rate >= 60:
        print("  1. ✅ Integrate with Phase 3 & 4 services")
        print("  2. ✅ Enable real-time Saudi stock analysis")
        print("  3. ✅ Deploy to production environment")
    else:
        print("  1. 🔧 Debug API connectivity issues")
        print("  2. 🔧 Check Saudi stock symbol formatting")
        print("  3. 🔧 Verify API key permissions")
    
    print("=" * 50)

if __name__ == "__main__":
    main()