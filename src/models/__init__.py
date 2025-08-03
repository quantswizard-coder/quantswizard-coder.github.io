"""
Bitcoin Quant Trading Models Package

This package contains trading models and strategies for Bitcoin quantitative trading.
"""

from .baselines import (
    BaselineStrategy,
    MovingAverageCrossover,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    MultiIndicatorStrategy
)

__all__ = [
    'BaselineStrategy',
    'MovingAverageCrossover', 
    'RSIStrategy',
    'MACDStrategy',
    'BollingerBandsStrategy',
    'MultiIndicatorStrategy'
]
