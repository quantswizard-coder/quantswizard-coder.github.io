"""Parameter optimization framework for trading strategies."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from itertools import product
import warnings
warnings.filterwarnings('ignore')

from ..backtesting.backtest_engine import BacktestEngine, BacktestConfig
from ..strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """Advanced parameter optimization for trading strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the parameter optimizer.
        
        Args:
            config: Optimization configuration
        """
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """Get default optimization configuration."""
        return {
            'optimization_method': 'grid_search',  # 'grid_search', 'random_search', 'bayesian'
            'scoring_metric': 'sharpe_ratio',      # Primary optimization metric
            'validation_method': 'walk_forward',   # 'walk_forward', 'time_series_split'
            'n_splits': 5,                         # Number of validation splits
            'min_trades_threshold': 10,            # Minimum trades required for valid result
            'max_iterations': 1000,                # Maximum optimization iterations
            'early_stopping': True,                # Stop if no improvement
            'early_stopping_rounds': 50,           # Rounds without improvement to stop
            'parallel_jobs': 1,                    # Number of parallel jobs (1 = sequential)
            'random_state': 42                     # Random seed for reproducibility
        }
    
    def optimize_strategy(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        parameter_space: Dict[str, List],
        backtest_config: Optional[BacktestConfig] = None
    ) -> Dict[str, Any]:
        """Optimize strategy parameters using specified method.
        
        Args:
            strategy_class: Strategy class to optimize
            data: Historical data for optimization
            parameter_space: Dictionary defining parameter ranges
            backtest_config: Backtesting configuration
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Starting parameter optimization for {strategy_class.__name__}")
        logger.info(f"Parameter space: {parameter_space}")
        
        # Set default backtest config if not provided
        if backtest_config is None:
            backtest_config = BacktestConfig(
                initial_capital=10000.0,
                commission_rate=0.001,
                slippage_rate=0.0005,
                max_positions=1
            )
        
        # Choose optimization method
        method = self.config.get('optimization_method', 'grid_search')
        
        if method == 'grid_search':
            return self._grid_search_optimization(
                strategy_class, data, parameter_space, backtest_config
            )
        elif method == 'random_search':
            return self._random_search_optimization(
                strategy_class, data, parameter_space, backtest_config
            )
        elif method == 'bayesian':
            return self._bayesian_optimization(
                strategy_class, data, parameter_space, backtest_config
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")
    
    def _grid_search_optimization(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        parameter_space: Dict[str, List],
        backtest_config: BacktestConfig
    ) -> Dict[str, Any]:
        """Perform grid search optimization."""
        
        # Generate all parameter combinations
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        param_combinations = list(product(*param_values))
        
        logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        results = []
        best_score = -np.inf
        best_params = None
        no_improvement_count = 0
        
        for i, param_combo in enumerate(param_combinations):
            # Create parameter dictionary
            params = dict(zip(param_names, param_combo))
            
            try:
                # Evaluate parameter combination
                score, metrics = self._evaluate_parameters(
                    strategy_class, data, params, backtest_config
                )
                
                # Store results
                result = {
                    'parameters': params.copy(),
                    'score': score,
                    'metrics': metrics,
                    'iteration': i
                }
                results.append(result)
                
                # Check for improvement
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    no_improvement_count = 0
                    logger.info(f"New best score: {score:.4f} with params: {params}")
                else:
                    no_improvement_count += 1
                
                # Early stopping
                if (self.config.get('early_stopping', True) and 
                    no_improvement_count >= self.config.get('early_stopping_rounds', 50)):
                    logger.info(f"Early stopping after {i+1} iterations")
                    break
                
                # Progress logging
                if (i + 1) % 50 == 0:
                    logger.info(f"Completed {i+1}/{len(param_combinations)} combinations")
                    
            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {e}")
                continue
        
        # Compile final results
        optimization_results = {
            'best_parameters': best_params,
            'best_score': best_score,
            'all_results': results,
            'total_combinations_tested': len(results),
            'optimization_method': 'grid_search',
            'scoring_metric': self.config.get('scoring_metric', 'sharpe_ratio')
        }
        
        logger.info(f"Optimization complete. Best score: {best_score:.4f}")
        logger.info(f"Best parameters: {best_params}")
        
        return optimization_results
    
    def _evaluate_parameters(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        params: Dict,
        backtest_config: BacktestConfig
    ) -> Tuple[float, Dict]:
        """Evaluate a single parameter combination using cross-validation.
        
        Args:
            strategy_class: Strategy class
            data: Historical data
            params: Parameters to test
            backtest_config: Backtesting configuration
            
        Returns:
            Tuple of (score, metrics_dict)
        """
        validation_method = self.config.get('validation_method', 'walk_forward')
        
        if validation_method == 'walk_forward':
            return self._walk_forward_validation(
                strategy_class, data, params, backtest_config
            )
        elif validation_method == 'time_series_split':
            return self._time_series_split_validation(
                strategy_class, data, params, backtest_config
            )
        else:
            raise ValueError(f"Unknown validation method: {validation_method}")
    
    def _walk_forward_validation(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        params: Dict,
        backtest_config: BacktestConfig
    ) -> Tuple[float, Dict]:
        """Perform walk-forward validation."""
        
        n_splits = self.config.get('n_splits', 5)
        scoring_metric = self.config.get('scoring_metric', 'sharpe_ratio')
        min_trades = self.config.get('min_trades_threshold', 10)
        
        # Calculate split points
        total_periods = len(data)
        test_size = total_periods // (n_splits + 1)
        
        scores = []
        all_metrics = []
        
        for i in range(n_splits):
            # Define train and test periods
            train_start = 0
            train_end = (i + 1) * test_size + test_size  # Expanding window
            test_start = train_end
            test_end = min(test_start + test_size, total_periods)
            
            if test_end <= test_start:
                continue
            
            # Split data
            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[test_start:test_end]
            
            if len(train_data) < 50 or len(test_data) < 20:  # Minimum data requirements
                continue
            
            try:
                # Create and test strategy
                strategy = strategy_class(params)
                engine = BacktestEngine(backtest_config)
                
                results = engine.run_backtest(
                    strategy=strategy,
                    data=test_data,
                    start_date=test_data.index[0],
                    end_date=test_data.index[-1]
                )
                
                # Check minimum trades requirement
                if results.total_trades < min_trades:
                    continue
                
                # Extract score
                if scoring_metric == 'sharpe_ratio':
                    score = results.sharpe_ratio
                elif scoring_metric == 'total_return':
                    score = results.total_return
                elif scoring_metric == 'calmar_ratio':
                    score = results.calmar_ratio
                elif scoring_metric == 'win_rate':
                    score = results.win_rate
                else:
                    score = results.sharpe_ratio  # Default
                
                # Handle invalid scores
                if np.isnan(score) or np.isinf(score):
                    continue
                
                scores.append(score)
                all_metrics.append({
                    'split': i,
                    'total_return': results.total_return,
                    'sharpe_ratio': results.sharpe_ratio,
                    'max_drawdown': results.max_drawdown,
                    'win_rate': results.win_rate,
                    'total_trades': results.total_trades
                })
                
            except Exception as e:
                logger.debug(f"Error in validation split {i}: {e}")
                continue
        
        if not scores:
            return -np.inf, {}
        
        # Calculate final score (mean across splits)
        final_score = np.mean(scores)
        
        # Compile metrics
        metrics = {
            'mean_score': final_score,
            'std_score': np.std(scores),
            'n_valid_splits': len(scores),
            'split_scores': scores,
            'split_metrics': all_metrics
        }
        
        return final_score, metrics
    
    def _time_series_split_validation(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        params: Dict,
        backtest_config: BacktestConfig
    ) -> Tuple[float, Dict]:
        """Perform time series split validation."""
        # Similar to walk-forward but with fixed window size
        # Implementation would be similar to walk_forward but with sliding window
        # For now, delegate to walk-forward
        return self._walk_forward_validation(strategy_class, data, params, backtest_config)
    
    def _random_search_optimization(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        parameter_space: Dict[str, List],
        backtest_config: BacktestConfig
    ) -> Dict[str, Any]:
        """Perform random search optimization."""
        max_iterations = self.config.get('max_iterations', 1000)
        
        results = []
        best_score = -np.inf
        best_params = None
        
        for i in range(max_iterations):
            # Randomly sample parameters
            params = {}
            for param_name, param_values in parameter_space.items():
                params[param_name] = np.random.choice(param_values)
            
            try:
                score, metrics = self._evaluate_parameters(
                    strategy_class, data, params, backtest_config
                )
                
                result = {
                    'parameters': params.copy(),
                    'score': score,
                    'metrics': metrics,
                    'iteration': i
                }
                results.append(result)
                
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    logger.info(f"New best score: {score:.4f} with params: {params}")
                
            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {e}")
                continue
        
        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'all_results': results,
            'total_combinations_tested': len(results),
            'optimization_method': 'random_search',
            'scoring_metric': self.config.get('scoring_metric', 'sharpe_ratio')
        }
    
    def _bayesian_optimization(
        self,
        strategy_class: type,
        data: pd.DataFrame,
        parameter_space: Dict[str, List],
        backtest_config: BacktestConfig
    ) -> Dict[str, Any]:
        """Perform Bayesian optimization (placeholder for future implementation)."""
        logger.warning("Bayesian optimization not yet implemented, falling back to grid search")
        return self._grid_search_optimization(strategy_class, data, parameter_space, backtest_config)
