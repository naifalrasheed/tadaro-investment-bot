#!/usr/bin/env python3
"""
Environment Variables Validation Test
Validates all required environment variables are properly configured
"""

import os
import sys

def validate_environment_variables():
    """Validate all environment variables required by the application"""
    print("🔍 Validating Environment Variables Configuration")
    print("=" * 70)

    # Critical environment variables (must be present)
    critical_vars = {
        'TWELVEDATA_API_KEY': 'TwelveData Pro 610 API key for stock data',
        'DATABASE_URL': 'PostgreSQL database connection URL',
        'SECRET_KEY': 'Flask session encryption key',
        'CLAUDE_API_KEY': 'Claude API key for AI chat functionality'
    }

    # Optional environment variables (used by application)
    optional_vars = {
        'FLASK_ENV': 'Flask environment (production/development)',
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage API key (fallback data source)',
        'NEWS_API_KEY': 'News API key for sentiment analysis',
        'MAIL_USERNAME': 'Email service username',
        'MAIL_PASSWORD': 'Email service password',
        'REDIS_URL': 'Redis cache URL',
        'LOG_LEVEL': 'Logging level (INFO, DEBUG, ERROR)'
    }

    print("\n📋 CRITICAL ENVIRONMENT VARIABLES:")
    print("-" * 50)

    critical_missing = []
    for var, description in critical_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'API_KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***masked***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value

            print(f"✅ {var:<20}: {display_value}")
            print(f"   Purpose: {description}")
        else:
            print(f"❌ {var:<20}: NOT SET")
            print(f"   Purpose: {description}")
            critical_missing.append(var)
        print()

    print("\n📋 OPTIONAL ENVIRONMENT VARIABLES:")
    print("-" * 50)

    optional_missing = []
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'API_KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***masked***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value

            print(f"✅ {var:<20}: {display_value}")
        else:
            print(f"⚠️  {var:<20}: NOT SET (optional)")
            optional_missing.append(var)
        print(f"   Purpose: {description}")
        print()

    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)

    if not critical_missing:
        print("🎉 ALL CRITICAL ENVIRONMENT VARIABLES ARE SET!")
    else:
        print(f"❌ MISSING {len(critical_missing)} CRITICAL VARIABLES:")
        for var in critical_missing:
            print(f"   - {var}")

    if optional_missing:
        print(f"\n⚠️  MISSING {len(optional_missing)} OPTIONAL VARIABLES:")
        for var in optional_missing:
            print(f"   - {var}")

    # Provide AWS App Runner configuration instructions
    if critical_missing or optional_missing:
        print("\n🔧 AWS APP RUNNER CONFIGURATION INSTRUCTIONS:")
        print("-" * 50)
        print("Add these environment variables to your App Runner service:")
        print("1. Navigate to AWS App Runner Console")
        print("2. Select your 'tadaro-investment-bot' service")
        print("3. Click 'Configuration' → 'Edit' → 'Environment variables'")
        print("4. Add the following variables:\n")

        for var in critical_missing:
            print(f"   {var}")
            print(f"   └─ Source: Secrets Manager (recommended)")
            print(f"   └─ Name: tadaro-investment-bot/{var.lower().replace('_', '-')}")
            print()

        for var in optional_missing:
            if var in ['FLASK_ENV', 'LOG_LEVEL']:
                print(f"   {var}")
                print(f"   └─ Source: Plain text")
                print(f"   └─ Value: production (for {var})")
            else:
                print(f"   {var}")
                print(f"   └─ Source: Secrets Manager (if available)")
            print()

    # Return validation status
    return len(critical_missing) == 0

def test_import_functionality():
    """Test that critical modules can import with current environment"""
    print("\n🧪 TESTING MODULE IMPORTS WITH CURRENT ENVIRONMENT")
    print("=" * 70)

    test_modules = [
        ('analysis.twelvedata_analyzer', 'TwelveDataAnalyzer'),
        ('claude_integration.claude_handler', 'ClaudeHandler'),
        ('config.production', 'ProductionConfig')
    ]

    for module_name, class_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)

            if class_name == 'TwelveDataAnalyzer':
                # Test TwelveData specifically
                if os.environ.get('TWELVEDATA_API_KEY'):
                    analyzer = cls()
                    print(f"✅ {module_name}.{class_name}: Import successful, API key configured")
                else:
                    print(f"⚠️  {module_name}.{class_name}: Import successful, but no API key")

            elif class_name == 'ClaudeHandler':
                # Test Claude API
                if os.environ.get('CLAUDE_API_KEY'):
                    handler = cls()
                    print(f"✅ {module_name}.{class_name}: Import successful, API key configured")
                else:
                    print(f"⚠️  {module_name}.{class_name}: Import successful, but no API key")

            else:
                print(f"✅ {module_name}.{class_name}: Import successful")

        except Exception as e:
            print(f"❌ {module_name}.{class_name}: Import failed - {str(e)}")

    return True

if __name__ == "__main__":
    print("🚀 Environment Variables Validation")
    print("Date:", sys.version)
    print("Working Directory:", os.getcwd())

    # Run validation
    env_valid = validate_environment_variables()
    import_test = test_import_functionality()

    if env_valid:
        print("\n🎉 ENVIRONMENT VALIDATION PASSED!")
        sys.exit(0)
    else:
        print("\n❌ ENVIRONMENT VALIDATION FAILED!")
        print("Configure missing environment variables before proceeding.")
        sys.exit(1)