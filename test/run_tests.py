#!/usr/bin/env python3
"""
Test runner for Dutch Cabo game tests
"""

import unittest
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import all test modules
from test.test_game_engine import TestGameEngine
from test.test_card_mechanics import TestCardMechanics  
from test.test_special_abilities import TestSpecialAbilities
from test.test_matching_logic import TestMatchingLogic


def create_test_suite():
    """Create a test suite with all test classes"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestGameEngine,
        TestCardMechanics,
        TestSpecialAbilities,
        TestMatchingLogic
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def main():
    """Run all tests"""
    print("=" * 60)
    print("Dutch Cabo Game - Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = create_test_suite()
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    # Print failures and errors if any
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)
    
    # Exit with error code if tests failed
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("\nAll tests passed! ✅")
        sys.exit(0)


if __name__ == "__main__":
    main() 