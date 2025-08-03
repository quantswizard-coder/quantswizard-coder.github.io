import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService, queryKeys } from '../../services/api';
import { StrategyOption } from '../../types';
import { Card } from '../ui/Card';
import { Select } from '../ui/Select';
import { InfoTooltip } from '../ui/Tooltip';

interface StrategySelectorProps {
  selectedStrategy: string;
  onStrategyChange: (strategyId: string) => void;
  className?: string;
}

export const StrategySelector: React.FC<StrategySelectorProps> = ({
  selectedStrategy,
  onStrategyChange,
  className,
}) => {
  const { data: strategiesResponse, isLoading, error } = useQuery({
    queryKey: queryKeys.strategies,
    queryFn: () => apiService.getAvailableStrategies(),
  });

  const strategies = strategiesResponse?.data || [];

  const strategyOptions = strategies.map((strategy: StrategyOption) => ({
    value: strategy.id,
    label: strategy.name,
    description: strategy.description,
  }));

  const selectedStrategyData = strategies.find((s: StrategyOption) => s.id === selectedStrategy);

  return (
    <Card
      title="Strategy Selection"
      subtitle="Choose your trading strategy"
      loading={isLoading}
      error={error ? 'Failed to load strategies' : undefined}
      className={className}
    >
      <div className="space-y-4">
        <Select
          label="Trading Strategy"
          value={selectedStrategy}
          onChange={onStrategyChange}
          options={strategyOptions}
          placeholder="Select a strategy..."
          fullWidth
        />

        {selectedStrategyData && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {selectedStrategyData.name}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {selectedStrategyData.description}
                </p>
              </div>
              <InfoTooltip
                title={selectedStrategyData.name}
                description={selectedStrategyData.description}
              />
            </div>

            {/* Strategy type badge */}
            <div className="mt-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                {selectedStrategyData.type.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
