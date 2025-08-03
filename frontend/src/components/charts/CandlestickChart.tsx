import React, { useMemo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { format } from 'date-fns';
import { CandlestickData, Trade } from '../../types';
import { Card } from '../ui/Card';

interface CandlestickChartProps {
  data: CandlestickData[];
  trades?: Trade[];
  loading?: boolean;
  className?: string;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  trades = [],
  loading = false,
  className,
}) => {
  const chartData = useMemo(() => {
    return data.map((candle, index) => {
      const timestamp = candle.timestamp;
      const tradesAtTime = trades.filter(trade => 
        Math.abs(new Date(trade.timestamp).getTime() - new Date(timestamp).getTime()) < 60000 // Within 1 minute
      );

      return {
        timestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
        // Candlestick body (for visualization)
        bodyLow: Math.min(candle.open, candle.close),
        bodyHigh: Math.max(candle.open, candle.close),
        isGreen: candle.close >= candle.open,
        // Trade markers
        buyTrades: tradesAtTime.filter(t => t.side === 'BUY'),
        sellTrades: tradesAtTime.filter(t => t.side === 'SELL'),
        formattedDate: format(new Date(timestamp), 'MMM dd, HH:mm'),
      };
    });
  }, [data, trades]);

  const currentPrice = data[data.length - 1]?.close || 0;
  const priceChange = data.length > 1 ? currentPrice - data[data.length - 2].close : 0;
  const priceChangePercent = data.length > 1 ? (priceChange / data[data.length - 2].close) * 100 : 0;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            {data.formattedDate}
          </p>
          <div className="space-y-1 text-xs">
            <p>Open: <span className="font-medium">${data.open.toFixed(2)}</span></p>
            <p>High: <span className="font-medium text-success-600">${data.high.toFixed(2)}</span></p>
            <p>Low: <span className="font-medium text-danger-600">${data.low.toFixed(2)}</span></p>
            <p>Close: <span className="font-medium">${data.close.toFixed(2)}</span></p>
            <p>Volume: <span className="font-medium">{data.volume.toLocaleString()}</span></p>
          </div>
          
          {(data.buyTrades.length > 0 || data.sellTrades.length > 0) && (
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs font-medium text-gray-900 dark:text-white">Trades:</p>
              {data.buyTrades.map((trade: Trade, i: number) => (
                <p key={i} className="text-xs text-success-600">
                  BUY {trade.quantity.toFixed(4)} @ ${trade.price.toFixed(2)}
                </p>
              ))}
              {data.sellTrades.map((trade: Trade, i: number) => (
                <p key={i} className="text-xs text-danger-600">
                  SELL {trade.quantity.toFixed(4)} @ ${trade.price.toFixed(2)}
                </p>
              ))}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Custom candlestick shape
  const CandlestickBar = (props: any) => {
    const { payload, x, y, width, height } = props;
    if (!payload) return null;

    const { open, high, low, close, isGreen } = payload;
    const color = isGreen ? '#22c55e' : '#ef4444';
    const bodyHeight = Math.abs(close - open) * (height / (payload.high - payload.low));
    const bodyY = y + (payload.high - Math.max(open, close)) * (height / (payload.high - payload.low));

    return (
      <g>
        {/* Wick */}
        <line
          x1={x + width / 2}
          y1={y}
          x2={x + width / 2}
          y2={y + height}
          stroke={color}
          strokeWidth={1}
        />
        {/* Body */}
        <rect
          x={x + width * 0.2}
          y={bodyY}
          width={width * 0.6}
          height={bodyHeight || 1}
          fill={color}
          stroke={color}
        />
      </g>
    );
  };

  return (
    <Card
      title="Price Chart"
      subtitle={`$${currentPrice.toFixed(2)} (${priceChangePercent >= 0 ? '+' : ''}${priceChangePercent.toFixed(2)}%)`}
      loading={loading}
      className={className}
    >
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
              domain={['dataMin - 100', 'dataMax + 100']}
              className="text-gray-600 dark:text-gray-400"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Candlestick bars */}
            <Bar
              dataKey="high"
              shape={<CandlestickBar />}
              isAnimationActive={false}
            />
            
            {/* Trade markers */}
            {chartData.map((point, index) => (
              <g key={index}>
                {point.buyTrades.map((trade: Trade, i: number) => (
                  <ReferenceDot
                    key={`buy-${index}-${i}`}
                    x={point.timestamp}
                    y={trade.price}
                    r={4}
                    fill="#22c55e"
                    stroke="#ffffff"
                    strokeWidth={2}
                  />
                ))}
                {point.sellTrades.map((trade: Trade, i: number) => (
                  <ReferenceDot
                    key={`sell-${index}-${i}`}
                    x={point.timestamp}
                    y={trade.price}
                    r={4}
                    fill="#ef4444"
                    stroke="#ffffff"
                    strokeWidth={2}
                  />
                ))}
              </g>
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-success-500 rounded-full"></div>
          <span className="text-gray-600 dark:text-gray-400">Buy Orders</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-danger-500 rounded-full"></div>
          <span className="text-gray-600 dark:text-gray-400">Sell Orders</span>
        </div>
      </div>
    </Card>
  );
};
