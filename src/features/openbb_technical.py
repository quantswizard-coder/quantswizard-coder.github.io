"""OpenBB Technical Indicators Integration for Bitcoin Quant Trading System.

This module provides technical indicators using OpenBB Platform with fallback
to pandas-ta when OpenBB is not available.
"""

import logging
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np

# Try to import OpenBB technical indicators
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    # Fallback to pandas-ta
    try:
        import pandas_ta as ta
        PANDAS_TA_AVAILABLE = True
    except ImportError:
        PANDAS_TA_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenBBTechnicalIndicators:
    """Technical indicators using OpenBB Platform with fallbacks."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize technical indicators calculator.
        
        Args:
            config: Configuration for technical indicators
        """
        self.config = config or self._get_default_config()
        self.available_backend = self._determine_backend()
        logger.info(f"Technical indicators backend: {self.available_backend}")
    
    def _get_default_config(self) -> Dict:
        """Get default technical indicators configuration."""
        return {
            "sma_periods": [20, 50, 200],
            "ema_periods": [12, 26],
            "rsi_period": 14,
            "macd": {
                "fast": 12,
                "slow": 26,
                "signal": 9
            },
            "bollinger_bands": {
                "period": 20,
                "std": 2
            },
            "atr_period": 14,
            "stochastic": {
                "k_period": 14,
                "d_period": 3
            }
        }
    
    def _determine_backend(self) -> str:
        """Determine which backend to use for technical indicators."""
        if OPENBB_AVAILABLE:
            return "openbb"
        elif PANDAS_TA_AVAILABLE:
            return "pandas_ta"
        else:
            return "manual"
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all configured technical indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with technical indicators added
        """
        if data.empty:
            logger.warning("Empty data provided for technical indicators")
            return data
        
        result_df = data.copy()
        
        try:
            # Moving Averages
            result_df = self.add_moving_averages(result_df)
            
            # RSI
            result_df = self.add_rsi(result_df)
            
            # MACD
            result_df = self.add_macd(result_df)
            
            # Bollinger Bands
            result_df = self.add_bollinger_bands(result_df)
            
            # ATR
            result_df = self.add_atr(result_df)
            
            # Stochastic
            result_df = self.add_stochastic(result_df)
            
            logger.info(f"Added technical indicators using {self.available_backend} backend")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return result_df
    
    def add_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add Simple and Exponential Moving Averages."""
        result_df = data.copy()
        
        # Simple Moving Averages
        for period in self.config["sma_periods"]:
            if self.available_backend == "pandas_ta":
                result_df[f'sma_{period}'] = ta.sma(data['close'], length=period)
            else:
                result_df[f'sma_{period}'] = data['close'].rolling(window=period).mean()
        
        # Exponential Moving Averages
        for period in self.config["ema_periods"]:
            if self.available_backend == "pandas_ta":
                result_df[f'ema_{period}'] = ta.ema(data['close'], length=period)
            else:
                result_df[f'ema_{period}'] = data['close'].ewm(span=period).mean()
        
        return result_df
    
    def add_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add Relative Strength Index."""
        result_df = data.copy()
        period = self.config["rsi_period"]
        
        if self.available_backend == "pandas_ta":
            result_df['rsi'] = ta.rsi(data['close'], length=period)
        else:
            # Manual RSI calculation
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            result_df['rsi'] = 100 - (100 / (1 + rs))
        
        return result_df
    
    def add_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add MACD (Moving Average Convergence Divergence)."""
        result_df = data.copy()
        fast = self.config["macd"]["fast"]
        slow = self.config["macd"]["slow"]
        signal = self.config["macd"]["signal"]
        
        if self.available_backend == "pandas_ta":
            macd_data = ta.macd(data['close'], fast=fast, slow=slow, signal=signal)
            result_df['macd'] = macd_data[f'MACD_{fast}_{slow}_{signal}']
            result_df['macd_signal'] = macd_data[f'MACDs_{fast}_{slow}_{signal}']
            result_df['macd_histogram'] = macd_data[f'MACDh_{fast}_{slow}_{signal}']
        else:
            # Manual MACD calculation
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            result_df['macd'] = ema_fast - ema_slow
            result_df['macd_signal'] = result_df['macd'].ewm(span=signal).mean()
            result_df['macd_histogram'] = result_df['macd'] - result_df['macd_signal']
        
        return result_df
    
    def add_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Bands."""
        result_df = data.copy()
        period = self.config["bollinger_bands"]["period"]
        std_dev = self.config["bollinger_bands"]["std"]
        
        if self.available_backend == "pandas_ta":
            bb_data = ta.bbands(data['close'], length=period, std=std_dev)
            result_df['bb_upper'] = bb_data[f'BBU_{period}_{std_dev}']
            result_df['bb_middle'] = bb_data[f'BBM_{period}_{std_dev}']
            result_df['bb_lower'] = bb_data[f'BBL_{period}_{std_dev}']
        else:
            # Manual Bollinger Bands calculation
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()
            result_df['bb_upper'] = sma + (std * std_dev)
            result_df['bb_middle'] = sma
            result_df['bb_lower'] = sma - (std * std_dev)
        
        return result_df
    
    def add_atr(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add Average True Range."""
        result_df = data.copy()
        period = self.config["atr_period"]
        
        if self.available_backend == "pandas_ta":
            result_df['atr'] = ta.atr(data['high'], data['low'], data['close'], length=period)
        else:
            # Manual ATR calculation
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            result_df['atr'] = true_range.rolling(window=period).mean()
        
        return result_df
    
    def add_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add Stochastic Oscillator."""
        result_df = data.copy()
        k_period = self.config["stochastic"]["k_period"]
        d_period = self.config["stochastic"]["d_period"]
        
        if self.available_backend == "pandas_ta":
            stoch_data = ta.stoch(data['high'], data['low'], data['close'], 
                                k=k_period, d=d_period)
            result_df['stoch_k'] = stoch_data[f'STOCHk_{k_period}_{d_period}_{d_period}']
            result_df['stoch_d'] = stoch_data[f'STOCHd_{k_period}_{d_period}_{d_period}']
        else:
            # Manual Stochastic calculation
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()
            k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
            result_df['stoch_k'] = k_percent
            result_df['stoch_d'] = k_percent.rolling(window=d_period).mean()
        
        return result_df
    
    def get_trading_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate basic trading signals from technical indicators.
        
        Args:
            data: DataFrame with technical indicators
            
        Returns:
            DataFrame with trading signals
        """
        signals_df = data.copy()
        
        # RSI signals
        if 'rsi' in signals_df.columns:
            signals_df['rsi_oversold'] = signals_df['rsi'] < 30
            signals_df['rsi_overbought'] = signals_df['rsi'] > 70
        
        # MACD signals
        if all(col in signals_df.columns for col in ['macd', 'macd_signal']):
            signals_df['macd_bullish'] = (signals_df['macd'] > signals_df['macd_signal']) & \
                                       (signals_df['macd'].shift(1) <= signals_df['macd_signal'].shift(1))
            signals_df['macd_bearish'] = (signals_df['macd'] < signals_df['macd_signal']) & \
                                       (signals_df['macd'].shift(1) >= signals_df['macd_signal'].shift(1))
        
        # Bollinger Bands signals
        if all(col in signals_df.columns for col in ['close', 'bb_upper', 'bb_lower']):
            signals_df['bb_squeeze'] = signals_df['close'] < signals_df['bb_lower']
            signals_df['bb_breakout'] = signals_df['close'] > signals_df['bb_upper']
        
        # Moving Average crossover
        if all(col in signals_df.columns for col in ['ema_12', 'ema_26']):
            signals_df['ma_golden_cross'] = (signals_df['ema_12'] > signals_df['ema_26']) & \
                                          (signals_df['ema_12'].shift(1) <= signals_df['ema_26'].shift(1))
            signals_df['ma_death_cross'] = (signals_df['ema_12'] < signals_df['ema_26']) & \
                                         (signals_df['ema_12'].shift(1) >= signals_df['ema_26'].shift(1))
        
        return signals_df
    
    def get_indicator_summary(self, data: pd.DataFrame) -> Dict:
        """Get summary of current technical indicator values.
        
        Args:
            data: DataFrame with technical indicators
            
        Returns:
            Dictionary with current indicator values
        """
        if data.empty:
            return {}
        
        latest = data.iloc[-1]
        summary = {
            'timestamp': latest.name,
            'price': latest.get('close', 0),
            'indicators': {}
        }
        
        # Add available indicators
        indicator_columns = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        for col in indicator_columns:
            if not col.startswith('_'):  # Skip private columns
                summary['indicators'][col] = latest.get(col, None)
        
        return summary
