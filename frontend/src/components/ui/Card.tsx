import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  loading?: boolean;
  error?: string;
  animate?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  action,
  loading = false,
  error,
  animate = true,
}) => {
  const cardContent = (
    <div
      className={clsx(
        'bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700',
        'transition-colors duration-200',
        className
      )}
    >
      {(title || subtitle || action) && (
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
            {action && <div>{action}</div>}
          </div>
        </div>
      )}
      
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <div className="text-danger-500 text-sm">{error}</div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {cardContent}
      </motion.div>
    );
  }

  return cardContent;
};

interface MetricCardProps {
  title: React.ReactNode;
  value: string | number;
  subtitle?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'danger' | 'warning' | 'neutral';
  loading?: boolean;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  color = 'neutral',
  loading = false,
  className,
}) => {
  const colorClasses = {
    primary: 'text-primary-600 dark:text-primary-400',
    success: 'text-success-600 dark:text-success-400',
    danger: 'text-danger-600 dark:text-danger-400',
    warning: 'text-warning-600 dark:text-warning-400',
    neutral: 'text-gray-600 dark:text-gray-400',
  };

  const trendClasses = {
    up: 'text-success-600 dark:text-success-400',
    down: 'text-danger-600 dark:text-danger-400',
    neutral: 'text-gray-600 dark:text-gray-400',
  };

  return (
    <Card className={className} animate>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            {icon && (
              <div className={clsx('w-5 h-5', colorClasses[color])}>
                {icon}
              </div>
            )}
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
          </div>
          
          {loading ? (
            <div className="mt-2">
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            </div>
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {value}
              </p>
              
              {(subtitle || (trend && trendValue)) && (
                <div className="mt-2 flex items-center space-x-2">
                  {subtitle && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {subtitle}
                    </p>
                  )}
                  {trend && trendValue && (
                    <span className={clsx('text-sm font-medium', trendClasses[trend])}>
                      {trend === 'up' && '↗'} 
                      {trend === 'down' && '↘'} 
                      {trendValue}
                    </span>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Card>
  );
};
