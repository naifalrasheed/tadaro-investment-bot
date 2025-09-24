#!/usr/bin/env python3
"""
Test to verify that weighted averaging has been completely eliminated
from data source comparison service
"""

import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_no_weighted_averaging():
    """Test that DataComparisonService uses priority-based selection only"""
    print("Testing DataComparisonService for weighted averaging elimination...")

    try:
        from data.data_comparison_service import DataComparisonService

        service = DataComparisonService()

        # Create mock data sources with different prices
        mock_sources = [
            {
                'symbol': 'MSFT',
                'current_price': 100.0,
                'data_source': 'yfinance',
                'success': True
            },
            {
                'symbol': 'MSFT',
                'current_price': 105.0,
                'data_source': 'alpha_vantage',
                'success': True
            },
            {
                'symbol': 'MSFT',
                'current_price': 102.0,
                'data_source': 'twelvedata',
                'success': True
            }
        ]

        print(f"Input sources:")
        for source in mock_sources:
            print(f"  - {source['data_source']}: ${source['current_price']}")

        # Test selection
        result = service.select_best_source(mock_sources)

        print(f"\nResult:")
        print(f"  - Selected source: {result.get('data_source')}")
        print(f"  - Selected price: ${result.get('current_price')}")
        print(f"  - Success: {result.get('success')}")

        # Verify no averaging occurred
        original_prices = [s['current_price'] for s in mock_sources]
        result_price = result.get('current_price')

        if result_price in original_prices:
            print("✅ SUCCESS: No weighted averaging - price matches one of the original sources")

            # Should select twelvedata (highest priority)
            if result.get('data_source') == 'twelvedata':
                print("✅ SUCCESS: Selected highest priority source (twelvedata)")
            else:
                print(f"⚠️  WARNING: Expected 'twelvedata' but got '{result.get('data_source')}'")

        else:
            print(f"❌ FAILED: Result price {result_price} is not from any original source")
            print("This suggests averaging is still occurring!")
            return False

        # Verify metadata
        if result.get('data_selection', {}).get('no_data_mixing'):
            print("✅ SUCCESS: Metadata confirms no data mixing")
        else:
            print("⚠️  WARNING: Metadata doesn't confirm no data mixing")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_legacy_method_redirect():
    """Test that legacy compare_and_select method redirects correctly"""
    print("\nTesting legacy method redirect...")

    try:
        from data.data_comparison_service import DataComparisonService

        service = DataComparisonService()

        mock_sources = [
            {
                'symbol': 'AAPL',
                'current_price': 150.0,
                'data_source': 'alpha_vantage',
                'success': True
            }
        ]

        # Test legacy method
        result = service.compare_and_select(mock_sources)

        if result.get('current_price') == 150.0:
            print("✅ SUCCESS: Legacy method works correctly")
            return True
        else:
            print("❌ FAILED: Legacy method not working")
            return False

    except Exception as e:
        print(f"❌ ERROR in legacy method test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WEIGHTED AVERAGING ELIMINATION TEST")
    print("=" * 60)

    test1_passed = test_no_weighted_averaging()
    test2_passed = test_legacy_method_redirect()

    print("\n" + "=" * 60)

    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED - Weighted averaging successfully eliminated!")
    else:
        print("❌ SOME TESTS FAILED - Review the output above")

    print("=" * 60)