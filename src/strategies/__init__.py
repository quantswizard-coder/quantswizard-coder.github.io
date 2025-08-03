"""Trading strategies package."""

from .base_strategy import BaseStrategy, TradingSignal, SignalType, PositionType, Position, Trade
from .ma_crossover import MovingAverageCrossoverStrategy
from .rsi_mean_reversion import RSIMeanReversionStrategy
from .ensemble_strategy import EnsembleStrategy, SimpleMomentumStrategy

__all__ = [
    'BaseStrategy',
    'TradingSignal',
    'SignalType',
    'PositionType',
    'Position',
    'Trade',
    'MovingAverageCrossoverStrategy',
    'RSIMeanReversionStrategy',
    'EnsembleStrategy',
    'SimpleMomentumStrategy'
]
