"""Simple test runner that adds src to path."""
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Run pytest
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "tests/"]))
