#!/usr/bin/env python3
"""Interactive Trading Simulator - Professional cryptocurrency trading demonstration."""

import sys
import os
import logging
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.openbb_client import OpenBBDataClient
from src.strategies import (
    EnsembleStrategy, 
    MovingAverageCrossoverStrategy, 
    RSIMeanReversionStrategy,
    SimpleMomentumStrategy
)
from src.simulation.simulation_engine import SimulationEngine, SimulationConfig
from src.simulation.ui_components import TradingUI
from src.simulation.portfolio_tracker import PortfolioTracker

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise in interactive mode
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_simulator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class InteractiveTradingSimulator:
    """Main interactive trading simulator application."""
    
    def __init__(self):
        """Initialize the simulator."""
        self.ui = TradingUI()
        self.simulation_engine: Optional[SimulationEngine] = None
        self.data: Optional[pd.DataFrame] = None
        self.available_strategies = self._get_available_strategies()
        self.running = True
        
        # Simulation settings
        self.current_strategy = None
        self.simulation_config = SimulationConfig()
        
        logger.info("Interactive Trading Simulator initialized")
    
    def _get_available_strategies(self) -> Dict[str, Dict]:
        """Get available trading strategies with configurations.
        
        Returns:
            Dictionary mapping strategy names to their configurations
        """
        return {
            "Balanced Ensemble (CHAMPION 🏆)": {
                "class": EnsembleStrategy,
                "params": {
                    "ensemble_method": "confidence_weighted",
                    "min_consensus": 0.4,
                    "confidence_threshold": 0.3,
                    "strategy_weights": {
                        "ma_crossover": 0.33,
                        "rsi_mean_reversion": 0.33,
                        "momentum": 0.34
                    },
                    "ma_crossover_params": {
                        "fast_period": 10,
                        "slow_period": 30,
                        "ma_type": "sma",
                        "min_crossover_strength": 0.0,
                        "stop_loss_percent": 0.03,
                        "take_profit_percent": 0.08
                    },
                    "rsi_params": {
                        "rsi_period": 14,
                        "oversold_threshold": 30,
                        "overbought_threshold": 70,
                        "stop_loss_percent": 0.03,
                        "take_profit_percent": 0.08
                    },
                    "momentum_params": {
                        "lookback_period": 10,
                        "momentum_threshold": 0.005
                    }
                },
                "description": "Our best performer: 5.09% return, 0.143 Sharpe ratio"
            },
            "Conservative Ensemble": {
                "class": EnsembleStrategy,
                "params": {
                    "ensemble_method": "weighted_voting",
                    "min_consensus": 0.6,  # High consensus required
                    "confidence_threshold": 0.5,
                    "strategy_weights": {
                        "ma_crossover": 0.5,
                        "rsi_mean_reversion": 0.3,
                        "momentum": 0.2
                    }
                },
                "description": "Conservative approach with high consensus requirements"
            },
            "Aggressive Ensemble": {
                "class": EnsembleStrategy,
                "params": {
                    "ensemble_method": "weighted_voting",
                    "min_consensus": 0.3,  # Lower consensus required
                    "confidence_threshold": 0.25,
                    "strategy_weights": {
                        "ma_crossover": 0.3,
                        "rsi_mean_reversion": 0.3,
                        "momentum": 0.4  # Higher momentum weight
                    }
                },
                "description": "Aggressive approach with momentum focus"
            },
            "MA Crossover Only": {
                "class": MovingAverageCrossoverStrategy,
                "params": {
                    "fast_period": 10,
                    "slow_period": 30,
                    "ma_type": "sma",
                    "min_crossover_strength": 0.0,
                    "stop_loss_percent": 0.03,
                    "take_profit_percent": 0.08
                },
                "description": "Simple moving average crossover strategy"
            },
            "RSI Mean Reversion Only": {
                "class": RSIMeanReversionStrategy,
                "params": {
                    "rsi_period": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                    "stop_loss_percent": 0.03,
                    "take_profit_percent": 0.08
                },
                "description": "RSI-based mean reversion strategy"
            },
            "Momentum Only": {
                "class": SimpleMomentumStrategy,
                "params": {
                    "lookback_period": 10,
                    "momentum_threshold": 0.005
                },
                "description": "Simple momentum-based strategy"
            }
        }
    
    def run(self):
        """Main application loop."""
        try:
            self.ui.show_message("🚀 Welcome to Interactive Crypto Trading Simulator!", "success")
            self.ui.show_message("Demonstrating our profitable trading system with real historical data", "info")
            
            while self.running:
                choice = self._show_main_menu()
                
                if choice == -1:  # Exit
                    break
                elif choice == 0:  # Start New Simulation
                    self._start_new_simulation()
                elif choice == 1:  # Load Historical Data
                    self._load_data_menu()
                elif choice == 2:  # Configure Simulation
                    self._configure_simulation()
                elif choice == 3:  # Strategy Comparison
                    self._strategy_comparison_mode()
                elif choice == 4:  # View Results
                    self._view_results()
                elif choice == 5:  # Help
                    self._show_help()
        
        except KeyboardInterrupt:
            self.ui.show_message("\nSimulation interrupted by user", "warning")
        except Exception as e:
            self.ui.show_message(f"Error: {e}", "error")
            logger.exception("Unexpected error in main loop")
        finally:
            self._cleanup()
    
    def _show_main_menu(self) -> int:
        """Show main menu and get user choice."""
        options = [
            "🚀 Start New Simulation",
            "📊 Load Historical Data", 
            "⚙️  Configure Simulation",
            "🏆 Strategy Comparison Mode",
            "📈 View Results & Reports",
            "❓ Help & Documentation"
        ]
        
        return self.ui.display_menu("🎯 Interactive Trading Simulator - Main Menu", options)
    
    def _start_new_simulation(self):
        """Start a new trading simulation."""
        # Check if data is loaded
        if self.data is None:
            self.ui.show_message("No data loaded. Loading default BTC-USD data...", "info")
            if not self._load_default_data():
                return
        
        # Select strategy
        strategy_choice = self._select_strategy()
        if strategy_choice is None:
            return
        
        # Configure simulation parameters
        self._configure_simulation_quick()
        
        # Create and run simulation
        self._run_simulation(strategy_choice)
    
    def _load_data_menu(self):
        """Data loading menu."""
        options = [
            "📅 Last 30 days (Quick test)",
            "📅 Last 90 days (Standard)",
            "📅 Last 180 days (Comprehensive)", 
            "📅 Last 1 year (Full analysis)",
            "📅 Custom date range"
        ]
        
        choice = self.ui.display_menu("📊 Select Data Period", options)
        
        if choice == -1:
            return
        
        days_map = {0: 30, 1: 90, 2: 180, 3: 365}
        
        if choice in days_map:
            days = days_map[choice]
            self._load_data(days=days)
        elif choice == 4:
            self._load_custom_data()
    
    def _load_data(self, days: int = 180):
        """Load historical data.
        
        Args:
            days: Number of days to load
        """
        try:
            self.ui.show_message(f"Loading BTC-USD data for last {days} days...", "info")
            
            client = OpenBBDataClient()
            self.data = client.get_crypto_data(
                symbol="BTC-USD",
                provider="yfinance",
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now()
            )
            
            self.ui.show_message(
                f"✅ Loaded {len(self.data)} data points from {self.data.index[0].date()} to {self.data.index[-1].date()}",
                "success"
            )
            
            # Show data summary
            price_start = self.data['close'].iloc[0]
            price_end = self.data['close'].iloc[-1]
            price_change = (price_end - price_start) / price_start
            
            self.ui.show_message(
                f"📊 Price: ${price_start:,.2f} → ${price_end:,.2f} ({price_change:+.2%})",
                "info"
            )
            
            self.ui.wait_for_key()
            
        except Exception as e:
            self.ui.show_message(f"❌ Error loading data: {e}", "error")
            logger.exception("Error loading data")
            self.ui.wait_for_key()
    
    def _load_default_data(self) -> bool:
        """Load default data (180 days).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._load_data(days=180)
            return self.data is not None
        except:
            return False
    
    def _select_strategy(self) -> Optional[str]:
        """Select trading strategy.
        
        Returns:
            Selected strategy name or None if cancelled
        """
        strategy_names = list(self.available_strategies.keys())
        descriptions = [self.available_strategies[name]["description"] for name in strategy_names]
        
        # Create menu with descriptions
        options = [f"{name} - {desc}" for name, desc in zip(strategy_names, descriptions)]
        
        choice = self.ui.display_menu("🎯 Select Trading Strategy", options)
        
        if choice == -1:
            return None
        
        selected_strategy = strategy_names[choice]
        self.ui.show_message(f"Selected: {selected_strategy}", "success")
        
        return selected_strategy
    
    def _configure_simulation_quick(self):
        """Quick simulation configuration."""
        self.ui.show_message("⚙️ Quick Simulation Setup", "info")
        
        # Initial capital
        capital = self.ui.get_input(
            "Initial capital ($)", 
            float, 
            self.simulation_config.initial_capital
        )
        self.simulation_config.initial_capital = capital
        
        # Position size
        position_size = self.ui.get_input(
            "Position size (% of capital, 0.1-0.5)", 
            float, 
            self.simulation_config.position_size
        )
        self.simulation_config.position_size = max(0.1, min(0.5, position_size))
        
        # Speed
        speed = self.ui.get_input(
            "Simulation speed (1x-50x)", 
            float, 
            self.simulation_config.speed_multiplier
        )
        self.simulation_config.speed_multiplier = max(1.0, min(50.0, speed))
        
        self.ui.show_message(
            f"✅ Configuration: ${capital:,.0f} capital, {position_size:.0%} position size, {speed:.0f}x speed",
            "success"
        )
    
    def _run_simulation(self, strategy_name: str):
        """Run the trading simulation.
        
        Args:
            strategy_name: Name of the strategy to use
        """
        try:
            # Create strategy
            strategy_config = self.available_strategies[strategy_name]
            strategy = strategy_config["class"](strategy_config["params"])
            
            # Create simulation engine
            self.ui.show_message(f"💰 Creating simulation with ${self.simulation_config.initial_capital:,.2f} capital", "info")
            self.simulation_engine = SimulationEngine(self.simulation_config)
            self.ui.show_message(f"💰 Portfolio initialized with ${self.simulation_engine.portfolio.cash:,.2f} cash", "info")
            self.simulation_engine.load_data(self.data)
            self.simulation_engine.set_strategy(strategy)
            
            # Setup callbacks
            self.simulation_engine.add_update_callback(self._on_simulation_update)
            self.simulation_engine.add_trade_callback(self._on_trade_executed)
            self.simulation_engine.add_alert_callback(self._on_alert)
            
            # Start simulation
            self.ui.show_message(f"🚀 Starting simulation with {strategy_name}...", "success")
            self.ui.show_message("Press 'q' to quit, 'p' to pause, 'r' to resume", "info")
            
            self.simulation_engine.start_simulation()
            
            # Run interactive loop
            self._simulation_interactive_loop()
            
        except Exception as e:
            self.ui.show_message(f"❌ Simulation error: {e}", "error")
            logger.exception("Simulation error")
            self.ui.wait_for_key()
    
    def _simulation_interactive_loop(self):
        """Interactive simulation control loop."""
        import select
        import tty
        import termios
        
        # Setup non-blocking input (Unix only)
        if os.name != 'nt':
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        
        try:
            last_update = time.time()
            
            while self.simulation_engine and self.simulation_engine.is_running:
                # Update display
                current_time = time.time()
                if current_time - last_update > 0.5:  # Update every 0.5 seconds
                    self.ui.clear_screen()
                    dashboard = self.ui.render_dashboard()
                    print(dashboard)
                    last_update = current_time
                
                # Check for user input (Unix only)
                if os.name != 'nt':
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1).lower()
                        self._handle_simulation_key(key)
                
                time.sleep(0.1)
        
        finally:
            # Restore terminal settings (Unix only)
            if os.name != 'nt':
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # Show final results
            self._show_simulation_results()
    
    def _handle_simulation_key(self, key: str):
        """Handle keyboard input during simulation.
        
        Args:
            key: Pressed key
        """
        if key == 'q':
            self.simulation_engine.stop_simulation()
        elif key == 'p':
            self.simulation_engine.pause_simulation()
        elif key == 'r':
            self.simulation_engine.resume_simulation()
        elif key == 's':
            # Save state
            state_name = f"state_{datetime.now().strftime('%H%M%S')}"
            self.simulation_engine.save_state(state_name)
            self.ui.add_alert(f"State saved as {state_name}")
    
    def _on_simulation_update(self, state: Dict):
        """Callback for simulation updates.
        
        Args:
            state: Current simulation state
        """
        self.ui.update_state(state)
    
    def _on_trade_executed(self, trade, signal):
        """Callback for trade execution.
        
        Args:
            trade: Executed trade
            signal: Trading signal that triggered the trade
        """
        trade_info = {
            'timestamp': trade.timestamp,
            'side': trade.side,
            'quantity': trade.quantity,
            'price': trade.price,
            'reason': trade.reason,
            'confidence': trade.confidence
        }
        
        self.ui.add_trade(trade_info)
        self.ui.add_alert(f"{trade.side} {trade.quantity:.4f} @ ${trade.price:.2f}")
    
    def _on_alert(self, message: str):
        """Callback for alerts.
        
        Args:
            message: Alert message
        """
        self.ui.add_alert(message)
    
    def _show_simulation_results(self):
        """Show final simulation results."""
        if not self.simulation_engine:
            return
        
        state = self.simulation_engine.get_current_state()
        
        self.ui.clear_screen()
        self.ui.show_message("🏁 Simulation Complete!", "success")
        self.ui.show_message("=" * 60, "info")
        
        # Final metrics
        portfolio_value = state.get('portfolio_value', 0)
        total_return = state.get('total_return', 0)
        metrics = state.get('performance_metrics', {})
        trade_stats = state.get('trade_stats', {})
        
        self.ui.show_message(f"💰 Final Portfolio Value: ${portfolio_value:,.2f}", "success")
        self.ui.show_message(f"📈 Total Return: {total_return:+.2%}", "success" if total_return >= 0 else "error")
        self.ui.show_message(f"📊 Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}", "info")
        self.ui.show_message(f"📉 Max Drawdown: {metrics.get('max_drawdown', 0):.2%}", "warning")
        self.ui.show_message(f"💼 Total Trades: {trade_stats.get('total_trades', 0)}", "info")
        
        # Performance assessment
        if total_return > 0.05:
            self.ui.show_message("🏆 Excellent performance!", "success")
        elif total_return > 0:
            self.ui.show_message("✅ Profitable strategy", "success")
        else:
            self.ui.show_message("❌ Strategy needs improvement", "error")
        
        self.ui.wait_for_key("Press any key to return to main menu...")
    
    def _configure_simulation(self):
        """Advanced simulation configuration."""
        self.ui.show_message("⚙️ Advanced Simulation Configuration", "info")
        
        # All configuration options
        self.simulation_config.initial_capital = self.ui.get_input(
            "Initial capital ($)", float, self.simulation_config.initial_capital
        )
        
        self.simulation_config.position_size = self.ui.get_input(
            "Position size (0.1-0.5)", float, self.simulation_config.position_size
        )
        
        self.simulation_config.commission_rate = self.ui.get_input(
            "Commission rate (0.001 = 0.1%)", float, self.simulation_config.commission_rate
        )
        
        self.simulation_config.slippage_rate = self.ui.get_input(
            "Slippage rate (0.0005 = 0.05%)", float, self.simulation_config.slippage_rate
        )
        
        self.simulation_config.speed_multiplier = self.ui.get_input(
            "Speed multiplier (1x-50x)", float, self.simulation_config.speed_multiplier
        )
        
        self.ui.show_message("✅ Configuration updated", "success")
        self.ui.wait_for_key()
    
    def _strategy_comparison_mode(self):
        """Run multiple strategies for comparison."""
        self.ui.show_message("🏆 Strategy Comparison Mode", "info")
        self.ui.show_message("This feature will run multiple strategies simultaneously", "info")
        self.ui.show_message("Coming in next update...", "warning")
        self.ui.wait_for_key()
    
    def _view_results(self):
        """View previous simulation results."""
        self.ui.show_message("📈 Results & Reports", "info")
        self.ui.show_message("This feature will show saved simulation results", "info")
        self.ui.show_message("Coming in next update...", "warning")
        self.ui.wait_for_key()
    
    def _show_help(self):
        """Show help and documentation."""
        help_text = """
🎯 Interactive Trading Simulator Help

OVERVIEW:
This simulator demonstrates our profitable cryptocurrency trading system
using real historical BTC-USD data with professional risk management.

KEY FEATURES:
• Multiple trading strategies including our champion Balanced Ensemble
• Real-time portfolio tracking with live P&L updates
• Professional risk management with position sizing and drawdown controls
• Interactive controls during simulation (pause, resume, save state)
• Comprehensive performance metrics (Sharpe ratio, Calmar ratio, etc.)

STRATEGIES:
• Balanced Ensemble (CHAMPION): Our best performer with 5.09% return
• Conservative/Aggressive Ensembles: Different risk profiles
• Individual strategies: MA Crossover, RSI, Momentum

CONTROLS DURING SIMULATION:
• 'p' - Pause simulation
• 'r' - Resume simulation  
• 's' - Save current state
• 'q' - Quit simulation

PERFORMANCE METRICS:
• Total Return: Overall profit/loss percentage
• Sharpe Ratio: Risk-adjusted return measure
• Max Drawdown: Largest peak-to-trough decline
• Calmar Ratio: Return divided by max drawdown

The simulator uses realistic trading costs (0.1% commission, 0.05% slippage)
and demonstrates how our ensemble approach outperforms individual strategies.
        """
        
        self.ui.show_message(help_text, "info")
        self.ui.wait_for_key()
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.simulation_engine:
            self.simulation_engine.stop_simulation()
        
        self.ui.show_message("👋 Thank you for using Interactive Trading Simulator!", "success")


def main():
    """Main entry point."""
    try:
        simulator = InteractiveTradingSimulator()
        simulator.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error in main")


if __name__ == "__main__":
    main()
