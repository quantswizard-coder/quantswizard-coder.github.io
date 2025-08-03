"""Performance metrics calculation for backtesting results."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Calculate comprehensive performance metrics for trading strategies."""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize performance metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        trades: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """Calculate all performance metrics.
        
        Args:
            returns: Strategy returns series
            benchmark_returns: Optional benchmark returns for comparison
            trades: Optional trades DataFrame for trade-specific metrics
            
        Returns:
            Dictionary with all performance metrics
        """
        metrics = {}
        
        # Basic return metrics
        metrics.update(self._calculate_return_metrics(returns))
        
        # Risk metrics
        metrics.update(self._calculate_risk_metrics(returns))
        
        # Risk-adjusted metrics
        metrics.update(self._calculate_risk_adjusted_metrics(returns))
        
        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics(returns))
        
        # Trade-specific metrics
        if trades is not None and not trades.empty:
            metrics.update(self._calculate_trade_metrics(trades))
        
        # Benchmark comparison
        if benchmark_returns is not None:
            metrics.update(self._calculate_benchmark_metrics(returns, benchmark_returns))
        
        return metrics
    
    def _calculate_return_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate return-based metrics."""
        if returns.empty:
            return {}
        
        # Total return
        total_return = (1 + returns).prod() - 1
        
        # Annualized return
        periods_per_year = self._get_periods_per_year(returns)
        n_periods = len(returns)
        annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
        
        # Average return
        avg_return = returns.mean()
        avg_return_annualized = avg_return * periods_per_year
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'avg_return': avg_return,
            'avg_return_annualized': avg_return_annualized
        }
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate risk-based metrics."""
        if returns.empty:
            return {}
        
        periods_per_year = self._get_periods_per_year(returns)
        
        # Volatility
        volatility = returns.std()
        volatility_annualized = volatility * np.sqrt(periods_per_year)
        
        # Downside deviation
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        downside_deviation_annualized = downside_deviation * np.sqrt(periods_per_year)
        
        # Value at Risk (VaR)
        var_95 = returns.quantile(0.05)
        var_99 = returns.quantile(0.01)
        
        # Expected Shortfall (Conditional VaR)
        es_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        es_99 = returns[returns <= var_99].mean() if len(returns[returns <= var_99]) > 0 else var_99
        
        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        return {
            'volatility': volatility,
            'volatility_annualized': volatility_annualized,
            'downside_deviation': downside_deviation,
            'downside_deviation_annualized': downside_deviation_annualized,
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall_95': es_95,
            'expected_shortfall_99': es_99,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def _calculate_risk_adjusted_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics."""
        if returns.empty:
            return {}
        
        periods_per_year = self._get_periods_per_year(returns)
        
        # Sharpe Ratio
        excess_returns = returns - self.risk_free_rate / periods_per_year
        sharpe_ratio = excess_returns.mean() / returns.std() if returns.std() > 0 else 0
        sharpe_ratio_annualized = sharpe_ratio * np.sqrt(periods_per_year)
        
        # Sortino Ratio
        downside_returns = returns[returns < self.risk_free_rate / periods_per_year]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
        sortino_ratio = excess_returns.mean() / downside_std if downside_std > 0 else 0
        sortino_ratio_annualized = sortino_ratio * np.sqrt(periods_per_year)
        
        # Calmar Ratio (requires drawdown calculation)
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        annualized_return = (cumulative_returns.iloc[-1]) ** (periods_per_year / len(returns)) - 1
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Information Ratio (vs risk-free rate)
        tracking_error = excess_returns.std()
        information_ratio = excess_returns.mean() / tracking_error if tracking_error > 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sharpe_ratio_annualized': sharpe_ratio_annualized,
            'sortino_ratio': sortino_ratio,
            'sortino_ratio_annualized': sortino_ratio_annualized,
            'calmar_ratio': calmar_ratio,
            'information_ratio': information_ratio
        }
    
    def _calculate_drawdown_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate drawdown-related metrics."""
        if returns.empty:
            return {}
        
        # Calculate drawdown series
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        # Maximum drawdown
        max_drawdown = drawdown.min()
        
        # Average drawdown
        avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0
        
        # Drawdown duration
        drawdown_periods = (drawdown < 0).astype(int)
        drawdown_duration = self._calculate_consecutive_periods(drawdown_periods)
        max_drawdown_duration = max(drawdown_duration) if drawdown_duration else 0
        avg_drawdown_duration = np.mean(drawdown_duration) if drawdown_duration else 0
        
        # Recovery time (time to recover from max drawdown)
        max_dd_idx = drawdown.idxmin()
        recovery_idx = drawdown[max_dd_idx:].ge(0).idxmax() if any(drawdown[max_dd_idx:] >= 0) else None
        recovery_time = (recovery_idx - max_dd_idx).days if recovery_idx else None
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'max_drawdown_duration': max_drawdown_duration,
            'avg_drawdown_duration': avg_drawdown_duration,
            'recovery_time_days': recovery_time
        }
    
    def _calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, float]:
        """Calculate trade-specific metrics."""
        if trades.empty:
            return {}
        
        # Basic trade statistics
        total_trades = len(trades)
        
        if 'pnl' in trades.columns:
            winning_trades = len(trades[trades['pnl'] > 0])
            losing_trades = len(trades[trades['pnl'] < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            loss_rate = losing_trades / total_trades if total_trades > 0 else 0
            
            # P&L statistics
            total_pnl = trades['pnl'].sum()
            avg_pnl = trades['pnl'].mean()
            
            # Win/Loss statistics
            winning_pnl = trades[trades['pnl'] > 0]['pnl']
            losing_pnl = trades[trades['pnl'] < 0]['pnl']
            
            avg_win = winning_pnl.mean() if len(winning_pnl) > 0 else 0
            avg_loss = losing_pnl.mean() if len(losing_pnl) > 0 else 0
            
            # Profit factor
            gross_profit = winning_pnl.sum() if len(winning_pnl) > 0 else 0
            gross_loss = abs(losing_pnl.sum()) if len(losing_pnl) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Expectancy
            expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)
            
            # Largest win/loss
            largest_win = winning_pnl.max() if len(winning_pnl) > 0 else 0
            largest_loss = losing_pnl.min() if len(losing_pnl) > 0 else 0
            
        else:
            # If no P&L column, set defaults
            win_rate = loss_rate = avg_win = avg_loss = 0
            total_pnl = avg_pnl = profit_factor = expectancy = 0
            largest_win = largest_loss = 0
        
        # Trade duration statistics
        if 'entry_time' in trades.columns and 'exit_time' in trades.columns:
            trade_durations = (pd.to_datetime(trades['exit_time']) - pd.to_datetime(trades['entry_time'])).dt.total_seconds() / 3600  # in hours
            avg_trade_duration = trade_durations.mean()
            max_trade_duration = trade_durations.max()
            min_trade_duration = trade_durations.min()
        else:
            avg_trade_duration = max_trade_duration = min_trade_duration = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades if 'pnl' in trades.columns else 0,
            'losing_trades': losing_trades if 'pnl' in trades.columns else 0,
            'win_rate': win_rate,
            'loss_rate': loss_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration_hours': avg_trade_duration,
            'max_trade_duration_hours': max_trade_duration,
            'min_trade_duration_hours': min_trade_duration
        }
    
    def _calculate_benchmark_metrics(self, returns: pd.Series, benchmark_returns: pd.Series) -> Dict[str, float]:
        """Calculate metrics relative to benchmark."""
        if returns.empty or benchmark_returns.empty:
            return {}
        
        # Align series
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        
        if aligned_returns.empty:
            return {}
        
        # Excess returns
        excess_returns = aligned_returns - aligned_benchmark
        
        # Tracking error
        tracking_error = excess_returns.std()
        
        # Information ratio
        information_ratio = excess_returns.mean() / tracking_error if tracking_error > 0 else 0
        
        # Beta
        covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
        benchmark_variance = aligned_benchmark.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Alpha
        periods_per_year = self._get_periods_per_year(returns)
        alpha = (aligned_returns.mean() - self.risk_free_rate / periods_per_year) - beta * (aligned_benchmark.mean() - self.risk_free_rate / periods_per_year)
        alpha_annualized = alpha * periods_per_year
        
        # Correlation
        correlation = aligned_returns.corr(aligned_benchmark)
        
        return {
            'tracking_error': tracking_error,
            'information_ratio_vs_benchmark': information_ratio,
            'beta': beta,
            'alpha': alpha,
            'alpha_annualized': alpha_annualized,
            'correlation_with_benchmark': correlation
        }
    
    def _get_periods_per_year(self, returns: pd.Series) -> int:
        """Estimate periods per year based on data frequency."""
        if len(returns) < 2:
            return 252  # Default to daily
        
        # Calculate average time difference
        time_diff = (returns.index[-1] - returns.index[0]) / (len(returns) - 1)
        
        if time_diff <= pd.Timedelta(minutes=5):
            return 252 * 24 * 12  # 5-minute data
        elif time_diff <= pd.Timedelta(hours=1):
            return 252 * 24  # Hourly data
        elif time_diff <= pd.Timedelta(days=1):
            return 252  # Daily data
        elif time_diff <= pd.Timedelta(weeks=1):
            return 52  # Weekly data
        else:
            return 12  # Monthly data
    
    def _calculate_consecutive_periods(self, binary_series: pd.Series) -> List[int]:
        """Calculate lengths of consecutive periods where condition is True."""
        consecutive_lengths = []
        current_length = 0
        
        for value in binary_series:
            if value == 1:
                current_length += 1
            else:
                if current_length > 0:
                    consecutive_lengths.append(current_length)
                    current_length = 0
        
        # Don't forget the last sequence if it ends with True
        if current_length > 0:
            consecutive_lengths.append(current_length)
        
        return consecutive_lengths
