import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { 
  EnsembleParams, 
  MACrossoverParams, 
  RSIParams, 
  MomentumParams,
  StrategyParams 
} from '../../types';
import { Card } from '../ui/Card';
import { Input, Slider } from '../ui/Input';
import { Select } from '../ui/Select';
import { InfoTooltip } from '../ui/Tooltip';

interface StrategyParametersProps {
  strategyType: string;
  parameters: StrategyParams;
  onChange: (parameters: StrategyParams) => void;
  className?: string;
}

export const StrategyParameters: React.FC<StrategyParametersProps> = ({
  strategyType,
  parameters,
  onChange,
  className,
}) => {
  const { control, watch, setValue } = useForm<any>({
    defaultValues: parameters,
    mode: 'onChange',
  });

  // Watch all form values and update parent
  const watchedValues = watch();
  React.useEffect(() => {
    onChange(watchedValues as StrategyParams);
  }, [watchedValues, onChange]);

  const renderEnsembleParameters = (params: EnsembleParams) => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Controller
          name="ensemble_method"
          control={control}
          render={({ field }) => (
            <Select
              label={
                <div className="flex items-center space-x-1">
                  <span>Ensemble Method</span>
                  <InfoTooltip
                    title="Ensemble Method"
                    description="How individual strategy signals are combined. Confidence-weighted gives more weight to high-confidence signals."
                  />
                </div>
              }
              value={field.value}
              onChange={field.onChange}
              options={[
                { value: 'confidence_weighted', label: 'Confidence Weighted', description: 'Weight by signal confidence' },
                { value: 'weighted_voting', label: 'Weighted Voting', description: 'Use predefined strategy weights' },
                { value: 'majority_voting', label: 'Majority Voting', description: 'Equal weight for all strategies' },
              ]}
              fullWidth
            />
          )}
        />

        <Controller
          name="min_consensus"
          control={control}
          render={({ field }) => (
            <Slider
              label={
                <div className="flex items-center space-x-1">
                  <span>Minimum Consensus</span>
                  <InfoTooltip
                    title="Minimum Consensus"
                    description="Minimum agreement required between strategies to generate a signal. Higher values are more conservative."
                  />
                </div>
              }
              value={field.value}
              onChange={field.onChange}
              min={0.1}
              max={0.9}
              step={0.1}
              formatValue={(v) => `${(v * 100).toFixed(0)}%`}
            />
          )}
        />
      </div>

      <Controller
        name="confidence_threshold"
        control={control}
        render={({ field }) => (
          <Slider
            label={
              <div className="flex items-center space-x-1">
                <span>Confidence Threshold</span>
                <InfoTooltip
                  title="Confidence Threshold"
                  description="Minimum confidence level required for signals. Higher values filter out weak signals."
                />
              </div>
            }
            value={field.value}
            onChange={field.onChange}
            min={0.1}
            max={0.9}
            step={0.1}
            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          />
        )}
      />

      {/* Strategy Weights */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white">Strategy Weights</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Controller
            name="strategy_weights.ma_crossover"
            control={control}
            render={({ field }) => (
              <Slider
                label="MA Crossover"
                value={field.value}
                onChange={(value) => {
                  field.onChange(value);
                  // Auto-balance other weights
                  const remaining = 1 - value;
                  const currentRsi = watchedValues.strategy_weights?.rsi_mean_reversion || 0.33;
                  const currentMomentum = watchedValues.strategy_weights?.momentum || 0.33;
                  const total = currentRsi + currentMomentum;
                  if (total > 0) {
                    setValue('strategy_weights.rsi_mean_reversion', (currentRsi / total) * remaining);
                    setValue('strategy_weights.momentum', (currentMomentum / total) * remaining);
                  }
                }}
                min={0.1}
                max={0.8}
                step={0.01}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
          />
          <Controller
            name="strategy_weights.rsi_mean_reversion"
            control={control}
            render={({ field }) => (
              <Slider
                label="RSI Mean Reversion"
                value={field.value}
                onChange={field.onChange}
                min={0.1}
                max={0.8}
                step={0.01}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
          />
          <Controller
            name="strategy_weights.momentum"
            control={control}
            render={({ field }) => (
              <Slider
                label="Momentum"
                value={field.value}
                onChange={field.onChange}
                min={0.1}
                max={0.8}
                step={0.01}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
          />
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Total: {((watchedValues.strategy_weights?.ma_crossover || 0) + 
                   (watchedValues.strategy_weights?.rsi_mean_reversion || 0) + 
                   (watchedValues.strategy_weights?.momentum || 0)).toFixed(2)}
        </div>
      </div>
    </div>
  );

  const renderMACrossoverParameters = (params: MACrossoverParams) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Controller
        name="fast_period"
        control={control}
        render={({ field }) => (
          <Input
            label={
              <div className="flex items-center space-x-1">
                <span>Fast Period</span>
                <InfoTooltip
                  title="Fast Moving Average Period"
                  description="Number of periods for the fast moving average. Smaller values are more responsive to price changes."
                />
              </div>
            }
            type="number"
            value={field.value}
            onChange={(e) => field.onChange(Number(e.target.value))}
            min={5}
            max={50}
            fullWidth
          />
        )}
      />
      <Controller
        name="slow_period"
        control={control}
        render={({ field }) => (
          <Input
            label={
              <div className="flex items-center space-x-1">
                <span>Slow Period</span>
                <InfoTooltip
                  title="Slow Moving Average Period"
                  description="Number of periods for the slow moving average. Should be larger than fast period."
                />
              </div>
            }
            type="number"
            value={field.value}
            onChange={(e) => field.onChange(Number(e.target.value))}
            min={20}
            max={200}
            fullWidth
          />
        )}
      />
      <Controller
        name="ma_type"
        control={control}
        render={({ field }) => (
          <Select
            label="MA Type"
            value={field.value}
            onChange={field.onChange}
            options={[
              { value: 'sma', label: 'Simple MA', description: 'Equal weight for all periods' },
              { value: 'ema', label: 'Exponential MA', description: 'More weight on recent prices' },
            ]}
            fullWidth
          />
        )}
      />
      <Controller
        name="min_crossover_strength"
        control={control}
        render={({ field }) => (
          <Slider
            label="Min Crossover Strength"
            value={field.value}
            onChange={field.onChange}
            min={0}
            max={0.1}
            step={0.01}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
        )}
      />
    </div>
  );

  const renderRSIParameters = (params: RSIParams) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Controller
        name="rsi_period"
        control={control}
        render={({ field }) => (
          <Input
            label={
              <div className="flex items-center space-x-1">
                <span>RSI Period</span>
                <InfoTooltip
                  title="RSI Period"
                  description="Number of periods for RSI calculation. 14 is the standard value."
                />
              </div>
            }
            type="number"
            value={field.value}
            onChange={(e) => field.onChange(Number(e.target.value))}
            min={5}
            max={30}
            fullWidth
          />
        )}
      />
      <div className="space-y-4">
        <Controller
          name="oversold_threshold"
          control={control}
          render={({ field }) => (
            <Slider
              label="Oversold Threshold"
              value={field.value}
              onChange={field.onChange}
              min={10}
              max={40}
              step={1}
              formatValue={(v) => v.toString()}
            />
          )}
        />
        <Controller
          name="overbought_threshold"
          control={control}
          render={({ field }) => (
            <Slider
              label="Overbought Threshold"
              value={field.value}
              onChange={field.onChange}
              min={60}
              max={90}
              step={1}
              formatValue={(v) => v.toString()}
            />
          )}
        />
      </div>
    </div>
  );

  const renderMomentumParameters = (params: MomentumParams) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Controller
        name="lookback_period"
        control={control}
        render={({ field }) => (
          <Input
            label={
              <div className="flex items-center space-x-1">
                <span>Lookback Period</span>
                <InfoTooltip
                  title="Lookback Period"
                  description="Number of periods to look back for momentum calculation."
                />
              </div>
            }
            type="number"
            value={String(field.value || '')}
            onChange={(e) => field.onChange(Number(e.target.value))}
            min={5}
            max={30}
            fullWidth
          />
        )}
      />
      <Controller
        name="momentum_threshold"
        control={control}
        render={({ field }) => (
          <Slider
            label="Momentum Threshold"
            value={Number(field.value) || 0}
            onChange={field.onChange}
            min={0.001}
            max={0.02}
            step={0.001}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
        )}
      />
    </div>
  );

  const renderParameters = () => {
    switch (strategyType) {
      case 'ensemble':
        return renderEnsembleParameters(parameters as EnsembleParams);
      case 'ma_crossover':
        return renderMACrossoverParameters(parameters as MACrossoverParams);
      case 'rsi':
        return renderRSIParameters(parameters as RSIParams);
      case 'momentum':
        return renderMomentumParameters(parameters as MomentumParams);
      default:
        return <div>No parameters available for this strategy.</div>;
    }
  };

  return (
    <Card
      title="Strategy Parameters"
      subtitle="Customize your strategy settings"
      className={className}
    >
      {renderParameters()}
    </Card>
  );
};
