import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';
import { PortfolioSnapshot } from '../../types';
import { Card } from '../ui/Card';

interface PortfolioChartProps {
  data: PortfolioSnapshot[];
  initialCapital: number;
  loading?: boolean;
  className?: string;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  data,
  initialCapital,
  loading = false,
  className,
}) => {
  const chartData = useMemo(() => {
    return data.map((snapshot) => ({
      timestamp: snapshot.timestamp,
      value: snapshot.totalValue,
      return: ((snapshot.totalValue - initialCapital) / initialCapital) * 100,
      drawdown: snapshot.maxDrawdown * 100,
      formattedDate: format(new Date(snapshot.timestamp), 'MMM dd, HH:mm'),
    }));
  }, [data, initialCapital]);

  const currentValue = data[data.length - 1]?.totalValue || initialCapital;
  const totalReturn = ((currentValue - initialCapital) / initialCapital) * 100;
  const isPositive = totalReturn >= 0;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {data.formattedDate}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Portfolio Value: <span className="font-medium">${data.value.toLocaleString()}</span>
          </p>
          <p className={`text-sm ${data.return >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            Return: <span className="font-medium">{data.return.toFixed(2)}%</span>
          </p>
          {data.drawdown < 0 && (
            <p className="text-sm text-danger-600">
              Drawdown: <span className="font-medium">{data.drawdown.toFixed(2)}%</span>
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card
      title="Portfolio Performance"
      subtitle={`Current Value: $${currentValue.toLocaleString()} (${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%)`}
      loading={loading}
      className={className}
    >
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              className="stroke-gray-200 dark:stroke-gray-700" 
            />
            <XAxis
              dataKey="formattedDate"
              className="text-gray-600 dark:text-gray-400"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              className="text-gray-600 dark:text-gray-400"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Reference line for initial capital */}
            <ReferenceLine
              y={initialCapital}
              stroke="#6b7280"
              strokeDasharray="5 5"
              label={{ value: "Initial Capital", position: "insideTopRight" }}
            />
            
            <Line
              type="monotone"
              dataKey="value"
              stroke={isPositive ? "#22c55e" : "#ef4444"}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: isPositive ? "#22c55e" : "#ef4444" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Summary stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Initial</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            ${initialCapital.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Current</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            ${currentValue.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">P&L</p>
          <p className={`text-lg font-semibold ${isPositive ? 'text-success-600' : 'text-danger-600'}`}>
            {totalReturn >= 0 ? '+' : ''}${(currentValue - initialCapital).toLocaleString()}
          </p>
        </div>
      </div>
    </Card>
  );
};
