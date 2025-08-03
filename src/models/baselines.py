"""
Baseline Trading Strategies for Bitcoin Quantitative Trading

This module implements fundamental trading strategies using technical indicators
from our OpenBB-enhanced data pipeline.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Signal(Enum):
    """Trading signal enumeration"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class TradeSignal:
    """Trade signal with metadata"""
    timestamp: pd.Timestamp
    signal: Signal
    price: float
    confidence: float
    reason: str
    indicators: Dict[str, float]


class BaselineStrategy(ABC):
    """
    Abstract base class for baseline trading strategies
    """
    
    def __init__(self, name: str):
        self.name = name
        self.signals = []
        self.performance_metrics = {}
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals from market data"""
        pass
    
    def calculate_returns(self, data: pd.DataFrame, signals: List[TradeSignal]) -> pd.Series:
        """Calculate strategy returns based on signals"""
        returns = pd.Series(0.0, index=data.index)
        position = 0
        
        for signal in signals:
            if signal.timestamp in data.index:
                idx = data.index.get_loc(signal.timestamp)
                
                if signal.signal == Signal.BUY and position <= 0:
                    position = 1
                elif signal.signal == Signal.SELL and position >= 0:
                    position = -1
                elif signal.signal == Signal.HOLD:
                    pass
                
                # Calculate return for next period
                if idx < len(data) - 1:
                    next_return = (data.iloc[idx + 1]['close'] / data.iloc[idx]['close'] - 1)
                    returns.iloc[idx + 1] = position * next_return
        
        return returns
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run backtest and calculate performance metrics"""
        signals = self.generate_signals(data)
        returns = self.calculate_returns(data, signals)
        
        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        max_drawdown = self._calculate_max_drawdown(returns)
        win_rate = self._calculate_win_rate(returns)
        
        self.performance_metrics = {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': len([s for s in signals if s.signal != Signal.HOLD]),
            'avg_confidence': np.mean([s.confidence for s in signals])
        }
        
        return self.performance_metrics
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """Calculate win rate (percentage of positive returns)"""
        non_zero_returns = returns[returns != 0]
        if len(non_zero_returns) == 0:
            return 0.0
        return (non_zero_returns > 0).mean()


class MovingAverageCrossover(BaselineStrategy):
    """
    Moving Average Crossover Strategy
    
    Generates BUY signal when short MA crosses above long MA
    Generates SELL signal when short MA crosses below long MA
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__(f"MA_Crossover_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate MA crossover signals"""
        signals = []
        
        # Use pre-calculated SMAs if available, otherwise calculate
        if f'sma_{self.short_window}' in data.columns and f'sma_{self.long_window}' in data.columns:
            short_ma = data[f'sma_{self.short_window}']
            long_ma = data[f'sma_{self.long_window}']
        else:
            short_ma = data['close'].rolling(window=self.short_window).mean()
            long_ma = data['close'].rolling(window=self.long_window).mean()
        
        # Generate crossover signals
        for i in range(1, len(data)):
            if pd.isna(short_ma.iloc[i]) or pd.isna(long_ma.iloc[i]):
                continue
                
            prev_short = short_ma.iloc[i-1]
            prev_long = long_ma.iloc[i-1]
            curr_short = short_ma.iloc[i]
            curr_long = long_ma.iloc[i]
            
            signal = Signal.HOLD
            confidence = 0.0
            reason = "No crossover"
            
            # Golden cross (bullish)
            if prev_short <= prev_long and curr_short > curr_long:
                signal = Signal.BUY
                confidence = min(0.9, abs(curr_short - curr_long) / curr_long)
                reason = f"Golden cross: SMA{self.short_window} > SMA{self.long_window}"
            
            # Death cross (bearish)
            elif prev_short >= prev_long and curr_short < curr_long:
                signal = Signal.SELL
                confidence = min(0.9, abs(curr_short - curr_long) / curr_long)
                reason = f"Death cross: SMA{self.short_window} < SMA{self.long_window}"
            
            if signal != Signal.HOLD:
                signals.append(TradeSignal(
                    timestamp=data.index[i],
                    signal=signal,
                    price=data.iloc[i]['close'],
                    confidence=confidence,
                    reason=reason,
                    indicators={
                        f'sma_{self.short_window}': curr_short,
                        f'sma_{self.long_window}': curr_long,
                        'price': data.iloc[i]['close']
                    }
                ))
        
        logger.info(f"Generated {len(signals)} MA crossover signals")
        return signals


class RSIStrategy(BaselineStrategy):
    """
    RSI-based Trading Strategy
    
    Generates BUY signal when RSI < oversold_threshold (default 30)
    Generates SELL signal when RSI > overbought_threshold (default 70)
    """
    
    def __init__(self, oversold_threshold: float = 30, overbought_threshold: float = 70):
        super().__init__(f"RSI_{oversold_threshold}_{overbought_threshold}")
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate RSI-based signals"""
        signals = []
        
        if 'rsi' not in data.columns:
            logger.warning("RSI column not found in data")
            return signals
        
        rsi = data['rsi']
        
        for i in range(1, len(data)):
            if pd.isna(rsi.iloc[i]):
                continue
            
            current_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1]
            
            signal = Signal.HOLD
            confidence = 0.0
            reason = "RSI in neutral zone"
            
            # Oversold condition (potential buy)
            if current_rsi < self.oversold_threshold and prev_rsi >= self.oversold_threshold:
                signal = Signal.BUY
                confidence = min(0.9, (self.oversold_threshold - current_rsi) / self.oversold_threshold)
                reason = f"RSI oversold: {current_rsi:.2f} < {self.oversold_threshold}"
            
            # Overbought condition (potential sell)
            elif current_rsi > self.overbought_threshold and prev_rsi <= self.overbought_threshold:
                signal = Signal.SELL
                confidence = min(0.9, (current_rsi - self.overbought_threshold) / (100 - self.overbought_threshold))
                reason = f"RSI overbought: {current_rsi:.2f} > {self.overbought_threshold}"
            
            if signal != Signal.HOLD:
                signals.append(TradeSignal(
                    timestamp=data.index[i],
                    signal=signal,
                    price=data.iloc[i]['close'],
                    confidence=confidence,
                    reason=reason,
                    indicators={
                        'rsi': current_rsi,
                        'price': data.iloc[i]['close']
                    }
                ))
        
        logger.info(f"Generated {len(signals)} RSI signals")
        return signals


class MACDStrategy(BaselineStrategy):
    """
    MACD-based Trading Strategy

    Generates BUY signal when MACD line crosses above signal line
    Generates SELL signal when MACD line crosses below signal line
    """

    def __init__(self):
        super().__init__("MACD_Crossover")

    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate MACD crossover signals"""
        signals = []

        if 'macd' not in data.columns or 'macd_signal' not in data.columns:
            logger.warning("MACD columns not found in data")
            return signals

        macd = data['macd']
        macd_signal = data['macd_signal']

        for i in range(1, len(data)):
            if pd.isna(macd.iloc[i]) or pd.isna(macd_signal.iloc[i]):
                continue

            prev_macd = macd.iloc[i-1]
            prev_signal = macd_signal.iloc[i-1]
            curr_macd = macd.iloc[i]
            curr_signal = macd_signal.iloc[i]

            signal = Signal.HOLD
            confidence = 0.0
            reason = "No MACD crossover"

            # Bullish crossover (MACD crosses above signal)
            if prev_macd <= prev_signal and curr_macd > curr_signal:
                signal = Signal.BUY
                confidence = min(0.9, abs(curr_macd - curr_signal) / abs(curr_signal) if curr_signal != 0 else 0.5)
                reason = f"MACD bullish crossover: {curr_macd:.2f} > {curr_signal:.2f}"

            # Bearish crossover (MACD crosses below signal)
            elif prev_macd >= prev_signal and curr_macd < curr_signal:
                signal = Signal.SELL
                confidence = min(0.9, abs(curr_macd - curr_signal) / abs(curr_signal) if curr_signal != 0 else 0.5)
                reason = f"MACD bearish crossover: {curr_macd:.2f} < {curr_signal:.2f}"

            if signal != Signal.HOLD:
                signals.append(TradeSignal(
                    timestamp=data.index[i],
                    signal=signal,
                    price=data.iloc[i]['close'],
                    confidence=confidence,
                    reason=reason,
                    indicators={
                        'macd': curr_macd,
                        'macd_signal': curr_signal,
                        'price': data.iloc[i]['close']
                    }
                ))

        logger.info(f"Generated {len(signals)} MACD signals")
        return signals


class BollingerBandsStrategy(BaselineStrategy):
    """
    Bollinger Bands Mean Reversion Strategy

    Generates BUY signal when price touches lower band (oversold)
    Generates SELL signal when price touches upper band (overbought)
    """

    def __init__(self, touch_threshold: float = 0.01):
        super().__init__(f"BollingerBands_{touch_threshold}")
        self.touch_threshold = touch_threshold  # How close to band constitutes a "touch"

    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate Bollinger Bands signals"""
        signals = []

        required_cols = ['bb_upper', 'bb_lower', 'bb_middle']
        if not all(col in data.columns for col in required_cols):
            logger.warning("Bollinger Bands columns not found in data")
            return signals

        for i in range(len(data)):
            if any(pd.isna(data.iloc[i][col]) for col in required_cols):
                continue

            price = data.iloc[i]['close']
            bb_upper = data.iloc[i]['bb_upper']
            bb_lower = data.iloc[i]['bb_lower']
            bb_middle = data.iloc[i]['bb_middle']

            signal = Signal.HOLD
            confidence = 0.0
            reason = "Price within bands"

            # Price near lower band (potential buy)
            lower_distance = abs(price - bb_lower) / bb_lower
            if lower_distance <= self.touch_threshold:
                signal = Signal.BUY
                confidence = min(0.9, 1 - lower_distance / self.touch_threshold)
                reason = f"Price near lower BB: {price:.2f} ≈ {bb_lower:.2f}"

            # Price near upper band (potential sell)
            upper_distance = abs(price - bb_upper) / bb_upper
            if upper_distance <= self.touch_threshold:
                signal = Signal.SELL
                confidence = min(0.9, 1 - upper_distance / self.touch_threshold)
                reason = f"Price near upper BB: {price:.2f} ≈ {bb_upper:.2f}"

            if signal != Signal.HOLD:
                signals.append(TradeSignal(
                    timestamp=data.index[i],
                    signal=signal,
                    price=price,
                    confidence=confidence,
                    reason=reason,
                    indicators={
                        'bb_upper': bb_upper,
                        'bb_lower': bb_lower,
                        'bb_middle': bb_middle,
                        'price': price
                    }
                ))

        logger.info(f"Generated {len(signals)} Bollinger Bands signals")
        return signals


class MultiIndicatorStrategy(BaselineStrategy):
    """
    Multi-Indicator Consensus Strategy

    Combines signals from multiple indicators with weighted voting
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        super().__init__("MultiIndicator_Consensus")
        self.weights = weights or {
            'ma_crossover': 0.3,
            'rsi': 0.25,
            'macd': 0.25,
            'bollinger': 0.2
        }

        # Initialize component strategies
        self.ma_strategy = MovingAverageCrossover(20, 50)
        self.rsi_strategy = RSIStrategy(30, 70)
        self.macd_strategy = MACDStrategy()
        self.bb_strategy = BollingerBandsStrategy(0.01)

    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate consensus signals from multiple indicators"""
        # Get signals from each strategy
        ma_signals = self.ma_strategy.generate_signals(data)
        rsi_signals = self.rsi_strategy.generate_signals(data)
        macd_signals = self.macd_strategy.generate_signals(data)
        bb_signals = self.bb_strategy.generate_signals(data)

        # Create signal dictionaries for easy lookup
        signal_dicts = {
            'ma_crossover': {s.timestamp: s for s in ma_signals},
            'rsi': {s.timestamp: s for s in rsi_signals},
            'macd': {s.timestamp: s for s in macd_signals},
            'bollinger': {s.timestamp: s for s in bb_signals}
        }

        # Get all unique timestamps
        all_timestamps = set()
        for signal_dict in signal_dicts.values():
            all_timestamps.update(signal_dict.keys())

        consensus_signals = []

        for timestamp in sorted(all_timestamps):
            if timestamp not in data.index:
                continue

            # Calculate weighted consensus
            buy_score = 0.0
            sell_score = 0.0
            total_weight = 0.0
            contributing_indicators = []

            for strategy_name, signals in signal_dicts.items():
                if timestamp in signals:
                    signal = signals[timestamp]
                    weight = self.weights.get(strategy_name, 0.0)

                    if signal.signal == Signal.BUY:
                        buy_score += weight * signal.confidence
                        contributing_indicators.append(f"{strategy_name}:BUY({signal.confidence:.2f})")
                    elif signal.signal == Signal.SELL:
                        sell_score += weight * signal.confidence
                        contributing_indicators.append(f"{strategy_name}:SELL({signal.confidence:.2f})")

                    total_weight += weight

            # Determine consensus signal
            if total_weight > 0:
                net_score = buy_score - sell_score
                confidence = max(buy_score, sell_score) / total_weight

                if net_score > 0.1:  # Minimum threshold for buy
                    final_signal = Signal.BUY
                    reason = f"Consensus BUY: {', '.join(contributing_indicators)}"
                elif net_score < -0.1:  # Minimum threshold for sell
                    final_signal = Signal.SELL
                    reason = f"Consensus SELL: {', '.join(contributing_indicators)}"
                else:
                    continue  # No clear consensus

                consensus_signals.append(TradeSignal(
                    timestamp=timestamp,
                    signal=final_signal,
                    price=data.loc[timestamp, 'close'],
                    confidence=confidence,
                    reason=reason,
                    indicators={
                        'buy_score': buy_score,
                        'sell_score': sell_score,
                        'net_score': net_score,
                        'total_weight': total_weight,
                        'price': data.loc[timestamp, 'close']
                    }
                ))

        logger.info(f"Generated {len(consensus_signals)} consensus signals")
        return consensus_signals
