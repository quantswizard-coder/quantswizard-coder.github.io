#!/usr/bin/env python3
"""Strategy parameter optimization runner."""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.openbb_client import OpenBBDataClient
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy
from src.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from src.optimization.parameter_optimizer import ParameterOptimizer
from src.optimization.strategy_configs import StrategyOptimizationConfigs
from src.backtesting.backtest_engine import BacktestConfig

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


def optimize_ma_crossover_strategy(data: pd.DataFrame, quick_mode: bool = False) -> dict:
    """Optimize Moving Average Crossover strategy."""
    logger.info("🔄 Optimizing MA Crossover Strategy...")
    
    # Get optimization configuration
    if quick_mode:
        config = StrategyOptimizationConfigs.get_quick_optimization_config()
    else:
        config = StrategyOptimizationConfigs.get_ma_crossover_config()
    
    # Filter parameter space with constraints
    parameter_space = config['parameter_space']
    constraints = config.get('constraints', [])
    
    if constraints:
        logger.info("Applying parameter constraints...")
        valid_combinations = StrategyOptimizationConfigs.filter_parameter_space(
            parameter_space, constraints
        )
        logger.info(f"Valid parameter combinations: {len(valid_combinations)}")
        
        # Convert back to parameter space format for optimizer
        if valid_combinations:
            # Use first 100 combinations to avoid excessive computation
            limited_combinations = valid_combinations[:100] if len(valid_combinations) > 100 else valid_combinations
            
            # Reconstruct parameter space from valid combinations
            filtered_space = {}
            for param_name in parameter_space.keys():
                unique_values = list(set(combo[param_name] for combo in limited_combinations))
                filtered_space[param_name] = unique_values
            
            parameter_space = filtered_space
    
    # Set up optimizer
    optimizer_config = config.get('optimization_config', {})
    optimizer = ParameterOptimizer(optimizer_config)
    
    # Set up backtesting configuration
    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        commission_rate=0.001,
        slippage_rate=0.0005,
        max_positions=1,
        position_sizing="fixed",
        position_size=0.95
    )
    
    # Run optimization
    results = optimizer.optimize_strategy(
        strategy_class=MovingAverageCrossoverStrategy,
        data=data,
        parameter_space=parameter_space,
        backtest_config=backtest_config
    )
    
    return results


def optimize_rsi_strategy(data: pd.DataFrame, quick_mode: bool = False) -> dict:
    """Optimize RSI Mean Reversion strategy."""
    logger.info("🔄 Optimizing RSI Mean Reversion Strategy...")
    
    # Get optimization configuration
    if quick_mode:
        # Create a quick RSI config
        config = {
            'parameter_space': {
                'rsi_period': [14, 21],
                'oversold_threshold': [25, 30, 35],
                'overbought_threshold': [65, 70, 75],
                'stop_loss_percent': [0.03, 0.05],
                'take_profit_percent': [0.10, 0.15]
            },
            'constraints': [
                lambda params: params['oversold_threshold'] < params['overbought_threshold'],
                lambda params: params['overbought_threshold'] - params['oversold_threshold'] >= 20,
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 3,
                'min_trades_threshold': 5,
                'early_stopping': True,
                'early_stopping_rounds': 20
            }
        }
    else:
        config = StrategyOptimizationConfigs.get_rsi_strategy_config()
    
    # Filter parameter space with constraints
    parameter_space = config['parameter_space']
    constraints = config.get('constraints', [])
    
    if constraints:
        logger.info("Applying parameter constraints...")
        valid_combinations = StrategyOptimizationConfigs.filter_parameter_space(
            parameter_space, constraints
        )
        logger.info(f"Valid parameter combinations: {len(valid_combinations)}")
        
        # Convert back to parameter space format for optimizer
        if valid_combinations:
            # Use first 50 combinations for RSI to avoid excessive computation
            limited_combinations = valid_combinations[:50] if len(valid_combinations) > 50 else valid_combinations
            
            # Reconstruct parameter space from valid combinations
            filtered_space = {}
            for param_name in parameter_space.keys():
                unique_values = list(set(combo[param_name] for combo in limited_combinations))
                filtered_space[param_name] = unique_values
            
            parameter_space = filtered_space
    
    # Set up optimizer
    optimizer_config = config.get('optimization_config', {})
    optimizer = ParameterOptimizer(optimizer_config)
    
    # Set up backtesting configuration
    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        commission_rate=0.001,
        slippage_rate=0.0005,
        max_positions=1,
        position_sizing="fixed",
        position_size=0.95
    )
    
    # Run optimization
    results = optimizer.optimize_strategy(
        strategy_class=RSIMeanReversionStrategy,
        data=data,
        parameter_space=parameter_space,
        backtest_config=backtest_config
    )
    
    return results


def save_optimization_results(results: dict, strategy_name: str, output_dir: str = "optimization_results"):
    """Save optimization results to file."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{strategy_name}_optimization_{timestamp}.json"
    filepath = Path(output_dir) / filename
    
    # Prepare results for JSON serialization
    json_results = {
        'strategy_name': strategy_name,
        'optimization_timestamp': timestamp,
        'best_parameters': results.get('best_parameters'),
        'best_score': results.get('best_score'),
        'total_combinations_tested': results.get('total_combinations_tested'),
        'optimization_method': results.get('optimization_method'),
        'scoring_metric': results.get('scoring_metric')
    }
    
    # Add summary statistics from all results
    all_results = results.get('all_results', [])
    if all_results:
        scores = [r['score'] for r in all_results if not pd.isna(r['score']) and r['score'] != -float('inf')]
        if scores:
            json_results['score_statistics'] = {
                'mean': float(pd.Series(scores).mean()),
                'std': float(pd.Series(scores).std()),
                'min': float(min(scores)),
                'max': float(max(scores)),
                'median': float(pd.Series(scores).median())
            }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    logger.info(f"Optimization results saved to: {filepath}")
    return filepath


def main():
    """Main optimization runner."""
    logger.info("🚀 Starting Strategy Parameter Optimization")
    logger.info("=" * 60)
    
    # Configuration
    QUICK_MODE = True  # Set to False for full optimization
    SYMBOL = "BTC-USD"
    DAYS = 180  # 6 months of data
    
    try:
        # Load data
        data = load_crypto_data(SYMBOL, DAYS)
        
        # Optimize MA Crossover Strategy
        logger.info("\n" + "=" * 60)
        ma_results = optimize_ma_crossover_strategy(data, quick_mode=QUICK_MODE)
        
        logger.info("📊 MA Crossover Optimization Results:")
        logger.info(f"   Best Score: {ma_results.get('best_score', 'N/A'):.4f}")
        logger.info(f"   Best Parameters: {ma_results.get('best_parameters', 'N/A')}")
        logger.info(f"   Combinations Tested: {ma_results.get('total_combinations_tested', 'N/A')}")
        
        # Save MA results
        ma_filepath = save_optimization_results(ma_results, "MA_Crossover")
        
        # Optimize RSI Strategy
        logger.info("\n" + "=" * 60)
        rsi_results = optimize_rsi_strategy(data, quick_mode=QUICK_MODE)
        
        logger.info("📊 RSI Mean Reversion Optimization Results:")
        logger.info(f"   Best Score: {rsi_results.get('best_score', 'N/A'):.4f}")
        logger.info(f"   Best Parameters: {rsi_results.get('best_parameters', 'N/A')}")
        logger.info(f"   Combinations Tested: {rsi_results.get('total_combinations_tested', 'N/A')}")
        
        # Save RSI results
        rsi_filepath = save_optimization_results(rsi_results, "RSI_Mean_Reversion")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ OPTIMIZATION COMPLETE")
        logger.info(f"📁 Results saved to:")
        logger.info(f"   MA Crossover: {ma_filepath}")
        logger.info(f"   RSI Strategy: {rsi_filepath}")
        
        # Compare strategies
        ma_score = ma_results.get('best_score', -float('inf'))
        rsi_score = rsi_results.get('best_score', -float('inf'))
        
        if ma_score > rsi_score:
            logger.info(f"🏆 Best Strategy: MA Crossover (Score: {ma_score:.4f})")
        elif rsi_score > ma_score:
            logger.info(f"🏆 Best Strategy: RSI Mean Reversion (Score: {rsi_score:.4f})")
        else:
            logger.info("🤝 Both strategies performed equally")
        
        logger.info("\n🎯 Next Steps:")
        logger.info("   1. Review optimization results")
        logger.info("   2. Test optimized parameters on out-of-sample data")
        logger.info("   3. Implement ensemble strategy combining best parameters")
        logger.info("   4. Set up real-time signal generation")
        
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
