#!/bin/bash
# Bitcoin Quant Trading System - Complete Setup Script

echo "🚀 Bitcoin Quant Trading System - Setup Script"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
echo "📚 Installing core dependencies..."
pip install pandas numpy setuptools wheel

# Install dashboard dependencies
echo "🎨 Installing dashboard dependencies..."
pip install streamlit plotly pyyaml python-dotenv

# Install data source
echo "📊 Installing data sources..."
pip install yfinance requests

# Install testing framework
echo "🧪 Installing testing framework..."
pip install pytest

# Test the setup
echo "🔍 Testing setup..."
python tests/test_setup.py

# Test data fetching
echo "📈 Testing Bitcoin data fetch..."
python test_data.py

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "🎯 Next Steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Launch dashboard: streamlit run ui/bitcoin_dashboard.py"
echo "3. Open browser: http://localhost:8501"
echo ""
echo "📚 Available Commands:"
echo "• Test setup: python tests/test_setup.py"
echo "• Test data: python test_data.py"
echo "• Run dashboard: streamlit run ui/bitcoin_dashboard.py"
echo ""
echo "🎉 Happy Trading! 🚀₿"
