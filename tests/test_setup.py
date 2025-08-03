"""Test basic setup and imports."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that core modules can be imported."""
    try:
        from utils.config import Config

        # Test basic instantiation
        config = Config()
        assert config is not None

        # Test configuration loading
        openbb_config = config.get_openbb_config()
        assert "providers" in openbb_config

        print("✅ All imports successful")

    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_yfinance_available():
    """Test that YFinance is available."""
    try:
        import yfinance as yf

        # Test basic YFinance functionality
        ticker = yf.Ticker("BTC-USD")
        assert ticker is not None

        print("✅ YFinance is available")

    except ImportError as e:
        pytest.fail(f"YFinance not available: {e}")


def test_project_structure():
    """Test that project structure is correct."""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "src",
        "src/data",
        "src/utils",
        "ui",
        "config",
        "data",
        "notebooks",
        "tests"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Missing directory: {dir_path}"
    
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        "PROJECT_PLAN.md",
        "config/openbb_providers.yaml",
        "src/__init__.py",
        "src/data/__init__.py",
        "src/main.py"
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Missing file: {file_path}"
    
    print("✅ Project structure is correct")


if __name__ == "__main__":
    test_imports()
    test_yfinance_available()
    test_project_structure()
    print("🎉 All tests passed!")
