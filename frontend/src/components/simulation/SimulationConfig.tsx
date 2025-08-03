import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { SimulationConfig as SimulationConfigType } from '../../types';
import { Card } from '../ui/Card';
import { Input, Slider } from '../ui/Input';
import { InfoTooltip } from '../ui/Tooltip';

interface SimulationConfigProps {
  config: SimulationConfigType;
  onChange: (config: SimulationConfigType) => void;
  className?: string;
}

export const SimulationConfig: React.FC<SimulationConfigProps> = ({
  config,
  onChange,
  className,
}) => {
  const { control, watch } = useForm({
    defaultValues: config,
    mode: 'onChange',
  });

  // Watch all form values and update parent
  const watchedValues = watch();
  React.useEffect(() => {
    onChange(watchedValues as SimulationConfigType);
  }, [watchedValues, onChange]);

  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;
  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatSpeed = (value: number) => `${value}x`;

  return (
    <Card
      title="Simulation Configuration"
      subtitle="Set up your trading simulation parameters"
      className={className}
    >
      <div className="space-y-6">
        {/* Capital and Position Sizing */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="initial_capital"
            control={control}
            render={({ field }) => (
              <Input
                label={
                  <div className="flex items-center space-x-1">
                    <span>Initial Capital</span>
                    <InfoTooltip
                      title="Initial Capital"
                      description="The starting amount of money for your trading simulation."
                    />
                  </div>
                }
                type="number"
                value={field.value}
                onChange={(e) => field.onChange(Number(e.target.value))}
                min={1000}
                max={1000000}
                step={1000}
                fullWidth
                leftIcon={<span className="text-gray-500">$</span>}
              />
            )}
          />

          <Controller
            name="position_size"
            control={control}
            render={({ field }) => (
              <Slider
                label={
                  <div className="flex items-center space-x-1">
                    <span>Position Size</span>
                    <InfoTooltip
                      title="Position Size"
                      description="Percentage of portfolio to risk per trade. Lower values are more conservative."
                    />
                  </div>
                }
                value={field.value}
                onChange={field.onChange}
                min={0.05}
                max={0.5}
                step={0.01}
                formatValue={formatPercentage}
              />
            )}
          />
        </div>

        {/* Trading Costs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="commission_rate"
            control={control}
            render={({ field }) => (
              <Slider
                label={
                  <div className="flex items-center space-x-1">
                    <span>Commission Rate</span>
                    <InfoTooltip
                      title="Commission Rate"
                      description="Trading commission as a percentage of trade value. Typical values are 0.1% to 0.25%."
                    />
                  </div>
                }
                value={field.value}
                onChange={field.onChange}
                min={0.0005}
                max={0.005}
                step={0.0001}
                formatValue={(v) => `${(v * 100).toFixed(2)}%`}
              />
            )}
          />

          <Controller
            name="slippage_rate"
            control={control}
            render={({ field }) => (
              <Slider
                label={
                  <div className="flex items-center space-x-1">
                    <span>Slippage Rate</span>
                    <InfoTooltip
                      title="Slippage Rate"
                      description="Price slippage as a percentage. Accounts for the difference between expected and actual execution price."
                    />
                  </div>
                }
                value={field.value}
                onChange={field.onChange}
                min={0.0001}
                max={0.002}
                step={0.0001}
                formatValue={(v) => `${(v * 100).toFixed(2)}%`}
              />
            )}
          />
        </div>

        {/* Risk Management */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="max_positions"
            control={control}
            render={({ field }) => (
              <Input
                label={
                  <div className="flex items-center space-x-1">
                    <span>Max Positions</span>
                    <InfoTooltip
                      title="Maximum Positions"
                      description="Maximum number of concurrent positions. Helps manage risk and diversification."
                    />
                  </div>
                }
                type="number"
                value={field.value}
                onChange={(e) => field.onChange(Number(e.target.value))}
                min={1}
                max={10}
                fullWidth
              />
            )}
          />

          <Controller
            name="speed_multiplier"
            control={control}
            render={({ field }) => (
              <Slider
                label={
                  <div className="flex items-center space-x-1">
                    <span>Simulation Speed</span>
                    <InfoTooltip
                      title="Simulation Speed"
                      description="How fast the simulation runs. Higher values complete faster but may be harder to follow."
                    />
                  </div>
                }
                value={field.value}
                onChange={field.onChange}
                min={1}
                max={50}
                step={1}
                formatValue={formatSpeed}
              />
            )}
          />
        </div>

        {/* Summary */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-3">Configuration Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Starting Capital</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {formatCurrency(watchedValues.initial_capital || 0)}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Position Size</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {formatPercentage(watchedValues.position_size || 0)}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Total Costs</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {((watchedValues.commission_rate || 0) + (watchedValues.slippage_rate || 0) * 100).toFixed(3)}%
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Max Risk per Trade</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {formatCurrency((watchedValues.initial_capital || 0) * (watchedValues.position_size || 0))}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
