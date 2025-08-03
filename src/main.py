"""Main entry point for Bitcoin Quant Trading System."""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from data.crypto_providers import CryptoProviderManager
from data.data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_data_pipeline(symbol: str, days: int = 365, provider: str = "yfinance"):
    """Set up and test the data pipeline.
    
    Args:
        symbol: Cryptocurrency symbol
        days: Number of days of historical data
        provider: Data provider to use
    """
    logger.info(f"Setting up data pipeline for {symbol}")
    
    try:
        # Initialize components
        provider_manager = CryptoProviderManager()
        validator = DataValidator()
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        # Get data
        logger.info(f"Fetching {days} days of {symbol} data from {provider}")
        data, actual_provider = provider_manager.get_best_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Retrieved {len(data)} records from {actual_provider}")
        
        # Validate data quality
        quality_metrics = validator.validate_dataframe(data)
        logger.info(f"Data quality score: {quality_metrics.overall_score:.1f}%")
        
        # Display summary
        print(f"\n=== Data Pipeline Summary ===")
        print(f"Symbol: {symbol}")
        print(f"Provider: {actual_provider}")
        print(f"Records: {len(data)}")
        print(f"Date Range: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"Quality Score: {quality_metrics.overall_score:.1f}%")
        print(f"Completeness: {quality_metrics.completeness:.1f}%")
        print(f"Accuracy: {quality_metrics.accuracy:.1f}%")
        print(f"Consistency: {quality_metrics.consistency:.1f}%")
        
        # Show recent data
        print(f"\n=== Recent Data (Last 5 Records) ===")
        print(data.tail().round(2))
        
        return data, quality_metrics
        
    except Exception as e:
        logger.error(f"Data pipeline setup failed: {str(e)}")
        raise


def test_multi_provider_validation(symbol: str, days: int = 30):
    """Test multi-provider data validation.
    
    Args:
        symbol: Cryptocurrency symbol
        days: Number of days of data
    """
    logger.info(f"Testing multi-provider validation for {symbol}")
    
    try:
        provider_manager = CryptoProviderManager()
        validator = DataValidator()
        
        # Get data from multiple providers
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        provider_data = provider_manager.get_cross_provider_validation(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if len(provider_data) < 2:
            logger.warning("Need at least 2 providers for validation")
            return
        
        # Compare providers
        comparison = provider_manager.compare_provider_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n=== Multi-Provider Comparison ===")
        print(comparison.round(2))
        
        # Cross-validate
        validation_scores = validator.cross_validate_providers(provider_data)
        
        print(f"\n=== Cross-Validation Scores ===")
        for provider, score in validation_scores.items():
            print(f"{provider}: {score:.1f}%")
        
        # Detect anomalies
        anomalies = provider_manager.detect_price_anomalies(provider_data)
        
        if not anomalies.empty:
            print(f"\n=== Price Anomalies Detected ===")
            print(anomalies)
        else:
            print(f"\n=== No Price Anomalies Detected ===")
        
        return comparison, validation_scores, anomalies
        
    except Exception as e:
        logger.error(f"Multi-provider validation failed: {str(e)}")
        raise


def run_dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    import sys
    
    dashboard_path = Path(__file__).parent.parent / "ui" / "bitcoin_dashboard.py"
    
    logger.info("Launching Streamlit dashboard...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to launch dashboard: {e}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bitcoin Quant Trading System")
    parser.add_argument("--mode", choices=["data", "validate", "dashboard"], 
                       default="dashboard", help="Operation mode")
    parser.add_argument("--symbol", default="BTCUSD", help="Cryptocurrency symbol")
    parser.add_argument("--days", type=int, default=365, help="Days of historical data")
    parser.add_argument("--provider", default="yfinance", help="Data provider")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Bitcoin Quant Trading System in {args.mode} mode")
    
    try:
        if args.mode == "data":
            setup_data_pipeline(args.symbol, args.days, args.provider)
            
        elif args.mode == "validate":
            test_multi_provider_validation(args.symbol, args.days)
            
        elif args.mode == "dashboard":
            run_dashboard()
            
        logger.info("Operation completed successfully")
        
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
