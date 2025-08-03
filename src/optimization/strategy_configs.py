"""Strategy-specific optimization configurations and parameter spaces."""

import numpy as np
from typing import Dict, List, Any


class StrategyOptimizationConfigs:
    """Predefined optimization configurations for different strategies."""
    
    @staticmethod
    def get_ma_crossover_config() -> Dict[str, Any]:
        """Get optimization configuration for Moving Average Crossover strategy."""
        return {
            'parameter_space': {
                'fast_period': [5, 10, 15, 20, 25, 30],
                'slow_period': [30, 40, 50, 60, 70, 80, 100, 120, 150, 200],
                'ma_type': ['sma', 'ema'],
                'min_crossover_strength': [0.005, 0.01, 0.015, 0.02, 0.025],
                'stop_loss_percent': [0.02, 0.03, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.05, 0.08, 0.10, 0.15, 0.20]
            },
            'constraints': [
                # Fast period must be less than slow period
                lambda params: params['fast_period'] < params['slow_period'],
                # Minimum gap between fast and slow periods
                lambda params: params['slow_period'] - params['fast_period'] >= 10,
                # Take profit should be larger than stop loss
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 5,
                'min_trades_threshold': 15,
                'early_stopping': True,
                'early_stopping_rounds': 100
            }
        }
    
    @staticmethod
    def get_rsi_strategy_config() -> Dict[str, Any]:
        """Get optimization configuration for RSI Mean Reversion strategy."""
        return {
            'parameter_space': {
                'rsi_period': [7, 10, 14, 18, 21, 25, 30],
                'oversold_threshold': [15, 20, 25, 30, 35],
                'overbought_threshold': [65, 70, 75, 80, 85],
                'extreme_oversold': [10, 15, 20],
                'extreme_overbought': [80, 85, 90],
                'stop_loss_percent': [0.02, 0.03, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.05, 0.08, 0.10, 0.15, 0.20]
            },
            'constraints': [
                # Oversold must be less than overbought
                lambda params: params['oversold_threshold'] < params['overbought_threshold'],
                # Extreme levels must be more extreme than regular levels
                lambda params: params['extreme_oversold'] < params['oversold_threshold'],
                lambda params: params['extreme_overbought'] > params['overbought_threshold'],
                # Reasonable gap between oversold and overbought
                lambda params: params['overbought_threshold'] - params['oversold_threshold'] >= 20,
                # Take profit should be larger than stop loss
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 5,
                'min_trades_threshold': 10,
                'early_stopping': True,
                'early_stopping_rounds': 100
            }
        }
    
    @staticmethod
    def get_macd_strategy_config() -> Dict[str, Any]:
        """Get optimization configuration for MACD strategy."""
        return {
            'parameter_space': {
                'fast_period': [8, 10, 12, 15, 18],
                'slow_period': [21, 24, 26, 30, 35],
                'signal_period': [6, 8, 9, 12, 15],
                'min_histogram_threshold': [0.0, 0.1, 0.2, 0.5],
                'stop_loss_percent': [0.02, 0.03, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.05, 0.08, 0.10, 0.15, 0.20]
            },
            'constraints': [
                # Fast period must be less than slow period
                lambda params: params['fast_period'] < params['slow_period'],
                # Signal period should be reasonable relative to fast period
                lambda params: params['signal_period'] <= params['fast_period'] + 5,
                # Take profit should be larger than stop loss
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 5,
                'min_trades_threshold': 12,
                'early_stopping': True,
                'early_stopping_rounds': 80
            }
        }
    
    @staticmethod
    def get_bollinger_bands_config() -> Dict[str, Any]:
        """Get optimization configuration for Bollinger Bands strategy."""
        return {
            'parameter_space': {
                'period': [15, 20, 25, 30],
                'std_dev': [1.5, 2.0, 2.5, 3.0],
                'entry_threshold': [0.0, 0.1, 0.2, 0.3],  # How close to bands to trigger
                'exit_threshold': [0.3, 0.5, 0.7, 1.0],   # How far from bands to exit
                'stop_loss_percent': [0.02, 0.03, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.05, 0.08, 0.10, 0.15, 0.20]
            },
            'constraints': [
                # Exit threshold should be greater than entry threshold
                lambda params: params['exit_threshold'] > params['entry_threshold'],
                # Take profit should be larger than stop loss
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 5,
                'min_trades_threshold': 10,
                'early_stopping': True,
                'early_stopping_rounds': 80
            }
        }
    
    @staticmethod
    def get_multi_timeframe_config() -> Dict[str, Any]:
        """Get optimization configuration for multi-timeframe strategies."""
        return {
            'parameter_space': {
                'short_timeframe_weight': [0.3, 0.4, 0.5, 0.6, 0.7],
                'medium_timeframe_weight': [0.2, 0.3, 0.4, 0.5],
                'long_timeframe_weight': [0.1, 0.2, 0.3, 0.4],
                'consensus_threshold': [0.5, 0.6, 0.7, 0.8],
                'stop_loss_percent': [0.03, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.08, 0.10, 0.15, 0.20]
            },
            'constraints': [
                # Weights should sum to approximately 1.0
                lambda params: abs(
                    params['short_timeframe_weight'] + 
                    params['medium_timeframe_weight'] + 
                    params['long_timeframe_weight'] - 1.0
                ) < 0.1,
                # Take profit should be larger than stop loss
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 4,
                'min_trades_threshold': 8,
                'early_stopping': True,
                'early_stopping_rounds': 60
            }
        }
    
    @staticmethod
    def get_quick_optimization_config() -> Dict[str, Any]:
        """Get a quick optimization configuration for testing."""
        return {
            'parameter_space': {
                'fast_period': [10, 20, 30],
                'slow_period': [40, 50, 60],
                'ma_type': ['sma'],
                'stop_loss_percent': [0.03, 0.05],
                'take_profit_percent': [0.10, 0.15]
            },
            'constraints': [
                lambda params: params['fast_period'] < params['slow_period'],
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
    
    @staticmethod
    def get_robust_optimization_config() -> Dict[str, Any]:
        """Get a robust optimization configuration with extensive parameter space."""
        return {
            'parameter_space': {
                'fast_period': list(range(5, 31, 2)),  # 5, 7, 9, ..., 29
                'slow_period': list(range(30, 201, 10)),  # 30, 40, 50, ..., 200
                'ma_type': ['sma', 'ema'],
                'min_crossover_strength': [0.005, 0.01, 0.015, 0.02, 0.025, 0.03],
                'stop_loss_percent': [0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10],
                'take_profit_percent': [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25]
            },
            'constraints': [
                lambda params: params['fast_period'] < params['slow_period'],
                lambda params: params['slow_period'] - params['fast_period'] >= 15,
                lambda params: params['take_profit_percent'] > params['stop_loss_percent']
            ],
            'optimization_config': {
                'scoring_metric': 'sharpe_ratio',
                'validation_method': 'walk_forward',
                'n_splits': 6,
                'min_trades_threshold': 20,
                'early_stopping': True,
                'early_stopping_rounds': 200,
                'max_iterations': 5000
            }
        }
    
    @staticmethod
    def apply_constraints(params: Dict[str, Any], constraints: List[callable]) -> bool:
        """Apply parameter constraints to validate a parameter combination.
        
        Args:
            params: Parameter dictionary to validate
            constraints: List of constraint functions
            
        Returns:
            True if all constraints are satisfied, False otherwise
        """
        try:
            for constraint in constraints:
                if not constraint(params):
                    return False
            return True
        except Exception:
            return False
    
    @staticmethod
    def filter_parameter_space(
        parameter_space: Dict[str, List], 
        constraints: List[callable]
    ) -> List[Dict[str, Any]]:
        """Filter parameter space to only include valid combinations.
        
        Args:
            parameter_space: Dictionary defining parameter ranges
            constraints: List of constraint functions
            
        Returns:
            List of valid parameter combinations
        """
        from itertools import product
        
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        param_combinations = list(product(*param_values))
        
        valid_combinations = []
        for param_combo in param_combinations:
            params = dict(zip(param_names, param_combo))
            if StrategyOptimizationConfigs.apply_constraints(params, constraints):
                valid_combinations.append(params)
        
        return valid_combinations
