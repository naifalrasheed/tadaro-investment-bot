#!/usr/bin/env python3
"""Test TwelveData API with hardcoded key"""

import sys
sys.path.append('/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src')

from analysis.twelvedata_analyzer import TwelveDataAnalyzer

def test_twelvedata_api():
    print("🧪 Testing TwelveData API with hardcoded Pro 610 key...")

    try:
        analyzer = TwelveDataAnalyzer()
        print(f"📋 Using API key: {analyzer.api_key[:8]}...{analyzer.api_key[-4:]}")

        # Test real-time price
        print("\n📊 Testing MSFT real-time price...")
        result = analyzer.get_real_time_price('MSFT')
        print(f"Result: {result}")

        if result.get('success'):
            print(f"✅ SUCCESS! MSFT Price: ${result.get('price')}")
            print(f"📡 Data Source: {result.get('data_source')}")
        else:
            print(f"❌ FAILED: {result.get('error')}")
            return False

        # Test quote data
        print("\n📈 Testing MSFT quote data...")
        quote_result = analyzer.get_quote('MSFT')

        if quote_result.get('success'):
            print(f"✅ Quote SUCCESS! Current Price: ${quote_result.get('close')}")
            print(f"📊 52-week High: ${quote_result.get('fifty_two_week', {}).get('high', 'N/A')}")
            print(f"📊 52-week Low: ${quote_result.get('fifty_two_week', {}).get('low', 'N/A')}")
            print(f"📊 Volume: {quote_result.get('volume', 'N/A'):,}")
        else:
            print(f"❌ Quote FAILED: {quote_result.get('error')}")
            return False

        print("\n🎉 All TwelveData tests passed! API is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Error testing TwelveData API: {str(e)}")
        return False

if __name__ == "__main__":
    test_twelvedata_api()