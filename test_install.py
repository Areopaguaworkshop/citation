#!/usr/bin/env python3
"""
Test script to verify the citation extractor installation and basic functionality.
"""

import sys
import os
import tempfile

def test_imports():
    """Test that all required imports work."""
    try:
        from citation import CitationExtractor
        print("✓ Citation extractor imported successfully")
        assert True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        assert False

def test_extractor_init():
    """Test that the extractor can be initialized."""
    try:
        from citation import CitationExtractor
        extractor = CitationExtractor()
        print("✓ Citation extractor initialized successfully")
        assert True
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        assert False

def test_cli_help():
    """Test that the CLI shows help."""
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "citation.cli", "--help"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ CLI help command works")
            assert True
        else:
            print(f"✗ CLI help failed: {result.stderr}")
            assert False
    except Exception as e:
        print(f"✗ CLI test error: {e}")
        assert False

def main():
    """Run all tests."""
    print("Testing citation extractor installation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_extractor_init,
        test_cli_help,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError:
            pass
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The citation extractor is ready to use.")
        return 0
    else:
        print("✗ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
