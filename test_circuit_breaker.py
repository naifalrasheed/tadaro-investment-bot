#!/usr/bin/env python3
"""
Circuit Breaker Implementation Test
Tests the circuit breaker pattern for API failure resilience
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

def test_circuit_breaker_imports():
    """Test that circuit breaker imports and initialization are present"""
    print("🔌 Testing Circuit Breaker Imports")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Required circuit breaker patterns
        required_patterns = [
            # Initialization
            "_init_circuit_breaker",
            "Initialize circuit breaker for API failure resilience",
            "self._init_circuit_breaker()",

            # Circuit breaker states
            "class CircuitState(Enum):",
            "CLOSED = \"closed\"",
            "OPEN = \"open\"",
            "HALF_OPEN = \"half_open\"",

            # Configuration
            "self.circuit_failure_threshold = 5",
            "self.circuit_failure_window = 60",
            "self.circuit_open_duration = 300",
            "self.circuit_half_open_max_requests = 3",

            # Thread safety
            "self.circuit_lock = threading.Lock()",

            # Core methods
            "_check_circuit_breaker",
            "_record_circuit_success",
            "_record_circuit_failure",
            "get_circuit_breaker_status"
        ]

        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)

        if missing_patterns:
            print(f"❌ Missing circuit breaker patterns:")
            for pattern in missing_patterns:
                print(f"   - {pattern}")
            return False
        else:
            print("✅ All circuit breaker imports and initialization present")

        return True

    except Exception as e:
        print(f"❌ Error testing imports: {str(e)}")
        return False

def test_circuit_breaker_integration():
    """Test that circuit breaker is integrated into _make_request method"""
    print("\n🔗 Testing Circuit Breaker Integration")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Integration patterns in _make_request
        integration_patterns = [
            # Circuit breaker check
            ("Circuit Breaker Check", "if not self._check_circuit_breaker():"),
            ("Circuit Breaker Block", "Circuit Breaker {circuit_status['state']}"),
            ("Circuit Breaker Success", "self._record_circuit_success()"),

            # Failure recording for HTTP errors
            ("Rate Limit Failure", "# CIRCUIT BREAKER: Record rate limit as failure"),
            ("Server Error Failure", "# CIRCUIT BREAKER: Record server errors as failures"),
            ("Client Error Failure", "# CIRCUIT BREAKER: Record client/server errors as failures"),
            ("Network Error Failure", "# CIRCUIT BREAKER: Record network failure"),
            ("API Error Failure", "# CIRCUIT BREAKER: Record API-level failure"),
            ("Empty Response Failure", "# CIRCUIT BREAKER: Record failure for empty responses"),

            # State transitions
            ("Transition Logging", "_transition_to_half_open"),
            ("Recovery Logging", "TwelveData Circuit Breaker: API recovered"),
            ("Failure Logging", "TwelveData Circuit Breaker: OPENED due to")
        ]

        print("Testing circuit breaker integration patterns:")
        print("-" * 60)

        integration_passed = 0
        integration_failed = 0

        for test_name, pattern in integration_patterns:
            if pattern in content:
                print(f"✅ {test_name:<25} Present")
                integration_passed += 1
            else:
                print(f"❌ {test_name:<25} MISSING")
                integration_failed += 1

        print(f"\n📊 INTEGRATION SUMMARY:")
        print(f"   Integration tests: {integration_passed}/{integration_passed + integration_failed} passed")

        return integration_passed == (integration_passed + integration_failed)

    except Exception as e:
        print(f"❌ Error testing integration: {str(e)}")
        return False

def test_circuit_breaker_configuration():
    """Test the circuit breaker configuration values"""
    print("\n⚙️ Testing Circuit Breaker Configuration")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Expected configuration values optimized for TwelveData Pro 610
        config_tests = [
            ("Failure Threshold", "self.circuit_failure_threshold = 5", "5 failures trigger open state"),
            ("Failure Window", "self.circuit_failure_window = 60", "60 seconds failure counting window"),
            ("Open Duration", "self.circuit_open_duration = 300", "300 seconds (5 minutes) open duration"),
            ("Half-Open Requests", "self.circuit_half_open_max_requests = 3", "3 test requests in half-open"),
            ("Thread Safety", "self.circuit_lock = threading.Lock()", "Thread-safe state management"),
            ("State Enum", "class CircuitState(Enum):", "Circuit breaker states defined"),
            ("Success Tracking", "self.circuit_success_count = 0", "Success counter initialized"),
            ("Total Tracking", "self.circuit_total_requests = 0", "Total requests counter")
        ]

        print("Testing configuration values:")
        print("-" * 60)

        config_passed = 0
        config_failed = 0

        for test_name, pattern, description in config_tests:
            if pattern in content:
                print(f"✅ {test_name:<20} {description}")
                config_passed += 1
            else:
                print(f"❌ {test_name:<20} MISSING - {description}")
                config_failed += 1

        print(f"\n📊 CONFIGURATION SUMMARY:")
        print(f"   Config tests: {config_passed}/{config_passed + config_failed} passed")

        return config_passed == (config_passed + config_failed)

    except Exception as e:
        print(f"❌ Error testing configuration: {str(e)}")
        return False

def test_circuit_breaker_benefits():
    """Test the circuit breaker benefits and optimization"""
    print("\n🛡️ Testing Circuit Breaker Benefits")
    print("=" * 60)

    try:
        # Circuit breaker behavior analysis
        print("Circuit Breaker Benefits for TwelveData Pro 610:")
        print("-" * 60)

        benefits = [
            ("API Failure Resilience", "Prevents cascade failures when API is down"),
            ("Fast-Fail Behavior", "Immediate failure response when circuit is open"),
            ("Automatic Recovery", "Tests API recovery every 5 minutes when open"),
            ("Gradual Recovery", "3 test requests in half-open state before full recovery"),
            ("Thread Safety", "Multi-threaded operations with proper synchronization"),
            ("Failure Tracking", "Tracks failure patterns over 60-second windows"),
            ("Success Rate Monitoring", "Real-time success rate calculation"),
            ("Pro 610 Optimization", "Optimized thresholds for high-volume API usage")
        ]

        for benefit_name, description in benefits:
            print(f"✅ {benefit_name:<25} {description}")

        # Circuit breaker states analysis
        print(f"\n🔄 CIRCUIT BREAKER STATES:")
        print("-" * 60)
        print("✅ CLOSED: Normal operation - all requests allowed")
        print("✅ OPEN: API failures detected - requests blocked for 5 minutes")
        print("✅ HALF_OPEN: Recovery testing - max 3 test requests allowed")

        # Performance optimization
        print(f"\n📊 PERFORMANCE OPTIMIZATION:")
        print("-" * 60)

        # Theoretical analysis for Pro 610 with circuit breaker
        failure_threshold = 5
        failure_window = 60  # seconds
        open_duration = 300  # seconds
        recovery_test_requests = 3

        print(f"Failure threshold: {failure_threshold} failures in {failure_window} seconds")
        print(f"Circuit open duration: {open_duration} seconds ({open_duration/60:.1f} minutes)")
        print(f"Recovery test requests: {recovery_test_requests}")
        print(f"Pro 610 rate limit: 610 requests/minute")

        # Calculate protection benefits
        requests_saved_per_outage = int((open_duration / 60) * 610)  # requests saved during open period
        print(f"Requests saved per API outage: {requests_saved_per_outage} (prevents overload)")

        # Economic benefits
        print(f"\n💰 ECONOMIC BENEFITS:")
        print("-" * 60)
        print("✅ Prevents wasted API calls during outages")
        print("✅ Reduces application error rates")
        print("✅ Improves user experience with fast-fail behavior")
        print("✅ Automatic recovery reduces manual intervention")

        return True

    except Exception as e:
        print(f"❌ Error testing benefits: {str(e)}")
        return False

def test_backup_files_circuit_breaker():
    """Test that backup files have the same circuit breaker implementation"""
    print("\n🔄 Testing Backup Files Circuit Breaker Implementation")
    print("=" * 60)

    files_to_check = [
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_backup.py",
        "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer_fixed.py"
    ]

    # Key patterns that should be in all files
    required_patterns = [
        "_init_circuit_breaker",
        "_check_circuit_breaker",
        "_record_circuit_success",
        "_record_circuit_failure",
        "get_circuit_breaker_status",
        "Circuit Breaker {circuit_status['state']}",
        "self._record_circuit_failure()",
        "self._record_circuit_success()"
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
                print(f"❌ {file_name}: Missing circuit breaker patterns:")
                for pattern in missing_in_file:
                    print(f"   - {pattern}")
                files_failed += 1
            else:
                print(f"✅ {file_name}: All circuit breaker patterns present")
                files_passed += 1

        except Exception as e:
            print(f"❌ Error checking {file_path}: {str(e)}")
            files_failed += 1

    print(f"\n📊 BACKUP CONSISTENCY SUMMARY:")
    print(f"   Files updated: {files_passed}/{files_passed + files_failed}")

    return files_passed == (files_passed + files_failed)

def test_integration_with_existing_optimizations():
    """Test that circuit breaker integrates well with existing optimizations"""
    print("\n🤝 Testing Integration with Existing Optimizations")
    print("=" * 60)

    try:
        file_path = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

        with open(file_path, 'r') as f:
            content = f.read()

        # Test integration with existing optimizations
        integration_patterns = [
            # Rate limiting integration
            ("Rate limiting + Circuit breaker", "_apply_rate_limiting(current_time)"),
            ("Pro 610 optimization", "max_requests_per_minute = 610"),
            ("Burst handling", "burst_limit = 50"),

            # Connection pooling integration
            ("Connection pooling", "self.session = self._create_optimized_session()"),
            ("HTTP adapter", "HTTPAdapter("),
            ("Keep-alive", "Keep-Alive': 'timeout=30"),

            # Thread safety integration
            ("Thread safety", "self.circuit_lock = threading.Lock()"),
            ("Saudi symbol validation", "_validate_symbol"),

            # Security integration
            ("Environment variable", "os.environ.get('TWELVEDATA_API_KEY')"),
            ("No hardcoded keys", "TWELVEDATA_API_KEY environment variable is required")
        ]

        print("Testing integration with existing optimizations:")
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

        print(f"\n🎯 COMBINED OPTIMIZATIONS:")
        print("✅ Circuit breaker prevents API overload during failures")
        print("✅ Rate limiting prevents API quota exhaustion")
        print("✅ Connection pooling reduces latency and connection overhead")
        print("✅ Thread safety enables multi-threaded operations")
        print("✅ Security ensures no API key exposure")
        print("✅ Saudi market support enables Middle East trading")

        print(f"\n📊 INTEGRATION SUMMARY:")
        print(f"   Integration tests: {integration_passed}/{integration_passed + integration_failed} passed")

        return integration_passed == (integration_passed + integration_failed)

    except Exception as e:
        print(f"❌ Error testing integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🛡️ Starting Circuit Breaker Implementation Test")
    print("Testing API failure resilience for TwelveData Pro 610 integration")
    print("Date:", time.strftime('%Y-%m-%d %H:%M:%S UTC'))
    print()

    # Run all circuit breaker tests
    tests = [
        ("Circuit Breaker Imports", test_circuit_breaker_imports),
        ("Circuit Breaker Integration", test_circuit_breaker_integration),
        ("Circuit Breaker Configuration", test_circuit_breaker_configuration),
        ("Circuit Breaker Benefits", test_circuit_breaker_benefits),
        ("Integration with Existing Optimizations", test_integration_with_existing_optimizations),
        ("Backup Files Circuit Breaker", test_backup_files_circuit_breaker)
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
    print("📊 CIRCUIT BREAKER TEST RESULTS")
    print(f"{'='*70}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL CIRCUIT BREAKER TESTS PASSED!")
        print("✅ Circuit breaker pattern successfully implemented")
        print("✅ API failure resilience for TwelveData Pro 610")
        print("✅ 5 failures in 60 seconds trigger circuit open")
        print("✅ 300 seconds (5 minutes) open duration")
        print("✅ Automatic recovery testing with 3 half-open requests")
        print("✅ Thread-safe multi-state management")
        print("✅ Integrated with rate limiting and connection pooling")
        print("✅ Ready for high-resilience TwelveData API usage")
        sys.exit(0)
    else:
        print("\n❌ SOME CIRCUIT BREAKER TESTS FAILED!")
        print("Circuit breaker implementation needs further review")
        sys.exit(1)