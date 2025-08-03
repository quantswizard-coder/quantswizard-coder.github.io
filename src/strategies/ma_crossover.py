"""Moving Average Crossover Strategy."""

import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy.
    
    Generates buy signals when fast MA crosses above slow MA,
    and sell signals when fast MA crosses below slow MA.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the MA Crossover strategy.
        
        Args:
            config: Strategy configuration containing:
                - fast_period: Fast MA period (default: 20)
                - slow_period: Slow MA period (default: 50)
                - ma_type: MA type ('sma' or 'ema', default: 'sma')
                - min_crossover_strength: Minimum strength for signal (default: 0.01)
        """
        super().__init__("MA_Crossover", config)
        
        self.fast_period = config.get('fast_period', 20)
        self.slow_period = config.get('slow_period', 50)
        self.ma_type = config.get('ma_type', 'sma')
        self.min_crossover_strength = config.get('min_crossover_strength', 0.01)
        
        # Validation
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")
        
        logger.info(f"Initialized MA Crossover: {self.fast_period}/{self.slow_period} {self.ma_type.upper()}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages and crossover signals.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added MA indicators
        """
        df = data.copy()
        
        # Calculate moving averages
        if self.ma_type == 'sma':
            df[f'ma_fast_{self.fast_period}'] = df['close'].rolling(
                window=self.fast_period, min_periods=self.fast_period
            ).mean()
            df[f'ma_slow_{self.slow_period}'] = df['close'].rolling(
                window=self.slow_period, min_periods=self.slow_period
            ).mean()
        elif self.ma_type == 'ema':
            df[f'ma_fast_{self.fast_period}'] = df['close'].ewm(
                span=self.fast_period, min_periods=self.fast_period
            ).mean()
            df[f'ma_slow_{self.slow_period}'] = df['close'].ewm(
                span=self.slow_period, min_periods=self.slow_period
            ).mean()
        else:
            raise ValueError(f"Unsupported MA type: {self.ma_type}")
        
        # Calculate crossover signals
        fast_col = f'ma_fast_{self.fast_period}'
        slow_col = f'ma_slow_{self.slow_period}'
        
        # Current position: 1 if fast > slow, -1 if fast < slow, 0 if equal
        df['ma_position'] = np.where(
            df[fast_col] > df[slow_col], 1,
            np.where(df[fast_col] < df[slow_col], -1, 0)
        )
        
        # Crossover detection: change in position
        df['ma_crossover'] = df['ma_position'].diff()
        
        # Calculate crossover strength (percentage difference)
        df['ma_strength'] = abs(df[fast_col] - df[slow_col]) / df[slow_col]
        
        # Calculate trend strength (slope of slow MA)
        df['trend_strength'] = df[slow_col].pct_change(periods=5)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate trading signals based on MA crossovers.
        
        Args:
            data: DataFrame with calculated indicators
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Calculate indicators if not present
        required_cols = ['ma_crossover', 'ma_strength', 'trend_strength']
        if not all(col in data.columns for col in required_cols):
            logger.debug("Calculating indicators for MA crossover strategy")
            data = self.calculate_indicators(data)

        # Check again after calculation
        if not all(col in data.columns for col in required_cols):
            logger.warning("Failed to calculate required indicators for MA crossover strategy")
            return signals
        
        # Get the latest data point
        if len(data) < self.slow_period + 1:
            logger.debug(f"Insufficient data: {len(data)} < {self.slow_period + 1}")
            return signals
        
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None
        
        # Check for crossover signals
        if latest['ma_crossover'] == 2.0:  # Fast MA crossed above slow MA
            confidence = self._calculate_buy_confidence(latest, data)
            if confidence > 0.5 and latest['ma_strength'] >= self.min_crossover_strength:
                signals.append(TradingSignal(
                    timestamp=latest.name,
                    signal=SignalType.BUY,
                    confidence=confidence,
                    price=latest['close'],
                    reason=f"MA bullish crossover (strength: {latest['ma_strength']:.3f})",
                    metadata={
                        'fast_ma': latest[f'ma_fast_{self.fast_period}'],
                        'slow_ma': latest[f'ma_slow_{self.slow_period}'],
                        'crossover_strength': latest['ma_strength'],
                        'trend_strength': latest['trend_strength']
                    }
                ))
        
        elif latest['ma_crossover'] == -2.0:  # Fast MA crossed below slow MA
            confidence = self._calculate_sell_confidence(latest, data)
            if confidence > 0.5 and latest['ma_strength'] >= self.min_crossover_strength:
                signals.append(TradingSignal(
                    timestamp=latest.name,
                    signal=SignalType.SELL,
                    confidence=confidence,
                    price=latest['close'],
                    reason=f"MA bearish crossover (strength: {latest['ma_strength']:.3f})",
                    metadata={
                        'fast_ma': latest[f'ma_fast_{self.fast_period}'],
                        'slow_ma': latest[f'ma_slow_{self.slow_period}'],
                        'crossover_strength': latest['ma_strength'],
                        'trend_strength': latest['trend_strength']
                    }
                ))
        
        # Add hold signal if no crossover
        if not signals:
            signals.append(TradingSignal(
                timestamp=latest.name,
                signal=SignalType.HOLD,
                confidence=0.5,
                price=latest['close'],
                reason="No MA crossover signal",
                metadata={'ma_position': latest['ma_position']}
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
        
        # Increase confidence based on crossover strength
        strength_bonus = min(0.3, latest['ma_strength'] * 10)
        confidence += strength_bonus
        
        # Increase confidence if trend is upward
        if latest['trend_strength'] > 0:
            trend_bonus = min(0.2, latest['trend_strength'] * 5)
            confidence += trend_bonus
        
        # Increase confidence if volume is above average (if available)
        if 'volume' in data.columns and len(data) >= 20:
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            if latest['volume'] > avg_volume * 1.2:
                confidence += 0.1
        
        # Decrease confidence if recent volatility is high
        if len(data) >= 10:
            recent_volatility = data['close'].pct_change().rolling(10).std().iloc[-1]
            if recent_volatility > 0.05:  # 5% daily volatility
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
        
        # Increase confidence based on crossover strength
        strength_bonus = min(0.3, latest['ma_strength'] * 10)
        confidence += strength_bonus
        
        # Increase confidence if trend is downward
        if latest['trend_strength'] < 0:
            trend_bonus = min(0.2, abs(latest['trend_strength']) * 5)
            confidence += trend_bonus
        
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
            'type': 'trend_following',
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'ma_type': self.ma_type,
                'min_crossover_strength': self.min_crossover_strength
            },
            'description': f"{self.ma_type.upper()} {self.fast_period}/{self.slow_period} crossover strategy"
        }
