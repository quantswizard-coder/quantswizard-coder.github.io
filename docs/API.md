# 🔌 API Documentation

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### Health Check
```http
GET /health
```
Returns server health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-01-01T12:00:00"
  }
}
```

### Get Available Strategies
```http
GET /strategies
```
Returns list of available trading strategies.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "balanced_ensemble",
      "name": "Balanced Ensemble (CHAMPION 🏆)",
      "description": "Combines MA Crossover, RSI Mean Reversion, and Momentum strategies",
      "type": "ensemble"
    }
  ]
}
```

### Get Strategy Defaults
```http
GET /strategies/{strategy_id}/defaults
```
Returns default parameters for a specific strategy.

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "Balanced Ensemble",
    "ensemble_method": "confidence_weighted",
    "min_consensus": 0.4,
    "confidence_threshold": 0.3
  }
}
```

### Get Market Data
```http
GET /market-data/{symbol}?days={days}
```
Returns historical market data for a symbol.

**Parameters:**
- `symbol`: Trading symbol (e.g., "BTC-USD")
- `days`: Number of days of historical data

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC-USD",
    "current_price": 45000.00,
    "price_change_24h": 1200.00,
    "price_change_percent_24h": 2.74,
    "data": [
      {
        "timestamp": "2025-01-01T00:00:00",
        "open": 44000.00,
        "high": 45500.00,
        "low": 43800.00,
        "close": 45000.00,
        "volume": 1234567
      }
    ]
  }
}
```

### Create Simulation
```http
POST /simulations
```
Creates a new trading simulation.

**Request Body:**
```json
{
  "strategy_id": "balanced_ensemble",
  "strategy_params": {
    "ensemble_method": "confidence_weighted",
    "min_consensus": 0.4
  },
  "config": {
    "initial_capital": 100000.0,
    "position_size": 0.2,
    "commission_rate": 0.001,
    "slippage_rate": 0.0005,
    "max_positions": 3,
    "speed_multiplier": 10
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "uuid-string"
  }
}
```

### Start Simulation
```http
POST /simulations/{simulation_id}/start
```
Starts a created simulation.

### Get Simulation State
```http
GET /simulations/{simulation_id}/state
```
Returns current simulation state and results.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "running",
    "progress": 0.75,
    "current_date": "2025-01-01T12:00:00",
    "portfolio": {
      "totalValue": 105000.0,
      "cash": 20000.0,
      "positions": []
    },
    "performance": {
      "totalReturn": 5.0,
      "sharpeRatio": 1.2,
      "maxDrawdown": -0.03,
      "winRate": 65.0
    },
    "trades": []
  }
}
```

## Error Handling

All endpoints return errors in the following format:
```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error
