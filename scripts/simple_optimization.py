#!/usr/bin/env python3
"""Simplified strategy optimization with full dataset testing."""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.openbb_client import OpenBBDataClient
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy
from src.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from src.backtesting.backtest_engine import BacktestEngine, BacktestConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_crypto_data(symbol: str = "BTC-USD", days: int = 365) -> pd.DataFrame:
    """Load cryptocurrency data for optimization."""
    logger.info(f"Loading {symbol} data for {days} days...")
    
    client = OpenBBDataClient()
    
    data = client.get_crypto_data(
        symbol=symbol,
        provider="yfinance",
        start_date=datetime.now() - timedelta(days=days),
        end_date=datetime.now()
    )
    
    logger.info(f"Loaded {len(data)} records from {data.index[0]} to {data.index[-1]}")
    return data


def test_strategy_parameters(strategy_class, data: pd.DataFrame, params: dict) -> dict:
    """Test a single parameter combination on full dataset."""
    
    try:
        # Create strategy with parameters
        strategy = strategy_class(params)
        
        # Set up backtesting
        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            commission_rate=0.001,
            slippage_rate=0.0005,
            max_positions=1,
            position_sizing="fixed",
            position_size=0.95
        )
        
        engine = BacktestEngine(backtest_config)
        
        # Run backtest on full dataset
        results = engine.run_backtest(
            strategy=strategy,
            data=data,
            start_date=data.index[0],
            end_date=data.index[-1]
        )
        
        return {
            'parameters': params,
            'total_return': results.total_return,
            'annualized_return': results.annualized_return,
            'sharpe_ratio': results.sharpe_ratio,
            'max_drawdown': results.max_drawdown,
            'win_rate': results.win_rate,
            'total_trades': results.total_trades,
            'calmar_ratio': results.calmar_ratio,
            'valid': results.total_trades >= 5  # Minimum trades for valid result
        }
        
    except Exception as e:
        logger.warning(f"Error testing parameters {params}: {e}")
        return {
            'parameters': params,
            'error': str(e),
            'valid': False
        }


def optimize_ma_crossover_simple(data: pd.DataFrame) -> dict:
    """Simple MA Crossover optimization."""
    logger.info("🔄 Simple MA Crossover Optimization...")
    
    # Define parameter space
    parameter_combinations = [
        # Conservative combinations
        {'fast_period': 10, 'slow_period': 30, 'ma_type': 'sma', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'fast_period': 15, 'slow_period': 45, 'ma_type': 'sma', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'fast_period': 20, 'slow_period': 50, 'ma_type': 'sma', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        
        # EMA combinations
        {'fast_period': 12, 'slow_period': 26, 'ma_type': 'ema', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'fast_period': 20, 'slow_period': 50, 'ma_type': 'ema', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        
        # Different risk parameters
        {'fast_period': 20, 'slow_period': 50, 'ma_type': 'sma', 'stop_loss_percent': 0.03, 'take_profit_percent': 0.08},
        {'fast_period': 20, 'slow_period': 50, 'ma_type': 'sma', 'stop_loss_percent': 0.07, 'take_profit_percent': 0.15},
        
        # Longer periods
        {'fast_period': 30, 'slow_period': 100, 'ma_type': 'sma', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'fast_period': 50, 'slow_period': 200, 'ma_type': 'sma', 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
    ]
    
    results = []
    best_score = -np.inf
    best_params = None
    
    for i, params in enumerate(parameter_combinations):
        logger.info(f"Testing MA combination {i+1}/{len(parameter_combinations)}: {params}")
        
        result = test_strategy_parameters(MovingAverageCrossoverStrategy, data, params)
        results.append(result)
        
        if result.get('valid', False):
            score = result.get('sharpe_ratio', -np.inf)
            if score > best_score:
                best_score = score
                best_params = params.copy()
                logger.info(f"New best MA score: {score:.4f} with {result['total_trades']} trades")
    
    return {
        'strategy': 'MA_Crossover',
        'best_parameters': best_params,
        'best_score': best_score,
        'all_results': results,
        'valid_results': [r for r in results if r.get('valid', False)]
    }


def optimize_rsi_simple(data: pd.DataFrame) -> dict:
    """Simple RSI optimization."""
    logger.info("🔄 Simple RSI Optimization...")
    
    # Define parameter space
    parameter_combinations = [
        # Standard RSI configurations
        {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'rsi_period': 14, 'oversold_threshold': 25, 'overbought_threshold': 75, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'rsi_period': 14, 'oversold_threshold': 20, 'overbought_threshold': 80, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        
        # Different RSI periods
        {'rsi_period': 10, 'oversold_threshold': 30, 'overbought_threshold': 70, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        {'rsi_period': 21, 'oversold_threshold': 30, 'overbought_threshold': 70, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
        
        # Different risk parameters
        {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70, 'stop_loss_percent': 0.03, 'take_profit_percent': 0.08},
        {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70, 'stop_loss_percent': 0.07, 'take_profit_percent': 0.15},
        
        # More extreme thresholds
        {'rsi_period': 14, 'oversold_threshold': 15, 'overbought_threshold': 85, 'stop_loss_percent': 0.05, 'take_profit_percent': 0.10},
    ]
    
    results = []
    best_score = -np.inf
    best_params = None
    
    for i, params in enumerate(parameter_combinations):
        logger.info(f"Testing RSI combination {i+1}/{len(parameter_combinations)}: {params}")
        
        result = test_strategy_parameters(RSIMeanReversionStrategy, data, params)
        results.append(result)
        
        if result.get('valid', False):
            score = result.get('sharpe_ratio', -np.inf)
            if score > best_score:
                best_score = score
                best_params = params.copy()
                logger.info(f"New best RSI score: {score:.4f} with {result['total_trades']} trades")
    
    return {
        'strategy': 'RSI_Mean_Reversion',
        'best_parameters': best_params,
        'best_score': best_score,
        'all_results': results,
        'valid_results': [r for r in results if r.get('valid', False)]
    }


def save_results(results: dict, filename: str):
    """Save optimization results."""
    Path("optimization_results").mkdir(exist_ok=True)
    
    filepath = Path("optimization_results") / filename
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        else:
            return obj
    
    results_clean = convert_types(results)
    
    with open(filepath, 'w') as f:
        json.dump(results_clean, f, indent=2, default=str)
    
    logger.info(f"Results saved to: {filepath}")
    return filepath


def display_results(results: dict):
    """Display optimization results in a nice format."""
    strategy = results['strategy']
    best_params = results['best_parameters']
    best_score = results['best_score']
    valid_results = results['valid_results']
    
    logger.info(f"\n📊 {strategy} Optimization Results:")
    logger.info(f"   Best Sharpe Ratio: {best_score:.4f}")
    logger.info(f"   Best Parameters: {best_params}")
    
    if valid_results:
        logger.info(f"   Valid Results: {len(valid_results)}/{len(results['all_results'])}")
        
        # Find best result details
        best_result = None
        for result in valid_results:
            if result.get('sharpe_ratio', -np.inf) == best_score:
                best_result = result
                break
        
        if best_result:
            logger.info(f"   Best Result Details:")
            logger.info(f"      Total Return: {best_result.get('total_return', 0):.2%}")
            logger.info(f"      Annualized Return: {best_result.get('annualized_return', 0):.2%}")
            logger.info(f"      Max Drawdown: {best_result.get('max_drawdown', 0):.2%}")
            logger.info(f"      Win Rate: {best_result.get('win_rate', 0):.2%}")
            logger.info(f"      Total Trades: {best_result.get('total_trades', 0)}")
            logger.info(f"      Calmar Ratio: {best_result.get('calmar_ratio', 0):.4f}")
    else:
        logger.warning(f"   No valid results found for {strategy}")


def main():
    """Main optimization runner."""
    logger.info("🚀 Simple Strategy Optimization")
    logger.info("=" * 60)
    
    # Load data (1 year for better signal generation)
    data = load_crypto_data("BTC-USD", days=365)
    
    # Optimize MA Crossover
    logger.info("\n" + "=" * 60)
    ma_results = optimize_ma_crossover_simple(data)
    display_results(ma_results)
    
    # Save MA results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ma_file = save_results(ma_results, f"MA_Crossover_simple_{timestamp}.json")
    
    # Optimize RSI
    logger.info("\n" + "=" * 60)
    rsi_results = optimize_rsi_simple(data)
    display_results(rsi_results)
    
    # Save RSI results
    rsi_file = save_results(rsi_results, f"RSI_simple_{timestamp}.json")
    
    # Compare strategies
    logger.info("\n" + "=" * 60)
    logger.info("🏆 STRATEGY COMPARISON:")
    
    ma_score = ma_results.get('best_score', -np.inf)
    rsi_score = rsi_results.get('best_score', -np.inf)
    
    if ma_score > rsi_score and ma_score > 0:
        logger.info(f"   Winner: MA Crossover (Sharpe: {ma_score:.4f})")
        logger.info(f"   Best Parameters: {ma_results['best_parameters']}")
    elif rsi_score > ma_score and rsi_score > 0:
        logger.info(f"   Winner: RSI Mean Reversion (Sharpe: {rsi_score:.4f})")
        logger.info(f"   Best Parameters: {rsi_results['best_parameters']}")
    else:
        logger.info("   No clear winner - both strategies need improvement")
    
    logger.info(f"\n📁 Results saved to:")
    logger.info(f"   {ma_file}")
    logger.info(f"   {rsi_file}")
    
    logger.info(f"\n🎯 Next Steps:")
    logger.info("   1. Review best performing parameters")
    logger.info("   2. Test on out-of-sample data")
    logger.info("   3. Implement ensemble strategy")
    logger.info("   4. Add more sophisticated risk management")


if __name__ == "__main__":
    main()
