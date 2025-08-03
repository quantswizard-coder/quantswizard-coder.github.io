import React, { forwardRef } from 'react';
import clsx from 'clsx';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: React.ReactNode;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  inputSize?: 'sm' | 'md' | 'lg';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({
    label,
    error,
    helperText,
    leftIcon,
    rightIcon,
    fullWidth = false,
    inputSize = 'md',
    className,
    ...props
  }, ref) => {
    const inputClasses = clsx(
      'block w-full rounded-lg border border-gray-300 dark:border-gray-600',
      'bg-white dark:bg-gray-800 text-gray-900 dark:text-white',
      'placeholder-gray-500 dark:placeholder-gray-400',
      'focus:border-primary-500 focus:ring-primary-500 focus:ring-1',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'transition-colors duration-200',
      leftIcon ? 'pl-10' : '',
      rightIcon ? 'pr-10' : '',
      error ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-500' : '',
      inputSize === 'sm' ? 'px-3 py-2 text-sm' : inputSize === 'lg' ? 'px-5 py-4 text-lg' : 'px-4 py-3 text-base',
      className
    );

    return (
      <div className={clsx('relative', fullWidth && 'w-full')}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <div className="w-5 h-5 text-gray-400 dark:text-gray-500">
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            ref={ref}
            className={inputClasses}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <div className="w-5 h-5 text-gray-400 dark:text-gray-500">
                {rightIcon}
              </div>
            </div>
          )}
        </div>
        
        {(error || helperText) && (
          <p className={clsx(
            'mt-2 text-sm',
            error ? 'text-danger-600 dark:text-danger-400' : 'text-gray-600 dark:text-gray-400'
          )}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

interface SliderProps {
  label?: React.ReactNode;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  formatValue?: (value: number) => string;
  error?: string;
  helperText?: string;
  className?: string;
}

export const Slider: React.FC<SliderProps> = ({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  formatValue = (v) => v.toString(),
  error,
  helperText,
  className,
}) => {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={clsx('w-full', className)}>
      {label && (
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
          <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
            {formatValue(value)}
          </span>
        </div>
      )}
      
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className={clsx(
            'w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4',
            '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-600',
            '[&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-sm',
            '[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full',
            '[&::-moz-range-thumb]:bg-primary-600 [&::-moz-range-thumb]:cursor-pointer',
            '[&::-moz-range-thumb]:border-none [&::-moz-range-thumb]:shadow-sm',
            error && 'focus:ring-danger-500'
          )}
        />
        
        {/* Progress fill */}
        <div
          className="absolute top-0 h-2 bg-primary-600 rounded-lg pointer-events-none"
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
        <span>{formatValue(min)}</span>
        <span>{formatValue(max)}</span>
      </div>
      
      {(error || helperText) && (
        <p className={clsx(
          'mt-2 text-sm',
          error ? 'text-danger-600 dark:text-danger-400' : 'text-gray-600 dark:text-gray-400'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};
