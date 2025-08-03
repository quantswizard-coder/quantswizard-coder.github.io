#!/usr/bin/env python3
"""
FastAPI server for the Trading Simulator frontend.
Provides REST API endpoints and WebSocket connections for real-time simulation data.
"""

import sys
import os
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Production Configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Configure logging for production
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if ENVIRONMENT == 'development'
           else '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Import our trading system components
try:
    from src.strategies.ensemble_strategy import EnsembleStrategy
    from src.strategies.ma_crossover import MovingAverageCrossoverStrategy
    from src.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
    from src.strategies.momentum import SimpleMomentumStrategy
    from src.simulation.simulation_engine import SimulationEngine, SimulationConfig
    from src.data.openbb_client import OpenBBDataClient
except ImportError as e:
    print(f"Warning: Could not import trading system components: {e}")
    print("API will run with mock data only")
    EnsembleStrategy = None
    MovingAverageCrossoverStrategy = None
    RSIMeanReversionStrategy = None
    SimpleMomentumStrategy = None
    SimulationEngine = None
    SimulationConfig = None
    OpenBBDataClient = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Trading Simulator API",
    description="Professional cryptocurrency trading strategy backtesting API",
    version="1.0.0"
)

# CORS middleware - Production ready
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global state
simulations: Dict[str, Dict[str, Any]] = {}
data_loader = OpenBBDataClient() if OpenBBDataClient else None

# Pydantic models
class StrategyParams(BaseModel):
    name: str
    description: str

class EnsembleParams(StrategyParams):
    ensemble_method: str
    min_consensus: float
    confidence_threshold: float
    strategy_weights: Dict[str, float]

class MACrossoverParams(StrategyParams):
    fast_period: int
    slow_period: int
    ma_type: str
    min_crossover_strength: float
    stop_loss_percent: float
    take_profit_percent: float

class RSIParams(StrategyParams):
    rsi_period: int
    oversold_threshold: int
    overbought_threshold: int
    stop_loss_percent: float
    take_profit_percent: float

class MomentumParams(StrategyParams):
    lookback_period: int
    momentum_threshold: float

class SimulationConfigModel(BaseModel):
    initial_capital: float
    position_size: float
    commission_rate: float
    slippage_rate: float
    max_positions: int
    speed_multiplier: int

class CreateSimulationRequest(BaseModel):
    strategy_id: str
    strategy_params: Dict[str, Any]
    config: SimulationConfigModel

# Strategy definitions
AVAILABLE_STRATEGIES = {
    "balanced_ensemble": {
        "id": "balanced_ensemble",
        "name": "Balanced Ensemble (CHAMPION 🏆)",
        "description": "Combines MA Crossover, RSI Mean Reversion, and Momentum strategies with confidence weighting",
        "type": "ensemble",
        "default_params": {
            "name": "Balanced Ensemble",
            "description": "Confidence-weighted ensemble strategy",
            "ensemble_method": "confidence_weighted",
            "min_consensus": 0.4,
            "confidence_threshold": 0.3,
            "strategy_weights": {
                "ma_crossover": 0.33,
                "rsi_mean_reversion": 0.33,
                "momentum": 0.34
            }
        }
    },
    "conservative_ensemble": {
        "id": "conservative_ensemble",
        "name": "Conservative Ensemble",
        "description": "High consensus ensemble with strict confidence requirements",
        "type": "ensemble",
        "default_params": {
            "name": "Conservative Ensemble",
            "description": "Conservative weighted voting ensemble",
            "ensemble_method": "weighted_voting",
            "min_consensus": 0.6,
            "confidence_threshold": 0.5,
            "strategy_weights": {
                "ma_crossover": 0.33,
                "rsi_mean_reversion": 0.33,
                "momentum": 0.34
            }
        }
    },
    "aggressive_ensemble": {
        "id": "aggressive_ensemble",
        "name": "Aggressive Ensemble",
        "description": "Low consensus ensemble for more frequent trading",
        "type": "ensemble",
        "default_params": {
            "name": "Aggressive Ensemble",
            "description": "Aggressive weighted voting ensemble",
            "ensemble_method": "weighted_voting",
            "min_consensus": 0.3,
            "confidence_threshold": 0.25,
            "strategy_weights": {
                "ma_crossover": 0.33,
                "rsi_mean_reversion": 0.33,
                "momentum": 0.34
            }
        }
    },
    "ma_crossover": {
        "id": "ma_crossover",
        "name": "MA Crossover Only",
        "description": "Moving Average crossover strategy with trend following",
        "type": "ma_crossover",
        "default_params": {
            "name": "MA Crossover",
            "description": "Moving average crossover strategy",
            "fast_period": 10,
            "slow_period": 30,
            "ma_type": "sma",
            "min_crossover_strength": 0.0,
            "stop_loss_percent": 0.03,
            "take_profit_percent": 0.08
        }
    },
    "rsi_mean_reversion": {
        "id": "rsi_mean_reversion",
        "name": "RSI Mean Reversion Only",
        "description": "RSI-based mean reversion strategy for range-bound markets",
        "type": "rsi",
        "default_params": {
            "name": "RSI Mean Reversion",
            "description": "RSI mean reversion strategy",
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "stop_loss_percent": 0.03,
            "take_profit_percent": 0.08
        }
    },
    "momentum": {
        "id": "momentum",
        "name": "Momentum Only",
        "description": "Pure momentum strategy following price trends",
        "type": "momentum",
        "default_params": {
            "name": "Momentum",
            "description": "Momentum strategy",
            "lookback_period": 10,
            "momentum_threshold": 0.005
        }
    }
}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/strategies")
async def get_available_strategies():
    """Get list of available trading strategies."""
    try:
        strategies = list(AVAILABLE_STRATEGIES.values())
        return {
            "success": True,
            "data": strategies
        }
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/{strategy_id}/defaults")
async def get_strategy_defaults(strategy_id: str):
    """Get default parameters for a specific strategy."""
    try:
        if strategy_id not in AVAILABLE_STRATEGIES:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        strategy = AVAILABLE_STRATEGIES[strategy_id]
        return {
            "success": True,
            "data": strategy["default_params"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy defaults: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str = "BTC-USD", days: int = 180):
    """Get historical market data for a symbol."""
    try:
        # Load data using our existing data loader
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        data = data_loader.get_crypto_data(symbol, start_date=start_date, end_date=end_date)
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data available for symbol")
        
        # Convert to the format expected by frontend
        candlestick_data = []
        for _, row in data.iterrows():
            candlestick_data.append({
                "timestamp": row.name.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        current_price = float(data['close'].iloc[-1])
        price_change_24h = float(data['close'].iloc[-1] - data['close'].iloc[-2])
        price_change_percent_24h = (price_change_24h / data['close'].iloc[-2]) * 100
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "data": candlestick_data,
                "current_price": current_price,
                "price_change_24h": price_change_24h,
                "price_change_percent_24h": price_change_percent_24h
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_strategy_instance(strategy_id: str, params: Dict[str, Any]):
    """Create a strategy instance from ID and parameters."""
    if strategy_id in ["balanced_ensemble", "conservative_ensemble", "aggressive_ensemble"]:
        return EnsembleStrategy(params)
    elif strategy_id == "ma_crossover":
        return MovingAverageCrossoverStrategy(params)
    elif strategy_id == "rsi_mean_reversion":
        return RSIMeanReversionStrategy(params)
    elif strategy_id == "momentum":
        return SimpleMomentumStrategy(params)
    else:
        raise ValueError(f"Unknown strategy: {strategy_id}")

@app.post("/api/simulations")
async def create_simulation(request: CreateSimulationRequest):
    """Create a new simulation."""
    try:
        simulation_id = str(uuid.uuid4())
        
        # Create simulation configuration
        config = SimulationConfig(
            initial_capital=request.config.initial_capital,
            position_size=request.config.position_size,
            commission_rate=request.config.commission_rate,
            slippage_rate=request.config.slippage_rate,
            max_positions=request.config.max_positions
        )
        
        # Create strategy instance
        strategy = create_strategy_instance(request.strategy_id, request.strategy_params)
        
        # Create simulation engine
        engine = SimulationEngine(config)
        
        # Load market data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        data = data_loader.get_crypto_data("BTC-USD", start_date=start_date, end_date=end_date)
        if data is None or data.empty:
            raise HTTPException(status_code=500, detail="Failed to load market data")
        
        engine.load_data(data)
        engine.set_strategy(strategy)
        
        # Store simulation
        simulations[simulation_id] = {
            "id": simulation_id,
            "engine": engine,
            "strategy_id": request.strategy_id,
            "strategy_params": request.strategy_params,
            "config": config,
            "status": "idle",
            "progress": 0.0,
            "current_date": None,
            "error_message": None,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created simulation {simulation_id}")
        
        return {
            "success": True,
            "data": {"simulation_id": simulation_id}
        }
    except Exception as e:
        logger.error(f"Error creating simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulations/{simulation_id}/start")
async def start_simulation(simulation_id: str, background_tasks: BackgroundTasks):
    """Start a simulation."""
    try:
        if simulation_id not in simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation = simulations[simulation_id]
        
        if simulation["status"] == "running":
            raise HTTPException(status_code=400, detail="Simulation already running")
        
        # Start simulation in background
        background_tasks.add_task(run_simulation, simulation_id)
        
        simulation["status"] = "running"
        logger.info(f"Started simulation {simulation_id}")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_simulation(simulation_id: str):
    """Run simulation in background using real simulation engine."""
    try:
        simulation = simulations[simulation_id]
        engine = simulation["engine"]

        logger.info(f"Starting real simulation {simulation_id}")

        # Start the real simulation engine
        engine.start_simulation()

        # Monitor simulation progress
        while engine.is_running:
            # Get current state from engine
            current_state = engine.get_current_state()

            # Update simulation state
            simulation["progress"] = current_state.get('progress', 0.0)
            simulation["current_date"] = current_state.get('timestamp').isoformat() if current_state.get('timestamp') else None

            # Check if simulation completed
            if current_state.get('progress', 0.0) >= 1.0:
                break

            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)

        # Mark as completed
        simulation["status"] = "completed"
        simulation["progress"] = 1.0

        logger.info(f"Completed real simulation {simulation_id}")

    except Exception as e:
        logger.error(f"Error running simulation {simulation_id}: {e}")
        simulation["status"] = "error"
        simulation["error_message"] = str(e)

@app.get("/api/simulations/{simulation_id}/state")
async def get_simulation_state(simulation_id: str):
    """Get current simulation state."""
    try:
        if simulation_id not in simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation = simulations[simulation_id]
        engine = simulation["engine"]

        # Get real data from simulation engine
        current_state = engine.get_current_state()

        # Extract data from current state
        portfolio_value = current_state.get('portfolio_value', 0.0)
        cash = current_state.get('cash', 0.0)
        positions = current_state.get('positions', {})
        total_return = current_state.get('total_return', 0.0)
        trade_stats = current_state.get('trade_stats', {})
        performance_metrics = current_state.get('performance_metrics', {})

        # Convert positions to API format (simplified for now)
        api_positions = []
        # Skip position details for now to avoid conversion issues
        # TODO: Implement proper position object handling

        # Convert to API format
        portfolio = {
            "timestamp": current_state.get('timestamp', datetime.now()).isoformat(),
            "totalValue": portfolio_value,
            "cash": cash,
            "positions": api_positions,
            "dailyReturn": 0.0,  # Would need daily tracking
            "totalReturn": total_return * 100,  # Convert to percentage
            "sharpeRatio": performance_metrics.get('sharpe_ratio', 0.0),
            "maxDrawdown": current_state.get('drawdown', 0.0) * 100,  # Convert to percentage
            "volatility": performance_metrics.get('volatility', 0.0)
        }

        performance = {
            "totalReturn": total_return * 100,  # Convert to percentage
            "sharpeRatio": performance_metrics.get('sharpe_ratio', 0.0),
            "maxDrawdown": current_state.get('drawdown', 0.0) * 100,  # Convert to percentage
            "volatility": performance_metrics.get('volatility', 0.0),
            "winRate": trade_stats.get('win_rate', 0.0) * 100,  # Convert to percentage
            "profitFactor": trade_stats.get('profit_factor', 0.0),
            "totalTrades": trade_stats.get('total_trades', 0),
            "avgTradeReturn": trade_stats.get('avg_return', 0.0) * 100,  # Convert to percentage
            "bestTrade": trade_stats.get('best_trade', 0.0) * 100,  # Convert to percentage
            "worstTrade": trade_stats.get('worst_trade', 0.0) * 100  # Convert to percentage
        }
        
        # Get trades from portfolio (simplified for now)
        api_trades = []
        # TODO: Extract actual trades from portfolio.trade_history when available

        state = {
            "status": simulation["status"],
            "progress": simulation["progress"],
            "current_date": simulation["current_date"],
            "portfolio": portfolio,
            "trades": api_trades,
            "performance": performance,
            "error_message": simulation.get("error_message")
        }
        
        return {
            "success": True,
            "data": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
