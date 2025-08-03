import React from 'react';
import { 
  PlayIcon, 
  PauseIcon, 
  StopIcon, 
  ArrowPathIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';
import { SimulationState } from '../../types';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
// import { motion } from 'framer-motion'; // Removed for now

interface SimulationControlsProps {
  simulationState?: SimulationState;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onReset: () => void;
  onExport: () => void;
  isStarting?: boolean;
  isPausing?: boolean;
  isStopping?: boolean;
  className?: string;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  simulationState,
  onStart,
  onPause,
  onStop,
  onReset,
  onExport,
  isStarting = false,
  isPausing = false,
  isStopping = false,
  className,
}) => {
  const status = simulationState?.status || 'idle';
  const progress = simulationState?.progress || 0;

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'text-success-600';
      case 'paused':
        return 'text-warning-600';
      case 'completed':
        return 'text-primary-600';
      case 'error':
        return 'text-danger-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Running';
      case 'paused':
        return 'Paused';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      default:
        return 'Ready';
    }
  };

  const canStart = status === 'idle' || status === 'paused';
  const canPause = status === 'running';
  const canStop = status === 'running' || status === 'paused';
  const canReset = status === 'completed' || status === 'error';
  const canExport = status === 'completed';

  return (
    <Card
      title="Simulation Controls"
      className={className}
    >
      <div className="space-y-6">
        {/* Status and Progress */}
        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <div className={`w-3 h-3 rounded-full ${
              status === 'running' ? 'bg-success-500 animate-pulse' :
              status === 'paused' ? 'bg-warning-500' :
              status === 'completed' ? 'bg-primary-500' :
              status === 'error' ? 'bg-danger-500' :
              'bg-gray-400'
            }`} />
            <span className={`font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
          
          {simulationState?.current_date && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Current Date: {new Date(simulationState.current_date).toLocaleDateString()}
            </p>
          )}
          {!simulationState?.current_date && status !== 'idle' && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Preparing simulation...
            </p>
          )}
        </div>

        {/* Progress Bar */}
        {(status === 'running' || status === 'paused') && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Progress</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {(progress * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Control Buttons */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <Button
            variant="success"
            onClick={onStart}
            disabled={!canStart}
            loading={isStarting}
            icon={<PlayIcon />}
            fullWidth
          >
            Start
          </Button>

          <Button
            variant="warning"
            onClick={onPause}
            disabled={!canPause}
            loading={isPausing}
            icon={<PauseIcon />}
            fullWidth
          >
            Pause
          </Button>

          <Button
            variant="danger"
            onClick={onStop}
            disabled={!canStop}
            loading={isStopping}
            icon={<StopIcon />}
            fullWidth
          >
            Stop
          </Button>

          <Button
            variant="secondary"
            onClick={onReset}
            disabled={!canReset}
            icon={<ArrowPathIcon />}
            fullWidth
          >
            Reset
          </Button>

          <Button
            variant="primary"
            onClick={onExport}
            disabled={!canExport}
            icon={<DocumentArrowDownIcon />}
            fullWidth
          >
            Export
          </Button>
        </div>

        {/* Error Message */}
        {status === 'error' && simulationState?.error_message && (
          <div className="bg-danger-50 dark:bg-danger-900 border border-danger-200 dark:border-danger-700 rounded-lg p-3">
            <p className="text-sm text-danger-800 dark:text-danger-200">
              <strong>Error:</strong> {simulationState.error_message}
            </p>
          </div>
        )}

        {/* Quick Stats */}
        {simulationState?.portfolio && (
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Portfolio Value</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                ${simulationState.portfolio.totalValue.toLocaleString()}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Trades</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {simulationState.trades?.length || 0}
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
