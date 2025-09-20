#!/usr/bin/env python3
"""
Test runner script for MyGPT application.
Provides convenient commands for running tests and coverage.
"""
import subprocess
import sys


def run_tests():
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    return subprocess.run(cmd).returncode


def run_tests_with_coverage():
    """Run tests with coverage report."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
    ]
    return subprocess.run(cmd).returncode


def run_coverage_only():
    """Run coverage report only."""
    cmd = ["python", "-m", "coverage", "report", "--show-missing"]
    return subprocess.run(cmd).returncode


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py [tests|coverage|coverage-only]")
        print("  tests        - Run tests only")
        print("  coverage     - Run tests with coverage")
        print("  coverage-only - Show coverage report only")
        sys.exit(1)

    command = sys.argv[1]

    if command == "tests":
        exit_code = run_tests()
    elif command == "coverage":
        exit_code = run_tests_with_coverage()
    elif command == "coverage-only":
        exit_code = run_coverage_only()
    else:
        print(f"Unknown command: {command}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
