"""Test suite runner and utilities"""
import pytest
import sys
import os
from pathlib import Path
import coverage


def run_tests(test_path=None, coverage_enabled=True, verbose=True):
    """
    Run the test suite with optional coverage reporting
    
    Args:
        test_path: Specific test file or directory to run (None for all tests)
        coverage_enabled: Whether to generate coverage report
        verbose: Whether to show verbose output
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Add backend directory to Python path
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    # Prepare pytest arguments
    pytest_args = []
    
    if verbose:
        pytest_args.append("-v")
    
    # Add test path if specified
    if test_path:
        pytest_args.append(test_path)
    else:
        pytest_args.append(str(Path(__file__).parent))
    
    # Additional useful flags
    pytest_args.extend([
        "-s",  # Don't capture stdout
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Ensure all markers are registered
        "-p", "no:warnings",  # Disable warnings
    ])
    
    if coverage_enabled:
        # Initialize coverage
        cov = coverage.Coverage(source=["app"])
        cov.start()
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    if coverage_enabled:
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\n" + "="*70)
        print("Coverage Report:")
        print("="*70)
        cov.report()
        
        # Generate HTML coverage report
        cov.html_report(directory="htmlcov")
        print(f"\nDetailed HTML coverage report generated in: {backend_dir}/htmlcov/index.html")
    
    return exit_code


def run_specific_test_module(module_name):
    """Run tests for a specific module"""
    test_file = Path(__file__).parent / f"test_{module_name}.py"
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return 1
    
    return run_tests(str(test_file))


def run_integration_tests():
    """Run only integration tests"""
    return pytest.main([
        "-v",
        "-m", "integration",
        str(Path(__file__).parent)
    ])


def run_unit_tests():
    """Run only unit tests"""
    return pytest.main([
        "-v",
        "-m", "not integration",
        str(Path(__file__).parent)
    ])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Olympian AI backend tests")
    parser.add_argument(
        "module",
        nargs="?",
        help="Specific module to test (e.g., 'chat_api', 'ollama_service')"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Less verbose output"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    
    args = parser.parse_args()
    
    if args.integration:
        exit_code = run_integration_tests()
    elif args.unit:
        exit_code = run_unit_tests()
    elif args.module:
        exit_code = run_specific_test_module(args.module)
    else:
        exit_code = run_tests(
            coverage_enabled=not args.no_coverage,
            verbose=not args.quiet
        )
    
    sys.exit(exit_code)
