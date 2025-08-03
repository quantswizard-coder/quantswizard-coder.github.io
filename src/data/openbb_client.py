"""OpenBB Data Client for Bitcoin Quant Trading System."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
import yaml
from pydantic import BaseModel
import warnings
warnings.filterwarnings('ignore')

# Try to import OpenBB, fallback to yfinance if not available
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    import yfinance as yf

logger = logging.getLogger(__name__)


class DataProviderConfig(BaseModel):
    """Configuration for a data provider."""
    
    enabled: bool
    priority: int
    description: str
    symbols: List[str]
    intervals: List[str]
    max_history_days: int
    api_key_required: bool = False
    exchanges: Optional[List[str]] = None
    max_requests_per_minute: Optional[int] = None


class OpenBBDataClient:
    """OpenBB data client for cryptocurrency data."""
    
    def __init__(self, config_path: str = "config/openbb_providers.yaml"):
        """Initialize the OpenBB data client.
        
        Args:
            config_path: Path to the provider configuration file
        """
        self.config = self._load_config(config_path)
        self.providers = self._initialize_providers()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load provider configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration if config file is not found."""
        return {
            "providers": {
                "yfinance": {
                    "enabled": True,
                    "priority": 1,
                    "description": "Yahoo Finance",
                    "symbols": ["BTC-USD"],
                    "intervals": ["1d"],
                    "max_history_days": 365
                }
            }
        }
    
    def _initialize_providers(self) -> Dict[str, DataProviderConfig]:
        """Initialize provider configurations."""
        providers = {}
        for name, config in self.config.get("providers", {}).items():
            if config.get("enabled", False):
                providers[name] = DataProviderConfig(**config)
        return providers
    
    def get_crypto_data(
        self,
        symbol: str,
        provider: str = "yfinance",
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get cryptocurrency historical data from OpenBB or fallback.

        Args:
            symbol: Cryptocurrency symbol (e.g., "BTCUSD", "BTC-USD")
            provider: Data provider name
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now().date()
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).date()

            logger.info(f"Fetching {symbol} data from {provider}")

            if OPENBB_AVAILABLE and provider != "yfinance":
                # Try OpenBB first for non-yfinance providers
                try:
                    data = obb.crypto.price.historical(
                        symbol=self._normalize_symbol_for_provider(symbol, provider),
                        provider=provider,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    )
                    df = data.to_dataframe()
                    logger.info(f"Successfully fetched {len(df)} records from OpenBB {provider}")
                except Exception as openbb_error:
                    logger.warning(f"OpenBB {provider} failed: {openbb_error}, trying yfinance")
                    df = self._get_yfinance_data(symbol, start_date, end_date, interval)
            else:
                # Use yfinance directly
                df = self._get_yfinance_data(symbol, start_date, end_date, interval)

            # Standardize column names and add metadata
            df = self._standardize_columns(df)
            df.attrs['provider'] = provider
            df.attrs['symbol'] = symbol
            df.attrs['fetch_time'] = datetime.now()

            logger.info(f"Successfully fetched {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Error fetching data from {provider}: {str(e)}")
            raise
    
    def get_multi_provider_data(
        self,
        symbol: str,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """Get data from multiple providers for comparison.
        
        Args:
            symbol: Cryptocurrency symbol
            providers: List of provider names (if None, uses all enabled)
            **kwargs: Additional arguments for get_crypto_data
            
        Returns:
            Dictionary mapping provider names to DataFrames
        """
        if providers is None:
            providers = list(self.providers.keys())
        
        results = {}
        for provider in providers:
            try:
                df = self.get_crypto_data(symbol, provider, **kwargs)
                results[provider] = df
            except Exception as e:
                logger.warning(f"Failed to get data from {provider}: {str(e)}")
                
        return results

    def _get_yfinance_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, datetime]],
        end_date: Optional[Union[str, datetime]],
        interval: str
    ) -> pd.DataFrame:
        """Get data using yfinance fallback."""
        import yfinance as yf

        # Normalize symbol for yfinance (expects BTC-USD format)
        if symbol.upper() == "BTCUSD":
            yf_symbol = "BTC-USD"
        elif symbol.upper() == "ETHUSD":
            yf_symbol = "ETH-USD"
        else:
            yf_symbol = symbol

        ticker = yf.Ticker(yf_symbol)

        if start_date and end_date:
            data = ticker.history(start=start_date, end=end_date, interval=interval)
        else:
            data = ticker.history(period="1y", interval=interval)

        return data

    def _normalize_symbol_for_provider(self, symbol: str, provider: str) -> str:
        """Normalize symbol format for different providers."""
        symbol_upper = symbol.upper()

        # Provider-specific symbol formatting
        if provider == "yfinance":
            if symbol_upper == "BTCUSD":
                return "BTC-USD"
            elif symbol_upper == "ETHUSD":
                return "ETH-USD"
            return symbol
        elif provider in ["tiingo", "alpha_vantage"]:
            # These providers typically use BTCUSD format
            if symbol_upper == "BTC-USD":
                return "BTCUSD"
            elif symbol_upper == "ETH-USD":
                return "ETHUSD"
            return symbol_upper
        else:
            # Default: return as-is
            return symbol

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names across providers."""
        column_mapping = {
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close'
        }
        
        # Rename columns if they exist
        df = df.rename(columns=column_mapping)
        
        # Ensure we have the basic OHLCV columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing column: {col}")
        
        return df
    
    def get_technical_indicators(
        self,
        data: pd.DataFrame,
        indicators: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Calculate technical indicators using OpenBB.
        
        Args:
            data: OHLCV DataFrame
            indicators: Dictionary of indicators to calculate
            
        Returns:
            DataFrame with technical indicators
        """
        if indicators is None:
            indicators = self.config.get("technical_indicators", {}).get("default_periods", {})
        
        result_df = data.copy()
        
        try:
            # Convert DataFrame to OpenBB format for technical analysis
            data_list = data.reset_index().to_dict('records')
            
            # Calculate RSI
            if 'rsi' in indicators:
                for period in indicators['rsi']:
                    rsi_data = obb.technical.rsi(data_list, length=period)
                    rsi_df = rsi_data.to_dataframe()
                    result_df[f'rsi_{period}'] = rsi_df['rsi']
            
            # Calculate MACD
            if 'macd' in indicators:
                macd_config = indicators['macd']
                macd_data = obb.technical.macd(
                    data_list,
                    fast=macd_config['fast'],
                    slow=macd_config['slow'],
                    signal=macd_config['signal']
                )
                macd_df = macd_data.to_dataframe()
                result_df['macd'] = macd_df['macd']
                result_df['macd_signal'] = macd_df['macd_signal']
                result_df['macd_histogram'] = macd_df['macd_histogram']
            
            # Calculate Bollinger Bands
            if 'bollinger_bands' in indicators:
                bb_config = indicators['bollinger_bands']
                bb_data = obb.technical.bbands(
                    data_list,
                    length=bb_config['period'],
                    std=bb_config['std']
                )
                bb_df = bb_data.to_dataframe()
                result_df['bb_upper'] = bb_df['bb_upper']
                result_df['bb_middle'] = bb_df['bb_middle']
                result_df['bb_lower'] = bb_df['bb_lower']
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            
        return result_df
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, float]:
        """Validate data quality metrics.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            'completeness': (1 - df.isnull().sum().sum() / df.size) * 100,
            'record_count': len(df),
            'date_range_days': (df.index[-1] - df.index[0]).days if len(df) > 0 else 0,
            'duplicate_count': df.duplicated().sum(),
            'zero_volume_count': (df['volume'] == 0).sum() if 'volume' in df.columns else 0
        }
        
        return metrics
