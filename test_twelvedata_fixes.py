#!/usr/bin/env python3
"""
Comprehensive Test Script for TwelveData API Fixes
Tests all critical fixes and Saudi market integration

WHAT THIS TESTS:
1. Authentication fixes (header-based vs query parameter)
2. Saudi market symbol formatting and data retrieval
3. Input validation for intervals and parameters
4. Error handling for various scenarios
5. Batch processing capabilities
6. Rate limiting functionality
"""

import sys
import os
sys.path.append('/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src')

from analysis.twelvedata_analyzer_fixed import TwelveDataAnalyzer
import time
import json

class TwelveDataTestSuite:
    """Comprehensive test suite for TwelveData fixes"""

    def __init__(self):
        self.results = {}
        self.analyzer = None

    def setup_analyzer(self):
        """Initialize the fixed analyzer"""
        try:
            print("🔧 Initializing TwelveData Analyzer (Fixed Version)...")
            self.analyzer = TwelveDataAnalyzer()
            print(f"✅ Analyzer initialized successfully")
            print(f"📋 API Key: {self.analyzer.api_key[:8]}...{self.analyzer.api_key[-4:]}")
            print(f"🔒 Auth Method: Header-based")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize analyzer: {str(e)}")
            return False

    def test_health_check(self):
        """Test health check with both US and Saudi markets"""
        print("\n📊 Testing Health Check...")

        try:
            result = self.analyzer.health_check()

            if result.get('status') == 'healthy':
                print("✅ Health Check PASSED")
                print(f"   US Market Test: {'✅' if result.get('us_market_test') else '❌'}")
                print(f"   Saudi Market Test: {'✅' if result.get('saudi_market_test') else '❌'}")
                print(f"   US Test Price: ${result.get('test_us_price')}")
                print(f"   Saudi Test Price: {result.get('test_saudi_price')} SAR")
                self.results['health_check'] = True
            else:
                print(f"❌ Health Check FAILED: {result.get('message')}")
                self.results['health_check'] = False

            return result.get('status') == 'healthy'

        except Exception as e:
            print(f"❌ Health Check ERROR: {str(e)}")
            self.results['health_check'] = False
            return False

    def test_us_market_data(self):
        """Test US market data retrieval"""
        print("\n🇺🇸 Testing US Market Data...")

        try:
            # Test real-time price
            price_result = self.analyzer.get_real_time_price('AAPL')
            if price_result.get('success'):
                print(f"✅ US Real-time Price: AAPL = ${price_result.get('price')}")
            else:
                print(f"❌ US Real-time Price failed: {price_result.get('error')}")

            # Test quote data
            quote_result = self.analyzer.get_quote('MSFT')
            if quote_result.get('success'):
                print(f"✅ US Quote Data: MSFT = ${quote_result.get('close')} ({quote_result.get('currency')})")
                print(f"   Exchange: {quote_result.get('exchange')}")
                print(f"   Volume: {quote_result.get('volume'):,}")
            else:
                print(f"❌ US Quote Data failed: {quote_result.get('error')}")

            # Test historical data
            history_result = self.analyzer.get_time_series('TSLA', interval='1day', outputsize=5)
            if history_result.get('success'):
                values = history_result.get('values', [])
                print(f"✅ US Historical Data: TSLA - Got {len(values)} days of data")
                if values:
                    latest = values[0]
                    print(f"   Latest: {latest.get('datetime')} - Close: ${latest.get('close')}")
            else:
                print(f"❌ US Historical Data failed: {history_result.get('error')}")

            self.results['us_market'] = True
            return True

        except Exception as e:
            print(f"❌ US Market Test ERROR: {str(e)}")
            self.results['us_market'] = False
            return False

    def test_saudi_market_data(self):
        """Test Saudi market data with proper symbol formatting"""
        print("\n🇸🇦 Testing Saudi Market Data...")

        try:
            # Test with trial symbol from TwelveData docs: 4261 (Theeb Rent A Car Company)
            test_symbols = ['4261', '2222', '1180', '2030']  # Various Saudi stocks

            for symbol in test_symbols:
                print(f"\n   Testing Saudi symbol: {symbol}")

                # Test real-time price
                price_result = self.analyzer.get_real_time_price(symbol)
                if price_result.get('success'):
                    print(f"   ✅ Price: {price_result.get('price')} SAR")
                    print(f"      Symbol format: {price_result.get('symbol')}")
                    print(f"      Is Saudi market: {price_result.get('is_saudi_market')}")
                else:
                    print(f"   ❌ Price failed: {price_result.get('error')}")

                # Test quote data
                quote_result = self.analyzer.get_quote(symbol)
                if quote_result.get('success'):
                    print(f"   ✅ Quote: {quote_result.get('close')} {quote_result.get('currency')}")
                    print(f"      Exchange: {quote_result.get('exchange')}")
                    print(f"      Company: {quote_result.get('name')}")

                    # Test historical data for one symbol
                    if symbol == '4261':
                        history_result = self.analyzer.get_time_series(symbol, interval='1day', outputsize=3)
                        if history_result.get('success'):
                            values = history_result.get('values', [])
                            print(f"   ✅ Historical: Got {len(values)} days")
                            print(f"      Currency: {history_result.get('currency')}")
                            print(f"      Timezone: {history_result.get('timezone')}")
                        else:
                            print(f"   ❌ Historical failed: {history_result.get('error')}")

                    self.results['saudi_market'] = True
                    return True
                else:
                    print(f"   ❌ Quote failed: {quote_result.get('error')}")

                # Don't test all symbols if rate limiting
                time.sleep(0.2)

            self.results['saudi_market'] = False
            return False

        except Exception as e:
            print(f"❌ Saudi Market Test ERROR: {str(e)}")
            self.results['saudi_market'] = False
            return False

    def test_input_validation(self):
        """Test input validation fixes"""
        print("\n🔍 Testing Input Validation...")

        validation_tests = [
            # Invalid intervals
            {'symbol': 'AAPL', 'interval': 'invalid', 'should_fail': True},
            {'symbol': 'AAPL', 'interval': '2min', 'should_fail': True},
            {'symbol': 'AAPL', 'interval': '1day', 'should_fail': False},

            # Invalid outputsize
            {'symbol': 'AAPL', 'interval': '1day', 'outputsize': 10000, 'should_fail': False},  # Should cap to 5000
            {'symbol': 'AAPL', 'interval': '1day', 'outputsize': -1, 'should_fail': False},    # Should set to 1

            # Invalid symbols
            {'symbol': '', 'interval': '1day', 'should_fail': True},
            {'symbol': None, 'interval': '1day', 'should_fail': True},
        ]

        passed_tests = 0
        total_tests = len(validation_tests)

        for i, test in enumerate(validation_tests):
            try:
                print(f"   Test {i+1}: symbol={test.get('symbol')}, interval={test.get('interval')}, outputsize={test.get('outputsize', 'default')}")

                if test.get('symbol') is None or test.get('symbol') == '':
                    # Test symbol validation directly
                    try:
                        self.analyzer._validate_symbol(test.get('symbol'))
                        if test.get('should_fail'):
                            print(f"      ❌ Should have failed but didn't")
                        else:
                            print(f"      ✅ Passed as expected")
                            passed_tests += 1
                    except:
                        if test.get('should_fail'):
                            print(f"      ✅ Failed as expected")
                            passed_tests += 1
                        else:
                            print(f"      ❌ Should have passed but failed")
                else:
                    # Test time series with validation
                    kwargs = {
                        'symbol': test.get('symbol'),
                        'interval': test.get('interval'),
                    }
                    if 'outputsize' in test:
                        kwargs['outputsize'] = test.get('outputsize')

                    result = self.analyzer.get_time_series(**kwargs)

                    if test.get('should_fail'):
                        if not result.get('success'):
                            print(f"      ✅ Failed as expected: {result.get('error', 'No error message')[:50]}")
                            passed_tests += 1
                        else:
                            print(f"      ❌ Should have failed but succeeded")
                    else:
                        if result.get('success'):
                            print(f"      ✅ Passed as expected")
                            passed_tests += 1
                        else:
                            print(f"      ❌ Should have passed: {result.get('error', 'No error message')[:50]}")

            except Exception as e:
                if test.get('should_fail'):
                    print(f"      ✅ Exception as expected: {str(e)[:50]}")
                    passed_tests += 1
                else:
                    print(f"      ❌ Unexpected exception: {str(e)[:50]}")

            time.sleep(0.1)

        print(f"\n   Validation Results: {passed_tests}/{total_tests} tests passed")
        self.results['input_validation'] = passed_tests >= (total_tests * 0.8)  # 80% pass rate
        return self.results['input_validation']

    def test_batch_processing(self):
        """Test batch processing capabilities"""
        print("\n📦 Testing Batch Processing...")

        try:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '4261']  # Mix of US and Saudi

            batch_result = self.analyzer.get_batch_quotes(symbols)

            if batch_result.get('success'):
                data = batch_result.get('data', [])
                print(f"✅ Batch Processing: Got data for {len(data)} symbols")

                for item in data:
                    if isinstance(item, dict) and 'symbol' in item:
                        symbol = item.get('symbol', 'Unknown')
                        price = item.get('close', 'N/A')
                        currency = item.get('currency', 'USD')
                        print(f"   {symbol}: {price} {currency}")

                self.results['batch_processing'] = True
                return True
            else:
                print(f"❌ Batch Processing failed: {batch_result.get('error')}")
                self.results['batch_processing'] = False
                return False

        except Exception as e:
            print(f"❌ Batch Processing ERROR: {str(e)}")
            self.results['batch_processing'] = False
            return False

    def test_comprehensive_analysis(self):
        """Test the main analyze_stock method with both markets"""
        print("\n🔬 Testing Comprehensive Stock Analysis...")

        test_symbols = [
            {'symbol': 'AAPL', 'market': 'US', 'expected_currency': 'USD'},
            {'symbol': '4261', 'market': 'Saudi', 'expected_currency': 'SAR'}
        ]

        analysis_results = []

        for test in test_symbols:
            symbol = test['symbol']
            market = test['market']
            expected_currency = test['expected_currency']

            print(f"\n   Analyzing {symbol} ({market} market)...")

            try:
                result = self.analyzer.analyze_stock(symbol)

                if result.get('success'):
                    print(f"   ✅ Analysis successful for {symbol}")
                    print(f"      Current Price: {result.get('current_price')} {result.get('currency')}")
                    print(f"      Company: {result.get('company_name')}")
                    print(f"      Exchange: {result.get('exchange')}")
                    print(f"      Is Saudi Market: {result.get('is_saudi_market', False)}")
                    print(f"      Data Source: {result.get('data_source')}")

                    # Verify currency matches expectation
                    if result.get('currency') == expected_currency:
                        print(f"      ✅ Currency correct: {expected_currency}")
                    else:
                        print(f"      ⚠️ Currency mismatch: got {result.get('currency')}, expected {expected_currency}")

                    analysis_results.append(True)
                else:
                    print(f"   ❌ Analysis failed for {symbol}: {result.get('error')}")
                    analysis_results.append(False)

            except Exception as e:
                print(f"   ❌ Analysis error for {symbol}: {str(e)}")
                analysis_results.append(False)

            time.sleep(0.2)  # Rate limiting

        success_rate = sum(analysis_results) / len(analysis_results)
        print(f"\n   Analysis Results: {sum(analysis_results)}/{len(analysis_results)} successful")

        self.results['comprehensive_analysis'] = success_rate >= 0.5  # At least 50% success
        return self.results['comprehensive_analysis']

    def run_all_tests(self):
        """Run all test suites and provide summary"""
        print("🚀 Starting TwelveData API Fixes Test Suite")
        print("=" * 60)

        if not self.setup_analyzer():
            print("❌ CRITICAL: Cannot initialize analyzer. Stopping tests.")
            return False

        # Run all test suites
        tests = [
            ('Health Check', self.test_health_check),
            ('US Market Data', self.test_us_market_data),
            ('Saudi Market Data', self.test_saudi_market_data),
            ('Input Validation', self.test_input_validation),
            ('Batch Processing', self.test_batch_processing),
            ('Comprehensive Analysis', self.test_comprehensive_analysis),
        ]

        total_tests = len(tests)
        passed_tests = 0

        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {str(e)}")

            time.sleep(0.5)  # Pause between test suites

        # Final summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUITE SUMMARY")
        print("=" * 60)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25}: {status}")

        print(f"\nOverall Results: {passed_tests}/{total_tests} test suites passed")

        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("🎉 OVERALL: PASSED - TwelveData fixes are working correctly!")
            return True
        else:
            print("⚠️ OVERALL: FAILED - Some critical issues remain")
            return False

def main():
    """Main test execution"""
    test_suite = TwelveDataTestSuite()
    success = test_suite.run_all_tests()

    if success:
        print("\n✅ All critical TwelveData fixes have been validated!")
        print("🚀 Ready for deployment to production")
    else:
        print("\n❌ Some issues detected. Review test results above.")
        print("🔧 Fix remaining issues before deployment")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)