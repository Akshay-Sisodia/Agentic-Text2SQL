#!/usr/bin/env python3
"""
Script to run the test suite for the Agentic Text2SQL project.
"""

import sys
import subprocess

def main():
    """Run the test suite."""
    print("Running Agentic Text2SQL test suite...")
    
    # Run pytest with UV (using configuration from pytest.ini)
    result = subprocess.run(
        ["uv", "run", "pytest"],
        check=False,
        capture_output=True,
        text=True
    )
    
    # Print test output
    print(result.stdout)
    
    # Print errors if any
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Return appropriate exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 