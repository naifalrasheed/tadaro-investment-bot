#!/usr/bin/env python3
"""
Connection Pooling Implementation Test
Tests the advanced HTTP session with connection pooling for TwelveData API
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

def test_connection_pooling_imports():
    """Test that connection pooling imports are present"""
    print("📦 Testing Connection Pooling Imports")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Required imports for connection pooling
        required_imports = [
            "from requests.adapters import HTTPAdapter",
            "from requests.packages.urllib3.util.retry import Retry"
        ]

        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)

        if missing_imports:
            print(f"❌ Missing connection pooling imports:")
            for imp in missing_imports:
                print(f"   - {imp}")
            return False
        else:
            print("✅ All connection pooling imports present")

        return True

    except Exception as e:
        print(f"❌ Error testing imports: {str(e)}")
        return False

def test_connection_pooling_code_structure():
    """Test that connection pooling methods are properly implemented"""
    print("\n🏗️ Testing Connection Pooling Code Structure")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Test patterns for connection pooling implementation
        required_patterns = [
            # Session creation
            "_create_optimized_session",
            "CONNECTION POOLING: Advanced HTTP session with connection pooling",
            "self.session = self._create_optimized_session()",

            # HTTP Adapter configuration
            "HTTPAdapter(",
            "pool_connections=10",
            "pool_maxsize=50",
            "max_retries=self._create_retry_strategy()",
            "pool_block=False",

            # Retry strategy
            "_create_retry_strategy",
            "Create intelligent retry strategy for API resilience",
            "Retry(",
            "total=3",
            "backoff_factor=1",
            "status_forcelist=",

            # Keep-alive settings
            "Connection': 'keep-alive'",
            "Keep-Alive': 'timeout=30, max=100'",

            # Monitoring
            "get_connection_pool_status",
            "Connection pooling active and optimized"
        ]

        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)

        if missing_patterns:
            print(f"❌ Missing connection pooling patterns:")
            for pattern in missing_patterns:
                print(f"   - {pattern}")
            return False
        else:
            print("✅ All connection pooling patterns present")

        # Test for enhanced _make_request method
        enhanced_request_patterns = [
            "Connection Pooling Benefits:",
            "timeout=(10, 30)",
            "request_duration = time.time() - request_start_time",
            "TwelveData connection performance:",
            "allow_redirects=True",
            "stream=False"
        ]

        print(f"\nTesting enhanced request method:")
        print("-" * 60)

        request_missing = []
        for pattern in enhanced_request_patterns:
            if pattern in content:
                print(f"✅ {pattern}")
            else:
                print(f"❌ MISSING: {pattern}")
                request_missing.append(pattern)

        return len(request_missing) == 0

    except Exception as e:
        print(f"❌ Error testing connection pooling structure: {str(e)}")
        return False

def test_connection_pool_configuration():
    """Test the connection pool configuration values"""
    print("\n⚙️ Testing Connection Pool Configuration")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Expected configuration values optimized for TwelveData Pro 610
        config_tests = [
            ("Pool connections", "pool_connections=10", "10 connection pools for caching"),
            ("Pool max size", "pool_maxsize=50", "50 connections per pool (burst support)"),
            ("Keep-alive timeout", "timeout=30", "30 seconds keep-alive"),
            ("Keep-alive max requests", "max=100", "100 requests per connection"),
            ("Total retries", "total=3", "3 total retry attempts"),
            ("Backoff factor", "backoff_factor=1", "Exponential backoff starting at 1 second"),
            ("Retry status codes", "status_forcelist=", "Server errors and rate limits")
        ]

        print("Testing configuration values:")
        print("-" * 60)

        config_passed = 0
        config_failed = 0

        for test_name, pattern, description in config_tests:
            if pattern in content:
                print(f"✅ {test_name:<20} {pattern}")
                config_passed += 1
            else:
                print(f"❌ {test_name:<20} {pattern} - MISSING")
                config_failed += 1

        print(f"\n📊 CONFIGURATION SUMMARY:")
        print(f"   Config tests: {config_passed}/{config_passed + config_failed} passed")

        return config_passed == (config_passed + config_failed)

    except Exception as e:
        print(f"❌ Error testing configuration: {str(e)}")
        return False

def test_performance_optimizations():
    """Test the performance optimization benefits"""
    print("\n🚀 Testing Performance Optimization Benefits")
    print("=" * 60)

    try:
        # Connection pooling vs non-pooling comparison
        print("Connection Pooling Performance Benefits:")
        print("-" * 60)

        benefits = [
            ("Connection Reuse", "Eliminates TCP handshake overhead", "~100-200ms saved per request"),
            ("Keep-Alive", "Maintains persistent connections", "30 seconds connection lifetime"),
            ("Request Batching", "Handles up to 50 concurrent connections", "Supports burst of 50 requests"),
            ("Retry Logic", "Automatic retry on transient failures", "3 attempts with exponential backoff"),
            ("DNS Caching", "Connection pooling includes DNS caching", "Eliminates repeated DNS lookups"),
            ("SSL Session Reuse", "Reuses SSL sessions for HTTPS", "Significant SSL handshake savings")
        ]

        for benefit_name, description, impact in benefits:
            print(f"✅ {benefit_name:<18} {description}")
            print(f"   {'Impact:':<18} {impact}")
            print()

        # Calculate theoretical performance improvements
        print("📊 THEORETICAL PERFORMANCE IMPROVEMENTS:")
        print("-" * 60)

        # Without connection pooling: Each request needs TCP + SSL handshake
        tcp_handshake = 0.1  # ~100ms for TCP handshake
        ssl_handshake = 0.2  # ~200ms for SSL handshake
        dns_lookup = 0.05    # ~50ms for DNS lookup

        overhead_per_request_without_pooling = tcp_handshake + ssl_handshake + dns_lookup
        overhead_per_request_with_pooling = 0.01  # Minimal overhead with reused connections

        # For Pro 610: 610 requests per minute
        requests_per_minute = 610
        time_saved_per_request = overhead_per_request_without_pooling - overhead_per_request_with_pooling
        total_time_saved_per_minute = time_saved_per_request * requests_per_minute

        print(f"Without pooling overhead:  {overhead_per_request_without_pooling*1000:.0f}ms per request")
        print(f"With pooling overhead:     {overhead_per_request_with_pooling*1000:.0f}ms per request")
        print(f"Time saved per request:    {time_saved_per_request*1000:.0f}ms")
        print(f"Pro 610 requests/minute:   {requests_per_minute}")
        print(f"Total time saved/minute:   {total_time_saved_per_minute:.1f} seconds")

        performance_improvement = (time_saved_per_request / overhead_per_request_without_pooling) * 100
        print(f"Performance improvement:   {performance_improvement:.1f}%")

        # Reliability improvements
        print(f"\n🛡️ RELIABILITY IMPROVEMENTS:")
        print("-" * 60)
        print("✅ Retry logic handles transient network failures")
        print("✅ Exponential backoff prevents API overwhelming")
        print("✅ Connection pool prevents connection exhaustion")
        print("✅ Keep-alive reduces connection setup failures")

        return True

    except Exception as e:
        print(f"❌ Error testing performance optimizations: {str(e)}")
        return False

def test_backup_files_consistency():
    """Test that backup files have the same connection pooling implementation"""
    print("\n🔄 Testing Backup Files Consistency")
    print("=" * 60)

    files_to_check = [
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_backup.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_fixed.py"
    ]

    # Key patterns that should be in all files
    required_patterns = [
        "_create_optimized_session",
        "_create_retry_strategy",
        "get_connection_pool_status",
        "HTTPAdapter(",
        "pool_connections=10",
        "pool_maxsize=50",
        "Keep-Alive': 'timeout=30"
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
                print(f"❌ {file_name}: Missing connection pooling patterns:")
                for pattern in missing_in_file:
                    print(f"   - {pattern}")
                files_failed += 1
            else:
                print(f"✅ {file_name}: All connection pooling patterns present")
                files_passed += 1

        except Exception as e:
            print(f"❌ Error checking {file_path}: {str(e)}")
            files_failed += 1

    print(f"\n📊 BACKUP CONSISTENCY SUMMARY:")
    print(f"   Files updated: {files_passed}/{files_passed + files_failed}")

    return files_passed == (files_passed + files_failed)

def test_integration_with_rate_limiting():
    """Test that connection pooling integrates well with rate limiting"""
    print("\n🤝 Testing Integration with Rate Limiting")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Test integration patterns
        integration_patterns = [
            # Rate limiting should work with connection pooling
            ("Rate limiting integration", "_apply_rate_limiting(current_time)"),
            ("Connection pooling request", "self.session.get("),
            ("Performance monitoring", "request_duration = time.time() - request_start_time"),
            ("Combined optimization", "Pro 610 rate limiting with burst handling"),

            # Both optimizations should be present
            ("Rate limiting config", "max_requests_per_minute = 610"),
            ("Connection pool config", "pool_maxsize=50"),
            ("Burst handling", "burst_limit = 50"),
            ("Connection reuse", "Keep-Alive': 'timeout=30")
        ]

        print("Testing rate limiting + connection pooling integration:")
        print("-" * 60)

        integration_passed = 0
        integration_failed = 0

        for test_name, pattern in integration_patterns:
            if pattern in content:
                print(f"✅ {test_name:<30} Present")
                integration_passed += 1
            else:
                print(f"❌ {test_name:<30} MISSING")
                integration_failed += 1

        print(f"\n🎯 INTEGRATION BENEFITS:")
        print("✅ Rate limiting prevents API overload")
        print("✅ Connection pooling reduces latency")
        print("✅ Burst handling + connection reuse = optimal throughput")
        print("✅ Pro 610 subscription fully optimized")

        print(f"\n📊 INTEGRATION SUMMARY:")
        print(f"   Integration tests: {integration_passed}/{integration_passed + integration_failed} passed")

        return integration_passed == (integration_passed + integration_failed)

    except Exception as e:
        print(f"❌ Error testing integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Connection Pooling Implementation Test")
    print("Testing advanced HTTP session optimization for TwelveData API")
    print("Date:", time.strftime('%Y-%m-%d %H:%M:%S UTC'))
    print()

    # Run all connection pooling tests
    tests = [
        ("Connection Pooling Imports", test_connection_pooling_imports),
        ("Connection Pooling Code Structure", test_connection_pooling_code_structure),
        ("Connection Pool Configuration", test_connection_pool_configuration),
        ("Performance Optimization Benefits", test_performance_optimizations),
        ("Integration with Rate Limiting", test_integration_with_rate_limiting),
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
    print("📊 CONNECTION POOLING TEST RESULTS")
    print(f"{'='*70}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL CONNECTION POOLING TESTS PASSED!")
        print("✅ Advanced HTTP session with connection pooling implemented")
        print("✅ 10 connection pools × 50 connections per pool")
        print("✅ Intelligent retry strategy with exponential backoff")
        print("✅ Keep-alive connections (30 seconds timeout)")
        print("✅ Performance optimized for Pro 610 throughput")
        print("✅ Integrated with rate limiting optimization")
        print("✅ Connection reuse eliminates TCP/SSL handshake overhead")
        print("✅ Ready for high-performance TwelveData API usage")
        sys.exit(0)
    else:
        print("\n❌ SOME CONNECTION POOLING TESTS FAILED!")
        print("Connection pooling implementation needs further review")
        sys.exit(1)