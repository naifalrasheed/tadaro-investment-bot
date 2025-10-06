#!/usr/bin/env python3
"""
EMERGENCY FIX: Stop Mock Data Usage and Force TwelveData API Key Update

This script fixes two critical issues:
1. Updates TwelveData API key in the deployed container
2. Disables mock data system that's overriding real financial data
"""

import os
import re

def fix_twelvedata_api_key():
    """Fix TwelveData API key in the analyzer"""
    print("🔧 Fixing TwelveData API key...")

    analyzer_file = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/twelvedata_analyzer.py"

    with open(analyzer_file, 'r') as f:
        content = f.read()

    # Force the correct API key regardless of environment
    old_pattern = r'self\.api_key = api_key or os\.environ\.get\(\'TWELVEDATA_API_KEY\', \'.*?\'\)'
    new_code = "self.api_key = '71cdbb03b46645628e8416eeb4836c99'  # Force working TwelveData API key"

    content = re.sub(old_pattern, new_code, content)

    # Also add debug logging to see what key is being used
    if 'logger.info(f"TwelveData API Key being used:' not in content:
        # Find the __init__ method and add logging
        init_pattern = r'(def __init__\(self.*?\n.*?self\.api_key = .*?\n)'
        debug_code = r'\1        logger.info(f"TwelveData API Key being used: {self.api_key[:8]}...{self.api_key[-4:]}")\n'
        content = re.sub(init_pattern, debug_code, content, flags=re.MULTILINE | re.DOTALL)

    with open(analyzer_file, 'w') as f:
        f.write(content)

    print("✅ TwelveData API key hardcoded to Pro 610 key")

def disable_mock_data_system():
    """Disable mock data system that's overriding real data"""
    print("🔧 Disabling mock data system...")

    analyzer_file = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/analysis/enhanced_stock_analyzer.py"

    with open(analyzer_file, 'r') as f:
        content = f.read()

    # Comment out the mock data section
    mock_section = """            # Next, check mock data (known popular stocks)
            mock_data = self._get_mock_data(symbol)
            if mock_data:
                self.logger.info(f"Using mock data for {symbol}")"""

    replacement = """            # DISABLED: Mock data system (was causing wrong financial data)
            # mock_data = self._get_mock_data(symbol)
            # if False:  # Never use mock data
            #     self.logger.info(f"Using mock data for {symbol}")"""

    content = content.replace(mock_section, replacement)

    # Also disable the rest of the mock data handling
    content = content.replace(
        "if mock_data:",
        "if False:  # Mock data disabled"
    )

    with open(analyzer_file, 'w') as f:
        f.write(content)

    print("✅ Mock data system disabled")

def force_real_data_sources():
    """Force usage of only real data sources"""
    print("🔧 Forcing real data sources only...")

    app_file = "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src/app.py"

    with open(app_file, 'r') as f:
        content = f.read()

    # Find the fallback to mock data section
    mock_fallback = "results = stock_analyzer._get_mock_data(symbol)"
    replacement = """# DISABLED: Mock data fallback - force failure instead
                # results = stock_analyzer._get_mock_data(symbol)
                results = None  # Force failure rather than fake data"""

    content = content.replace(mock_fallback, replacement)

    # Also replace the last resort mock data
    last_resort = 'results = stock_analyzer._get_mock_data(symbol)'
    replacement2 = '''# DISABLED: Last resort mock data
                # results = stock_analyzer._get_mock_data(symbol)
                results = None  # Fail rather than show fake data'''

    content = content.replace(last_resort, replacement2)

    with open(app_file, 'w') as f:
        f.write(content)

    print("✅ Mock data fallbacks disabled in app.py")

def main():
    print("🚨 EMERGENCY DATA SOURCE FIX")
    print("=" * 50)
    print()
    print("This will fix:")
    print("1. TwelveData API key hardcoded to Pro 610 key")
    print("2. Disable mock data system causing wrong numbers")
    print("3. Force real data sources only")
    print()

    try:
        fix_twelvedata_api_key()
        disable_mock_data_system()
        force_real_data_sources()

        print()
        print("=" * 50)
        print("✅ EMERGENCY FIX COMPLETED!")
        print()
        print("Next steps:")
        print("1. Rebuild container: docker build -t tadaro-investment-bot:emergency-fix .")
        print("2. Push to ECR and deploy")
        print("3. Test MSFT - should show real TwelveData now")
        print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()