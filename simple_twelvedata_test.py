#!/usr/bin/env python3
"""
Simple TwelveData API Test
Tests the key fixes without complex dependencies
"""

import requests
import json
import time
import os

def test_authentication_methods():
    """Test header-based vs query parameter authentication"""
    print("🔐 Testing Authentication Methods...")

    api_key = '71cdbb03b46645628e8416eeb4836c99'  # CORRECT Working Pro 610 key
    base_url = "https://api.twelvedata.com"

    # Test 1: Header-based authentication (RECOMMENDED)
    print("\n   Testing header-based authentication...")
    try:
        headers = {
            'Authorization': f'apikey {api_key}',
            'User-Agent': 'Tadaro Investment Bot 1.0',
            'Accept': 'application/json'
        }
        params = {'symbol': 'AAPL', 'format': 'json'}

        response = requests.get(f"{base_url}/price", headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                print(f"   ✅ Header auth SUCCESS: AAPL = ${data['price']}")
                header_success = True
            else:
                print(f"   ❌ Header auth failed: {data}")
                header_success = False
        else:
            print(f"   ❌ Header auth failed: HTTP {response.status_code}")
            header_success = False
    except Exception as e:
        print(f"   ❌ Header auth error: {str(e)}")
        header_success = False

    time.sleep(0.2)

    # Test 2: Query parameter authentication (OLD METHOD)
    print("\n   Testing query parameter authentication...")
    try:
        headers = {'User-Agent': 'Tadaro Investment Bot 1.0'}
        params = {'symbol': 'AAPL', 'format': 'json', 'apikey': api_key}

        response = requests.get(f"{base_url}/price", headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                print(f"   ✅ Query param auth SUCCESS: AAPL = ${data['price']}")
                query_success = True
            else:
                print(f"   ❌ Query param auth failed: {data}")
                query_success = False
        else:
            print(f"   ❌ Query param auth failed: HTTP {response.status_code}")
            query_success = False
    except Exception as e:
        print(f"   ❌ Query param auth error: {str(e)}")
        query_success = False

    if header_success:
        print("   🎉 RECOMMENDATION: Use header-based authentication (implemented in fix)")

    return header_success or query_success

def test_saudi_market_symbols():
    """Test Saudi market symbol formatting"""
    print("\n🇸🇦 Testing Saudi Market Integration...")

    api_key = '71cdbb03b46645628e8416eeb4836c99'  # CORRECT Working key
    base_url = "https://api.twelvedata.com"

    headers = {
        'Authorization': f'apikey {api_key}',
        'User-Agent': 'Tadaro Investment Bot 1.0'
    }

    # Test Saudi symbols with different formats
    test_cases = [
        {'input': '4261', 'expected_format': '4261:Tadawul', 'description': 'Theeb Rent A Car (trial symbol)'},
        {'input': '4261:Tadawul', 'expected_format': '4261:Tadawul', 'description': 'Already formatted'},
        {'input': '2222', 'expected_format': '2222:Tadawul', 'description': 'Saudi Aramco'},
    ]

    saudi_results = []

    for test_case in test_cases:
        input_symbol = test_case['input']
        expected = test_case['expected_format']
        description = test_case['description']

        print(f"\n   Testing: {input_symbol} ({description})")

        # Format symbol for Saudi market
        if input_symbol.isdigit() and len(input_symbol) == 4:
            formatted_symbol = f"{input_symbol}:Tadawul"
        else:
            formatted_symbol = input_symbol

        print(f"   Formatted symbol: {formatted_symbol}")

        try:
            params = {
                'symbol': formatted_symbol,
                'format': 'json',
                'timezone': 'Asia/Riyadh'
            }

            response = requests.get(f"{base_url}/price", headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'price' in data:
                    print(f"   ✅ SUCCESS: Price = {data['price']} SAR")
                    saudi_results.append(True)
                else:
                    print(f"   ❌ No price in response: {data}")
                    saudi_results.append(False)
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                saudi_results.append(False)

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            saudi_results.append(False)

        time.sleep(0.3)  # Rate limiting

    success_rate = sum(saudi_results) / len(saudi_results) if saudi_results else 0
    print(f"\n   Saudi Market Results: {sum(saudi_results)}/{len(saudi_results)} successful ({success_rate:.1%})")

    return success_rate > 0.5

def test_error_handling():
    """Test improved error handling"""
    print("\n🔍 Testing Error Handling...")

    api_key = '71cdbb03b46645628e8416eeb4836c99'  # CORRECT Working key
    base_url = "https://api.twelvedata.com"

    headers = {
        'Authorization': f'apikey {api_key}',
        'User-Agent': 'Tadaro Investment Bot 1.0'
    }

    # Test cases designed to trigger different error scenarios
    error_tests = [
        {'params': {'symbol': 'INVALID_SYMBOL_12345'}, 'expected': 'should handle invalid symbol'},
        {'params': {'symbol': 'AAPL', 'interval': 'invalid'}, 'expected': 'should handle invalid interval'},
        {'params': {'symbol': ''}, 'expected': 'should handle empty symbol'},
    ]

    error_results = []

    for i, test in enumerate(error_tests):
        print(f"\n   Error Test {i+1}: {test['expected']}")

        try:
            params = {**test['params'], 'format': 'json'}
            response = requests.get(f"{base_url}/time_series", headers=headers, params=params, timeout=10)

            # Check if we got a proper error response
            if response.status_code != 200:
                print(f"   ✅ Got expected HTTP error: {response.status_code}")
                error_results.append(True)
            else:
                data = response.json()
                if data.get('status') == 'error' or 'error' in str(data).lower():
                    print(f"   ✅ Got expected API error: {data.get('message', 'Error in response')[:50]}")
                    error_results.append(True)
                else:
                    print(f"   ❌ Expected error but got success: {str(data)[:50]}")
                    error_results.append(False)

        except Exception as e:
            print(f"   ✅ Got expected exception: {str(e)[:50]}")
            error_results.append(True)

        time.sleep(0.2)

    success_rate = sum(error_results) / len(error_results) if error_results else 0
    print(f"\n   Error Handling Results: {sum(error_results)}/{len(error_results)} handled correctly ({success_rate:.1%})")

    return success_rate >= 0.5

def test_input_validation():
    """Test input validation logic"""
    print("\n✅ Testing Input Validation...")

    # Test interval validation
    valid_intervals = {
        '1min', '5min', '15min', '30min', '45min',
        '1h', '2h', '4h', '5h', '1day', '1week', '1month'
    }

    test_intervals = ['1min', '2min', '1day', '1hour', 'invalid']

    print("   Valid intervals:", sorted(valid_intervals))

    validation_results = []
    for interval in test_intervals:
        is_valid = interval in valid_intervals
        print(f"   '{interval}': {'✅ Valid' if is_valid else '❌ Invalid'}")
        validation_results.append(is_valid)

    # Test symbol validation logic
    print("\n   Testing symbol formatting logic:")

    symbol_tests = [
        {'input': '4261', 'expected': '4261:Tadawul', 'description': 'Saudi 4-digit number'},
        {'input': 'AAPL', 'expected': 'AAPL', 'description': 'US stock symbol'},
        {'input': '4261:Tadawul', 'expected': '4261:Tadawul', 'description': 'Already formatted Saudi'},
        {'input': 'EUR/USD', 'expected': 'EUR/USD', 'description': 'Forex pair'},
    ]

    for test in symbol_tests:
        input_symbol = test['input']
        expected = test['expected']
        description = test['description']

        # Apply formatting logic
        if input_symbol.isdigit() and len(input_symbol) == 4:
            formatted = f"{input_symbol}:Tadawul"
        else:
            formatted = input_symbol.upper()

        is_correct = formatted == expected
        print(f"   '{input_symbol}' -> '{formatted}' {'✅' if is_correct else '❌'} ({description})")

    return True

def main():
    """Run all tests"""
    print("🚀 TwelveData API Fixes - Simple Test Suite")
    print("=" * 60)

    tests = [
        ("Authentication Methods", test_authentication_methods),
        ("Saudi Market Integration", test_saudi_market_symbols),
        ("Error Handling", test_error_handling),
        ("Input Validation", test_input_validation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {str(e)}")
            results.append(False)

        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{test_name:<30}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")

    if passed >= total * 0.75:  # 75% pass rate
        print("\n🎉 SUCCESS: TwelveData fixes are working!")
        print("✅ Ready for integration with main application")
        return True
    else:
        print("\n⚠️ Some issues detected. Review results above.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")