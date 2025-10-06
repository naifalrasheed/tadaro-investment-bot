#!/usr/bin/env python3
"""
Saudi Symbol Validation Enhancement Test
Tests comprehensive Saudi market symbol formatting and validation
"""

import os
import sys
import time
from contextlib import contextmanager

# Add src to path for imports
sys.path.append('/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src')

@contextmanager
def temp_env_var(key, value):
    """Temporarily set an environment variable"""
    old_value = os.environ.get(key)
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value

    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value

def test_saudi_symbol_patterns():
    """Test that comprehensive Saudi symbol patterns are recognized"""
    print("🇸🇦 Testing Saudi Symbol Pattern Recognition")
    print("=" * 60)

    try:
        # Set a test API key
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            # Test cases for Saudi symbol validation
            test_cases = [
                # Format: (input_symbol, expected_output, test_description)
                ("4261", "4261:Tadawul", "4-digit pure number"),
                ("12345", "12345:Tadawul", "5-digit pure number"),
                ("2222A", "2222A:Tadawul", "4-digit + single letter"),
                ("1180B", "1180B:Tadawul", "4-digit + single letter variant"),
                ("4260AB", "4260AB:Tadawul", "4-digit + multiple letters"),
                ("4261.SAU", "4261:Tadawul", ".SAU format conversion"),
                ("4261:Tadawul", "4261:Tadawul", "Already formatted (uppercase)"),
                ("4261:tadawul", "4261:TADAWUL", "Already formatted (lowercase)"),
                ("AAPL", "AAPL", "US stock (should not change)"),
                ("MSFT", "MSFT", "US stock (should not change)"),
                ("TSLA", "TSLA", "US stock (should not change)"),
                ("12", "12", "Too short for Saudi format"),
                ("123", "123", "Too short for Saudi format"),
                ("ABCD", "ABCD", "Pure letters (not Saudi)"),
            ]

            passed_tests = 0
            failed_tests = 0

            print("Testing symbol validation patterns:")
            print("-" * 60)

            for input_symbol, expected, description in test_cases:
                try:
                    result = analyzer._validate_symbol(input_symbol)

                    if result == expected:
                        print(f"✅ {description:<35} '{input_symbol}' -> '{result}'")
                        passed_tests += 1
                    else:
                        print(f"❌ {description:<35} '{input_symbol}' -> '{result}' (expected '{expected}')")
                        failed_tests += 1

                except Exception as e:
                    print(f"💥 {description:<35} '{input_symbol}' -> ERROR: {str(e)}")
                    failed_tests += 1

            # Test individual Saudi symbol detection
            print(f"\n🔍 Testing _is_saudi_symbol() method:")
            print("-" * 60)

            saudi_detection_cases = [
                ("4261", True, "4-digit number"),
                ("12345", True, "5-digit number"),
                ("2222A", True, "4-digit + letter"),
                ("1180BC", True, "4-digit + multiple letters"),
                ("AAPL", False, "US ticker"),
                ("12", False, "Too short"),
                ("ABC123", False, "Letters first"),
                ("4261:Tadawul", False, "Already formatted (should not detect)"),
            ]

            saudi_passed = 0
            saudi_failed = 0

            for symbol, expected_is_saudi, description in saudi_detection_cases:
                try:
                    is_saudi = analyzer._is_saudi_symbol(symbol)

                    if is_saudi == expected_is_saudi:
                        print(f"✅ {description:<35} '{symbol}' -> {is_saudi}")
                        saudi_passed += 1
                    else:
                        print(f"❌ {description:<35} '{symbol}' -> {is_saudi} (expected {expected_is_saudi})")
                        saudi_failed += 1

                except Exception as e:
                    print(f"💥 {description:<35} '{symbol}' -> ERROR: {str(e)}")
                    saudi_failed += 1

            # Summary
            total_tests = passed_tests + failed_tests + saudi_passed + saudi_failed
            total_passed = passed_tests + saudi_passed

            print(f"\n📊 SAUDI SYMBOL VALIDATION SUMMARY:")
            print(f"   Symbol Formatting Tests: {passed_tests}/{passed_tests + failed_tests} passed")
            print(f"   Saudi Detection Tests:   {saudi_passed}/{saudi_passed + saudi_failed} passed")
            print(f"   Overall:                 {total_passed}/{total_tests} passed")

            return total_passed == total_tests

    except Exception as e:
        print(f"❌ Error during Saudi symbol testing: {str(e)}")
        return False

def test_regex_patterns():
    """Test that regex patterns work correctly"""
    print("\n🔍 Testing Regex Pattern Validation")
    print("=" * 60)

    try:
        import re

        # Test the patterns directly
        patterns = [
            r'^[0-9]{4}[A-Z]$',  # 4 digits + 1 letter
            r'^[0-9]{4}[A-Z][0-9]$',  # 4 digits + letter + digit
        ]

        test_cases = [
            ("2222A", patterns[0], True, "4 digits + letter"),
            ("1180B", patterns[0], True, "4 digits + letter variant"),
            ("4261C", patterns[0], True, "4 digits + letter (C)"),
            ("22222A", patterns[0], False, "5 digits + letter (should not match pattern 1)"),
            ("2222AB", patterns[0], False, "4 digits + 2 letters (should not match pattern 1)"),
            ("2222A1", patterns[1], True, "4 digits + letter + digit"),
            ("1180B2", patterns[1], True, "4 digits + letter + digit variant"),
            ("2222A", patterns[1], False, "4 digits + letter only (should not match pattern 2)"),
        ]

        passed_regex = 0
        failed_regex = 0

        print("Testing individual regex patterns:")
        print("-" * 60)

        for test_symbol, pattern, should_match, description in test_cases:
            try:
                matches = bool(re.match(pattern, test_symbol))

                if matches == should_match:
                    print(f"✅ {description:<40} '{test_symbol}' -> {matches}")
                    passed_regex += 1
                else:
                    print(f"❌ {description:<40} '{test_symbol}' -> {matches} (expected {should_match})")
                    failed_regex += 1

            except Exception as e:
                print(f"💥 {description:<40} '{test_symbol}' -> ERROR: {str(e)}")
                failed_regex += 1

        print(f"\n📊 REGEX PATTERN SUMMARY:")
        print(f"   Regex Tests: {passed_regex}/{passed_regex + failed_regex} passed")

        return passed_regex == (passed_regex + failed_regex)

    except Exception as e:
        print(f"❌ Error during regex testing: {str(e)}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n⚠️ Testing Edge Cases and Error Handling")
    print("=" * 60)

    try:
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            edge_cases = [
                # Format: (input, expected_behavior, description)
                ("", "ValueError", "Empty string"),
                (None, "ValueError", "None input"),
                ("   ", "ValueError after strip", "Whitespace only"),
                ("4261   ", "4261:Tadawul", "Trailing whitespace"),
                ("   4261", "4261:Tadawul", "Leading whitespace"),
                ("  4261  ", "4261:Tadawul", "Leading and trailing whitespace"),
                ("4261:TADAWUL", "4261:TADAWUL", "Already formatted (exact case)"),
                ("4261:tadawul", "4261:TADAWUL", "Already formatted (lowercase)"),
                ("4261.sau", "4261:Tadawul", "SAU format (lowercase)"),
                ("4261.SAU", "4261:Tadawul", "SAU format (uppercase)"),
            ]

            edge_passed = 0
            edge_failed = 0

            print("Testing edge cases:")
            print("-" * 60)

            for input_val, expected_behavior, description in edge_cases:
                try:
                    if expected_behavior == "ValueError":
                        # Should raise ValueError
                        try:
                            result = analyzer._validate_symbol(input_val)
                            print(f"❌ {description:<40} No exception raised (got '{result}')")
                            edge_failed += 1
                        except ValueError:
                            print(f"✅ {description:<40} Correctly raised ValueError")
                            edge_passed += 1
                        except Exception as e:
                            print(f"❌ {description:<40} Wrong exception: {type(e).__name__}")
                            edge_failed += 1
                    elif expected_behavior == "ValueError after strip":
                        # Should raise ValueError after stripping
                        try:
                            result = analyzer._validate_symbol(input_val)
                            print(f"❌ {description:<40} No exception raised (got '{result}')")
                            edge_failed += 1
                        except ValueError:
                            print(f"✅ {description:<40} Correctly raised ValueError")
                            edge_passed += 1
                    else:
                        # Should return expected result
                        result = analyzer._validate_symbol(input_val)
                        if result == expected_behavior:
                            print(f"✅ {description:<40} '{input_val}' -> '{result}'")
                            edge_passed += 1
                        else:
                            print(f"❌ {description:<40} '{input_val}' -> '{result}' (expected '{expected_behavior}')")
                            edge_failed += 1

                except Exception as e:
                    print(f"💥 {description:<40} Unexpected error: {str(e)}")
                    edge_failed += 1

            print(f"\n📊 EDGE CASE SUMMARY:")
            print(f"   Edge Case Tests: {edge_passed}/{edge_passed + edge_failed} passed")

            return edge_passed == (edge_passed + edge_failed)

    except Exception as e:
        print(f"❌ Error during edge case testing: {str(e)}")
        return False

def test_backward_compatibility():
    """Test that existing functionality still works"""
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 60)

    try:
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            # Test that old functionality still works
            backward_cases = [
                ("AAPL", "AAPL", "US stock unchanged"),
                ("MSFT", "MSFT", "Another US stock unchanged"),
                ("BTC-USD", "BTC-USD", "Crypto unchanged"),
                ("SPY", "SPY", "ETF unchanged"),
                ("4261", "4261:Tadawul", "Original 4-digit Saudi (should still work)"),
            ]

            backward_passed = 0
            backward_failed = 0

            print("Testing backward compatibility:")
            print("-" * 60)

            for input_symbol, expected, description in backward_cases:
                try:
                    result = analyzer._validate_symbol(input_symbol)

                    if result == expected:
                        print(f"✅ {description:<35} '{input_symbol}' -> '{result}'")
                        backward_passed += 1
                    else:
                        print(f"❌ {description:<35} '{input_symbol}' -> '{result}' (expected '{expected}')")
                        backward_failed += 1

                except Exception as e:
                    print(f"💥 {description:<35} '{input_symbol}' -> ERROR: {str(e)}")
                    backward_failed += 1

            print(f"\n📊 BACKWARD COMPATIBILITY SUMMARY:")
            print(f"   Compatibility Tests: {backward_passed}/{backward_passed + backward_failed} passed")

            return backward_passed == (backward_passed + backward_failed)

    except Exception as e:
        print(f"❌ Error during backward compatibility testing: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Saudi Symbol Validation Enhancement Test")
    print("Testing comprehensive Saudi market symbol formatting and validation")
    print("Date:", time.strftime('%Y-%m-%d %H:%M:%S UTC'))
    print()

    # Run all Saudi symbol validation tests
    tests = [
        ("Saudi Symbol Patterns", test_saudi_symbol_patterns),
        ("Regex Pattern Validation", test_regex_patterns),
        ("Edge Cases and Error Handling", test_edge_cases),
        ("Backward Compatibility", test_backward_compatibility)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*70}")

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")

        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))

    # Final summary
    print(f"\n{'='*70}")
    print("📊 SAUDI SYMBOL VALIDATION TEST RESULTS SUMMARY")
    print(f"{'='*70}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL SAUDI SYMBOL VALIDATION TESTS PASSED!")
        print("✅ 4-digit Saudi symbols supported")
        print("✅ 5-digit Saudi symbols supported")
        print("✅ Alphanumeric Saudi symbols supported")
        print("✅ .SAU format conversion working")
        print("✅ Already formatted symbols handled")
        print("✅ Edge cases and error handling robust")
        print("✅ Backward compatibility maintained")
        print("✅ Ready for comprehensive Saudi market integration")
        sys.exit(0)
    else:
        print("\n❌ SOME SAUDI SYMBOL VALIDATION TESTS FAILED!")
        print("Saudi symbol validation implementation needs review")
        sys.exit(1)