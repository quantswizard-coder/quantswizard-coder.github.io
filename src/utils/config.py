"""Configuration management utilities."""

import os
from pathlib import Path
from typing import Dict, Any

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for the Bitcoin Quant Trading System."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.load_environment()
        
    def load_environment(self):
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
    
    def get_openbb_config(self) -> Dict[str, Any]:
        """Get OpenBB provider configuration.
        
        Returns:
            Dictionary with OpenBB configuration
        """
        config_file = self.config_dir / "openbb_providers.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_openbb_config()
    
    def _get_default_openbb_config(self) -> Dict[str, Any]:
        """Get default OpenBB configuration."""
        return {
            "providers": {
                "yfinance": {
                    "enabled": True,
                    "priority": 1,
                    "description": "Yahoo Finance",
                    "symbols": ["BTC-USD", "ETH-USD"],
                    "intervals": ["1d", "1h"],
                    "max_history_days": 365
                }
            },
            "validation": {
                "cross_provider_check": True,
                "max_price_deviation_percent": 5.0,
                "min_data_completeness_percent": 95.0
            },
            "cache": {
                "enabled": True,
                "directory": "data/openbb_cache",
                "max_age_hours": 24
            }
        }
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys from environment variables.
        
        Returns:
            Dictionary with API keys
        """
        return {
            "tiingo": os.getenv("TIINGO_API_KEY", ""),
            "alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
            "fmp": os.getenv("FMP_API_KEY", ""),
            "polygon": os.getenv("POLYGON_API_KEY", ""),
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration.
        
        Returns:
            Dictionary with database configuration
        """
        return {
            "url": os.getenv("DATABASE_URL", "sqlite:///data/trading_data.db"),
            "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true"
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Dictionary with logging configuration
        """
        return {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "logs/bitcoin_quant.log"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    def get_mlflow_config(self) -> Dict[str, str]:
        """Get MLflow configuration.
        
        Returns:
            Dictionary with MLflow configuration
        """
        return {
            "tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
            "experiment_name": os.getenv("MLFLOW_EXPERIMENT_NAME", "bitcoin-quant-trading")
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration.
        
        Returns:
            Dictionary with trading configuration
        """
        return {
            "paper_trading": os.getenv("PAPER_TRADING", "true").lower() == "true",
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "0.1")),
            "risk_tolerance": float(os.getenv("RISK_TOLERANCE", "0.02")),
            "base_currency": os.getenv("BASE_CURRENCY", "USD")
        }
