#!/usr/bin/env python3
"""
Security Fix Validation Test
Tests that hardcoded API keys have been removed and environment variable is required
"""

import os
import sys
import tempfile
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

def test_security_fix():
    """Test that hardcoded API keys are removed and environment variable is required"""
    print("🔒 Testing TwelveData Security Fix")
    print("=" * 60)

    # Test 1: No environment variable should raise ValueError
    print("\n1. Testing without TWELVEDATA_API_KEY environment variable...")
    with temp_env_var('TWELVEDATA_API_KEY', None):
        try:
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer
            analyzer = TwelveDataAnalyzer()
            print("❌ SECURITY FAILURE: TwelveDataAnalyzer instantiated without API key!")
            return False
        except ValueError as e:
            if "TWELVEDATA_API_KEY environment variable is required" in str(e):
                print("✅ SUCCESS: Properly requires environment variable")
            else:
                print(f"❌ WRONG ERROR: {str(e)}")
                return False
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            return False

    # Test 2: With environment variable should work
    print("\n2. Testing with valid TWELVEDATA_API_KEY environment variable...")
    test_key = "test_key_1234567890abcdef1234567890abcdef"  # Mock 32-char key

    with temp_env_var('TWELVEDATA_API_KEY', test_key):
        try:
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer
            analyzer = TwelveDataAnalyzer()

            if analyzer.api_key == test_key:
                print("✅ SUCCESS: API key loaded from environment variable")
            else:
                print(f"❌ FAILURE: API key mismatch. Expected: {test_key}, Got: {analyzer.api_key}")
                return False

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

    # Test 3: Explicit API key parameter should work
    print("\n3. Testing with explicit API key parameter...")
    explicit_key = "explicit_key_1234567890abcdef1234567890"

    with temp_env_var('TWELVEDATA_API_KEY', None):
        try:
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer
            analyzer = TwelveDataAnalyzer(api_key=explicit_key)

            if analyzer.api_key == explicit_key:
                print("✅ SUCCESS: Explicit API key parameter works")
            else:
                print(f"❌ FAILURE: API key mismatch. Expected: {explicit_key}, Got: {analyzer.api_key}")
                return False

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

    # Test 4: Check that no hardcoded keys exist in source code
    print("\n4. Checking source code for hardcoded API keys...")

    files_to_check = [
        'analysis/twelvedata_analyzer.py',
        'analysis/twelvedata_analyzer_backup.py',
        'analysis/twelvedata_analyzer_fixed.py'
    ]

    hardcoded_key = "71cdbb03b46645628e8416eeb4836c99"
    base_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src"

    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
                if hardcoded_key in content:
                    print(f"❌ SECURITY FAILURE: Hardcoded key found in {file_path}")
                    return False
                else:
                    print(f"✅ SUCCESS: No hardcoded key in {file_path}")
        else:
            print(f"⚠️  WARNING: File {file_path} not found")

    print("\n" + "=" * 60)
    print("🎉 ALL SECURITY TESTS PASSED!")
    print("✅ Hardcoded API keys successfully removed")
    print("✅ Environment variable requirement enforced")
    print("✅ Proper error messages provided")

    return True

def test_initialization_robustness():
    """Test various initialization scenarios"""
    print("\n🔧 Testing Initialization Robustness")
    print("=" * 60)

    # Test invalid key formats
    test_cases = [
        ("", "Empty string"),
        ("short", "Too short key"),
        ("123", "Numeric only"),
        ("a" * 10, "Too short"),
        ("a" * 100, "Very long key")
    ]

    with temp_env_var('TWELVEDATA_API_KEY', None):
        for test_key, description in test_cases:
            print(f"\nTesting {description}: '{test_key}'")
            try:
                from analysis.twelvedata_analyzer import TwelveDataAnalyzer
                analyzer = TwelveDataAnalyzer(api_key=test_key)
                print(f"⚠️  WARNING: {description} was accepted (may be valid)")
            except ValueError as e:
                print(f"✅ EXPECTED: {description} rejected - {str(e)}")
            except Exception as e:
                print(f"❌ UNEXPECTED ERROR: {str(e)}")
                return False

    return True

if __name__ == "__main__":
    print("🚀 Starting TwelveData Security Fix Validation")
    print("Date:", sys.version)

    # Run security tests
    security_passed = test_security_fix()
    robustness_passed = test_initialization_robustness()

    if security_passed and robustness_passed:
        print("\n🎉 ALL TESTS PASSED - SECURITY FIX VALIDATED!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - SECURITY ISSUES REMAIN!")
        sys.exit(1)