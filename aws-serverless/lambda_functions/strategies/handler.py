"""
Strategies Lambda function for Trading Simulator API
"""
import json
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Handle strategy-related API requests
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        path_parameters = event.get('pathParameters') or {}
        
        if http_method == 'GET' and path == '/api/strategies':
            return get_strategies()
        elif http_method == 'GET' and 'strategyId' in path_parameters:
            return get_strategy_defaults(path_parameters['strategyId'])
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    "success": False,
                    "error": "Endpoint not found"
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


def get_strategies():
    """
    Get available trading strategies
    """
    strategies = [
        {
            "id": "ma_crossover",
            "name": "Moving Average Crossover",
            "description": "Classic trend-following strategy using moving average crossovers",
            "category": "Trend Following",
            "risk_level": "Medium",
            "parameters": {
                "fast_period": {"type": "int", "default": 10, "min": 5, "max": 50},
                "slow_period": {"type": "int", "default": 20, "min": 10, "max": 200}
            }
        },
        {
            "id": "rsi_mean_reversion",
            "name": "RSI Mean Reversion",
            "description": "Contrarian strategy based on RSI overbought/oversold levels",
            "category": "Mean Reversion",
            "risk_level": "Medium",
            "parameters": {
                "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30},
                "oversold_threshold": {"type": "float", "default": 30.0, "min": 10.0, "max": 40.0},
                "overbought_threshold": {"type": "float", "default": 70.0, "min": 60.0, "max": 90.0}
            }
        },
        {
            "id": "momentum",
            "name": "Momentum Strategy",
            "description": "Trend-following strategy based on price momentum",
            "category": "Momentum",
            "risk_level": "High",
            "parameters": {
                "lookback_period": {"type": "int", "default": 20, "min": 5, "max": 100},
                "momentum_threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.1}
            }
        },
        {
            "id": "balanced_ensemble",
            "name": "Balanced Ensemble",
            "description": "Combines multiple strategies with equal weighting",
            "category": "Ensemble",
            "risk_level": "Medium",
            "parameters": {
                "ensemble_method": {"type": "str", "default": "equal_weight", "options": ["equal_weight", "confidence_weighted"]},
                "min_consensus": {"type": "float", "default": 0.5, "min": 0.3, "max": 0.8},
                "strategy_weights": {
                    "ma_crossover": {"type": "float", "default": 0.33, "min": 0.0, "max": 1.0},
                    "rsi_mean_reversion": {"type": "float", "default": 0.33, "min": 0.0, "max": 1.0},
                    "momentum": {"type": "float", "default": 0.34, "min": 0.0, "max": 1.0}
                }
            }
        },
        {
            "id": "confidence_weighted_ensemble",
            "name": "Confidence Weighted Ensemble",
            "description": "Ensemble strategy with confidence-based weighting",
            "category": "Ensemble",
            "risk_level": "Medium",
            "parameters": {
                "ensemble_method": {"type": "str", "default": "confidence_weighted", "options": ["confidence_weighted", "adaptive"]},
                "confidence_threshold": {"type": "float", "default": 0.3, "min": 0.1, "max": 0.7},
                "min_consensus": {"type": "float", "default": 0.4, "min": 0.2, "max": 0.8}
            }
        },
        {
            "id": "adaptive_ensemble",
            "name": "Adaptive Ensemble",
            "description": "Dynamic ensemble that adapts to market conditions",
            "category": "Ensemble",
            "risk_level": "Medium-High",
            "parameters": {
                "ensemble_method": {"type": "str", "default": "adaptive", "options": ["adaptive", "market_regime"]},
                "adaptation_period": {"type": "int", "default": 50, "min": 20, "max": 200},
                "volatility_threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.05}
            }
        }
    ]
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            "success": True,
            "data": strategies,
            "timestamp": datetime.utcnow().isoformat()
        })
    }


def get_strategy_defaults(strategy_id):
    """
    Get default parameters for a specific strategy
    """
    # Get strategies and find the requested one
    strategies_response = get_strategies()
    strategies_data = json.loads(strategies_response['body'])
    
    strategy = next((s for s in strategies_data['data'] if s['id'] == strategy_id), None)
    
    if not strategy:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": f"Strategy '{strategy_id}' not found"
            })
        }
    
    # Extract default values from parameters
    defaults = {}
    for param_name, param_config in strategy['parameters'].items():
        if isinstance(param_config, dict) and 'default' in param_config:
            defaults[param_name] = param_config['default']
        elif isinstance(param_config, dict):
            # Handle nested parameters (like strategy_weights)
            nested_defaults = {}
            for nested_name, nested_config in param_config.items():
                if isinstance(nested_config, dict) and 'default' in nested_config:
                    nested_defaults[nested_name] = nested_config['default']
            if nested_defaults:
                defaults[param_name] = nested_defaults
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            "success": True,
            "data": {
                "strategy_id": strategy_id,
                "name": strategy['name'],
                "defaults": defaults
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    }


def get_cors_headers():
    """
    Get CORS headers for responses
    """
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': os.getenv('CORS_ORIGINS', '*'),
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
