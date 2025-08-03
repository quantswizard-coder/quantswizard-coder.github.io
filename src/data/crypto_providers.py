"""Multi-provider cryptocurrency data management."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Try to import OpenBB, fallback if not available
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    import yfinance as yf

try:
    from .openbb_client import OpenBBDataClient
except ImportError:
    from src.data.openbb_client import OpenBBDataClient

try:
    from ..utils.openbb_helpers import OpenBBHelpers
except ImportError:
    try:
        from src.utils.openbb_helpers import OpenBBHelpers
    except ImportError:
        # Create a minimal fallback if openbb_helpers is not available
        class OpenBBHelpers:
            @staticmethod
            def is_openbb_available():
                return False

logger = logging.getLogger(__name__)


class CryptoProviderManager:
    """Manages multiple cryptocurrency data providers."""
    
    def __init__(self, config_path: str = "config/openbb_providers.yaml"):
        """Initialize the provider manager.
        
        Args:
            config_path: Path to provider configuration
        """
        self.client = OpenBBDataClient(config_path)
        self.provider_priority = self._get_provider_priority()
        
    def _get_provider_priority(self) -> List[str]:
        """Get providers sorted by priority."""
        providers = [(name, config.priority) for name, config in self.client.providers.items()]
        providers.sort(key=lambda x: x[1])
        return [name for name, _ in providers]
    
    def get_best_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> Tuple[pd.DataFrame, str]:
        """Get the best available data from providers.
        
        Args:
            symbol: Cryptocurrency symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            Tuple of (DataFrame, provider_name)
        """
        for provider in self.provider_priority:
            try:
                logger.info(f"Trying provider: {provider}")
                
                # Map symbol format for different providers
                mapped_symbol = self._map_symbol(symbol, provider)
                
                data = self.client.get_crypto_data(
                    symbol=mapped_symbol,
                    provider=provider,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval
                )
                
                # Validate data quality
                quality_metrics = self.client.validate_data_quality(data)
                
                if self._is_data_acceptable(quality_metrics):
                    logger.info(f"Successfully got data from {provider}")
                    return data, provider
                else:
                    logger.warning(f"Data quality issues with {provider}: {quality_metrics}")
                    
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {str(e)}")
                continue
        
        raise Exception("No providers returned acceptable data")
    
    def _map_symbol(self, symbol: str, provider: str) -> str:
        """Map symbol format for different providers.
        
        Args:
            symbol: Standard symbol (e.g., "BTCUSD")
            provider: Provider name
            
        Returns:
            Provider-specific symbol format
        """
        symbol_mappings = {
            "yfinance": {
                "BTCUSD": "BTC-USD",
                "ETHUSD": "ETH-USD",
                "BTCEUR": "BTC-EUR",
                "ETHEUR": "ETH-EUR"
            },
            "tiingo": {
                "BTCUSD": "BTCUSD",
                "ETHUSD": "ETHUSD"
            },
            "alpha_vantage": {
                "BTCUSD": "BTC",
                "ETHUSD": "ETH"
            },
            "fmp": {
                "BTCUSD": "BTCUSD",
                "ETHUSD": "ETHUSD"
            }
        }
        
        provider_mapping = symbol_mappings.get(provider, {})
        return provider_mapping.get(symbol, symbol)
    
    def _is_data_acceptable(self, quality_metrics: Dict[str, float]) -> bool:
        """Check if data quality is acceptable.
        
        Args:
            quality_metrics: Data quality metrics
            
        Returns:
            True if data is acceptable
        """
        min_completeness = self.client.config.get("validation", {}).get(
            "min_data_completeness_percent", 95.0
        )
        
        return (
            quality_metrics["completeness"] >= min_completeness and
            quality_metrics["record_count"] > 0 and
            quality_metrics["duplicate_count"] == 0
        )
    
    def get_cross_provider_validation(
        self,
        symbol: str,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """Get data from multiple providers for cross-validation.
        
        Args:
            symbol: Cryptocurrency symbol
            providers: List of providers to use
            **kwargs: Additional arguments
            
        Returns:
            Dictionary of provider data
        """
        if providers is None:
            providers = self.provider_priority[:3]  # Use top 3 providers
        
        results = {}
        for provider in providers:
            try:
                mapped_symbol = self._map_symbol(symbol, provider)
                data = self.client.get_crypto_data(
                    symbol=mapped_symbol,
                    provider=provider,
                    **kwargs
                )
                results[provider] = data
            except Exception as e:
                logger.warning(f"Failed to get data from {provider}: {str(e)}")
        
        return results
    
    def compare_provider_data(
        self,
        symbol: str,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Compare data across providers.
        
        Args:
            symbol: Cryptocurrency symbol
            providers: List of providers to compare
            **kwargs: Additional arguments
            
        Returns:
            DataFrame with comparison metrics
        """
        provider_data = self.get_cross_provider_validation(symbol, providers, **kwargs)
        
        if len(provider_data) < 2:
            raise ValueError("Need at least 2 providers for comparison")
        
        comparison_results = []
        
        for provider, data in provider_data.items():
            if len(data) > 0:
                metrics = {
                    'provider': provider,
                    'record_count': len(data),
                    'start_date': data.index[0],
                    'end_date': data.index[-1],
                    'avg_close': data['close'].mean(),
                    'std_close': data['close'].std(),
                    'min_close': data['close'].min(),
                    'max_close': data['close'].max(),
                    'avg_volume': data['volume'].mean() if 'volume' in data.columns else 0,
                    'completeness': (1 - data.isnull().sum().sum() / data.size) * 100
                }
                comparison_results.append(metrics)
        
        return pd.DataFrame(comparison_results)
    
    def detect_price_anomalies(
        self,
        provider_data: Dict[str, pd.DataFrame],
        max_deviation_percent: float = 5.0
    ) -> pd.DataFrame:
        """Detect price anomalies across providers.
        
        Args:
            provider_data: Dictionary of provider data
            max_deviation_percent: Maximum allowed price deviation
            
        Returns:
            DataFrame with anomaly information
        """
        if len(provider_data) < 2:
            return pd.DataFrame()
        
        # Align data by date
        aligned_data = {}
        common_dates = None
        
        for provider, data in provider_data.items():
            if len(data) > 0:
                aligned_data[provider] = data['close']
                if common_dates is None:
                    common_dates = set(data.index)
                else:
                    common_dates = common_dates.intersection(set(data.index))
        
        if not common_dates:
            return pd.DataFrame()
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame()
        for provider, prices in aligned_data.items():
            comparison_df[provider] = prices.reindex(sorted(common_dates))
        
        # Calculate deviations
        anomalies = []
        for date in comparison_df.index:
            prices = comparison_df.loc[date].dropna()
            if len(prices) >= 2:
                mean_price = prices.mean()
                for provider, price in prices.items():
                    deviation_percent = abs((price - mean_price) / mean_price) * 100
                    if deviation_percent > max_deviation_percent:
                        anomalies.append({
                            'date': date,
                            'provider': provider,
                            'price': price,
                            'mean_price': mean_price,
                            'deviation_percent': deviation_percent
                        })
        
        return pd.DataFrame(anomalies)
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get status of all configured providers.
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        
        for provider_name in self.provider_priority:
            try:
                # Test with a simple data request
                test_data = self.client.get_crypto_data(
                    symbol=self._map_symbol("BTCUSD", provider_name),
                    provider=provider_name,
                    start_date=(datetime.now() - timedelta(days=7)).date(),
                    end_date=datetime.now().date()
                )
                
                status[provider_name] = {
                    'status': 'active',
                    'last_update': datetime.now(),
                    'record_count': len(test_data),
                    'data_quality': self.client.validate_data_quality(test_data)
                }
                
            except Exception as e:
                status[provider_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_update': datetime.now()
                }
        
        return status
