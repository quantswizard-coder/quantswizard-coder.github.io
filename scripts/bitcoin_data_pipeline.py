#!/usr/bin/env python3
"""Complete Bitcoin Data Pipeline for OpenBB Integration.

This script implements the complete Phase 1 data pipeline:
1. Multi-provider data collection
2. Data validation and quality assurance
3. Technical indicators calculation
4. Data persistence and caching
5. Comprehensive reporting
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np

from data.openbb_client import OpenBBDataClient
from data.crypto_providers import CryptoProviderManager
from data.data_validation import DataValidator
from features.openbb_technical import OpenBBTechnicalIndicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bitcoin_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BitcoinDataPipeline:
    """Complete Bitcoin data pipeline with OpenBB integration."""
    
    def __init__(self, config_path: str = "config/openbb_providers.yaml"):
        """Initialize the Bitcoin data pipeline.
        
        Args:
            config_path: Path to OpenBB provider configuration
        """
        self.config_path = config_path
        self.setup_directories()
        
        # Initialize components
        try:
            self.openbb_client = OpenBBDataClient(config_path)
            self.provider_manager = CryptoProviderManager(config_path)
            self.validator = DataValidator()
            self.tech_indicators = OpenBBTechnicalIndicators()
            logger.info("Bitcoin data pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    def setup_directories(self):
        """Create necessary directories."""
        directories = [
            "data", "data/raw", "data/processed", "data/openbb_cache",
            "logs", "reports"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def run_complete_pipeline(
        self,
        symbol: str = "BTCUSD",
        days_back: int = 365,
        interval: str = "1d"
    ) -> dict:
        """Run the complete data pipeline.
        
        Args:
            symbol: Bitcoin symbol to process
            days_back: Number of days of historical data
            interval: Data interval
            
        Returns:
            Pipeline results dictionary
        """
        logger.info(f"Starting complete Bitcoin data pipeline for {symbol}")
        
        pipeline_start = datetime.now()
        results = {
            'symbol': symbol,
            'interval': interval,
            'days_back': days_back,
            'pipeline_start': pipeline_start,
            'stages': {}
        }
        
        try:
            # Stage 1: Data Collection
            logger.info("Stage 1: Multi-provider data collection")
            collection_results = self._run_data_collection(symbol, days_back, interval)
            results['stages']['data_collection'] = collection_results
            
            if not collection_results.get('success', False):
                logger.error("Data collection failed, stopping pipeline")
                return results
            
            # Stage 2: Data Validation
            logger.info("Stage 2: Data validation and quality assurance")
            validation_results = self._run_data_validation(collection_results['data'])
            results['stages']['data_validation'] = validation_results
            
            # Stage 3: Technical Indicators
            logger.info("Stage 3: Technical indicators calculation")
            technical_results = self._run_technical_analysis(collection_results['data'])
            results['stages']['technical_analysis'] = technical_results
            
            # Stage 4: Data Persistence
            logger.info("Stage 4: Data persistence and caching")
            persistence_results = self._run_data_persistence(
                collection_results['data'],
                technical_results.get('data_with_indicators'),
                symbol
            )
            results['stages']['data_persistence'] = persistence_results
            
            # Stage 5: Reporting
            logger.info("Stage 5: Comprehensive reporting")
            report_results = self._generate_comprehensive_report(results)
            results['stages']['reporting'] = report_results
            
            results['pipeline_end'] = datetime.now()
            results['total_duration'] = (results['pipeline_end'] - pipeline_start).total_seconds()
            results['success'] = True
            
            logger.info(f"Pipeline completed successfully in {results['total_duration']:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['error'] = str(e)
            results['success'] = False
            return results
    
    def _run_data_collection(self, symbol: str, days_back: int, interval: str) -> dict:
        """Run multi-provider data collection."""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get best available data
            best_data, best_provider = self.provider_manager.get_best_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            # Get cross-provider validation data
            provider_data = self.provider_manager.get_cross_provider_validation(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            return {
                'success': True,
                'data': best_data,
                'best_provider': best_provider,
                'provider_data': provider_data,
                'record_count': len(best_data),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_data_validation(self, data: pd.DataFrame) -> dict:
        """Run comprehensive data validation."""
        try:
            # Basic validation
            validation_metrics = self.validator.validate_dataframe(data)
            
            # Additional quality checks
            quality_score = validation_metrics.overall_score
            
            return {
                'success': True,
                'validation_metrics': validation_metrics.dict(),
                'quality_score': quality_score,
                'is_acceptable': quality_score >= 80.0,
                'record_count': len(data),
                'completeness': validation_metrics.completeness
            }
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_technical_analysis(self, data: pd.DataFrame) -> dict:
        """Run technical indicators calculation."""
        try:
            # Calculate all technical indicators
            data_with_indicators = self.tech_indicators.calculate_all_indicators(data)
            
            # Generate trading signals
            signals_data = self.tech_indicators.get_trading_signals(data_with_indicators)
            
            # Get current indicator summary
            indicator_summary = self.tech_indicators.get_indicator_summary(data_with_indicators)
            
            # Count indicators added
            indicators_added = len(data_with_indicators.columns) - len(data.columns)
            
            return {
                'success': True,
                'data_with_indicators': data_with_indicators,
                'signals_data': signals_data,
                'indicator_summary': indicator_summary,
                'indicators_added': indicators_added,
                'latest_price': data_with_indicators['close'].iloc[-1],
                'latest_rsi': data_with_indicators.get('rsi', pd.Series([None])).iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_data_persistence(
        self,
        raw_data: pd.DataFrame,
        processed_data: pd.DataFrame,
        symbol: str
    ) -> dict:
        """Save data to files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save raw data
            raw_file = f"data/raw/{symbol}_raw_{timestamp}.csv"
            raw_data.to_csv(raw_file)
            
            # Save processed data with indicators
            if processed_data is not None:
                processed_file = f"data/processed/{symbol}_processed_{timestamp}.csv"
                processed_data.to_csv(processed_file)
            else:
                processed_file = None
            
            return {
                'success': True,
                'raw_file': raw_file,
                'processed_file': processed_file,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Data persistence failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_comprehensive_report(self, pipeline_results: dict) -> dict:
        """Generate comprehensive pipeline report."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"reports/bitcoin_pipeline_report_{timestamp}.json"
            
            # Create serializable report
            report = {
                'pipeline_summary': {
                    'symbol': pipeline_results['symbol'],
                    'success': pipeline_results.get('success', False),
                    'duration_seconds': pipeline_results.get('total_duration', 0),
                    'timestamp': timestamp
                },
                'data_collection': {
                    'success': pipeline_results['stages']['data_collection']['success'],
                    'best_provider': pipeline_results['stages']['data_collection'].get('best_provider'),
                    'record_count': pipeline_results['stages']['data_collection'].get('record_count', 0)
                },
                'data_validation': {
                    'success': pipeline_results['stages']['data_validation']['success'],
                    'quality_score': pipeline_results['stages']['data_validation'].get('quality_score', 0),
                    'is_acceptable': pipeline_results['stages']['data_validation'].get('is_acceptable', False)
                },
                'technical_analysis': {
                    'success': pipeline_results['stages']['technical_analysis']['success'],
                    'indicators_added': pipeline_results['stages']['technical_analysis'].get('indicators_added', 0),
                    'latest_price': pipeline_results['stages']['technical_analysis'].get('latest_price'),
                    'latest_rsi': pipeline_results['stages']['technical_analysis'].get('latest_rsi')
                }
            }
            
            # Save report
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Comprehensive report saved to {report_file}")
            
            return {
                'success': True,
                'report_file': report_file,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'success': False, 'error': str(e)}


def main():
    """Main function to run the complete Bitcoin data pipeline."""
    logger.info("Starting Bitcoin Data Pipeline")
    
    try:
        # Initialize pipeline
        pipeline = BitcoinDataPipeline()
        
        # Run complete pipeline
        results = pipeline.run_complete_pipeline(
            symbol="BTCUSD",
            days_back=365,
            interval="1d"
        )
        
        if results.get('success', False):
            logger.info("=== PIPELINE SUMMARY ===")
            logger.info(f"Symbol: {results['symbol']}")
            logger.info(f"Duration: {results['total_duration']:.2f} seconds")
            
            # Data collection summary
            dc = results['stages']['data_collection']
            logger.info(f"Data Collection: {dc['record_count']} records from {dc['best_provider']}")
            
            # Validation summary
            dv = results['stages']['data_validation']
            logger.info(f"Data Quality: {dv['quality_score']:.1f}/100 ({'PASS' if dv['is_acceptable'] else 'FAIL'})")
            
            # Technical analysis summary
            ta = results['stages']['technical_analysis']
            logger.info(f"Technical Analysis: {ta['indicators_added']} indicators added")
            logger.info(f"Current Price: ${ta['latest_price']:.2f}")
            if ta['latest_rsi']:
                logger.info(f"Current RSI: {ta['latest_rsi']:.1f}")
            
            logger.info("Bitcoin Data Pipeline completed successfully!")
        else:
            logger.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
