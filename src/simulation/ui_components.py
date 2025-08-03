"""UI components for interactive trading simulation."""

import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Try to import rich for better terminal formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

logger = logging.getLogger(__name__)


class TradingUI:
    """Terminal-based UI for interactive trading simulation."""
    
    def __init__(self, use_rich: bool = True):
        """Initialize the trading UI.
        
        Args:
            use_rich: Whether to use rich library for enhanced formatting
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        
        if self.use_rich:
            self.console = Console()
            self.layout = Layout()
            self._setup_rich_layout()
        
        # UI state
        self.current_state: Dict[str, Any] = {}
        self.recent_trades: List[Dict] = []
        self.alerts: List[str] = []
        self.max_recent_trades = 10
        self.max_alerts = 5
        
        # Display settings
        self.refresh_rate = 0.5  # seconds
        self.show_debug = False
        
        logger.info(f"Trading UI initialized (Rich: {self.use_rich})")
    
    def _setup_rich_layout(self):
        """Setup rich layout structure."""
        if not self.use_rich:
            return
        
        # Create layout structure
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split_column(
            Layout(name="portfolio", ratio=2),
            Layout(name="positions", ratio=1)
        )
        
        self.layout["right"].split_column(
            Layout(name="performance", ratio=1),
            Layout(name="trades", ratio=1),
            Layout(name="alerts", ratio=1)
        )
    
    def update_state(self, state: Dict[str, Any]):
        """Update UI state.
        
        Args:
            state: Current simulation state
        """
        self.current_state = state
    
    def add_trade(self, trade_info: Dict[str, Any]):
        """Add trade to recent trades display.
        
        Args:
            trade_info: Trade information dictionary
        """
        self.recent_trades.insert(0, trade_info)
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades = self.recent_trades[:self.max_recent_trades]
    
    def add_alert(self, message: str):
        """Add alert message.
        
        Args:
            message: Alert message
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.alerts.insert(0, f"[{timestamp}] {message}")
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[:self.max_alerts]
    
    def render_dashboard(self) -> str:
        """Render the complete dashboard.
        
        Returns:
            Formatted dashboard string
        """
        if self.use_rich:
            return self._render_rich_dashboard()
        else:
            return self._render_simple_dashboard()
    
    def _render_rich_dashboard(self) -> str:
        """Render dashboard using rich formatting."""
        if not self.use_rich:
            return ""
        
        # Header
        header_text = Text("🚀 Interactive Crypto Trading Simulator", style="bold blue")
        if self.current_state.get('timestamp'):
            header_text.append(f" | {self.current_state['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.layout["header"].update(Panel(Align.center(header_text)))
        
        # Portfolio panel
        portfolio_table = self._create_portfolio_table()
        self.layout["portfolio"].update(Panel(portfolio_table, title="💰 Portfolio", border_style="green"))
        
        # Positions panel
        positions_table = self._create_positions_table()
        self.layout["positions"].update(Panel(positions_table, title="📊 Positions", border_style="blue"))
        
        # Performance panel
        performance_table = self._create_performance_table()
        self.layout["performance"].update(Panel(performance_table, title="📈 Performance", border_style="yellow"))
        
        # Recent trades panel
        trades_table = self._create_trades_table()
        self.layout["trades"].update(Panel(trades_table, title="💼 Recent Trades", border_style="cyan"))
        
        # Alerts panel
        alerts_text = self._create_alerts_text()
        self.layout["alerts"].update(Panel(alerts_text, title="🚨 Alerts", border_style="red"))
        
        # Footer
        footer_text = self._create_footer_text()
        self.layout["footer"].update(Panel(Align.center(footer_text)))
        
        return str(self.layout)
    
    def _create_portfolio_table(self) -> Table:
        """Create portfolio information table."""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        
        if not self.current_state:
            table.add_row("No data", "")
            return table
        
        # Portfolio value
        portfolio_value = self.current_state.get('portfolio_value', 0)
        table.add_row("Portfolio Value", f"${portfolio_value:,.2f}")
        
        # Cash
        cash = self.current_state.get('cash', 0)
        table.add_row("Cash", f"${cash:,.2f}")
        
        # Total return
        total_return = self.current_state.get('total_return', 0)
        return_color = "green" if total_return >= 0 else "red"
        table.add_row("Total Return", f"[{return_color}]{total_return:+.2%}[/{return_color}]")
        
        # Current price
        price = self.current_state.get('price', 0)
        table.add_row("BTC Price", f"${price:,.2f}")
        
        # Drawdown
        drawdown = self.current_state.get('drawdown', 0)
        dd_color = "red" if drawdown < -0.05 else "yellow" if drawdown < 0 else "green"
        table.add_row("Drawdown", f"[{dd_color}]{drawdown:.2%}[/{dd_color}]")
        
        return table
    
    def _create_positions_table(self) -> Table:
        """Create positions table."""
        table = Table(show_header=True, box=None)
        table.add_column("Symbol", style="bold")
        table.add_column("Quantity")
        table.add_column("Avg Price")
        table.add_column("Current")
        table.add_column("P&L")
        
        positions = self.current_state.get('positions', {})
        
        if not positions:
            table.add_row("No positions", "", "", "", "")
            return table
        
        for symbol, position in positions.items():
            quantity = position.quantity
            avg_price = position.avg_entry_price
            current_price = position.current_price
            unrealized_pnl = position.unrealized_pnl
            
            pnl_color = "green" if unrealized_pnl >= 0 else "red"
            
            table.add_row(
                symbol,
                f"{quantity:.4f}",
                f"${avg_price:.2f}",
                f"${current_price:.2f}",
                f"[{pnl_color}]{unrealized_pnl:+.2f}[/{pnl_color}]"
            )
        
        return table
    
    def _create_performance_table(self) -> Table:
        """Create performance metrics table."""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        
        metrics = self.current_state.get('performance_metrics', {})
        trade_stats = self.current_state.get('trade_stats', {})
        
        # Sharpe ratio
        sharpe = metrics.get('sharpe_ratio', 0)
        sharpe_color = "green" if sharpe > 0.5 else "yellow" if sharpe > 0 else "red"
        table.add_row("Sharpe Ratio", f"[{sharpe_color}]{sharpe:.3f}[/{sharpe_color}]")
        
        # Max drawdown
        max_dd = metrics.get('max_drawdown', 0)
        table.add_row("Max Drawdown", f"{max_dd:.2%}")
        
        # Total trades
        total_trades = trade_stats.get('total_trades', 0)
        table.add_row("Total Trades", str(total_trades))
        
        # Win rate (simplified)
        if total_trades > 0:
            table.add_row("Avg Confidence", f"{trade_stats.get('avg_confidence', 0):.2%}")
        
        return table
    
    def _create_trades_table(self) -> Table:
        """Create recent trades table."""
        table = Table(show_header=True, box=None)
        table.add_column("Time", style="dim")
        table.add_column("Side")
        table.add_column("Price")
        table.add_column("Qty")
        table.add_column("Reason", max_width=20)
        
        if not self.recent_trades:
            table.add_row("No trades yet", "", "", "", "")
            return table
        
        for trade in self.recent_trades[:5]:  # Show last 5 trades
            side = trade.get('side', '')
            side_color = "green" if side == 'BUY' else "red"
            
            table.add_row(
                trade.get('timestamp', '').strftime('%H:%M:%S') if isinstance(trade.get('timestamp'), datetime) else str(trade.get('timestamp', '')),
                f"[{side_color}]{side}[/{side_color}]",
                f"${trade.get('price', 0):.2f}",
                f"{trade.get('quantity', 0):.4f}",
                str(trade.get('reason', ''))[:20]
            )
        
        return table
    
    def _create_alerts_text(self) -> Text:
        """Create alerts text."""
        if not self.alerts:
            return Text("No alerts", style="dim")
        
        text = Text()
        for alert in self.alerts:
            text.append(alert + "\n", style="red")
        
        return text
    
    def _create_footer_text(self) -> Text:
        """Create footer text with controls."""
        text = Text()
        
        # Status
        if self.current_state.get('is_running'):
            if self.current_state.get('is_paused'):
                text.append("⏸️  PAUSED", style="yellow")
            else:
                text.append("▶️  RUNNING", style="green")
        else:
            text.append("⏹️  STOPPED", style="red")
        
        # Progress
        progress = self.current_state.get('progress', 0)
        text.append(f" | Progress: {progress:.1%}")
        
        # Controls
        text.append(" | Controls: [P]ause [R]esume [S]top [Q]uit", style="dim")
        
        return text
    
    def _render_simple_dashboard(self) -> str:
        """Render dashboard using simple text formatting."""
        lines = []
        lines.append("=" * 80)
        lines.append("🚀 Interactive Crypto Trading Simulator")
        lines.append("=" * 80)
        
        if not self.current_state:
            lines.append("No data available")
            return "\n".join(lines)
        
        # Portfolio section
        lines.append("\n💰 PORTFOLIO:")
        lines.append(f"  Portfolio Value: ${self.current_state.get('portfolio_value', 0):,.2f}")
        lines.append(f"  Cash: ${self.current_state.get('cash', 0):,.2f}")
        lines.append(f"  Total Return: {self.current_state.get('total_return', 0):+.2%}")
        lines.append(f"  Current Drawdown: {self.current_state.get('drawdown', 0):.2%}")
        
        # Current price
        lines.append(f"\n📊 MARKET:")
        lines.append(f"  BTC Price: ${self.current_state.get('price', 0):,.2f}")
        
        # Positions
        positions = self.current_state.get('positions', {})
        lines.append(f"\n📈 POSITIONS ({len(positions)}):")
        if positions:
            for symbol, pos in positions.items():
                lines.append(f"  {symbol}: {pos.quantity:.4f} @ ${pos.avg_entry_price:.2f} (P&L: {pos.unrealized_pnl:+.2f})")
        else:
            lines.append("  No open positions")
        
        # Performance
        metrics = self.current_state.get('performance_metrics', {})
        lines.append(f"\n📊 PERFORMANCE:")
        lines.append(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        lines.append(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        
        # Recent trades
        lines.append(f"\n💼 RECENT TRADES:")
        if self.recent_trades:
            for trade in self.recent_trades[:3]:
                timestamp = trade.get('timestamp', '')
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime('%H:%M:%S')
                lines.append(f"  {timestamp} {trade.get('side', '')} {trade.get('quantity', 0):.4f} @ ${trade.get('price', 0):.2f}")
        else:
            lines.append("  No trades yet")
        
        # Status
        lines.append(f"\n🎮 STATUS:")
        if self.current_state.get('is_running'):
            status = "PAUSED" if self.current_state.get('is_paused') else "RUNNING"
        else:
            status = "STOPPED"
        lines.append(f"  {status} | Progress: {self.current_state.get('progress', 0):.1%}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_menu(self, title: str, options: List[str]) -> int:
        """Display a menu and get user selection.
        
        Args:
            title: Menu title
            options: List of menu options
            
        Returns:
            Selected option index (0-based)
        """
        while True:
            self.clear_screen()
            
            if self.use_rich:
                self.console.print(f"\n[bold blue]{title}[/bold blue]\n")
                for i, option in enumerate(options):
                    self.console.print(f"  {i + 1}. {option}")
                self.console.print(f"\n  0. Exit")
                choice = self.console.input("\n[bold]Select option: [/bold]")
            else:
                print(f"\n{title}\n")
                for i, option in enumerate(options):
                    print(f"  {i + 1}. {option}")
                print(f"\n  0. Exit")
                choice = input("\nSelect option: ")
            
            try:
                choice_int = int(choice)
                if choice_int == 0:
                    return -1  # Exit
                elif 1 <= choice_int <= len(options):
                    return choice_int - 1
                else:
                    if self.use_rich:
                        self.console.print("[red]Invalid choice. Please try again.[/red]")
                    else:
                        print("Invalid choice. Please try again.")
                    time.sleep(1)
            except ValueError:
                if self.use_rich:
                    self.console.print("[red]Please enter a number.[/red]")
                else:
                    print("Please enter a number.")
                time.sleep(1)
    
    def get_input(self, prompt: str, input_type: type = str, default: Any = None):
        """Get user input with type validation.
        
        Args:
            prompt: Input prompt
            input_type: Expected input type
            default: Default value if empty input
            
        Returns:
            Validated input value
        """
        while True:
            try:
                if self.use_rich:
                    if default is not None:
                        user_input = self.console.input(f"[bold]{prompt}[/bold] (default: {default}): ")
                    else:
                        user_input = self.console.input(f"[bold]{prompt}[/bold]: ")
                else:
                    if default is not None:
                        user_input = input(f"{prompt} (default: {default}): ")
                    else:
                        user_input = input(f"{prompt}: ")
                
                if not user_input and default is not None:
                    return default
                
                if input_type == bool:
                    return user_input.lower() in ['y', 'yes', 'true', '1']
                else:
                    return input_type(user_input)
                    
            except ValueError:
                if self.use_rich:
                    self.console.print(f"[red]Please enter a valid {input_type.__name__}[/red]")
                else:
                    print(f"Please enter a valid {input_type.__name__}")
    
    def show_message(self, message: str, style: str = "info"):
        """Show a message to the user.
        
        Args:
            message: Message to display
            style: Message style (info, success, warning, error)
        """
        if self.use_rich:
            color_map = {
                'info': 'blue',
                'success': 'green', 
                'warning': 'yellow',
                'error': 'red'
            }
            color = color_map.get(style, 'white')
            self.console.print(f"[{color}]{message}[/{color}]")
        else:
            print(message)
    
    def wait_for_key(self, message: str = "Press any key to continue..."):
        """Wait for user to press a key.
        
        Args:
            message: Message to display
        """
        if self.use_rich:
            self.console.input(f"[dim]{message}[/dim]")
        else:
            input(message)
