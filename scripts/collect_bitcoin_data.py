#!/usr/bin/env python3
"""Bitcoin Data Collection Script for OpenBB Integration.

This script implements Phase 1 of the PROJECT_PLAN.md:
- OpenBB Platform setup and provider configuration
- Multi-provider crypto data pipeline
- Data validation across OpenBB providers
- Data caching and persistence strategy
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np

from data.openbb_client import OpenBBDataClient
from data.crypto_providers import CryptoProviderManager
from data.data_validation import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bitcoin_data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BitcoinDataCollector:
    """Bitcoin data collector using OpenBB Platform."""
    
    def __init__(self, config_path: str = "config/openbb_providers.yaml"):
        """Initialize the Bitcoin data collector.
        
        Args:
            config_path: Path to OpenBB provider configuration
        """
        self.config_path = config_path
        self.data_dir = Path("data")
        self.cache_dir = Path("data/openbb_cache")
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize components
        try:
            self.openbb_client = OpenBBDataClient(config_path)
            self.provider_manager = CryptoProviderManager(config_path)
            self.validator = DataValidator()
            logger.info("Bitcoin data collector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data collector: {e}")
            raise
    
    def collect_bitcoin_data(
        self,
        symbol: str = "BTCUSD",
        days_back: int = 365,
        interval: str = "1d"
    ) -> dict:
        """Collect Bitcoin data from multiple providers.
        
        Args:
            symbol: Bitcoin symbol to collect
            days_back: Number of days of historical data
            interval: Data interval
            
        Returns:
            Dictionary with collection results
        """
        logger.info(f"Starting Bitcoin data collection for {symbol}")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        results = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval,
            'providers': {},
            'validation': {},
            'best_data': None,
            'best_provider': None,
            'collection_time': datetime.now()
        }
        
        try:
            # Step 1: Get data from best available provider
            logger.info("Getting best available data...")
            best_data, best_provider = self.provider_manager.get_best_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            results['best_data'] = best_data
            results['best_provider'] = best_provider
            
            logger.info(f"Best data from {best_provider}: {len(best_data)} records")
            
            # Step 2: Cross-provider validation
            logger.info("Performing cross-provider validation...")
            provider_data = self.provider_manager.get_cross_provider_validation(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            results['providers'] = provider_data
            
            # Step 3: Validate each provider's data
            for provider, data in provider_data.items():
                if not data.empty:
                    validation_metrics = self.validator.validate_dataframe(data)
                    results['validation'][provider] = validation_metrics.dict()
                    logger.info(f"{provider} validation score: {validation_metrics.overall_score:.1f}")
            
            # Step 4: Compare providers
            if len(provider_data) > 1:
                comparison = self.provider_manager.compare_provider_data(symbol)
                results['provider_comparison'] = comparison
                logger.info("Provider comparison completed")
            
            # Step 5: Save data
            self._save_data(results)
            
            logger.info("Bitcoin data collection completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error during data collection: {e}")
            results['error'] = str(e)
            return results
    
    def _save_data(self, results: dict):
        """Save collected data to files.
        
        Args:
            results: Collection results dictionary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = results['symbol']
        
        # Save best data as CSV
        if results['best_data'] is not None and not results['best_data'].empty:
            csv_path = self.data_dir / f"{symbol}_data_{timestamp}.csv"
            results['best_data'].to_csv(csv_path)
            logger.info(f"Saved best data to {csv_path}")
        
        # Save validation results
        validation_path = self.data_dir / f"{symbol}_validation_{timestamp}.json"
        import json
        with open(validation_path, 'w') as f:
            # Convert non-serializable objects
            serializable_results = self._make_serializable(results)
            json.dump(serializable_results, f, indent=2, default=str)
        logger.info(f"Saved validation results to {validation_path}")
    
    def _make_serializable(self, obj):
        """Make object JSON serializable."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            return f"DataFrame with {len(obj)} records"
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return obj
    
    def get_provider_status(self) -> dict:
        """Get status of all configured providers."""
        logger.info("Checking provider status...")
        return self.provider_manager.get_provider_status()
    
    def run_data_quality_report(self, symbol: str = "BTCUSD") -> dict:
        """Run comprehensive data quality report.
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Data quality report
        """
        logger.info(f"Running data quality report for {symbol}")
        
        try:
            # Get data from all providers
            provider_data = self.provider_manager.get_cross_provider_validation(symbol)
            
            report = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'providers': {},
                'anomalies': None,
                'recommendations': []
            }
            
            # Validate each provider
            for provider, data in provider_data.items():
                if not data.empty:
                    metrics = self.validator.validate_dataframe(data)
                    report['providers'][provider] = metrics.dict()
            
            # Detect anomalies
            if len(provider_data) > 1:
                anomalies = self.provider_manager.detect_price_anomalies(provider_data)
                if not anomalies.empty:
                    report['anomalies'] = anomalies.to_dict('records')
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, report: dict) -> list:
        """Generate data quality recommendations."""
        recommendations = []
        
        for provider, metrics in report.get('providers', {}).items():
            if metrics['overall_score'] < 80:
                recommendations.append(f"Consider reviewing {provider} data quality (score: {metrics['overall_score']:.1f})")
            
            if metrics['completeness'] < 95:
                recommendations.append(f"{provider} has incomplete data ({metrics['completeness']:.1f}% complete)")
        
        if report.get('anomalies'):
            recommendations.append(f"Found {len(report['anomalies'])} price anomalies across providers")
        
        return recommendations


def main():
    """Main function to run Bitcoin data collection."""
    logger.info("Starting Bitcoin data collection script")
    
    try:
        # Initialize collector
        collector = BitcoinDataCollector()
        
        # Check provider status
        status = collector.get_provider_status()
        logger.info("Provider status:")
        for provider, info in status.items():
            logger.info(f"  {provider}: {info['status']}")
        
        # Collect Bitcoin data
        results = collector.collect_bitcoin_data(
            symbol="BTCUSD",
            days_back=365,
            interval="1d"
        )
        
        if 'error' not in results:
            logger.info(f"Successfully collected {len(results['best_data'])} records from {results['best_provider']}")
            
            # Run quality report
            quality_report = collector.run_data_quality_report("BTCUSD")
            logger.info("Data quality report completed")
            
            if quality_report.get('recommendations'):
                logger.info("Recommendations:")
                for rec in quality_report['recommendations']:
                    logger.info(f"  - {rec}")
        else:
            logger.error(f"Data collection failed: {results['error']}")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
