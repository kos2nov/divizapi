#!/usr/bin/env python3
"""
Test runner script for the Echo Service.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the test suite."""
    print("🧪 Running Echo Service Tests")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "-v", 
            "--tb=short",
            str(project_root / "tests")
        ], cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
