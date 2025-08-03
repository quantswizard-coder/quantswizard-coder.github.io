import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService, queryKeys } from '../services/api';
import { PortfolioChart } from '../components/charts/PortfolioChart';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { PerformanceMetrics } from '../components/dashboard/PerformanceMetrics';
import { TradeHistory } from '../components/dashboard/TradeHistory';
import { useSimulation } from '../hooks/useSimulation';

export const Dashboard: React.FC = () => {
  const { simulationState, simulationId } = useSimulation();

  // Get market data for the chart
  const { data: marketDataResponse, isLoading: isLoadingMarketData } = useQuery({
    queryKey: queryKeys.marketData('BTC-USD', 180),
    queryFn: () => apiService.getMarketData('BTC-USD', 180),
  });

  const marketData = marketDataResponse?.data;
  const portfolio = simulationState?.portfolio;
  const trades = simulationState?.trades || [];
  const performance = simulationState?.performance;

  // Mock portfolio history for demonstration
  const portfolioHistory = React.useMemo(() => {
    if (!portfolio) return [];
    
    // Generate some sample portfolio snapshots
    const snapshots = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      
      // Simulate portfolio value changes
      const baseValue = 100000;
      const variation = Math.sin(i / 5) * 5000 + Math.random() * 2000 - 1000;
      const totalValue = baseValue + variation;
      
      snapshots.push({
        timestamp: date.toISOString(),
        totalValue,
        cash: totalValue * 0.2,
        positions: [],
        dailyReturn: (variation / baseValue) * 100,
        totalReturn: ((totalValue - baseValue) / baseValue) * 100,
        sharpeRatio: 1.2,
        maxDrawdown: -0.05,
        volatility: 0.15,
      });
    }
    
    return snapshots;
  }, [portfolio]);

  const hasData = simulationState && simulationState.status !== 'idle';

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No Simulation Data
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Start a simulation to view performance metrics, charts, and trade history.
            </p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                Getting Started
              </h4>
              <ol className="text-sm text-gray-600 dark:text-gray-400 space-y-2 text-left">
                <li>1. Go to the Strategy tab to select and configure your trading strategy</li>
                <li>2. Visit the Simulation tab to set up capital and risk parameters</li>
                <li>3. Start your simulation and return here to monitor performance</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Performance Metrics */}
      {performance && portfolio && (
        <PerformanceMetrics
          metrics={performance}
          initialCapital={100000} // This should come from simulation config
          currentValue={portfolio.totalValue}
          loading={!simulationState}
        />
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Portfolio Performance Chart */}
        <PortfolioChart
          data={portfolioHistory}
          initialCapital={100000}
          loading={!simulationState}
        />

        {/* Price Chart with Trade Markers */}
        <CandlestickChart
          data={marketData?.data || []}
          trades={trades}
          loading={isLoadingMarketData}
        />
      </div>

      {/* Trade History */}
      <TradeHistory
        trades={trades}
        loading={!simulationState}
      />
    </div>
  );
};
