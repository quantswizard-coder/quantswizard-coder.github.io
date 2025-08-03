import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService, queryKeys } from '../services/api';
import { StrategyParams, StrategyOption } from '../types';
import { StrategySelector } from '../components/strategy/StrategySelector';
import { StrategyParameters } from '../components/strategy/StrategyParameters';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { BookmarkIcon, TrashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface SavedConfig {
  id: string;
  name: string;
  strategyId: string;
  strategyName: string;
  parameters: StrategyParams;
  createdAt: string;
}

export const Strategy: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [strategyParameters, setStrategyParameters] = useState<StrategyParams | null>(null);
  const [savedConfigs, setSavedConfigs] = useState<SavedConfig[]>([]);
  const [configName, setConfigName] = useState('');

  // Load strategies
  const { data: strategiesResponse, isLoading } = useQuery({
    queryKey: queryKeys.strategies,
    queryFn: () => apiService.getAvailableStrategies(),
  });

  const strategies = strategiesResponse?.data || [];

  // Load default parameters when strategy changes
  const { data: defaultParamsResponse } = useQuery({
    queryKey: queryKeys.strategyDefaults(selectedStrategy),
    queryFn: () => apiService.getStrategyDefaults(selectedStrategy),
    enabled: !!selectedStrategy,
  });

  // Load saved configurations from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('trading-simulator-configs');
    if (saved) {
      try {
        setSavedConfigs(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load saved configurations:', error);
      }
    }
  }, []);

  // Update parameters when defaults are loaded
  useEffect(() => {
    if (defaultParamsResponse?.data) {
      setStrategyParameters(defaultParamsResponse.data);
    }
  }, [defaultParamsResponse]);

  // Set initial strategy
  useEffect(() => {
    if (strategies.length > 0 && !selectedStrategy) {
      setSelectedStrategy(strategies[0].id);
    }
  }, [strategies, selectedStrategy]);

  // Save current strategy to localStorage whenever it changes
  useEffect(() => {
    if (selectedStrategy && strategyParameters) {
      localStorage.setItem('current-strategy', JSON.stringify(selectedStrategy));
      localStorage.setItem('current-strategy-params', JSON.stringify(strategyParameters));
    }
  }, [selectedStrategy, strategyParameters]);

  const handleSaveConfiguration = () => {
    if (!configName.trim()) {
      toast.error('Please enter a configuration name');
      return;
    }

    if (!selectedStrategy || !strategyParameters) {
      toast.error('Please select a strategy and configure parameters');
      return;
    }

    const selectedStrategyData = strategies.find((s: StrategyOption) => s.id === selectedStrategy);
    if (!selectedStrategyData) return;

    const newConfig: SavedConfig = {
      id: Date.now().toString(),
      name: configName.trim(),
      strategyId: selectedStrategy,
      strategyName: selectedStrategyData.name,
      parameters: strategyParameters,
      createdAt: new Date().toISOString(),
    };

    const updatedConfigs = [...savedConfigs, newConfig];
    setSavedConfigs(updatedConfigs);
    localStorage.setItem('trading-simulator-configs', JSON.stringify(updatedConfigs));
    
    setConfigName('');
    toast.success('Configuration saved successfully');
  };

  const handleLoadConfiguration = (config: SavedConfig) => {
    setSelectedStrategy(config.strategyId);
    setStrategyParameters(config.parameters);
    toast.success(`Loaded configuration: ${config.name}`);
  };

  const handleDeleteConfiguration = (configId: string) => {
    const updatedConfigs = savedConfigs.filter(config => config.id !== configId);
    setSavedConfigs(updatedConfigs);
    localStorage.setItem('trading-simulator-configs', JSON.stringify(updatedConfigs));
    toast.success('Configuration deleted');
  };

  const selectedStrategyData = strategies.find((s: StrategyOption) => s.id === selectedStrategy);

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <StrategySelector
        selectedStrategy={selectedStrategy}
        onStrategyChange={setSelectedStrategy}
      />

      {/* Strategy Parameters */}
      {selectedStrategyData && strategyParameters && (
        <StrategyParameters
          strategyType={selectedStrategyData.type}
          parameters={strategyParameters}
          onChange={setStrategyParameters}
        />
      )}

      {/* Save Configuration */}
      <Card title="Save Configuration" subtitle="Save your strategy settings for later use">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={configName}
              onChange={(e) => setConfigName(e.target.value)}
              placeholder="Enter configuration name..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <Button
            onClick={handleSaveConfiguration}
            icon={<BookmarkIcon />}
            disabled={!configName.trim() || !selectedStrategy || !strategyParameters}
          >
            Save Configuration
          </Button>
        </div>
      </Card>

      {/* Saved Configurations */}
      {savedConfigs.length > 0 && (
        <Card title="Saved Configurations" subtitle={`${savedConfigs.length} saved configurations`}>
          <div className="space-y-3">
            {savedConfigs.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {config.name}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {config.strategyName} • Saved {new Date(config.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleLoadConfiguration(config)}
                  >
                    Load
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    icon={<TrashIcon />}
                    onClick={() => handleDeleteConfiguration(config.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Strategy Status */}
      {selectedStrategy && strategyParameters && (
        <Card
          title="✅ Strategy Ready for Simulation"
          className="border-success-200 bg-success-50 dark:bg-success-900/20"
        >
          <div className="space-y-2">
            <p className="text-sm text-success-700 dark:text-success-300">
              <strong>{selectedStrategyData?.name}</strong> is configured and ready to use.
            </p>
            <p className="text-xs text-success-600 dark:text-success-400">
              Go to the Simulation tab to create and run your backtest.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};
