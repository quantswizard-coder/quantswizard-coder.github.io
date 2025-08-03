# 📁 Clean Codebase Structure

## Overview
This document describes the organized, clean structure of the Interactive Trading Simulator codebase after comprehensive cleanup.

## Directory Structure

```
📁 Interactive Trading Simulator/
├── 📄 README.md                    # Main project documentation
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Git ignore rules
├── 📄 pyproject.toml               # Python project configuration
├── 📄 requirements.txt             # Python dependencies
├── 📄 setup.sh                     # Environment setup script
├── 📄 start_trading_simulator.sh   # One-command startup script
├── 📄 stop_trading_simulator.sh    # Clean shutdown script
├── 📄 FRONTEND_SETUP_GUIDE.md      # Detailed frontend setup guide
├── 📄 CODEBASE_STRUCTURE.md        # This file
│
├── 📁 frontend/                    # React + TypeScript Frontend
│   ├── 📁 public/                 # Static assets
│   ├── 📁 src/                    # Source code
│   │   ├── 📁 components/         # Reusable UI components
│   │   │   ├── 📁 ui/             # Base UI components (Button, Input, etc.)
│   │   │   ├── 📁 charts/         # Chart components (Portfolio, Candlestick)
│   │   │   ├── 📁 dashboard/      # Dashboard-specific components
│   │   │   ├── 📁 strategy/       # Strategy configuration components
│   │   │   ├── 📁 simulation/     # Simulation control components
│   │   │   └── 📁 layout/         # Layout components (Header, Sidebar)
│   │   ├── 📁 pages/              # Main application pages
│   │   ├── 📁 hooks/              # Custom React hooks
│   │   ├── 📁 services/           # API integration
│   │   ├── 📁 contexts/           # React contexts (Theme, etc.)
│   │   ├── 📁 types/              # TypeScript type definitions
│   │   ├── 📄 App.tsx             # Main application component
│   │   ├── 📄 index.tsx           # Application entry point
│   │   └── 📄 index.css           # Global styles
│   ├── 📄 package.json            # Node.js dependencies
│   ├── 📄 tsconfig.json           # TypeScript configuration
│   ├── 📄 tailwind.config.js      # Tailwind CSS configuration
│   └── 📄 README.md               # Frontend-specific documentation
│
├── 📁 backend/                     # Python FastAPI Backend
│   ├── 📄 api_server.py           # Main FastAPI application
│   └── 📄 requirements.txt        # Backend Python dependencies
│
├── 📁 src/                        # Core Trading System
│   ├── 📁 strategies/             # Trading strategy implementations
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_strategy.py    # Base strategy interface
│   │   ├── 📄 ensemble_strategy.py # Ensemble strategies
│   │   ├── 📄 ma_crossover.py     # Moving Average Crossover
│   │   └── 📄 rsi_mean_reversion.py # RSI Mean Reversion
│   ├── 📁 simulation/             # Simulation engine
│   │   ├── 📄 __init__.py
│   │   ├── 📄 simulation_engine.py # Main simulation engine
│   │   └── 📄 portfolio_tracker.py # Portfolio management
│   ├── 📁 data/                   # Data providers and processing
│   │   ├── 📄 __init__.py
│   │   └── 📄 openbb_client.py    # OpenBB data integration
│   ├── 📁 backtesting/            # Performance analysis
│   │   ├── 📄 __init__.py
│   │   ├── 📄 backtest_engine.py  # Backtesting engine
│   │   └── 📄 performance_metrics.py # Performance calculations
│   ├── 📁 risk_management/        # Risk management utilities
│   ├── 📁 optimization/           # Strategy optimization
│   ├── 📁 features/               # Feature engineering
│   ├── 📁 utils/                  # Shared utilities
│   └── 📄 main.py                 # Main entry point
│
├── 📁 scripts/                    # Utility and execution scripts
│   ├── 📄 interactive_trading_simulator.py # Terminal-based simulator
│   ├── 📄 bitcoin_data_pipeline.py         # Data collection pipeline
│   ├── 📄 collect_bitcoin_data.py          # Data collection utility
│   ├── 📄 optimize_strategies.py           # Strategy optimization
│   ├── 📄 simple_optimization.py           # Simple optimization
│   └── 📄 fixed_optimization.py            # Fixed parameter optimization
│
├── 📁 config/                     # Configuration files
│   └── 📄 openbb_providers.yaml   # OpenBB provider configuration
│
├── 📁 docs/                       # Documentation
│   ├── 📄 README.md               # Documentation index
│   ├── 📄 ARCHITECTURE.md         # System architecture overview
│   ├── 📄 API.md                  # API documentation
│   ├── 📄 GPU_TRAINING_GUIDE.md   # GPU training guide
│   └── 📄 index.html              # Documentation website
│
├── 📁 tests/                      # Test suite
│   ├── 📄 __init__.py
│   └── 📄 test_setup.py           # Setup tests
│
├── 📁 notebooks/                  # Jupyter notebooks
│   └── 📄 openbb_data_exploration.ipynb # Data exploration
│
├── 📁 data/                       # Data storage (auto-generated)
│   ├── 📁 raw/                    # Raw market data
│   │   └── 📄 .gitkeep
│   └── 📁 processed/              # Processed data
│       └── 📄 .gitkeep
│
├── 📁 results/                    # Simulation results (auto-generated)
│   └── 📄 .gitkeep
│
├── 📁 reports/                    # Analysis reports (auto-generated)
│   └── 📄 .gitkeep
│
└── 📁 optimization_results/       # Optimization results (auto-generated)
    └── 📄 .gitkeep
```

## Key Features of Clean Structure

### ✅ **Removed Redundant Files**
- Legacy documentation files (8 files removed)
- Archive directory with old experiments
- UI directory (replaced by React frontend)
- Cloud setup directory (not needed)
- Visualization directory (replaced by React charts)
- Debug and test files
- Log files and cache
- Virtual environment (should be recreated)

### ✅ **Organized Components**
- **Frontend**: Modern React + TypeScript structure
- **Backend**: Clean FastAPI implementation
- **Core System**: Modular Python architecture
- **Documentation**: Comprehensive and up-to-date
- **Configuration**: Centralized and clean

### ✅ **Proper Separation**
- **Frontend** (`frontend/`): All React/TypeScript code
- **Backend** (`backend/`): FastAPI server
- **Core Logic** (`src/`): Trading system implementation
- **Scripts** (`scripts/`): Utility and execution scripts
- **Data** (`data/`): Auto-generated data files
- **Results** (`results/`, `reports/`, `optimization_results/`): Auto-generated outputs

### ✅ **Clean Practices**
- Comprehensive `.gitignore` file
- `.gitkeep` files for empty directories
- No redundant or legacy files
- Clear naming conventions
- Proper documentation structure

## File Count Summary

**Before Cleanup**: ~150+ files including redundant/legacy files
**After Cleanup**: ~50 essential files + auto-generated content

## Maintenance

This structure is designed to be:
- **Self-documenting**: Clear file and directory names
- **Scalable**: Easy to add new features
- **Maintainable**: Logical organization
- **Professional**: Suitable for production use

All auto-generated files (data, results, logs) are properly ignored by Git and can be safely deleted and regenerated.
