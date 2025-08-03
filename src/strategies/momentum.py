"""Simple momentum strategy for trend following."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class SimpleMomentumStrategy(BaseStrategy):
    """Simple momentum strategy that follows price trends."""
    
    def __init__(self, params: Optional[Dict] = None):
        """Initialize the momentum strategy.
        
        Args:
            params: Strategy parameters including lookback period and threshold
        """
        config = params or {}
        super().__init__("SimpleMomentumStrategy", config)
        
        # Strategy parameters
        self.lookback_period = config.get('lookback_period', 10)
        self.momentum_threshold = config.get('momentum_threshold', 0.005)  # 0.5% threshold
        
        logger.info(f"Initialized SimpleMomentumStrategy with lookback_period={self.lookback_period}, "
                   f"momentum_threshold={self.momentum_threshold}")
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate trading signals based on momentum.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of trading signals
        """
        if len(data) < self.lookback_period + 1:
            return []
        
        signals = []
        
        # Calculate momentum as percentage change over lookback period
        data = data.copy()
        data['momentum'] = data['close'].pct_change(periods=self.lookback_period)
        
        for i in range(self.lookback_period, len(data)):
            current_momentum = data['momentum'].iloc[i]
            timestamp = data.index[i]
            price = data['close'].iloc[i]
            
            # Skip if momentum is NaN
            if pd.isna(current_momentum):
                continue
            
            signal_type = None
            confidence = 0.0
            
            # Generate signals based on momentum threshold
            if current_momentum > self.momentum_threshold:
                # Strong positive momentum - buy signal
                signal_type = SignalType.BUY
                confidence = min(abs(current_momentum) / (self.momentum_threshold * 2), 1.0)
            elif current_momentum < -self.momentum_threshold:
                # Strong negative momentum - sell signal
                signal_type = SignalType.SELL
                confidence = min(abs(current_momentum) / (self.momentum_threshold * 2), 1.0)
            
            if signal_type:
                signal = TradingSignal(
                    timestamp=timestamp,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=price,
                    metadata={
                        'momentum': current_momentum,
                        'threshold': self.momentum_threshold,
                        'lookback_period': self.lookback_period
                    }
                )
                signals.append(signal)
        
        logger.info(f"Generated {len(signals)} momentum signals")
        return signals
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and parameters."""
        return {
            'name': 'Simple Momentum',
            'description': 'Follows price momentum over a specified lookback period',
            'type': 'momentum',
            'parameters': {
                'lookback_period': {
                    'value': self.lookback_period,
                    'description': 'Number of periods to calculate momentum',
                    'min': 5,
                    'max': 30
                },
                'momentum_threshold': {
                    'value': self.momentum_threshold,
                    'description': 'Minimum momentum required for signal',
                    'min': 0.001,
                    'max': 0.02
                }
            }
        }
    
    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        if 'lookback_period' in params:
            self.lookback_period = int(params['lookback_period'])
        if 'momentum_threshold' in params:
            self.momentum_threshold = float(params['momentum_threshold'])
        
        logger.info(f"Updated parameters: lookback_period={self.lookback_period}, "
                   f"momentum_threshold={self.momentum_threshold}")
