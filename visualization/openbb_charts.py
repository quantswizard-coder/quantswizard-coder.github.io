"""OpenBB native charting integration for crypto data visualization."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# Try to import OpenBB charting, fallback gracefully
try:
    from openbb import obb
    OPENBB_CHARTING_AVAILABLE = True
except ImportError:
    OPENBB_CHARTING_AVAILABLE = False
    logger.warning("OpenBB charting not available, using fallback visualizations")


class OpenBBChartManager:
    """Manager for OpenBB native charting and custom visualizations."""
    
    def __init__(self):
        """Initialize the chart manager."""
        self.charting_available = OPENBB_CHARTING_AVAILABLE
    
    def create_crypto_price_chart(
        self,
        data: pd.DataFrame,
        symbol: str = "BTC-USD",
        provider: str = "yfinance",
        indicators: Optional[Dict] = None
    ) -> go.Figure:
        """Create cryptocurrency price chart with technical indicators.
        
        Args:
            data: OHLCV DataFrame
            symbol: Cryptocurrency symbol
            provider: Data provider name
            indicators: Technical indicators to display
            
        Returns:
            Plotly figure
        """
        
        if self.charting_available:
            try:
                return self._create_openbb_chart(data, symbol, provider, indicators)
            except Exception as e:
                logger.warning(f"OpenBB charting failed: {e}, using fallback")
        
        return self._create_fallback_chart(data, symbol, provider, indicators)
    
    def _create_openbb_chart(
        self,
        data: pd.DataFrame,
        symbol: str,
        provider: str,
        indicators: Optional[Dict]
    ) -> go.Figure:
        """Create chart using OpenBB native charting."""
        
        # Convert data to OpenBB format if needed
        if not hasattr(data, 'chart'):
            # This would be the actual OpenBB data object with charting capabilities
            # For now, we'll use the fallback method
            return self._create_fallback_chart(data, symbol, provider, indicators)
        
        # Use OpenBB's native charting
        chart_config = {
            "title": f"{symbol} Price Chart - {provider.title()}",
            "indicators": indicators or {}
        }
        
        # This would be the actual OpenBB charting call
        # fig = data.charting.to_chart(**chart_config)
        # return fig
        
        # For now, fallback to custom implementation
        return self._create_fallback_chart(data, symbol, provider, indicators)
    
    def _create_fallback_chart(
        self,
        data: pd.DataFrame,
        symbol: str,
        provider: str,
        indicators: Optional[Dict]
    ) -> go.Figure:
        """Create chart using custom Plotly implementation."""
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{symbol} Price', 'Volume', 'Technical Indicators'),
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Main price chart (candlestick)
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name='Price'
                ),
                row=1, col=1
            )
        else:
            # Fallback to line chart if OHLC not available
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
        
        # Add moving averages if available
        if indicators and 'sma' in indicators:
            for period in indicators['sma'].get('length', [20, 50]):
                col_name = f'sma_{period}'
                if col_name in data.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[col_name],
                            mode='lines',
                            name=f'SMA {period}',
                            line=dict(width=1)
                        ),
                        row=1, col=1
                    )
        
        # Add EMA if available
        if indicators and 'ema' in indicators:
            for period in indicators['ema'].get('length', [12, 26]):
                col_name = f'ema_{period}'
                if col_name in data.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[col_name],
                            mode='lines',
                            name=f'EMA {period}',
                            line=dict(width=1, dash='dash')
                        ),
                        row=1, col=1
                    )
        
        # Volume chart
        if 'volume' in data.columns:
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['volume'],
                    name='Volume',
                    marker_color='rgba(0,100,80,0.6)'
                ),
                row=2, col=1
            )
        
        # Technical indicators (RSI, MACD)
        if 'rsi' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['rsi'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=3, col=1
            )
            
            # Add RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color='blue')
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['macd_signal'],
                    mode='lines',
                    name='MACD Signal',
                    line=dict(color='red')
                ),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} Analysis - {provider.title()}",
            xaxis_title="Date",
            height=800,
            showlegend=True,
            template="plotly_white"
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Indicator Value", row=3, col=1)
        
        return fig
    
    def create_strategy_performance_chart(
        self,
        equity_curve: pd.Series,
        benchmark: pd.Series,
        trades: Optional[pd.DataFrame] = None
    ) -> go.Figure:
        """Create strategy performance comparison chart.
        
        Args:
            equity_curve: Strategy equity curve
            benchmark: Benchmark price series
            trades: Optional trades DataFrame
            
        Returns:
            Plotly figure
        """
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Portfolio Performance', 'Drawdown'),
            row_heights=[0.7, 0.3]
        )
        
        # Normalize both series to start at 100
        equity_normalized = (equity_curve / equity_curve.iloc[0]) * 100
        benchmark_normalized = (benchmark / benchmark.iloc[0]) * 100
        
        # Portfolio performance
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_normalized,
                mode='lines',
                name='Strategy',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=benchmark.index,
                y=benchmark_normalized,
                mode='lines',
                name='Benchmark (Buy & Hold)',
                line=dict(color='gray', width=1)
            ),
            row=1, col=1
        )
        
        # Add trade markers if provided
        if trades is not None and not trades.empty:
            # Buy signals
            buy_trades = trades[trades['pnl'] > 0] if 'pnl' in trades.columns else trades
            if not buy_trades.empty:
                fig.add_trace(
                    go.Scatter(
                        x=buy_trades['entry_time'],
                        y=[equity_normalized.loc[equity_normalized.index.get_loc(t, method='nearest')] 
                           for t in buy_trades['entry_time']],
                        mode='markers',
                        name='Winning Trades',
                        marker=dict(color='green', size=8, symbol='triangle-up')
                    ),
                    row=1, col=1
                )
            
            # Sell signals
            sell_trades = trades[trades['pnl'] <= 0] if 'pnl' in trades.columns else pd.DataFrame()
            if not sell_trades.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sell_trades['entry_time'],
                        y=[equity_normalized.loc[equity_normalized.index.get_loc(t, method='nearest')] 
                           for t in sell_trades['entry_time']],
                        mode='markers',
                        name='Losing Trades',
                        marker=dict(color='red', size=8, symbol='triangle-down')
                    ),
                    row=1, col=1
                )
        
        # Drawdown calculation
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100
        
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                name='Drawdown (%)',
                line=dict(color='red', width=1),
                fill='tonexty'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title="Strategy Performance Analysis",
            height=600,
            showlegend=True,
            template="plotly_white"
        )
        
        fig.update_yaxes(title_text="Normalized Value", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        return fig
    
    def create_provider_comparison_chart(
        self,
        provider_data: Dict[str, pd.DataFrame],
        symbol: str = "BTC-USD"
    ) -> go.Figure:
        """Create multi-provider data comparison chart.
        
        Args:
            provider_data: Dictionary mapping provider names to DataFrames
            symbol: Cryptocurrency symbol
            
        Returns:
            Plotly figure
        """
        
        fig = go.Figure()
        
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        
        for i, (provider, data) in enumerate(provider_data.items()):
            if data is not None and not data.empty and 'close' in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['close'],
                        mode='lines',
                        name=f'{provider.title()}',
                        line=dict(color=colors[i % len(colors)], width=2)
                    )
                )
        
        fig.update_layout(
            title=f"{symbol} Price Comparison Across Providers",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500,
            showlegend=True,
            template="plotly_white"
        )
        
        return fig
