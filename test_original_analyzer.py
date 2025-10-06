#!/usr/bin/env python3
"""
Test the original (fixed) TwelveData analyzer
"""

import sys
sys.path.append('/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src')

# Simple test without pandas dependency
def simple_test():
    print("🧪 Testing Original TwelveData Analyzer (Fixed Version)")
    print("=" * 60)

    # Test without importing pandas/numpy to avoid environment issues
    try:
        from analysis.twelvedata_analyzer import TwelveDataAnalyzer
        print("✅ Successfully imported TwelveDataAnalyzer")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    try:
        # Initialize analyzer
        analyzer = TwelveDataAnalyzer()
        print(f"✅ Analyzer initialized with key: {analyzer.api_key[:8]}...{analyzer.api_key[-4:]}")

        # Test health check
        health = analyzer.health_check()
        print(f"Health check: {health.get('status')} - {health.get('message')}")

        # Test simple price fetch
        price_result = analyzer.get_real_time_price('AAPL')
        if price_result.get('success'):
            print(f"✅ AAPL Price: ${price_result.get('price')}")
        else:
            print(f"❌ Price fetch failed: {price_result.get('error')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = simple_test()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")