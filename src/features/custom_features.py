"""Custom feature engineering beyond OpenBB technical indicators."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CustomFeatureEngineer:
    """Custom feature engineering for cryptocurrency trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the custom feature engineer.
        
        Args:
            config: Configuration dictionary for feature parameters
        """
        self.config = config or {}
        
    def add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added price features
        """
        df = data.copy()
        
        # Price returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Price gaps
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        df['gap_filled'] = np.where(
            (df['gap'] > 0) & (df['low'] <= df['close'].shift(1)), 1,
            np.where((df['gap'] < 0) & (df['high'] >= df['close'].shift(1)), 1, 0)
        )
        
        # High-Low spread
        df['hl_spread'] = (df['high'] - df['low']) / df['close']
        df['hl_spread_ma'] = df['hl_spread'].rolling(window=20).mean()
        
        # Price position within daily range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # Intraday momentum
        df['intraday_momentum'] = (df['close'] - df['open']) / df['open']
        
        return df
    
    def add_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added volume features
        """
        df = data.copy()
        
        if 'volume' not in df.columns:
            logger.warning("Volume column not found, skipping volume features")
            return df
        
        # Volume moving averages
        for period in [5, 10, 20, 50]:
            df[f'volume_ma_{period}'] = df['volume'].rolling(window=period).mean()
        
        # Volume ratios
        df['volume_ratio_5'] = df['volume'] / df['volume'].rolling(window=5).mean()
        df['volume_ratio_20'] = df['volume'] / df['volume'].rolling(window=20).mean()
        
        # Volume-Price Trend (VPT)
        df['vpt'] = (df['volume'] * df['returns']).cumsum()
        
        # On-Balance Volume (OBV)
        df['obv'] = np.where(df['returns'] > 0, df['volume'], 
                            np.where(df['returns'] < 0, -df['volume'], 0)).cumsum()
        
        # Volume-Weighted Average Price (VWAP) approximation
        df['vwap'] = (df['close'] * df['volume']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
        
        # Accumulation/Distribution Line
        df['ad_line'] = (((df['close'] - df['low']) - (df['high'] - df['close'])) / 
                        (df['high'] - df['low']) * df['volume']).cumsum()
        
        return df
    
    def add_volatility_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add volatility-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added volatility features
        """
        df = data.copy()
        
        # Historical volatility (different periods)
        for period in [5, 10, 20, 50]:
            df[f'volatility_{period}'] = df['returns'].rolling(window=period).std() * np.sqrt(252)
        
        # Parkinson volatility (using high-low)
        df['parkinson_vol'] = np.sqrt(
            (1 / (4 * np.log(2))) * 
            (np.log(df['high'] / df['low']) ** 2).rolling(window=20).mean() * 252
        )
        
        # Garman-Klass volatility
        df['gk_vol'] = np.sqrt(
            (0.5 * (np.log(df['high'] / df['low']) ** 2) - 
             (2 * np.log(2) - 1) * (np.log(df['close'] / df['open']) ** 2)).rolling(window=20).mean() * 252
        )
        
        # Volatility regime (high/low volatility periods)
        vol_median = df['volatility_20'].rolling(window=100).median()
        df['vol_regime'] = np.where(df['volatility_20'] > vol_median, 1, 0)
        
        # Volatility mean reversion
        df['vol_mean_reversion'] = (df['volatility_20'] - df['volatility_20'].rolling(window=50).mean()) / df['volatility_20'].rolling(window=50).std()
        
        return df
    
    def add_momentum_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add momentum-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added momentum features
        """
        df = data.copy()
        
        # Rate of Change (ROC) for different periods
        for period in [5, 10, 20, 50]:
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        # Momentum oscillator
        df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        # Price acceleration
        df['price_acceleration'] = df['returns'].diff()
        
        # Trend strength
        for period in [10, 20, 50]:
            df[f'trend_strength_{period}'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period)
        
        # Moving average convergence/divergence ratios
        df['ma_ratio_20_50'] = df['close'].rolling(20).mean() / df['close'].rolling(50).mean()
        df['ma_ratio_10_20'] = df['close'].rolling(10).mean() / df['close'].rolling(20).mean()
        
        return df
    
    def add_pattern_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add pattern recognition features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added pattern features
        """
        df = data.copy()
        
        # Doji patterns (open ≈ close)
        body_size = abs(df['close'] - df['open']) / df['close']
        df['doji'] = (body_size < 0.001).astype(int)
        
        # Hammer/Hanging man patterns
        lower_shadow = df['open'].combine(df['close'], min) - df['low']
        upper_shadow = df['high'] - df['open'].combine(df['close'], max)
        body = abs(df['close'] - df['open'])
        
        df['hammer'] = ((lower_shadow > 2 * body) & (upper_shadow < 0.1 * body)).astype(int)
        
        # Engulfing patterns
        df['bullish_engulfing'] = (
            (df['close'] > df['open']) &  # Current candle is bullish
            (df['close'].shift(1) < df['open'].shift(1)) &  # Previous candle is bearish
            (df['open'] < df['close'].shift(1)) &  # Current open < previous close
            (df['close'] > df['open'].shift(1))  # Current close > previous open
        ).astype(int)
        
        df['bearish_engulfing'] = (
            (df['close'] < df['open']) &  # Current candle is bearish
            (df['close'].shift(1) > df['open'].shift(1)) &  # Previous candle is bullish
            (df['open'] > df['close'].shift(1)) &  # Current open > previous close
            (df['close'] < df['open'].shift(1))  # Current close < previous open
        ).astype(int)
        
        # Support/Resistance levels (simplified)
        df['local_high'] = (
            (df['high'] > df['high'].shift(1)) & 
            (df['high'] > df['high'].shift(-1))
        ).astype(int)
        
        df['local_low'] = (
            (df['low'] < df['low'].shift(1)) & 
            (df['low'] < df['low'].shift(-1))
        ).astype(int)
        
        return df
    
    def add_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features.
        
        Args:
            data: DataFrame with datetime index
            
        Returns:
            DataFrame with added time features
        """
        df = data.copy()
        
        # Extract time components
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Cyclical encoding for time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Market session indicators (assuming UTC time)
        df['asian_session'] = ((df['hour'] >= 0) & (df['hour'] < 8)).astype(int)
        df['european_session'] = ((df['hour'] >= 8) & (df['hour'] < 16)).astype(int)
        df['american_session'] = ((df['hour'] >= 16) & (df['hour'] < 24)).astype(int)
        
        # Weekend indicator
        df['weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        return df
    
    def add_all_custom_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add all custom features to the dataset.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with all custom features added
        """
        logger.info("Adding custom features...")
        
        df = data.copy()
        
        # Add all feature categories
        df = self.add_price_features(df)
        df = self.add_volume_features(df)
        df = self.add_volatility_features(df)
        df = self.add_momentum_features(df)
        df = self.add_pattern_features(df)
        df = self.add_time_features(df)
        
        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Added {len(df.columns) - len(data.columns)} custom features")
        
        return df
    
    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """Get feature groups for importance analysis.
        
        Returns:
            Dictionary mapping feature group names to feature lists
        """
        return {
            'price': ['returns', 'log_returns', 'gap', 'hl_spread', 'price_position', 'intraday_momentum'],
            'volume': ['volume_ratio_5', 'volume_ratio_20', 'vpt', 'obv', 'vwap', 'ad_line'],
            'volatility': ['volatility_5', 'volatility_10', 'volatility_20', 'parkinson_vol', 'gk_vol', 'vol_regime'],
            'momentum': ['roc_5', 'roc_10', 'roc_20', 'momentum_10', 'momentum_20', 'trend_strength_20'],
            'patterns': ['doji', 'hammer', 'bullish_engulfing', 'bearish_engulfing', 'local_high', 'local_low'],
            'time': ['hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'asian_session', 'european_session']
        }
