import unittest
import os
import sys

def run_all_tests():
    """Run all test files using unittest discovery"""
    loader = unittest.TestLoader()
    
    # Get the directory of this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Discover tests in the tests directory
    tests_dir = os.path.join(base_dir, 'tests')
    if os.path.exists(tests_dir):
        suite.addTest(loader.discover(tests_dir))
    
    # Discover test files in the base directory
    for file in os.listdir(base_dir):
        if file.startswith('test_') and file.endswith('.py'):
            # Import the module
            module_name = file[:-3]  # Remove .py extension
            
            # Make sure the current directory is in sys.path
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
                
            try:
                # Import the module
                __import__(module_name)
                module = sys.modules[module_name]
                
                # Add tests from this module
                suite.addTest(loader.loadTestsFromModule(module))
            except (ImportError, KeyError) as e:
                print(f"Warning: Could not import {module_name}: {e}")
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())