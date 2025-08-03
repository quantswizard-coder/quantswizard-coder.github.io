"""OpenBB utility functions and helpers."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import OpenBB, fallback gracefully if not available
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    logger.warning("OpenBB not available, some features will be limited")


class OpenBBHelpers:
    """Helper utilities for OpenBB integration."""
    
    @staticmethod
    def is_openbb_available() -> bool:
        """Check if OpenBB is available."""
        return OPENBB_AVAILABLE
    
    @staticmethod
    def get_available_crypto_providers() -> List[str]:
        """Get list of available crypto data providers."""
        if not OPENBB_AVAILABLE:
            return ["yfinance"]  # Fallback
        
        try:
            # Get available providers for crypto data
            providers = ["yfinance", "tiingo", "alpha_vantage"]
            # Filter to only available ones
            available = []
            for provider in providers:
                try:
                    # Test provider availability
                    test_data = obb.crypto.price.historical(
                        "BTCUSD", 
                        provider=provider,
                        start_date=(datetime.now() - timedelta(days=1)).date(),
                        end_date=datetime.now().date()
                    )
                    if not test_data.to_dataframe().empty:
                        available.append(provider)
                except Exception as e:
                    logger.debug(f"Provider {provider} not available: {e}")
            
            return available if available else ["yfinance"]
            
        except Exception as e:
            logger.error(f"Error checking providers: {e}")
            return ["yfinance"]
    
    @staticmethod
    def normalize_symbol_for_provider(symbol: str, provider: str) -> str:
        """Normalize cryptocurrency symbol for specific provider."""
        symbol_upper = symbol.upper()
        
        # Provider-specific symbol formatting
        if provider == "yfinance":
            if symbol_upper in ["BTCUSD", "BTC"]:
                return "BTC-USD"
            elif symbol_upper in ["ETHUSD", "ETH"]:
                return "ETH-USD"
            elif symbol_upper in ["ADAUSD", "ADA"]:
                return "ADA-USD"
            elif symbol_upper in ["SOLUSD", "SOL"]:
                return "SOL-USD"
            return symbol
            
        elif provider in ["tiingo", "alpha_vantage"]:
            # These providers typically use BTCUSD format
            if symbol_upper == "BTC-USD":
                return "BTCUSD"
            elif symbol_upper == "ETH-USD":
                return "ETHUSD"
            elif symbol_upper == "ADA-USD":
                return "ADAUSD"
            elif symbol_upper == "SOL-USD":
                return "SOLUSD"
            return symbol_upper
            
        else:
            # Default: return as-is
            return symbol
    
    @staticmethod
    def get_crypto_data_with_fallback(
        symbol: str,
        providers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get crypto data with automatic provider fallback."""
        
        if not OPENBB_AVAILABLE:
            logger.warning("OpenBB not available, using yfinance fallback")
            return OpenBBHelpers._get_yfinance_fallback(symbol, start_date, end_date, interval)
        
        for provider in providers:
            try:
                normalized_symbol = OpenBBHelpers.normalize_symbol_for_provider(symbol, provider)
                
                data = obb.crypto.price.historical(
                    normalized_symbol,
                    provider=provider,
                    start_date=start_date.date() if start_date else None,
                    end_date=end_date.date() if end_date else None,
                    interval=interval
                )
                
                df = data.to_dataframe()
                if not df.empty:
                    logger.info(f"Successfully fetched data from {provider}")
                    return OpenBBHelpers._standardize_columns(df)
                    
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        # Final fallback to yfinance
        logger.warning("All OpenBB providers failed, using yfinance fallback")
        return OpenBBHelpers._get_yfinance_fallback(symbol, start_date, end_date, interval)
    
    @staticmethod
    def _get_yfinance_fallback(
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Fallback to yfinance when OpenBB is not available."""
        try:
            import yfinance as yf
            
            # Normalize symbol for yfinance
            yf_symbol = OpenBBHelpers.normalize_symbol_for_provider(symbol, "yfinance")
            ticker = yf.Ticker(yf_symbol)
            
            if start_date and end_date:
                data = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                data = ticker.history(period="1y", interval=interval)
            
            return OpenBBHelpers._standardize_columns(data)
            
        except Exception as e:
            logger.error(f"YFinance fallback failed: {e}")
            return None
    
    @staticmethod
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
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
    
    @staticmethod
    def get_technical_indicators_openbb(
        data: pd.DataFrame,
        indicators: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Calculate technical indicators using OpenBB if available."""
        
        if not OPENBB_AVAILABLE:
            logger.warning("OpenBB not available, skipping technical indicators")
            return data
        
        if indicators is None:
            indicators = {
                'rsi': {'length': 14},
                'sma': {'length': [20, 50, 200]},
                'ema': {'length': [12, 26]},
                'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                'bbands': {'length': 20, 'std': 2}
            }
        
        result_df = data.copy()
        
        try:
            # Convert DataFrame to format expected by OpenBB technical functions
            data_list = data.reset_index().to_dict('records')
            
            # Calculate RSI
            if 'rsi' in indicators:
                rsi_config = indicators['rsi']
                rsi_data = obb.technical.rsi(data_list, length=rsi_config['length'])
                rsi_df = rsi_data.to_dataframe()
                result_df['rsi'] = rsi_df['rsi']
            
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
            if 'bbands' in indicators:
                bb_config = indicators['bbands']
                bb_data = obb.technical.bbands(
                    data_list,
                    length=bb_config['length'],
                    std=bb_config['std']
                )
                bb_df = bb_data.to_dataframe()
                result_df['bb_upper'] = bb_df['bb_upper']
                result_df['bb_middle'] = bb_df['bb_middle']
                result_df['bb_lower'] = bb_df['bb_lower']
            
        except Exception as e:
            logger.error(f"Error calculating OpenBB technical indicators: {e}")
            
        return result_df
    
    @staticmethod
    def validate_openbb_installation() -> Dict[str, Any]:
        """Validate OpenBB installation and available features."""
        validation_result = {
            'openbb_available': OPENBB_AVAILABLE,
            'version': None,
            'crypto_providers': [],
            'technical_indicators': False,
            'charting': False
        }
        
        if not OPENBB_AVAILABLE:
            return validation_result
        
        try:
            # Check version
            validation_result['version'] = obb.__version__ if hasattr(obb, '__version__') else 'unknown'
            
            # Check crypto providers
            validation_result['crypto_providers'] = OpenBBHelpers.get_available_crypto_providers()
            
            # Check technical indicators
            try:
                test_data = pd.DataFrame({
                    'close': [100, 101, 102, 101, 100],
                    'high': [101, 102, 103, 102, 101],
                    'low': [99, 100, 101, 100, 99],
                    'open': [100, 101, 102, 101, 100],
                    'volume': [1000, 1100, 1200, 1100, 1000]
                })
                test_list = test_data.to_dict('records')
                obb.technical.rsi(test_list, length=14)
                validation_result['technical_indicators'] = True
            except:
                validation_result['technical_indicators'] = False
            
            # Check charting
            try:
                # This is a basic check - actual charting might need more setup
                validation_result['charting'] = hasattr(obb, 'charting')
            except:
                validation_result['charting'] = False
                
        except Exception as e:
            logger.error(f"Error validating OpenBB installation: {e}")
        
        return validation_result
