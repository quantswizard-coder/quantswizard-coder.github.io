# 🚀 Interactive Trading Simulator - Full-Stack Application

A comprehensive cryptocurrency trading strategy backtesting and simulation platform with a professional React + TypeScript frontend and Python backend. This system allows you to test various trading strategies against historical Bitcoin data with real-time visualization and analysis.

## ✅ **Status: COMPLETE & OPERATIONAL**

**🌐 Live Demo:** https://quantswizard-coder.github.io - Professional web interface
**🎯 Local Frontend:** http://localhost:3000 - Development server
**🔧 Python Backend:** http://localhost:8000 - FastAPI with comprehensive endpoints
**📊 Real-time Data:** Bitcoin price monitoring with Yahoo Finance integration
**🏗️ Professional Setup:** Modern full-stack architecture with TypeScript and Python

## 🎯 **Features**

### 📊 **Professional Trading Strategies**
- **6 Trading Strategies** with detailed descriptions:
  - 🏆 **Balanced Ensemble (CHAMPION)** - Confidence-weighted multi-strategy approach
  - 🛡️ **Conservative Ensemble** - High consensus requirements
  - ⚡ **Aggressive Ensemble** - Low consensus for frequent trading
  - 📈 **MA Crossover Only** - Moving average trend following
  - 🔄 **RSI Mean Reversion Only** - Range-bound market strategy
  - 🚀 **Momentum Only** - Pure trend momentum strategy

### 🎮 **Interactive Web Interface**
- **Real-time Portfolio Visualization** with interactive charts
- **Strategy Configuration** with dynamic parameter controls
- **Performance Metrics Dashboard** with comprehensive analysis
- **Trade History Analysis** with sortable, filterable tables
- **Dark/Light Theme Support** with responsive design

### 🔧 **Modern Full-Stack Architecture**
- **React + TypeScript Frontend** with professional UI components
- **Python FastAPI Backend** with comprehensive REST API
- **Real-time Data Integration** with Yahoo Finance
- **Modular, Clean Codebase** with proper separation of concerns
- **Type Safety** throughout the entire stack

## 🚀 **Quick Start**

### **One-Command Startup**
```bash
./start_trading_simulator.sh
```

This will:
1. ✅ Check prerequisites (Node.js, Python, npm, pip)
2. ✅ Install all dependencies automatically
3. ✅ Start both frontend and backend services
4. ✅ Open your browser to http://localhost:3000

### **Manual Setup**
```bash
# Backend
cd backend
pip install -r requirements.txt
python api_server.py

# Frontend (in new terminal)
cd frontend
npm install
npm start
```

## 📁 **Clean Codebase Structure**

```
├── 📁 frontend/                 # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/              # Main application pages
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API integration
│   │   └── types/              # TypeScript definitions
│   └── package.json
│
├── 📁 backend/                  # Python FastAPI Backend
│   ├── api_server.py           # Main API server
│   └── requirements.txt        # Python dependencies
│
├── 📁 src/                     # Core Trading System
│   ├── strategies/             # Trading strategies
│   ├── simulation/             # Simulation engine
│   ├── data/                   # Data providers
│   ├── backtesting/            # Performance analysis
│   └── utils/                  # Utilities
│
├── 📁 scripts/                 # Utility Scripts
│   ├── interactive_trading_simulator.py  # Terminal interface
│   ├── bitcoin_data_pipeline.py          # Data collection
│   └── optimization scripts
│
├── 📁 data/                    # Data Storage
│   ├── raw/                    # Raw market data
│   └── processed/              # Processed data
│
├── 📁 config/                  # Configuration
├── 📁 docs/                    # Documentation
├── 📁 tests/                   # Test suite
└── 📁 notebooks/               # Jupyter notebooks
```

## 🛠️ **Technology Stack**

### **Frontend**
- **React 18+** with TypeScript for type safety
- **Tailwind CSS** for responsive styling
- **Framer Motion** for smooth animations
- **React Query** for data fetching and caching
- **Recharts** for interactive visualizations

### **Backend**
- **Python 3.8+** with FastAPI framework
- **Pandas/NumPy** for data processing
- **Yahoo Finance** for market data
- **Pydantic** for data validation
- **Uvicorn** for ASGI server

## 📊 **Performance Metrics**

The application tracks comprehensive trading performance metrics:

- **Total Return** - Portfolio gain/loss percentage
- **Sharpe Ratio** - Risk-adjusted return measure
- **Maximum Drawdown** - Largest peak-to-trough decline
- **Volatility** - Standard deviation of returns
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Ratio of gross profit to gross loss

## 🎯 **Usage Guide**

### **1. Strategy Configuration**
1. Go to the **Strategy** tab
2. Select from 6 professional strategies
3. Customize parameters with interactive controls
4. Save configurations for later use

### **2. Simulation Setup**
1. Go to the **Simulation** tab
2. Configure capital, position size, and costs
3. Set simulation speed (1x to 50x)
4. Click "Create & Start Simulation"

### **3. Performance Analysis**
1. Go to the **Dashboard** tab
2. View real-time portfolio performance
3. Analyze comprehensive metrics
4. Review detailed trade history

## 🔧 **Development**

### **Adding New Strategies**
1. Create strategy class in `src/strategies/`
2. Implement `generate_signals()` method
3. Add to strategy registry in backend
4. Update frontend strategy selector

### **Extending the API**
1. Add endpoints in `backend/api_server.py`
2. Update frontend API service
3. Add TypeScript types
4. Test integration

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **React Team** for the excellent framework
- **FastAPI** for the high-performance backend
- **Yahoo Finance** for market data
- **Tailwind CSS** for the utility-first styling

---

**Built with ❤️ for professional cryptocurrency trading strategy analysis and backtesting.**
