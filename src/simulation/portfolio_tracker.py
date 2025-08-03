"""Portfolio tracking for interactive trading simulation."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade execution."""
    timestamp: datetime
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    commission: float
    slippage: float
    strategy: str
    reason: str
    confidence: float
    metadata: Dict = field(default_factory=dict)
    
    @property
    def total_cost(self) -> float:
        """Total cost including commission and slippage."""
        base_cost = self.quantity * self.price
        return base_cost + self.commission + self.slippage
    
    @property
    def net_quantity(self) -> float:
        """Net quantity considering buy/sell direction."""
        return self.quantity if self.side == 'BUY' else -self.quantity


@dataclass
class Position:
    """Represents a current position in an asset."""
    symbol: str
    quantity: float
    avg_entry_price: float
    entry_timestamp: datetime
    unrealized_pnl: float = 0.0
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        return abs(self.quantity) * self.current_price
    
    @property
    def is_long(self) -> bool:
        """True if this is a long position."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """True if this is a short position."""
        return self.quantity < 0
    
    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized P&L based on current price."""
        self.current_price = current_price
        if self.quantity != 0:
            self.unrealized_pnl = (current_price - self.avg_entry_price) * self.quantity


class PortfolioTracker:
    """Tracks portfolio state and performance metrics in real-time."""
    
    def __init__(self, initial_capital: float = 10000.0):
        """Initialize portfolio tracker.
        
        Args:
            initial_capital: Starting capital amount
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.portfolio_history: List[Dict] = []
        
        # Performance tracking
        self.peak_value = initial_capital
        self.max_drawdown = 0.0
        self.total_commission = 0.0
        self.total_slippage = 0.0
        
        # Recent performance for rolling metrics
        self.recent_returns = deque(maxlen=252)  # 1 year of daily returns
        self.daily_values = deque(maxlen=252)
        
        # Initialize first portfolio snapshot
        self._update_portfolio_history()
    
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        strategy: str,
        reason: str,
        confidence: float,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        metadata: Optional[Dict] = None
    ) -> Trade:
        """Execute a trade and update portfolio state.
        
        Args:
            symbol: Asset symbol
            side: 'BUY' or 'SELL'
            quantity: Number of shares/units
            price: Execution price
            strategy: Strategy name that generated the trade
            reason: Reason for the trade
            confidence: Signal confidence (0.0 to 1.0)
            commission_rate: Commission rate (default 0.1%)
            slippage_rate: Slippage rate (default 0.05%)
            metadata: Additional trade metadata
            
        Returns:
            Trade object representing the executed trade
        """
        
        # Calculate costs
        base_value = quantity * price
        commission = base_value * commission_rate
        slippage = base_value * slippage_rate
        
        # Create trade record
        trade = Trade(
            timestamp=datetime.now(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            commission=commission,
            slippage=slippage,
            strategy=strategy,
            reason=reason,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        # Update portfolio state
        self._process_trade(trade)
        
        # Record trade
        self.trades.append(trade)
        
        # Update tracking
        self.total_commission += commission
        self.total_slippage += slippage
        
        logger.info(f"Executed {side} {quantity:.4f} {symbol} @ ${price:.2f} "
                   f"(Strategy: {strategy}, Confidence: {confidence:.3f})")
        
        return trade
    
    def _process_trade(self, trade: Trade):
        """Process trade and update positions and cash."""
        
        symbol = trade.symbol
        net_quantity = trade.net_quantity
        total_cost = trade.total_cost
        
        # Update cash
        if trade.side == 'BUY':
            self.cash -= total_cost
        else:  # SELL
            self.cash += total_cost
        
        # Update position
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Calculate new average entry price
            old_value = position.quantity * position.avg_entry_price
            new_value = net_quantity * trade.price
            total_quantity = position.quantity + net_quantity
            
            if total_quantity != 0:
                position.avg_entry_price = (old_value + new_value) / total_quantity
                position.quantity = total_quantity
            else:
                # Position closed
                del self.positions[symbol]
        else:
            # New position
            if net_quantity != 0:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=net_quantity,
                    avg_entry_price=trade.price,
                    entry_timestamp=trade.timestamp,
                    current_price=trade.price
                )
    
    def update_market_prices(self, prices: Dict[str, float]):
        """Update current market prices and unrealized P&L.
        
        Args:
            prices: Dictionary mapping symbols to current prices
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_unrealized_pnl(price)
    
    def get_portfolio_value(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate total portfolio value.
        
        Args:
            current_prices: Current market prices for positions
            
        Returns:
            Total portfolio value including cash and positions
        """
        if current_prices:
            self.update_market_prices(current_prices)
        
        total_value = self.cash
        
        for position in self.positions.values():
            total_value += position.market_value
        
        return total_value
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_realized_pnl(self) -> float:
        """Calculate realized P&L from closed trades."""
        # This is a simplified calculation
        # In practice, would need to track specific position closes
        total_trade_value = sum(
            trade.net_quantity * trade.price for trade in self.trades
        )
        total_costs = self.total_commission + self.total_slippage
        return -total_costs  # Simplified - costs reduce P&L
    
    def get_total_return(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate total return percentage.
        
        Args:
            current_prices: Current market prices
            
        Returns:
            Total return as percentage
        """
        current_value = self.get_portfolio_value(current_prices)
        return (current_value - self.initial_capital) / self.initial_capital
    
    def get_drawdown(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate current drawdown from peak.
        
        Args:
            current_prices: Current market prices
            
        Returns:
            Current drawdown as percentage (negative value)
        """
        current_value = self.get_portfolio_value(current_prices)
        
        # Update peak
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            drawdown = (current_value - self.peak_value) / self.peak_value
            
            # Update max drawdown
            if drawdown < self.max_drawdown:
                self.max_drawdown = drawdown
            
            return drawdown
        
        return 0.0
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trade statistics.
        
        Returns:
            Dictionary with trade statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # Calculate basic stats
        total_trades = len(self.trades)
        buy_trades = [t for t in self.trades if t.side == 'BUY']
        sell_trades = [t for t in self.trades if t.side == 'SELL']
        
        # For simplified P&L calculation, assume each trade pair (buy-sell) is one round trip
        round_trips = min(len(buy_trades), len(sell_trades))
        
        return {
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'round_trips': round_trips,
            'total_commission': self.total_commission,
            'total_slippage': self.total_slippage,
            'avg_confidence': np.mean([t.confidence for t in self.trades]) if self.trades else 0.0
        }
    
    def _update_portfolio_history(self):
        """Update portfolio history for performance tracking."""
        current_value = self.get_portfolio_value()
        
        snapshot = {
            'timestamp': datetime.now(),
            'total_value': current_value,
            'cash': self.cash,
            'positions_value': current_value - self.cash,
            'unrealized_pnl': self.get_unrealized_pnl(),
            'total_return': self.get_total_return(),
            'drawdown': self.get_drawdown(),
            'num_positions': len(self.positions)
        }
        
        self.portfolio_history.append(snapshot)
        
        # Update daily tracking
        self.daily_values.append(current_value)
        
        if len(self.daily_values) > 1:
            daily_return = (current_value - self.daily_values[-2]) / self.daily_values[-2]
            self.recent_returns.append(daily_return)
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if len(self.portfolio_history) < 2:
            return {}
        
        current_value = self.portfolio_history[-1]['total_value']
        total_return = self.get_total_return()
        
        # Calculate Sharpe ratio (simplified)
        if len(self.recent_returns) > 1:
            returns_array = np.array(list(self.recent_returns))
            sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
        else:
            sharpe_ratio = 0.0
        
        # Calculate Calmar ratio
        calmar_ratio = total_return / abs(self.max_drawdown) if self.max_drawdown < 0 else 0.0
        
        return {
            'total_return': total_return,
            'annualized_return': total_return,  # Simplified
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'current_drawdown': self.get_drawdown(),
            'calmar_ratio': calmar_ratio,
            'current_value': current_value,
            'peak_value': self.peak_value
        }
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.portfolio_history.clear()
        self.peak_value = self.initial_capital
        self.max_drawdown = 0.0
        self.total_commission = 0.0
        self.total_slippage = 0.0
        self.recent_returns.clear()
        self.daily_values.clear()
        
        # Initialize first snapshot
        self._update_portfolio_history()
