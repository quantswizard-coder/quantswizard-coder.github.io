"""Base strategy framework for cryptocurrency trading."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PositionType(Enum):
    """Position types."""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass
class TradingSignal:
    """Trading signal with metadata."""
    timestamp: datetime
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    price: float
    reason: str
    metadata: Dict[str, Any] = None


@dataclass
class Position:
    """Trading position."""
    symbol: str
    position_type: PositionType
    entry_price: float
    entry_time: datetime
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class Trade:
    """Completed trade record."""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_percent: float
    position_type: PositionType
    exit_reason: str
    metadata: Dict[str, Any] = None


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        self.name = name
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.signals: List[TradingSignal] = []
        
        # Risk management parameters
        self.max_position_size = config.get('max_position_size', 1.0)
        self.stop_loss_percent = config.get('stop_loss_percent', 0.05)
        self.take_profit_percent = config.get('take_profit_percent', 0.10)
        self.max_positions = config.get('max_positions', 1)
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """Generate trading signals from market data.
        
        Args:
            data: OHLCV DataFrame with technical indicators
            
        Returns:
            List of trading signals
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators required by the strategy.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added technical indicators
        """
        pass
    
    def process_signals(self, signals: List[TradingSignal], current_price: float) -> List[Dict]:
        """Process signals and generate trading actions.
        
        Args:
            signals: List of trading signals
            current_price: Current market price
            
        Returns:
            List of trading actions
        """
        actions = []
        
        for signal in signals:
            if signal.signal == SignalType.BUY:
                action = self._process_buy_signal(signal, current_price)
                if action:
                    actions.append(action)
                    
            elif signal.signal == SignalType.SELL:
                action = self._process_sell_signal(signal, current_price)
                if action:
                    actions.append(action)
        
        return actions
    
    def _process_buy_signal(self, signal: TradingSignal, current_price: float) -> Optional[Dict]:
        """Process a buy signal."""
        # Check if we can open a new position
        if len(self.positions) >= self.max_positions:
            logger.debug(f"Max positions reached ({self.max_positions})")
            return None
        
        # Calculate position size
        position_size = self._calculate_position_size(current_price, signal.confidence)
        
        # Create position
        position = Position(
            symbol="BTC-USD",  # TODO: Make this configurable
            position_type=PositionType.LONG,
            entry_price=current_price,
            entry_time=signal.timestamp,
            size=position_size,
            stop_loss=current_price * (1 - self.stop_loss_percent),
            take_profit=current_price * (1 + self.take_profit_percent),
            metadata={'signal_confidence': signal.confidence, 'signal_reason': signal.reason}
        )
        
        return {
            'action': 'open_position',
            'position': position,
            'signal': signal
        }
    
    def _process_sell_signal(self, signal: TradingSignal, current_price: float) -> Optional[Dict]:
        """Process a sell signal."""
        # Check if we have positions to close
        if not self.positions:
            logger.debug("No positions to close")
            return None
        
        # For now, close all positions on sell signal
        # TODO: Implement more sophisticated position management
        actions = []
        for symbol, position in self.positions.items():
            trade = self._close_position(position, current_price, signal.timestamp, "sell_signal")
            actions.append({
                'action': 'close_position',
                'trade': trade,
                'signal': signal
            })
        
        return actions[0] if actions else None
    
    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size based on price and confidence."""
        base_size = self.max_position_size
        confidence_adjusted_size = base_size * confidence
        return min(confidence_adjusted_size, self.max_position_size)
    
    def _close_position(self, position: Position, exit_price: float, exit_time: datetime, reason: str) -> Trade:
        """Close a position and create a trade record."""
        pnl = (exit_price - position.entry_price) * position.size
        pnl_percent = (exit_price - position.entry_price) / position.entry_price
        
        if position.position_type == PositionType.SHORT:
            pnl = -pnl
            pnl_percent = -pnl_percent
        
        trade = Trade(
            symbol=position.symbol,
            entry_time=position.entry_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            pnl=pnl,
            pnl_percent=pnl_percent,
            position_type=position.position_type,
            exit_reason=reason,
            metadata=position.metadata
        )
        
        self.trades.append(trade)
        return trade
    
    def check_risk_management(self, current_price: float, timestamp: datetime) -> List[Dict]:
        """Check risk management rules and generate actions."""
        actions = []
        
        for symbol, position in list(self.positions.items()):
            # Check stop loss
            if position.stop_loss and current_price <= position.stop_loss:
                trade = self._close_position(position, current_price, timestamp, "stop_loss")
                actions.append({
                    'action': 'close_position',
                    'trade': trade,
                    'reason': 'stop_loss'
                })
                del self.positions[symbol]
            
            # Check take profit
            elif position.take_profit and current_price >= position.take_profit:
                trade = self._close_position(position, current_price, timestamp, "take_profit")
                actions.append({
                    'action': 'close_position',
                    'trade': trade,
                    'reason': 'take_profit'
                })
                del self.positions[symbol]
        
        return actions
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate strategy performance metrics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_percent': 0.0,
                'avg_trade_pnl': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        trades_df = pd.DataFrame([
            {
                'pnl': trade.pnl,
                'pnl_percent': trade.pnl_percent,
                'exit_time': trade.exit_time
            }
            for trade in self.trades
        ])
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = trades_df['pnl'].sum()
        total_pnl_percent = trades_df['pnl_percent'].sum()
        avg_trade_pnl = trades_df['pnl'].mean()
        
        # Calculate max drawdown
        cumulative_pnl = trades_df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0.0
        
        # Calculate Sharpe ratio (simplified)
        if trades_df['pnl_percent'].std() > 0:
            sharpe_ratio = trades_df['pnl_percent'].mean() / trades_df['pnl_percent'].std()
        else:
            sharpe_ratio = 0.0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
    
    def reset(self):
        """Reset strategy state."""
        self.positions.clear()
        self.trades.clear()
        self.signals.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current strategy status."""
        return {
            'name': self.name,
            'active_positions': len(self.positions),
            'total_trades': len(self.trades),
            'recent_signals': len([s for s in self.signals if s.signal != SignalType.HOLD]),
            'performance': self.get_performance_metrics()
        }
