// Core trading types
export interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  commission: number;
  slippage: number;
  strategy: string;
  reason: string;
  confidence: number;
  pnl?: number;
  metadata?: Record<string, any>;
}

export interface Position {
  symbol: string;
  quantity: number;
  avgEntryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  entryTimestamp: string;
  marketValue: number;
}

export interface PortfolioSnapshot {
  timestamp: string;
  totalValue: number;
  cash: number;
  positions: Position[];
  dailyReturn: number;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
}

export interface PerformanceMetrics {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgTradeReturn: number;
  bestTrade: number;
  worstTrade: number;
}

// Strategy configuration types
export interface BaseStrategyParams {
  name: string;
  description: string;
}

export interface EnsembleParams extends BaseStrategyParams {
  ensemble_method: 'confidence_weighted' | 'weighted_voting' | 'majority_voting';
  min_consensus: number;
  confidence_threshold: number;
  strategy_weights: {
    ma_crossover: number;
    rsi_mean_reversion: number;
    momentum: number;
  };
}

export interface MACrossoverParams extends BaseStrategyParams {
  fast_period: number;
  slow_period: number;
  ma_type: 'sma' | 'ema';
  min_crossover_strength: number;
  stop_loss_percent: number;
  take_profit_percent: number;
}

export interface RSIParams extends BaseStrategyParams {
  rsi_period: number;
  oversold_threshold: number;
  overbought_threshold: number;
  stop_loss_percent: number;
  take_profit_percent: number;
}

export interface MomentumParams extends BaseStrategyParams {
  lookback_period: number;
  momentum_threshold: number;
}

export type StrategyParams = EnsembleParams | MACrossoverParams | RSIParams | MomentumParams;

// Simulation configuration
export interface SimulationConfig {
  initial_capital: number;
  position_size: number;
  commission_rate: number;
  slippage_rate: number;
  max_positions: number;
  start_date?: string;
  end_date?: string;
  speed_multiplier: number;
}

// Market data
export interface CandlestickData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketData {
  symbol: string;
  data: CandlestickData[];
  current_price: number;
  price_change_24h: number;
  price_change_percent_24h: number;
}

// Simulation state
export interface SimulationState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  progress: number;
  current_date: string;
  portfolio: PortfolioSnapshot;
  trades: Trade[];
  performance: PerformanceMetrics;
  error_message?: string;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface StrategyOption {
  id: string;
  name: string;
  description: string;
  type: 'ensemble' | 'ma_crossover' | 'rsi' | 'momentum';
  default_params: StrategyParams;
}

// Theme and UI types
export interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
}

export interface TooltipInfo {
  title: string;
  description: string;
  formula?: string;
}

// Chart data types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

export interface TradeMarker {
  x: string | number;
  y: number;
  type: 'BUY' | 'SELL';
  trade: Trade;
}

// Export configuration
export interface ExportConfig {
  format: 'csv' | 'pdf';
  includeCharts: boolean;
  includeTrades: boolean;
  includeMetrics: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
}
