import React, { useState } from 'react';
import { SimulationConfig as SimulationConfigComponent } from '../components/simulation/SimulationConfig';
import { SimulationControls } from '../components/simulation/SimulationControls';
import { useSimulation } from '../hooks/useSimulation';
import { SimulationConfig as SimulationConfigType, StrategyParams } from '../types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { PlayIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export const Simulation: React.FC = () => {
  const {
    simulationState,
    createSimulation,
    startSimulation,
    pauseSimulation,
    stopSimulation,
    resetSimulation,
    isCreating,
    isStarting,
    isPausing,
    isStopping,
  } = useSimulation();

  const [config, setConfig] = useState<SimulationConfigType>({
    initial_capital: 100000,
    position_size: 0.2,
    commission_rate: 0.001,
    slippage_rate: 0.0005,
    max_positions: 3,
    speed_multiplier: 10,
  });

  const handleCreateAndStartSimulation = async () => {
    // Get strategy configuration from localStorage or use default
    const savedStrategy = localStorage.getItem('current-strategy');
    const savedParams = localStorage.getItem('current-strategy-params');

    console.log('Saved strategy:', savedStrategy);
    console.log('Saved params:', savedParams);

    if (!savedStrategy || !savedParams) {
      // Use default strategy if none configured
      console.log('No strategy configured, using default Balanced Ensemble');
      const defaultStrategyId = 'balanced_ensemble';
      const defaultParams = {
        name: 'Balanced Ensemble',
        description: 'Default balanced ensemble strategy',
        ensemble_method: 'confidence_weighted' as const,
        min_consensus: 0.4,
        confidence_threshold: 0.3,
        strategy_weights: {
          ma_crossover: 0.33,
          rsi_mean_reversion: 0.33,
          momentum: 0.34
        }
      };

      try {
        console.log('Creating simulation with default strategy:', { defaultStrategyId, defaultParams, config });

        await createSimulation({
          strategyId: defaultStrategyId,
          strategyParams: defaultParams,
          config,
        });

        setTimeout(() => {
          console.log('Starting simulation...');
          startSimulation();
        }, 1000);

        toast.success('Using default Balanced Ensemble strategy');
        return;
      } catch (error) {
        console.error('Failed to create simulation with default strategy:', error);
        toast.error('Please configure a strategy first in the Strategy tab');
        return;
      }
    }

    try {
      const strategyId = JSON.parse(savedStrategy);
      const strategyParams: StrategyParams = JSON.parse(savedParams);

      console.log('Creating simulation with:', { strategyId, strategyParams, config });

      // Create simulation
      await createSimulation({
        strategyId,
        strategyParams,
        config,
      });

      // Start simulation automatically after creation
      setTimeout(() => {
        console.log('Starting simulation...');
        startSimulation();
      }, 1000);
    } catch (error) {
      console.error('Failed to create simulation:', error);
      toast.error('Failed to create simulation. Please check your configuration.');
    }
  };

  const handleExport = async () => {
    try {
      // This would call the export API
      toast.success('Export functionality coming soon!');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const hasActiveSimulation = simulationState && simulationState.status !== 'idle';

  // Get current strategy info for display
  const savedStrategy = localStorage.getItem('current-strategy');
  const savedParams = localStorage.getItem('current-strategy-params');
  let currentStrategyName = 'Balanced Ensemble (Default)';

  if (savedStrategy && savedParams) {
    try {
      const strategyId = JSON.parse(savedStrategy);
      const strategyParams = JSON.parse(savedParams);
      currentStrategyName = strategyParams.name || strategyId;
    } catch (error) {
      console.error('Error parsing strategy info:', error);
    }
  }

  return (
    <div className="space-y-6">
      {/* Current Strategy Status */}
      <Card
        title="📊 Current Strategy"
        className="border-primary-200 bg-primary-50 dark:bg-primary-900/20"
      >
        <div className="space-y-2">
          <p className="text-sm text-primary-700 dark:text-primary-300">
            <strong>{currentStrategyName}</strong> is ready for simulation.
          </p>
          <p className="text-xs text-primary-600 dark:text-primary-400">
            {savedStrategy && savedParams
              ? 'Strategy configured in Strategy tab.'
              : 'Using default strategy. Configure in Strategy tab for custom settings.'
            }
          </p>
        </div>
      </Card>

      {/* Simulation Configuration */}
      <SimulationConfigComponent
        config={config}
        onChange={setConfig}
      />

      {/* Simulation Controls */}
      <SimulationControls
        simulationState={simulationState}
        onStart={startSimulation}
        onPause={pauseSimulation}
        onStop={stopSimulation}
        onReset={resetSimulation}
        onExport={handleExport}
        isStarting={isStarting}
        isPausing={isPausing}
        isStopping={isStopping}
      />

      {/* Quick Start */}
      {!hasActiveSimulation && (
        <Card
          title="Quick Start"
          subtitle="Create and start a new simulation with current settings"
        >
          <div className="text-center space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              Ready to test your trading strategy? Click below to create and start a new simulation.
            </p>
            <Button
              variant="primary"
              size="lg"
              icon={<PlayIcon />}
              onClick={handleCreateAndStartSimulation}
              loading={isCreating}
              disabled={isCreating}
            >
              {isCreating ? 'Creating Simulation...' : 'Create & Start Simulation'}
            </Button>
          </div>
        </Card>
      )}

      {/* Simulation Status */}
      {hasActiveSimulation && (
        <Card title="Simulation Status">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                {simulationState.status}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Progress</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {(simulationState.progress * 100).toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Current Date</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {simulationState.current_date 
                  ? new Date(simulationState.current_date).toLocaleDateString()
                  : 'N/A'
                }
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Configuration Summary */}
      <Card title="Current Configuration" subtitle="Review your simulation settings">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Initial Capital</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              ${config.initial_capital.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Position Size</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {(config.position_size * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Commission</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {(config.commission_rate * 100).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Speed</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {config.speed_multiplier}x
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
