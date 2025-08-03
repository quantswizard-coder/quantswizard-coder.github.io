"""RSI Mean Reversion Strategy."""

import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class RSIMeanReversionStrategy(BaseStrategy):
    """RSI Mean Reversion Strategy.
    
    Generates buy signals when RSI is oversold (< oversold_threshold),
    and sell signals when RSI is overbought (> overbought_threshold).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the RSI Mean Reversion strategy.
        
        Args:
            config: Strategy configuration containing:
                - rsi_period: RSI calculation period (default: 14)
                - oversold_threshold: RSI oversold level (default: 30)
                - overbought_threshold: RSI overbought level (default: 70)
                - extreme_oversold: Extreme oversold level (default: 20)
                - extreme_overbought: Extreme overbought level (default: 80)
        """
        super().__init__("RSI_Mean_Reversion", config)
        
        self.rsi_period = config.get('rsi_period', 14)
        self.oversold_threshold = config.get('oversold_threshold', 30)
        self.overbought_threshold = config.get('overbought_threshold', 70)
        self.extreme_oversold = config.get('extreme_oversold', 20)
        self.extreme_overbought = config.get('extreme_overbought', 80)
        
        # Validation
        if self.oversold_threshold >= self.overbought_threshold:
            raise ValueError("Oversold threshold must be less than overbought threshold")
        
        logger.info(f"Initialized RSI Mean Reversion: period={self.rsi_period}, "
                   f"thresholds=({self.oversold_threshold}, {self.overbought_threshold})")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI and related indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added RSI indicators
        """
        df = data.copy()
        
        # Calculate RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # RSI momentum (rate of change)
        df['rsi_momentum'] = df['rsi'].diff()
        
        # RSI smoothed (3-period SMA of RSI)
        df['rsi_smooth'] = df['rsi'].rolling(window=3, min_periods=1).mean()
        
        # RSI divergence detection (simplified)
        df['price_momentum'] = df['close'].pct_change(periods=5)
        df['rsi_change'] = df['rsi'].diff(periods=5)
        
        # Signal zones
        df['rsi_oversold'] = df['rsi'] < self.oversold_threshold
        df['rsi_overbought'] = df['rsi'] > self.overbought_threshold
        df['rsi_extreme_oversold'] = df['rsi'] < self.extreme_oversold
        df['rsi_extreme_overbought'] = df['rsi'] > self.extreme_overbought
        
        # RSI trend (above/below 50)
        df['rsi_bullish'] = df['rsi'] > 50
        df['rsi_bearish'] = df['rsi'] < 50
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI (Relative Strength Index).
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI series
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate trading signals based on RSI levels.
        
        Args:
            data: DataFrame with calculated indicators
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Calculate indicators if not present
        required_cols = ['rsi', 'rsi_oversold', 'rsi_overbought']
        if not all(col in data.columns for col in required_cols):
            logger.debug("Calculating indicators for RSI strategy")
            data = self.calculate_indicators(data)

        # Check again after calculation
        if not all(col in data.columns for col in required_cols):
            logger.warning("Failed to calculate required indicators for RSI strategy")
            return signals
        
        # Get the latest data point
        if len(data) < self.rsi_period + 1:
            logger.debug(f"Insufficient data: {len(data)} < {self.rsi_period + 1}")
            return signals
        
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None
        
        # Check for oversold buy signals
        if latest['rsi_oversold'] and not pd.isna(latest['rsi']):
            confidence = self._calculate_buy_confidence(latest, data)
            if confidence > 0.5:
                reason = f"RSI oversold: {latest['rsi']:.1f}"
                if latest['rsi_extreme_oversold']:
                    reason = f"RSI extremely oversold: {latest['rsi']:.1f}"
                    confidence = min(1.0, confidence + 0.2)
                
                signals.append(TradingSignal(
                    timestamp=latest.name,
                    signal=SignalType.BUY,
                    confidence=confidence,
                    price=latest['close'],
                    reason=reason,
                    metadata={
                        'rsi': latest['rsi'],
                        'rsi_momentum': latest.get('rsi_momentum', 0),
                        'is_extreme': latest['rsi_extreme_oversold']
                    }
                ))
        
        # Check for overbought sell signals
        elif latest['rsi_overbought'] and not pd.isna(latest['rsi']):
            confidence = self._calculate_sell_confidence(latest, data)
            if confidence > 0.5:
                reason = f"RSI overbought: {latest['rsi']:.1f}"
                if latest['rsi_extreme_overbought']:
                    reason = f"RSI extremely overbought: {latest['rsi']:.1f}"
                    confidence = min(1.0, confidence + 0.2)
                
                signals.append(TradingSignal(
                    timestamp=latest.name,
                    signal=SignalType.SELL,
                    confidence=confidence,
                    price=latest['close'],
                    reason=reason,
                    metadata={
                        'rsi': latest['rsi'],
                        'rsi_momentum': latest.get('rsi_momentum', 0),
                        'is_extreme': latest['rsi_extreme_overbought']
                    }
                ))
        
        # Add hold signal if no clear signal
        if not signals:
            signals.append(TradingSignal(
                timestamp=latest.name,
                signal=SignalType.HOLD,
                confidence=0.5,
                price=latest['close'],
                reason=f"RSI neutral: {latest['rsi']:.1f}",
                metadata={'rsi': latest['rsi']}
            ))
        
        return signals
    
    def _calculate_buy_confidence(self, latest: pd.Series, data: pd.DataFrame) -> float:
        """Calculate confidence for buy signals.
        
        Args:
            latest: Latest data point
            data: Full DataFrame
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for lower RSI values
        rsi_strength = (self.oversold_threshold - latest['rsi']) / self.oversold_threshold
        confidence += min(0.3, rsi_strength * 0.5)
        
        # Increase confidence if RSI is turning up
        if 'rsi_momentum' in latest and latest['rsi_momentum'] > 0:
            confidence += 0.1
        
        # Increase confidence if price momentum is positive (potential divergence)
        if 'price_momentum' in latest and latest['price_momentum'] > 0:
            confidence += 0.1
        
        # Increase confidence if volume is above average (if available)
        if 'volume' in data.columns and len(data) >= 20:
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            if latest['volume'] > avg_volume * 1.2:
                confidence += 0.1
        
        # Decrease confidence if in strong downtrend
        if len(data) >= 20:
            price_trend = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            if price_trend < -0.1:  # 10% decline over 20 periods
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_sell_confidence(self, latest: pd.Series, data: pd.DataFrame) -> float:
        """Calculate confidence for sell signals.
        
        Args:
            latest: Latest data point
            data: Full DataFrame
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for higher RSI values
        rsi_strength = (latest['rsi'] - self.overbought_threshold) / (100 - self.overbought_threshold)
        confidence += min(0.3, rsi_strength * 0.5)
        
        # Increase confidence if RSI is turning down
        if 'rsi_momentum' in latest and latest['rsi_momentum'] < 0:
            confidence += 0.1
        
        # Increase confidence if price momentum is negative (potential divergence)
        if 'price_momentum' in latest and latest['price_momentum'] < 0:
            confidence += 0.1
        
        # Increase confidence if volume is above average (if available)
        if 'volume' in data.columns and len(data) >= 20:
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            if latest['volume'] > avg_volume * 1.2:
                confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and parameters."""
        return {
            'name': self.name,
            'type': 'mean_reversion',
            'parameters': {
                'rsi_period': self.rsi_period,
                'oversold_threshold': self.oversold_threshold,
                'overbought_threshold': self.overbought_threshold,
                'extreme_oversold': self.extreme_oversold,
                'extreme_overbought': self.extreme_overbought
            },
            'description': f"RSI({self.rsi_period}) mean reversion with {self.oversold_threshold}/{self.overbought_threshold} thresholds"
        }
