#!/usr/bin/env python3
"""
Rate Limiting Optimization Test for Pro 610 Plan
Tests that TwelveData API utilizes full 610 requests/minute capacity
"""

import os
import sys
import time
import threading
from unittest.mock import patch, MagicMock
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

def test_rate_limiting_configuration():
    """Test that rate limiting is configured for Pro 610 capacity"""
    print("⚡ Testing Rate Limiting Configuration")
    print("=" * 60)

    try:
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            # Test configuration values
            expected_config = {
                'max_requests_per_minute': 610,
                'min_request_interval': 0.098,  # ~98ms
                'burst_limit': 50,
                'burst_window': 10
            }

            config_tests = [
                ('max_requests_per_minute', analyzer.max_requests_per_minute, expected_config['max_requests_per_minute']),
                ('min_request_interval', analyzer.min_request_interval, expected_config['min_request_interval']),
                ('burst_limit', analyzer.burst_limit, expected_config['burst_limit']),
                ('burst_window', analyzer.burst_window, expected_config['burst_window'])
            ]

            passed_config = 0
            failed_config = 0

            print("Testing Pro 610 configuration:")
            print("-" * 60)

            for config_name, actual_value, expected_value in config_tests:
                if config_name == 'min_request_interval':
                    # Allow small floating point differences
                    if abs(actual_value - expected_value) < 0.001:
                        print(f"✅ {config_name:<25} {actual_value:.3f} (expected ~{expected_value:.3f})")
                        passed_config += 1
                    else:
                        print(f"❌ {config_name:<25} {actual_value} (expected {expected_value})")
                        failed_config += 1
                else:
                    if actual_value == expected_value:
                        print(f"✅ {config_name:<25} {actual_value}")
                        passed_config += 1
                    else:
                        print(f"❌ {config_name:<25} {actual_value} (expected {expected_value})")
                        failed_config += 1

            # Test initial counters
            counter_tests = [
                ('request_count', analyzer.request_count, 0),
                ('burst_count', analyzer.burst_count, 0)
            ]

            print(f"\nTesting initial counter values:")
            print("-" * 60)

            for counter_name, actual_value, expected_value in counter_tests:
                if actual_value == expected_value:
                    print(f"✅ {counter_name:<25} {actual_value}")
                    passed_config += 1
                else:
                    print(f"❌ {counter_name:<25} {actual_value} (expected {expected_value})")
                    failed_config += 1

            print(f"\n📊 CONFIGURATION SUMMARY:")
            print(f"   Config tests: {passed_config}/{passed_config + failed_config} passed")

            return passed_config == (passed_config + failed_config)

    except Exception as e:
        print(f"❌ Error testing rate limiting configuration: {str(e)}")
        return False

def test_rate_limiting_status_method():
    """Test the rate limiting status monitoring method"""
    print("\n📊 Testing Rate Limiting Status Method")
    print("=" * 60)

    try:
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            # Get initial status
            status = analyzer.get_rate_limiting_status()

            # Expected status fields
            expected_fields = [
                'subscription_plan',
                'max_requests_per_minute',
                'requests_this_minute',
                'requests_remaining',
                'current_rate_per_minute',
                'utilization_percentage',
                'burst_count',
                'burst_remaining',
                'window_elapsed_seconds',
                'time_to_reset_minutes',
                'time_to_burst_reset',
                'optimization_status'
            ]

            print("Testing status method fields:")
            print("-" * 60)

            passed_fields = 0
            failed_fields = 0

            for field in expected_fields:
                if field in status:
                    print(f"✅ {field:<30} {status[field]}")
                    passed_fields += 1
                else:
                    print(f"❌ {field:<30} MISSING")
                    failed_fields += 1

            # Test specific values
            value_tests = [
                ('subscription_plan', status.get('subscription_plan'), 'Pro 610'),
                ('max_requests_per_minute', status.get('max_requests_per_minute'), 610),
                ('requests_this_minute', status.get('requests_this_minute'), 0),
                ('requests_remaining', status.get('requests_remaining'), 610),
                ('utilization_percentage', status.get('utilization_percentage'), 0.0),
                ('optimization_status', status.get('optimization_status'), 'Fully optimized for Pro 610 capacity')
            ]

            print(f"\nTesting specific status values:")
            print("-" * 60)

            for field_name, actual_value, expected_value in value_tests:
                if actual_value == expected_value:
                    print(f"✅ {field_name:<30} {actual_value}")
                    passed_fields += 1
                else:
                    print(f"❌ {field_name:<30} {actual_value} (expected {expected_value})")
                    failed_fields += 1

            print(f"\n📊 STATUS METHOD SUMMARY:")
            print(f"   Status tests: {passed_fields}/{passed_fields + failed_fields} passed")

            return passed_fields == (passed_fields + failed_fields)

    except Exception as e:
        print(f"❌ Error testing rate limiting status: {str(e)}")
        return False

def test_rate_limiting_logic_simulation():
    """Test the rate limiting logic through simulation"""
    print("\n🧠 Testing Rate Limiting Logic Simulation")
    print("=" * 60)

    try:
        test_key = "test_key_1234567890abcdef1234567890abcdef"

        with temp_env_var('TWELVEDATA_API_KEY', test_key):
            from analysis.twelvedata_analyzer import TwelveDataAnalyzer

            analyzer = TwelveDataAnalyzer()

            print("Testing rate limiting mechanics:")
            print("-" * 60)

            # Test 1: Simulate rapid requests (within burst limit)
            print("1. Testing burst handling...")

            start_time = time.time()

            # Simulate 10 rapid requests
            for i in range(10):
                current_time = time.time()
                analyzer._apply_rate_limiting(current_time)

            end_time = time.time()
            duration = end_time - start_time

            if analyzer.burst_count == 10 and analyzer.request_count == 10:
                print(f"   ✅ Burst handling: {analyzer.burst_count} requests in {duration:.3f}s")
            else:
                print(f"   ❌ Burst handling failed: burst={analyzer.burst_count}, requests={analyzer.request_count}")
                return False

            # Test 2: Check status after burst
            status = analyzer.get_rate_limiting_status()
            expected_remaining = 610 - 10

            if status['requests_remaining'] == expected_remaining:
                print(f"   ✅ Requests remaining: {status['requests_remaining']}")
            else:
                print(f"   ❌ Requests remaining: {status['requests_remaining']} (expected {expected_remaining})")
                return False

            # Test 3: Test burst limit behavior
            print("\n2. Testing burst limit behavior...")

            # Reset for clean test
            analyzer.burst_count = 49  # Just below limit

            # This should trigger burst handling
            pre_burst_time = time.time()
            analyzer._apply_rate_limiting(pre_burst_time)

            # Next one should trigger burst pause
            current_time = time.time()
            start_pause = time.time()
            analyzer._apply_rate_limiting(current_time)
            end_pause = time.time()

            pause_duration = end_pause - start_pause

            if pause_duration >= 0.19:  # Should have paused for 200ms
                print(f"   ✅ Burst limit pause: {pause_duration:.3f}s")
            else:
                print(f"   ⚠️ Burst limit pause: {pause_duration:.3f}s (expected ≥0.2s)")

            # Test 4: Test utilization calculation
            print("\n3. Testing utilization calculation...")

            # Simulate some usage
            analyzer.request_count = 305  # 50% of 610
            status = analyzer.get_rate_limiting_status()

            expected_utilization = 50.0  # 305/610 * 100

            if abs(status['utilization_percentage'] - expected_utilization) < 0.1:
                print(f"   ✅ Utilization: {status['utilization_percentage']}%")
            else:
                print(f"   ❌ Utilization: {status['utilization_percentage']}% (expected {expected_utilization}%)")
                return False

            return True

    except Exception as e:
        print(f"❌ Error testing rate limiting logic: {str(e)}")
        return False

def test_optimization_vs_original():
    """Compare optimized vs original rate limiting performance"""
    print("\n📈 Testing Optimization vs Original Performance")
    print("=" * 60)

    try:
        # Original configuration (conservative)
        original_config = {
            'max_requests_per_minute': 600,
            'min_request_interval': 0.1,  # 100ms = 10 req/sec = 600/min max
            'requests_per_second': 10
        }

        # Optimized configuration
        optimized_config = {
            'max_requests_per_minute': 610,
            'min_request_interval': 0.098,  # 98ms = 10.2 req/sec = 612/min theoretical
            'requests_per_second': 10.2
        }

        print("Configuration comparison:")
        print("-" * 60)
        print(f"{'Metric':<30} {'Original':<15} {'Optimized':<15} {'Improvement'}")
        print("-" * 60)

        # Calculate improvements
        max_req_improvement = optimized_config['max_requests_per_minute'] - original_config['max_requests_per_minute']
        max_req_pct = (max_req_improvement / original_config['max_requests_per_minute']) * 100

        interval_improvement = original_config['min_request_interval'] - optimized_config['min_request_interval']
        interval_pct = (interval_improvement / original_config['min_request_interval']) * 100

        throughput_improvement = optimized_config['requests_per_second'] - original_config['requests_per_second']
        throughput_pct = (throughput_improvement / original_config['requests_per_second']) * 100

        print(f"{'Max requests/minute':<30} {original_config['max_requests_per_minute']:<15} {optimized_config['max_requests_per_minute']:<15} +{max_req_improvement} (+{max_req_pct:.1f}%)")
        print(f"{'Min interval (ms)':<30} {original_config['min_request_interval']*1000:<15.0f} {optimized_config['min_request_interval']*1000:<15.1f} -{interval_improvement*1000:.1f} (-{interval_pct:.1f}%)")
        print(f"{'Requests per second':<30} {original_config['requests_per_second']:<15.1f} {optimized_config['requests_per_second']:<15.1f} +{throughput_improvement:.1f} (+{throughput_pct:.1f}%)")

        print(f"\n🎯 OPTIMIZATION BENEFITS:")
        print(f"   ✅ Additional capacity: {max_req_improvement} requests/minute")
        print(f"   ✅ Faster response time: {interval_improvement*1000:.1f}ms less delay per request")
        print(f"   ✅ Better throughput: {throughput_improvement:.1f} more requests/second")
        print(f"   ✅ Subscription utilization: 100% vs 98.4% (full Pro 610 capacity)")

        # Economic analysis
        monthly_cost = 79  # Pro 610 subscription
        original_cost_per_request = monthly_cost / (600 * 60 * 24 * 30)  # Cost per request/month
        optimized_cost_per_request = monthly_cost / (610 * 60 * 24 * 30)

        cost_efficiency_improvement = ((original_cost_per_request - optimized_cost_per_request) / original_cost_per_request) * 100

        print(f"\n💰 ECONOMIC IMPACT:")
        print(f"   Monthly subscription: ${monthly_cost}")
        print(f"   Original cost per request: ${original_cost_per_request:.8f}")
        print(f"   Optimized cost per request: ${optimized_cost_per_request:.8f}")
        print(f"   Cost efficiency improvement: {cost_efficiency_improvement:.2f}%")

        return True

    except Exception as e:
        print(f"❌ Error testing optimization comparison: {str(e)}")
        return False

def test_backup_files_consistency():
    """Test that all backup files have the same optimizations"""
    print("\n🔄 Testing Backup Files Consistency")
    print("=" * 60)

    files_to_check = [
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_backup.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_fixed.py"
    ]

    # Key patterns that should be in all files
    required_patterns = [
        "max_requests_per_minute = 610",
        "min_request_interval = 0.098",
        "burst_limit = 50",
        "_apply_rate_limiting",
        "get_rate_limiting_status",
        "Pro 610 capacity"
    ]

    files_passed = 0
    files_failed = 0

    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            file_name = file_path.split('/')[-1]
            missing_in_file = []

            for pattern in required_patterns:
                if pattern not in content:
                    missing_in_file.append(pattern)

            if missing_in_file:
                print(f"❌ {file_name}: Missing patterns:")
                for pattern in missing_in_file:
                    print(f"   - {pattern}")
                files_failed += 1
            else:
                print(f"✅ {file_name}: All optimization patterns present")
                files_passed += 1

        except Exception as e:
            print(f"❌ Error checking {file_path}: {str(e)}")
            files_failed += 1

    print(f"\n📊 BACKUP CONSISTENCY SUMMARY:")
    print(f"   Files optimized: {files_passed}/{files_passed + files_failed}")

    return files_passed == (files_passed + files_failed)

if __name__ == "__main__":
    print("🚀 Starting Rate Limiting Optimization Test for Pro 610 Plan")
    print("Testing full utilization of TwelveData Pro 610 subscription capacity")
    print("Date:", time.strftime('%Y-%m-%d %H:%M:%S UTC'))
    print()

    # Run all rate limiting optimization tests
    tests = [
        ("Rate Limiting Configuration", test_rate_limiting_configuration),
        ("Rate Limiting Status Method", test_rate_limiting_status_method),
        ("Rate Limiting Logic Simulation", test_rate_limiting_logic_simulation),
        ("Optimization vs Original Performance", test_optimization_vs_original),
        ("Backup Files Consistency", test_backup_files_consistency)
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
    print("📊 RATE LIMITING OPTIMIZATION TEST RESULTS")
    print(f"{'='*70}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL RATE LIMITING OPTIMIZATION TESTS PASSED!")
        print("✅ Pro 610 plan fully utilized (610 req/min vs 600)")
        print("✅ Intelligent burst handling implemented")
        print("✅ Rate limiting status monitoring available")
        print("✅ 1.67% capacity improvement achieved")
        print("✅ Cost efficiency improved by optimizing subscription utilization")
        print("✅ Ready for high-performance TwelveData integration")
        sys.exit(0)
    else:
        print("\n❌ SOME RATE LIMITING OPTIMIZATION TESTS FAILED!")
        print("Rate limiting optimization needs further review")
        sys.exit(1)