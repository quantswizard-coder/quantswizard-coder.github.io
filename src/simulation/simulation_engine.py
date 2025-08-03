"""Core simulation engine for interactive trading."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
import time
import threading
from dataclasses import dataclass

from .portfolio_tracker import PortfolioTracker
from ..strategies.base_strategy import BaseStrategy
from ..backtesting.backtest_engine import BacktestConfig

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for trading simulation."""
    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005   # 0.05%
    max_positions: int = 5
    position_size: float = 0.20     # 20% of capital per position
    speed_multiplier: float = 1.0   # 1x = real-time
    step_mode: bool = False         # True for step-by-step execution
    
    # Risk management
    max_drawdown_limit: float = 0.25  # 25% max drawdown
    daily_loss_limit: float = 0.05    # 5% daily loss limit
    
    # Simulation parameters
    update_interval: float = 0.1      # Update frequency in seconds
    save_state_interval: int = 100    # Save state every N updates


class SimulationEngine:
    """Core engine for interactive trading simulation."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize simulation engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        logger.info(f"SimulationEngine: Creating portfolio with ${config.initial_capital:,.2f}")
        self.portfolio = PortfolioTracker(config.initial_capital)
        logger.info(f"SimulationEngine: Portfolio created with ${self.portfolio.cash:,.2f} cash")
        
        # Simulation state
        self.is_running = False
        self.is_paused = False
        self.current_date_index = 0
        self.data: Optional[pd.DataFrame] = None
        self.strategy: Optional[BaseStrategy] = None
        
        # Threading for real-time updates
        self.simulation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Callbacks for UI updates
        self.update_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # State management
        self.saved_states: Dict[str, Dict] = {}
        self.simulation_log: List[Dict] = []
        
        logger.info(f"Simulation engine initialized with ${config.initial_capital:,.2f} capital")
    
    def load_data(self, data: pd.DataFrame):
        """Load historical data for simulation.
        
        Args:
            data: OHLCV DataFrame with datetime index
        """
        self.data = data.copy()
        self.current_date_index = 0
        
        logger.info(f"Loaded {len(data)} data points from {data.index[0]} to {data.index[-1]}")
    
    def set_strategy(self, strategy: BaseStrategy):
        """Set the trading strategy.
        
        Args:
            strategy: Trading strategy instance
        """
        self.strategy = strategy
        logger.info(f"Strategy set: {strategy.name}")
    
    def add_update_callback(self, callback: Callable):
        """Add callback for portfolio updates."""
        self.update_callbacks.append(callback)
    
    def add_trade_callback(self, callback: Callable):
        """Add callback for trade executions."""
        self.trade_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts and notifications."""
        self.alert_callbacks.append(callback)
    
    def start_simulation(self):
        """Start the simulation."""
        if self.data is None or self.strategy is None:
            raise ValueError("Data and strategy must be set before starting simulation")
        
        if self.is_running:
            logger.warning("Simulation is already running")
            return
        
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        
        if self.config.step_mode:
            logger.info("Simulation started in step-by-step mode")
        else:
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self._run_simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            logger.info(f"Simulation started at {self.config.speed_multiplier}x speed")
    
    def pause_simulation(self):
        """Pause the simulation."""
        if self.is_running:
            self.is_paused = True
            logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume the simulation."""
        if self.is_running and self.is_paused:
            self.is_paused = False
            logger.info("Simulation resumed")
    
    def stop_simulation(self):
        """Stop the simulation."""
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=1.0)
            
            logger.info("Simulation stopped")
    
    def step_forward(self) -> bool:
        """Execute one simulation step.
        
        Returns:
            True if step was executed, False if simulation is complete
        """
        if not self.is_running or self.data is None or self.strategy is None:
            return False
        
        if self.current_date_index >= len(self.data):
            self._finish_simulation()
            return False
        
        # Get current data slice
        current_data = self.data.iloc[:self.current_date_index + 1]
        current_price = self.data.iloc[self.current_date_index]['close']
        current_timestamp = self.data.index[self.current_date_index]
        
        # Update portfolio with current prices
        self.portfolio.update_market_prices({'BTC-USD': current_price})
        
        # Generate signals from strategy
        try:
            signals = self.strategy.generate_signals(current_data)
            
            # Process signals
            for signal in signals:
                self._process_signal(signal, current_price, current_timestamp)
                
        except Exception as e:
            logger.error(f"Error generating signals at {current_timestamp}: {e}")
        
        # Check risk limits
        self._check_risk_limits()
        
        # Update portfolio history
        self.portfolio._update_portfolio_history()

        # Update callbacks
        self._trigger_update_callbacks()

        # Log simulation step
        self._log_simulation_step(current_timestamp, current_price)

        # Move to next time step
        self.current_date_index += 1
        
        return True
    
    def _run_simulation_loop(self):
        """Main simulation loop for threaded execution."""
        while self.is_running and not self.stop_event.is_set():
            if not self.is_paused:
                if not self.step_forward():
                    break
                
                # Sleep based on speed multiplier
                sleep_time = self.config.update_interval / self.config.speed_multiplier
                time.sleep(sleep_time)
            else:
                time.sleep(0.1)  # Short sleep when paused
        
        self._finish_simulation()
    
    def _process_signal(self, signal, current_price: float, timestamp: datetime):
        """Process a trading signal.
        
        Args:
            signal: TradingSignal object
            current_price: Current market price
            timestamp: Current timestamp
        """
        from ..strategies.base_strategy import SignalType
        
        if signal.signal == SignalType.HOLD:
            return
        
        # Calculate position size
        portfolio_value = self.portfolio.get_portfolio_value({'BTC-USD': current_price})
        position_size_dollars = portfolio_value * self.config.position_size
        quantity = position_size_dollars / current_price

        logger.info(f"Trade calculation: portfolio_value=${portfolio_value:.2f}, cash=${self.portfolio.cash:.2f}, position_size={self.config.position_size:.2f}, quantity={quantity:.6f}")
        
        # Check if we have enough cash for buy orders
        if signal.signal == SignalType.BUY:
            required_cash = quantity * current_price * (1 + self.config.commission_rate + self.config.slippage_rate)
            if required_cash > self.portfolio.cash:
                # Adjust quantity to available cash
                quantity = self.portfolio.cash / (current_price * (1 + self.config.commission_rate + self.config.slippage_rate))

                if quantity < 0.001:  # Minimum trade size
                    logger.warning(f"Insufficient cash for trade: ${self.portfolio.cash:.2f} available")
                    return

            # Check position limits for BUY signals
            if len(self.portfolio.positions) >= self.config.max_positions:
                logger.warning("Maximum positions limit reached, skipping BUY signal")
                return

        elif signal.signal == SignalType.SELL:
            # For SELL signals, check if we have a position to sell
            if 'BTC-USD' not in self.portfolio.positions:
                logger.warning("No position to sell, skipping SELL signal")
                return

            # Adjust quantity to available position
            available_quantity = self.portfolio.positions['BTC-USD'].quantity
            if available_quantity <= 0:
                logger.warning("No long position to sell, skipping SELL signal")
                return

            # Use the available quantity or the calculated quantity, whichever is smaller
            quantity = min(quantity, available_quantity)
        
        # Execute trade
        try:
            trade = self.portfolio.execute_trade(
                symbol='BTC-USD',
                side='BUY' if signal.signal == SignalType.BUY else 'SELL',
                quantity=quantity,
                price=current_price,
                strategy=self.strategy.name,
                reason=signal.reason,
                confidence=signal.confidence,
                commission_rate=self.config.commission_rate,
                slippage_rate=self.config.slippage_rate,
                metadata={'signal_metadata': signal.metadata}
            )
            
            # Trigger trade callbacks
            for callback in self.trade_callbacks:
                try:
                    callback(trade, signal)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    def _check_risk_limits(self):
        """Check risk management limits."""
        current_prices = {'BTC-USD': self.data.iloc[self.current_date_index]['close']}
        
        # Check drawdown limit
        drawdown = self.portfolio.get_drawdown(current_prices)
        if drawdown < -self.config.max_drawdown_limit:
            self._trigger_alert(f"Maximum drawdown exceeded: {drawdown:.2%}")
            self.stop_simulation()
        
        # Check daily loss limit (simplified)
        if len(self.portfolio.portfolio_history) > 1:
            current_value = self.portfolio.get_portfolio_value(current_prices)
            previous_value = self.portfolio.portfolio_history[-2]['total_value']
            daily_return = (current_value - previous_value) / previous_value
            
            if daily_return < -self.config.daily_loss_limit:
                self._trigger_alert(f"Daily loss limit exceeded: {daily_return:.2%}")
                self.pause_simulation()
    
    def _trigger_update_callbacks(self):
        """Trigger all update callbacks."""
        for callback in self.update_callbacks:
            try:
                callback(self.get_current_state())
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    def _trigger_alert(self, message: str):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def _log_simulation_step(self, timestamp: datetime, price: float):
        """Log current simulation step."""
        portfolio_value = self.portfolio.get_portfolio_value({'BTC-USD': price})
        
        log_entry = {
            'timestamp': timestamp,
            'price': price,
            'portfolio_value': portfolio_value,
            'cash': self.portfolio.cash,
            'positions': len(self.portfolio.positions),
            'total_return': self.portfolio.get_total_return({'BTC-USD': price}),
            'drawdown': self.portfolio.get_drawdown({'BTC-USD': price})
        }
        
        self.simulation_log.append(log_entry)
    
    def _finish_simulation(self):
        """Finish simulation and generate final report."""
        self.is_running = False
        
        if self.data is not None:
            final_price = self.data.iloc[-1]['close']
            final_metrics = self.portfolio.get_performance_metrics()
            
            logger.info("Simulation completed!")
            logger.info(f"Final portfolio value: ${self.portfolio.get_portfolio_value({'BTC-USD': final_price}):,.2f}")
            logger.info(f"Total return: {final_metrics.get('total_return', 0):.2%}")
            logger.info(f"Max drawdown: {final_metrics.get('max_drawdown', 0):.2%}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current simulation state.
        
        Returns:
            Dictionary with current state information
        """
        if self.data is None or self.current_date_index >= len(self.data):
            return {}
        
        current_price = self.data.iloc[self.current_date_index]['close']
        current_timestamp = self.data.index[self.current_date_index]
        
        return {
            'timestamp': current_timestamp,
            'price': current_price,
            'portfolio_value': self.portfolio.get_portfolio_value({'BTC-USD': current_price}),
            'cash': self.portfolio.cash,
            'positions': dict(self.portfolio.positions),
            'total_return': self.portfolio.get_total_return({'BTC-USD': current_price}),
            'drawdown': self.portfolio.get_drawdown({'BTC-USD': current_price}),
            'trade_stats': self.portfolio.get_trade_statistics(),
            'performance_metrics': self.portfolio.get_performance_metrics(),
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'progress': self.current_date_index / len(self.data) if self.data is not None else 0
        }
    
    def save_state(self, name: str):
        """Save current simulation state.
        
        Args:
            name: Name for the saved state
        """
        state = {
            'config': self.config,
            'portfolio_state': {
                'cash': self.portfolio.cash,
                'positions': dict(self.portfolio.positions),
                'trades': self.portfolio.trades.copy(),
                'portfolio_history': self.portfolio.portfolio_history.copy()
            },
            'simulation_state': {
                'current_date_index': self.current_date_index,
                'simulation_log': self.simulation_log.copy()
            }
        }
        
        self.saved_states[name] = state
        logger.info(f"State saved as '{name}'")
    
    def load_state(self, name: str):
        """Load a previously saved state.
        
        Args:
            name: Name of the state to load
        """
        if name not in self.saved_states:
            raise ValueError(f"No saved state named '{name}'")
        
        state = self.saved_states[name]
        
        # Restore portfolio state
        portfolio_state = state['portfolio_state']
        self.portfolio.cash = portfolio_state['cash']
        self.portfolio.positions = portfolio_state['positions']
        self.portfolio.trades = portfolio_state['trades']
        self.portfolio.portfolio_history = portfolio_state['portfolio_history']
        
        # Restore simulation state
        sim_state = state['simulation_state']
        self.current_date_index = sim_state['current_date_index']
        self.simulation_log = sim_state['simulation_log']
        
        logger.info(f"State '{name}' loaded")
    
    def reset_simulation(self):
        """Reset simulation to initial state."""
        self.stop_simulation()
        self.portfolio.reset()
        self.current_date_index = 0
        self.simulation_log.clear()
        logger.info("Simulation reset to initial state")
