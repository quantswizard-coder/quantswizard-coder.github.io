"""Ensemble strategy that combines multiple trading signals."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .base_strategy import BaseStrategy, TradingSignal, SignalType
from .ma_crossover import MovingAverageCrossoverStrategy
from .rsi_mean_reversion import RSIMeanReversionStrategy

logger = logging.getLogger(__name__)


class EnsembleStrategy(BaseStrategy):
    """Ensemble strategy combining multiple sub-strategies with voting."""
    
    def __init__(self, params: Optional[Dict] = None):
        """Initialize the ensemble strategy.

        Args:
            params: Strategy parameters including sub-strategy configurations
        """
        config = params or {}
        super().__init__("EnsembleStrategy", config)
        
        # Default ensemble parameters
        self.ensemble_method = params.get('ensemble_method', 'weighted_voting')
        self.min_consensus = params.get('min_consensus', 0.6)  # 60% agreement required
        self.confidence_threshold = params.get('confidence_threshold', 0.5)
        
        # Sub-strategy weights
        self.strategy_weights = params.get('strategy_weights', {
            'ma_crossover': 0.4,
            'rsi_mean_reversion': 0.3,
            'momentum': 0.3
        })
        
        # Initialize sub-strategies
        self.sub_strategies = self._initialize_sub_strategies(params)
        
        logger.info(f"Initialized Ensemble Strategy with {len(self.sub_strategies)} sub-strategies")
        logger.info(f"Ensemble method: {self.ensemble_method}, min consensus: {self.min_consensus}")
    
    def _initialize_sub_strategies(self, params: Dict) -> Dict[str, BaseStrategy]:
        """Initialize all sub-strategies.
        
        Args:
            params: Main strategy parameters
            
        Returns:
            Dictionary of initialized sub-strategies
        """
        sub_strategies = {}
        
        # MA Crossover Strategy
        ma_params = params.get('ma_crossover_params', {
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'sma',
            'min_crossover_strength': 0.0,  # Accept all crossovers
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.08
        })
        sub_strategies['ma_crossover'] = MovingAverageCrossoverStrategy(ma_params)
        
        # RSI Mean Reversion Strategy
        rsi_params = params.get('rsi_params', {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'stop_loss_percent': 0.03,
            'take_profit_percent': 0.08
        })
        sub_strategies['rsi_mean_reversion'] = RSIMeanReversionStrategy(rsi_params)
        
        # Simple Momentum Strategy (built-in)
        momentum_params = params.get('momentum_params', {
            'lookback_period': 20,
            'momentum_threshold': 0.02
        })
        sub_strategies['momentum'] = SimpleMomentumStrategy(momentum_params)
        
        return sub_strategies
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for all sub-strategies.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with all indicators
        """
        result_data = data.copy()
        
        # Calculate indicators for each sub-strategy
        for name, strategy in self.sub_strategies.items():
            try:
                strategy_data = strategy.calculate_indicators(data)
                
                # Add strategy-specific columns with prefix
                for col in strategy_data.columns:
                    if col not in data.columns:  # Only add new columns
                        result_data[f"{name}_{col}"] = strategy_data[col]
                        
            except Exception as e:
                logger.warning(f"Error calculating indicators for {name}: {e}")
        
        return result_data


    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate ensemble signals by combining sub-strategy signals.

        Args:
            data: OHLCV DataFrame with indicators

        Returns:
            List of ensemble trading signals
        """
        if len(data) < 50:  # Need sufficient data
            return []

        # Get signals from all sub-strategies
        # Each strategy calculates its own indicators to avoid column conflicts
        sub_signals = {}
        for name, strategy in self.sub_strategies.items():
            try:
                # Let each strategy calculate its own indicators and generate signals
                signals = strategy.generate_signals(data)
                sub_signals[name] = signals
                logger.info(f"Strategy {name} generated {len(signals)} signals")
                if signals:
                    for signal in signals:
                        logger.info(f"  {name}: {signal.signal} at {signal.timestamp} with confidence {signal.confidence:.3f}")
            except Exception as e:
                logger.warning(f"Error generating signals for {name}: {e}")
                sub_signals[name] = []
        
        # Combine signals using ensemble method
        if self.ensemble_method == 'weighted_voting':
            return self._weighted_voting_ensemble(sub_signals, data)
        elif self.ensemble_method == 'majority_voting':
            return self._majority_voting_ensemble(sub_signals, data)
        elif self.ensemble_method == 'confidence_weighted':
            return self._confidence_weighted_ensemble(sub_signals, data)
        else:
            return self._simple_average_ensemble(sub_signals, data)
    
    def _weighted_voting_ensemble(
        self, 
        sub_signals: Dict[str, List[TradingSignal]], 
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """Combine signals using weighted voting.
        
        Args:
            sub_signals: Dictionary of sub-strategy signals
            data: OHLCV DataFrame
            
        Returns:
            List of ensemble signals
        """
        ensemble_signals = []
        
        # Get the latest timestamp
        if data.empty:
            return []
        
        latest_timestamp = data.index[-1]
        latest_price = data['close'].iloc[-1]
        
        # Collect latest signals from each strategy
        latest_signals = {}
        for strategy_name, signals in sub_signals.items():
            if signals:
                # Get the most recent signal
                latest_signal = signals[-1]
                latest_signals[strategy_name] = latest_signal
        
        if not latest_signals:
            return []
        
        # Calculate weighted vote
        buy_weight = 0.0
        sell_weight = 0.0
        hold_weight = 0.0
        total_confidence = 0.0
        
        for strategy_name, signal in latest_signals.items():
            weight = self.strategy_weights.get(strategy_name, 0.0)
            confidence = signal.confidence
            
            if signal.signal == SignalType.BUY:
                buy_weight += weight * confidence
            elif signal.signal == SignalType.SELL:
                sell_weight += weight * confidence
            else:
                hold_weight += weight * confidence
            
            total_confidence += weight * confidence
        
        # Determine ensemble signal
        max_weight = max(buy_weight, sell_weight, hold_weight)
        
        if max_weight == 0:
            return []
        
        # Check if consensus meets minimum threshold
        consensus_strength = max_weight / sum(self.strategy_weights.values())

        logger.info(f"Consensus check: max_weight={max_weight:.3f}, total_weights={sum(self.strategy_weights.values()):.3f}, consensus={consensus_strength:.3f}, min_required={self.min_consensus:.3f}")

        if consensus_strength < self.min_consensus:
            logger.info(f"Consensus too low: {consensus_strength:.3f} < {self.min_consensus:.3f}")
            return []  # No consensus

        # Generate ensemble signal
        if max_weight == buy_weight:
            signal_type = SignalType.BUY
        elif max_weight == sell_weight:
            signal_type = SignalType.SELL
        else:
            logger.info("Max weight is HOLD, skipping signal")
            return []  # Don't generate HOLD signals

        # Calculate ensemble confidence - only consider active signals (not HOLD)
        active_signals = [sig for sig in latest_signals.values() if sig.signal != SignalType.HOLD]
        if active_signals:
            ensemble_confidence = min(1.0, sum(sig.confidence for sig in active_signals) / len(active_signals))
        else:
            ensemble_confidence = 0.0

        logger.info(f"Confidence check: ensemble_confidence={ensemble_confidence:.3f} (from {len(active_signals)} active signals), threshold={self.confidence_threshold:.3f}")

        if ensemble_confidence < self.confidence_threshold:
            logger.info(f"Confidence too low: {ensemble_confidence:.3f} < {self.confidence_threshold:.3f}")
            return []
        
        # Create ensemble signal
        ensemble_signal = TradingSignal(
            timestamp=latest_timestamp,
            signal=signal_type,
            confidence=ensemble_confidence,
            price=latest_price,
            reason=f"Ensemble {signal_type.value} (consensus: {consensus_strength:.2f})",
            metadata={
                'ensemble_method': 'weighted_voting',
                'consensus_strength': consensus_strength,
                'contributing_strategies': list(latest_signals.keys()),
                'buy_weight': buy_weight,
                'sell_weight': sell_weight,
                'sub_signals': {name: {'signal': str(sig.signal), 'confidence': sig.confidence}
                              for name, sig in latest_signals.items()}
            }
        )
        
        ensemble_signals.append(ensemble_signal)
        
        logger.info(f"Ensemble signal: {signal_type} with confidence {ensemble_confidence:.3f} "
                   f"(consensus: {consensus_strength:.3f})")
        
        return ensemble_signals
    
    def _majority_voting_ensemble(
        self, 
        sub_signals: Dict[str, List[TradingSignal]], 
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """Simple majority voting ensemble."""
        # Implementation similar to weighted voting but with equal weights
        equal_weights = {name: 1.0/len(sub_signals) for name in sub_signals.keys()}
        
        # Temporarily override weights
        original_weights = self.strategy_weights.copy()
        self.strategy_weights = equal_weights
        
        result = self._weighted_voting_ensemble(sub_signals, data)
        
        # Restore original weights
        self.strategy_weights = original_weights
        
        return result
    
    def _confidence_weighted_ensemble(
        self,
        sub_signals: Dict[str, List[TradingSignal]],
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """Ensemble weighted by signal confidence."""
        logger.info(f"Confidence weighted ensemble: {len(sub_signals)} strategies")

        # Similar to weighted voting but weights are determined by confidence
        latest_signals = {}
        for strategy_name, signals in sub_signals.items():
            if signals:
                latest_signals[strategy_name] = signals[-1]
                logger.info(f"  {strategy_name}: {signals[-1].signal} confidence {signals[-1].confidence:.3f}")

        if not latest_signals:
            logger.info("No signals from any strategy")
            return []

        # Calculate confidence-based weights
        confidence_weights = {}
        total_confidence = sum(sig.confidence for sig in latest_signals.values())

        logger.info(f"Total confidence: {total_confidence:.3f}")

        if total_confidence == 0:
            logger.info("Zero total confidence")
            return []

        for strategy_name, signal in latest_signals.items():
            confidence_weights[strategy_name] = signal.confidence / total_confidence
            logger.info(f"  {strategy_name} weight: {confidence_weights[strategy_name]:.3f}")

        # Temporarily override weights
        original_weights = self.strategy_weights.copy()
        self.strategy_weights = confidence_weights

        result = self._weighted_voting_ensemble(sub_signals, data)

        # Restore original weights
        self.strategy_weights = original_weights

        logger.info(f"Confidence weighted ensemble result: {len(result)} signals")

        return result
    
    def _simple_average_ensemble(
        self, 
        sub_signals: Dict[str, List[TradingSignal]], 
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """Simple average of all signals."""
        return self._majority_voting_ensemble(sub_signals, data)


class SimpleMomentumStrategy(BaseStrategy):
    """Simple momentum strategy for ensemble use."""
    
    def __init__(self, params: Optional[Dict] = None):
        """Initialize momentum strategy."""
        config = params or {}
        super().__init__("SimpleMomentumStrategy", config)
        self.lookback_period = params.get('lookback_period', 20)
        self.momentum_threshold = params.get('momentum_threshold', 0.02)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators."""
        result = data.copy()
        
        # Simple momentum: current price vs N periods ago
        result['momentum'] = data['close'].pct_change(periods=self.lookback_period)
        
        # Momentum strength
        result['momentum_strength'] = abs(result['momentum'])
        
        # Momentum direction
        result['momentum_direction'] = np.where(result['momentum'] > 0, 1, -1)
        
        return result
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate momentum-based signals."""
        if len(data) < self.lookback_period + 5:
            return []
        
        data_with_indicators = self.calculate_indicators(data)
        
        # Get latest values
        latest_momentum = data_with_indicators['momentum'].iloc[-1]
        latest_strength = data_with_indicators['momentum_strength'].iloc[-1]
        latest_price = data['close'].iloc[-1]
        latest_timestamp = data.index[-1]
        
        # Check for valid momentum
        if pd.isna(latest_momentum) or pd.isna(latest_strength):
            return []
        
        # Generate signal based on momentum
        if latest_strength > self.momentum_threshold:
            if latest_momentum > 0:
                signal_type = SignalType.BUY
            else:
                signal_type = SignalType.SELL
            
            # Confidence based on momentum strength
            confidence = min(1.0, latest_strength / (self.momentum_threshold * 2))
            
            signal = TradingSignal(
                timestamp=latest_timestamp,
                signal=signal_type,
                confidence=confidence,
                price=latest_price,
                reason=f"Momentum {signal_type.value} (strength: {latest_strength:.3f})",
                metadata={
                    'momentum': latest_momentum,
                    'momentum_strength': latest_strength,
                    'lookback_period': self.lookback_period
                }
            )
            
            return [signal]
        
        return []
