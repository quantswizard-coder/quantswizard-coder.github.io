import React from 'react';
import {
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { PerformanceMetrics as PerformanceMetricsType } from '../../types';
import { MetricCard } from '../ui/Card';
import { InfoTooltip } from '../ui/Tooltip';

interface PerformanceMetricsProps {
  metrics: PerformanceMetricsType;
  initialCapital: number;
  currentValue: number;
  loading?: boolean;
  className?: string;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  metrics,
  initialCapital,
  currentValue,
  loading = false,
  className,
}) => {
  const formatPercentage = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals);

  const totalReturnColor = metrics.totalReturn >= 0 ? 'success' : 'danger';
  const sharpeColor = metrics.sharpeRatio >= 1 ? 'success' : metrics.sharpeRatio >= 0 ? 'warning' : 'danger';

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 ${className}`}>
      {/* Portfolio Value */}
      <MetricCard
        title="Portfolio Value"
        value={formatCurrency(currentValue)}
        subtitle={`Initial: ${formatCurrency(initialCapital)}`}
        trend={currentValue >= initialCapital ? 'up' : 'down'}
        trendValue={formatCurrency(currentValue - initialCapital)}
        icon={<CurrencyDollarIcon />}
        color="primary"
        loading={loading}
      />

      {/* Total Return */}
      <MetricCard
        title={
          <div className="flex items-center space-x-1">
            <span>Total Return</span>
            <InfoTooltip
              title="Total Return"
              description="The percentage gain or loss of the portfolio from the initial capital."
              formula="(Current Value - Initial Capital) / Initial Capital × 100"
            />
          </div>
        }
        value={formatPercentage(metrics.totalReturn)}
        trend={metrics.totalReturn >= 0 ? 'up' : 'down'}
        icon={metrics.totalReturn >= 0 ? <ArrowTrendingUpIcon /> : <ArrowTrendingDownIcon />}
        color={totalReturnColor}
        loading={loading}
      />

      {/* Sharpe Ratio */}
      <MetricCard
        title={
          <div className="flex items-center space-x-1">
            <span>Sharpe Ratio</span>
            <InfoTooltip
              title="Sharpe Ratio"
              description="Measures risk-adjusted returns. Higher values indicate better risk-adjusted performance. Values above 1 are considered good, above 2 are excellent."
              formula="(Portfolio Return - Risk-free Rate) / Portfolio Volatility"
            />
          </div>
        }
        value={formatNumber(metrics.sharpeRatio, 3)}
        subtitle={
          metrics.sharpeRatio >= 2 ? 'Excellent' :
          metrics.sharpeRatio >= 1 ? 'Good' :
          metrics.sharpeRatio >= 0 ? 'Fair' : 'Poor'
        }
        icon={<ChartBarIcon />}
        color={sharpeColor}
        loading={loading}
      />

      {/* Maximum Drawdown */}
      <MetricCard
        title={
          <div className="flex items-center space-x-1">
            <span>Max Drawdown</span>
            <InfoTooltip
              title="Maximum Drawdown"
              description="The largest peak-to-trough decline in portfolio value. Lower values indicate better risk management."
              formula="(Peak Value - Trough Value) / Peak Value × 100"
            />
          </div>
        }
        value={formatPercentage(metrics.maxDrawdown)}
        subtitle="Peak to trough"
        icon={<ArrowTrendingDownIcon />}
        color={Math.abs(metrics.maxDrawdown) <= 5 ? 'success' : Math.abs(metrics.maxDrawdown) <= 15 ? 'warning' : 'danger'}
        loading={loading}
      />

      {/* Total Trades */}
      <MetricCard
        title="Total Trades"
        value={metrics.totalTrades.toString()}
        subtitle={`Win Rate: ${formatPercentage(metrics.winRate)}`}
        icon={<ArrowPathIcon />}
        color="neutral"
        loading={loading}
      />

      {/* Additional metrics row */}
      <MetricCard
        title={
          <div className="flex items-center space-x-1">
            <span>Volatility</span>
            <InfoTooltip
              title="Volatility"
              description="Standard deviation of returns, measuring the degree of variation in portfolio value. Lower values indicate more stable returns."
            />
          </div>
        }
        value={formatPercentage(metrics.volatility)}
        subtitle="Annualized"
        color="neutral"
        loading={loading}
      />

      <MetricCard
        title={
          <div className="flex items-center space-x-1">
            <span>Profit Factor</span>
            <InfoTooltip
              title="Profit Factor"
              description="Ratio of gross profit to gross loss. Values above 1 indicate profitability, above 2 are considered good."
              formula="Total Winning Trades / Total Losing Trades"
            />
          </div>
        }
        value={formatNumber(metrics.profitFactor)}
        subtitle={metrics.profitFactor >= 2 ? 'Excellent' : metrics.profitFactor >= 1 ? 'Profitable' : 'Unprofitable'}
        color={metrics.profitFactor >= 2 ? 'success' : metrics.profitFactor >= 1 ? 'warning' : 'danger'}
        loading={loading}
      />

      <MetricCard
        title="Avg Trade Return"
        value={formatPercentage(metrics.avgTradeReturn)}
        subtitle="Per trade"
        color={metrics.avgTradeReturn >= 0 ? 'success' : 'danger'}
        loading={loading}
      />

      <MetricCard
        title="Best Trade"
        value={formatPercentage(metrics.bestTrade)}
        subtitle="Single trade"
        color="success"
        loading={loading}
      />

      <MetricCard
        title="Worst Trade"
        value={formatPercentage(metrics.worstTrade)}
        subtitle="Single trade"
        color="danger"
        loading={loading}
      />
    </div>
  );
};
