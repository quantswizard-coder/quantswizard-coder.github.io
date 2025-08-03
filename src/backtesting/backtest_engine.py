"""Comprehensive backtesting engine for cryptocurrency trading strategies."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from ..strategies.base_strategy import BaseStrategy, TradingSignal, SignalType, Trade
    from ..risk_management.position_sizing import RiskManager
except ImportError:
    from strategies.base_strategy import BaseStrategy, TradingSignal, SignalType, Trade
    from risk_management.position_sizing import RiskManager

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005   # 0.05%
    max_positions: int = 1
    position_sizing: str = "fixed"  # "fixed", "percent", "kelly"
    position_size: float = 1.0      # 100% of capital for fixed
    enable_shorting: bool = False
    margin_requirement: float = 1.0  # 100% margin


@dataclass
class BacktestResults:
    """Comprehensive backtesting results."""
    # Performance metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Trading metrics
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Risk metrics
    var_95: float  # Value at Risk
    expected_shortfall: float
    
    # Time series
    equity_curve: pd.Series
    drawdown_series: pd.Series
    trades_df: pd.DataFrame
    
    # Additional metrics
    start_date: datetime
    end_date: datetime
    duration_days: int
    metadata: Dict[str, Any]


class BacktestEngine:
    """Comprehensive backtesting engine."""
    
    def __init__(self, config: BacktestConfig):
        """Initialize the backtesting engine.
        
        Args:
            config: Backtesting configuration
        """
        self.config = config
        self.reset()
    
    def reset(self):
        """Reset the backtesting state."""
        self.capital = self.config.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_history = []
        self.current_time = None
        
    def run_backtest(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BacktestResults:
        """Run a comprehensive backtest.
        
        Args:
            strategy: Trading strategy to test
            data: Historical OHLCV data
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            BacktestResults with comprehensive metrics
        """
        logger.info(f"Starting backtest for {strategy.name}")
        
        # Reset strategy and engine
        strategy.reset()
        self.reset()
        
        # Filter data by date range
        if start_date or end_date:
            data = self._filter_data_by_date(data, start_date, end_date)
        
        if data.empty:
            raise ValueError("No data available for backtesting")
        
        # Calculate technical indicators
        data_with_indicators = strategy.calculate_indicators(data)
        
        # Initialize tracking
        equity_values = []
        timestamps = []
        
        # Run simulation
        for i, (timestamp, row) in enumerate(data_with_indicators.iterrows()):
            self.current_time = timestamp
            current_price = row['close']
            
            # Get current data slice for strategy
            current_data = data_with_indicators.iloc[:i+1]
            
            # Generate signals
            signals = strategy.generate_signals(current_data)
            
            # Process signals
            for signal in signals:
                if signal.signal != SignalType.HOLD:
                    self._process_signal(signal, current_price, strategy)
            
            # Check risk management
            risk_actions = strategy.check_risk_management(current_price, timestamp)
            for action in risk_actions:
                self._process_risk_action(action)
            
            # Update equity
            current_equity = self._calculate_current_equity(current_price)
            equity_values.append(current_equity)
            timestamps.append(timestamp)
            
            # Log progress
            if i % 100 == 0:
                logger.debug(f"Processed {i}/{len(data_with_indicators)} bars")
        
        # Create results
        results = self._create_results(
            equity_values, timestamps, strategy.trades, 
            data_with_indicators.index[0], data_with_indicators.index[-1]
        )
        
        logger.info(f"Backtest completed: {results.total_return:.2%} return, "
                   f"{results.sharpe_ratio:.2f} Sharpe, {results.max_drawdown:.2%} max DD")
        
        return results
    
    def _filter_data_by_date(
        self, 
        data: pd.DataFrame, 
        start_date: Optional[datetime], 
        end_date: Optional[datetime]
    ) -> pd.DataFrame:
        """Filter data by date range."""
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        return data
    
    def _process_signal(self, signal: TradingSignal, current_price: float, strategy: BaseStrategy):
        """Process a trading signal."""
        if signal.signal == SignalType.BUY:
            self._execute_buy(signal, current_price, strategy)
        elif signal.signal == SignalType.SELL:
            self._execute_sell(signal, current_price, strategy)
    
    def _execute_buy(self, signal: TradingSignal, current_price: float, strategy: BaseStrategy):
        """Execute a buy order."""
        # Check if we can open a position
        if len(self.positions) >= self.config.max_positions:
            return
        
        # Calculate position size
        position_value = self._calculate_position_size(current_price, signal.confidence)
        if position_value <= 0:
            return
        
        # Apply slippage and commission
        execution_price = current_price * (1 + self.config.slippage_rate)
        commission = position_value * self.config.commission_rate
        
        # Check if we have enough capital
        total_cost = position_value + commission
        if total_cost > self.capital:
            return
        
        # Execute trade
        shares = position_value / execution_price
        self.capital -= total_cost
        
        # Create position
        position_id = f"pos_{len(self.positions)}"
        self.positions[position_id] = {
            'shares': shares,
            'entry_price': execution_price,
            'entry_time': self.current_time,
            'signal': signal
        }
        
        logger.debug(f"Opened position: {shares:.4f} shares at ${execution_price:.2f}")
    
    def _execute_sell(self, signal: TradingSignal, current_price: float, strategy: BaseStrategy):
        """Execute a sell order."""
        if not self.positions:
            return
        
        # For now, close all positions (FIFO)
        for position_id, position in list(self.positions.items()):
            self._close_position(position_id, position, current_price, "signal")
    
    def _close_position(self, position_id: str, position: Dict, exit_price: float, reason: str):
        """Close a position."""
        # Apply slippage and commission
        execution_price = exit_price * (1 - self.config.slippage_rate)
        position_value = position['shares'] * execution_price
        commission = position_value * self.config.commission_rate
        
        # Calculate P&L
        entry_value = position['shares'] * position['entry_price']
        gross_pnl = position_value - entry_value
        net_pnl = gross_pnl - commission - (entry_value * self.config.commission_rate)
        
        # Update capital
        self.capital += position_value - commission
        
        # Create trade record
        trade = Trade(
            symbol="BTC-USD",
            entry_time=position['entry_time'],
            exit_time=self.current_time,
            entry_price=position['entry_price'],
            exit_price=execution_price,
            size=position['shares'],
            pnl=net_pnl,
            pnl_percent=net_pnl / entry_value,
            position_type=position.get('position_type', 'LONG'),
            exit_reason=reason,
            metadata={'commission': commission}
        )
        
        self.trades.append(trade)
        del self.positions[position_id]
        
        logger.debug(f"Closed position: {trade.pnl:.2f} P&L ({trade.pnl_percent:.2%})")
    
    def _process_risk_action(self, action: Dict):
        """Process a risk management action."""
        if action['action'] == 'close_position':
            # Find and close the position
            for position_id, position in list(self.positions.items()):
                if position['entry_time'] == action['trade'].entry_time:
                    self._close_position(
                        position_id, position, 
                        action['trade'].exit_price, 
                        action['reason']
                    )
                    break
    
    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size based on configuration."""
        if self.config.position_sizing == "fixed":
            return self.capital * self.config.position_size
        elif self.config.position_sizing == "percent":
            return self.capital * self.config.position_size * confidence
        else:  # Default to fixed
            return self.capital * self.config.position_size
    
    def _calculate_current_equity(self, current_price: float) -> float:
        """Calculate current total equity."""
        equity = self.capital
        
        # Add unrealized P&L from open positions
        for position in self.positions.values():
            current_value = position['shares'] * current_price
            entry_value = position['shares'] * position['entry_price']
            unrealized_pnl = current_value - entry_value
            equity += unrealized_pnl
        
        return equity
    
    def _create_results(
        self, 
        equity_values: List[float], 
        timestamps: List[datetime],
        trades: List[Trade],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResults:
        """Create comprehensive backtest results."""
        
        # Create equity curve
        equity_series = pd.Series(equity_values, index=timestamps)
        
        # Calculate returns
        returns = equity_series.pct_change().dropna()
        
        # Performance metrics
        total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
        duration_years = (end_date - start_date).days / 365.25
        annualized_return = (1 + total_return) ** (1 / duration_years) - 1 if duration_years > 0 else 0
        volatility = returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown calculation
        running_max = equity_series.expanding().max()
        drawdown_series = (equity_series - running_max) / running_max
        max_drawdown = drawdown_series.min()
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Trading metrics
        if trades:
            trades_df = pd.DataFrame([
                {
                    'entry_time': t.entry_time,
                    'exit_time': t.exit_time,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'exit_reason': t.exit_reason
                }
                for t in trades
            ])
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            wins = [t.pnl for t in trades if t.pnl > 0]
            losses = [t.pnl for t in trades if t.pnl < 0]
            
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            profit_factor = abs(sum(wins) / sum(losses)) if losses else float('inf')
        else:
            trades_df = pd.DataFrame()
            total_trades = win_rate = avg_win = avg_loss = profit_factor = 0
        
        # Risk metrics
        var_95 = returns.quantile(0.05) if len(returns) > 0 else 0
        expected_shortfall = returns[returns <= var_95].mean() if len(returns) > 0 else 0
        
        return BacktestResults(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            var_95=var_95,
            expected_shortfall=expected_shortfall,
            equity_curve=equity_series,
            drawdown_series=drawdown_series,
            trades_df=trades_df,
            start_date=start_date,
            end_date=end_date,
            duration_days=(end_date - start_date).days,
            metadata={'initial_capital': self.config.initial_capital}
        )
