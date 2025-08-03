"""Advanced position sizing and risk management."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AdvancedPositionSizer:
    """Advanced position sizing with multiple methodologies."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the position sizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'max_position_size': 0.25,          # Maximum 25% of capital per position
            'max_portfolio_risk': 0.02,         # Maximum 2% portfolio risk per trade
            'kelly_lookback_days': 60,          # Days for Kelly calculation
            'volatility_lookback_days': 20,     # Days for volatility calculation
            'min_position_size': 0.01,          # Minimum 1% position size
            'risk_free_rate': 0.02,             # Annual risk-free rate
            'confidence_scaling': True,         # Scale position by signal confidence
            'volatility_scaling': True,         # Scale position by volatility
            'correlation_limit': 0.7,           # Maximum correlation between positions
            'max_drawdown_limit': 0.15,         # Stop trading if drawdown > 15%
        }
    
    def calculate_position_size(
        self,
        signal_confidence: float,
        current_price: float,
        stop_loss_price: float,
        portfolio_value: float,
        historical_returns: pd.Series,
        method: str = "kelly"
    ) -> float:
        """Calculate optimal position size.
        
        Args:
            signal_confidence: Signal confidence (0.0 to 1.0)
            current_price: Current asset price
            stop_loss_price: Stop loss price
            portfolio_value: Current portfolio value
            historical_returns: Historical returns for Kelly calculation
            method: Position sizing method ('kelly', 'fixed_risk', 'volatility_adjusted')
            
        Returns:
            Position size as fraction of portfolio value
        """
        
        if method == "kelly":
            base_size = self._kelly_criterion(historical_returns, signal_confidence)
        elif method == "fixed_risk":
            base_size = self._fixed_risk_sizing(current_price, stop_loss_price, portfolio_value)
        elif method == "volatility_adjusted":
            base_size = self._volatility_adjusted_sizing(historical_returns)
        else:
            base_size = self.config['max_position_size'] / 4  # Conservative default
        
        # Apply scaling factors
        if self.config.get('confidence_scaling', True):
            base_size *= signal_confidence
        
        if self.config.get('volatility_scaling', True):
            volatility_factor = self._calculate_volatility_factor(historical_returns)
            base_size *= volatility_factor
        
        # Apply limits
        max_size = self.config.get('max_position_size', 0.25)
        min_size = self.config.get('min_position_size', 0.01)
        
        final_size = max(min_size, min(max_size, base_size))
        
        logger.debug(f"Position sizing: method={method}, base={base_size:.3f}, "
                    f"confidence={signal_confidence:.3f}, final={final_size:.3f}")
        
        return final_size
    
    def _kelly_criterion(self, returns: pd.Series, signal_confidence: float) -> float:
        """Calculate Kelly criterion position size.
        
        Args:
            returns: Historical returns series
            signal_confidence: Signal confidence
            
        Returns:
            Kelly optimal position size
        """
        if len(returns) < 10:
            return self.config.get('min_position_size', 0.01)
        
        # Filter to recent returns
        lookback_days = self.config.get('kelly_lookback_days', 60)
        recent_returns = returns.tail(lookback_days)
        
        # Calculate win rate and average win/loss
        positive_returns = recent_returns[recent_returns > 0]
        negative_returns = recent_returns[recent_returns < 0]
        
        if len(positive_returns) == 0 or len(negative_returns) == 0:
            return self.config.get('min_position_size', 0.01)
        
        win_rate = len(positive_returns) / len(recent_returns)
        avg_win = positive_returns.mean()
        avg_loss = abs(negative_returns.mean())
        
        if avg_loss == 0:
            return self.config.get('min_position_size', 0.01)
        
        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / avg_loss
        p = win_rate * signal_confidence  # Adjust win rate by confidence
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Apply conservative scaling (typically use 25-50% of Kelly)
        kelly_scaling = 0.25
        scaled_kelly = kelly_fraction * kelly_scaling
        
        # Ensure positive and reasonable
        return max(0.01, min(0.25, scaled_kelly))
    
    def _fixed_risk_sizing(
        self,
        current_price: float,
        stop_loss_price: float,
        portfolio_value: float
    ) -> float:
        """Calculate position size based on fixed risk per trade.
        
        Args:
            current_price: Current asset price
            stop_loss_price: Stop loss price
            portfolio_value: Current portfolio value
            
        Returns:
            Position size as fraction of portfolio
        """
        if stop_loss_price <= 0 or current_price <= 0:
            return self.config.get('min_position_size', 0.01)
        
        # Calculate risk per share
        risk_per_share = abs(current_price - stop_loss_price)
        risk_percentage = risk_per_share / current_price
        
        # Maximum portfolio risk per trade
        max_portfolio_risk = self.config.get('max_portfolio_risk', 0.02)
        
        # Position size = max_risk / risk_per_share_percentage
        position_size = max_portfolio_risk / risk_percentage
        
        return max(0.01, min(0.25, position_size))
    
    def _volatility_adjusted_sizing(self, returns: pd.Series) -> float:
        """Calculate position size adjusted for volatility.
        
        Args:
            returns: Historical returns series
            
        Returns:
            Volatility-adjusted position size
        """
        if len(returns) < 10:
            return self.config.get('min_position_size', 0.01)
        
        # Calculate recent volatility
        lookback_days = self.config.get('volatility_lookback_days', 20)
        recent_returns = returns.tail(lookback_days)
        volatility = recent_returns.std() * np.sqrt(252)  # Annualized
        
        # Base position size inversely related to volatility
        # Higher volatility = smaller position
        base_volatility = 0.20  # 20% annual volatility as baseline
        volatility_ratio = base_volatility / max(volatility, 0.05)  # Avoid division by zero
        
        base_size = self.config.get('max_position_size', 0.25) / 4
        adjusted_size = base_size * volatility_ratio
        
        return max(0.01, min(0.25, adjusted_size))
    
    def _calculate_volatility_factor(self, returns: pd.Series) -> float:
        """Calculate volatility scaling factor.
        
        Args:
            returns: Historical returns series
            
        Returns:
            Volatility scaling factor (0.5 to 1.5)
        """
        if len(returns) < 10:
            return 1.0
        
        # Calculate recent volatility
        recent_returns = returns.tail(20)
        current_vol = recent_returns.std() * np.sqrt(252)
        
        # Calculate longer-term volatility
        longer_returns = returns.tail(60) if len(returns) >= 60 else returns
        long_term_vol = longer_returns.std() * np.sqrt(252)
        
        if long_term_vol == 0:
            return 1.0
        
        # If current volatility is lower than long-term, increase position
        # If current volatility is higher, decrease position
        vol_ratio = long_term_vol / current_vol
        
        # Scale between 0.5 and 1.5
        scaling_factor = max(0.5, min(1.5, vol_ratio))
        
        return scaling_factor


class RiskManager:
    """Comprehensive risk management system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the risk manager.
        
        Args:
            config: Risk management configuration
        """
        self.config = config or self._get_default_config()
        self.position_sizer = AdvancedPositionSizer(config)
        self.current_positions = {}
        self.portfolio_history = []
        
    def _get_default_config(self) -> Dict:
        """Get default risk management configuration."""
        return {
            'max_positions': 3,                 # Maximum concurrent positions
            'max_correlation': 0.7,             # Maximum correlation between positions
            'max_sector_exposure': 0.5,         # Maximum exposure to single sector
            'max_drawdown_limit': 0.15,         # Stop trading if drawdown > 15%
            'daily_loss_limit': 0.05,           # Stop trading if daily loss > 5%
            'position_timeout_days': 30,        # Close positions after 30 days
            'rebalance_threshold': 0.1,         # Rebalance if allocation drifts > 10%
            'emergency_stop': False,            # Emergency stop flag
        }
    
    def check_risk_limits(
        self,
        new_signal: Dict,
        current_portfolio: Dict,
        portfolio_history: List[Dict]
    ) -> Tuple[bool, str]:
        """Check if new signal passes risk limits.
        
        Args:
            new_signal: New trading signal
            current_portfolio: Current portfolio state
            portfolio_history: Historical portfolio values
            
        Returns:
            Tuple of (allowed, reason)
        """
        
        # Check emergency stop
        if self.config.get('emergency_stop', False):
            return False, "Emergency stop activated"
        
        # Check maximum positions
        current_positions = len(current_portfolio.get('positions', {}))
        max_positions = self.config.get('max_positions', 3)
        if current_positions >= max_positions:
            return False, f"Maximum positions limit reached ({max_positions})"
        
        # Check drawdown limit
        if len(portfolio_history) > 1:
            current_value = current_portfolio.get('total_value', 0)
            peak_value = max(h.get('total_value', 0) for h in portfolio_history)
            
            if peak_value > 0:
                drawdown = (peak_value - current_value) / peak_value
                max_dd_limit = self.config.get('max_drawdown_limit', 0.15)
                
                if drawdown > max_dd_limit:
                    return False, f"Maximum drawdown exceeded: {drawdown:.2%} > {max_dd_limit:.2%}"
        
        # Check daily loss limit
        if len(portfolio_history) > 0:
            previous_value = portfolio_history[-1].get('total_value', 0)
            current_value = current_portfolio.get('total_value', 0)
            
            if previous_value > 0:
                daily_return = (current_value - previous_value) / previous_value
                daily_loss_limit = self.config.get('daily_loss_limit', 0.05)
                
                if daily_return < -daily_loss_limit:
                    return False, f"Daily loss limit exceeded: {daily_return:.2%}"
        
        # Check correlation limits (placeholder - would need actual correlation calculation)
        # This would require historical price data for correlation analysis
        
        return True, "Risk checks passed"
    
    def calculate_optimal_position_size(
        self,
        signal: Dict,
        portfolio_value: float,
        historical_data: pd.DataFrame
    ) -> float:
        """Calculate optimal position size for a signal.
        
        Args:
            signal: Trading signal with confidence and metadata
            portfolio_value: Current portfolio value
            historical_data: Historical price data
            
        Returns:
            Optimal position size as fraction of portfolio
        """
        
        # Extract signal information
        confidence = signal.get('confidence', 0.5)
        current_price = signal.get('price', 0)
        
        # Calculate stop loss price (if not provided)
        stop_loss_price = signal.get('stop_loss_price')
        if not stop_loss_price:
            # Use default 5% stop loss
            stop_loss_price = current_price * 0.95
        
        # Calculate historical returns
        if 'close' in historical_data.columns:
            returns = historical_data['close'].pct_change().dropna()
        else:
            # Fallback to minimal position size
            return self.config.get('min_position_size', 0.01)
        
        # Use Kelly criterion as default method
        position_size = self.position_sizer.calculate_position_size(
            signal_confidence=confidence,
            current_price=current_price,
            stop_loss_price=stop_loss_price,
            portfolio_value=portfolio_value,
            historical_returns=returns,
            method="kelly"
        )
        
        return position_size
    
    def update_risk_metrics(self, portfolio_state: Dict):
        """Update risk metrics and check for emergency conditions.
        
        Args:
            portfolio_state: Current portfolio state
        """
        self.portfolio_history.append(portfolio_state.copy())
        
        # Keep only recent history (last 100 days)
        if len(self.portfolio_history) > 100:
            self.portfolio_history = self.portfolio_history[-100:]
        
        # Check for emergency stop conditions
        if len(self.portfolio_history) >= 2:
            current_value = portfolio_state.get('total_value', 0)
            peak_value = max(h.get('total_value', 0) for h in self.portfolio_history)
            
            if peak_value > 0:
                drawdown = (peak_value - current_value) / peak_value
                emergency_dd_limit = 0.25  # Emergency stop at 25% drawdown
                
                if drawdown > emergency_dd_limit:
                    self.config['emergency_stop'] = True
                    logger.warning(f"Emergency stop activated due to {drawdown:.2%} drawdown")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary.
        
        Returns:
            Dictionary with risk metrics
        """
        if not self.portfolio_history:
            return {'status': 'No history available'}
        
        current_state = self.portfolio_history[-1]
        
        # Calculate drawdown
        peak_value = max(h.get('total_value', 0) for h in self.portfolio_history)
        current_value = current_state.get('total_value', 0)
        drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0
        
        # Calculate recent volatility
        if len(self.portfolio_history) >= 10:
            values = [h.get('total_value', 0) for h in self.portfolio_history[-10:]]
            returns = pd.Series(values).pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        else:
            volatility = 0
        
        return {
            'current_drawdown': drawdown,
            'recent_volatility': volatility,
            'emergency_stop': self.config.get('emergency_stop', False),
            'positions_count': len(current_state.get('positions', {})),
            'max_positions': self.config.get('max_positions', 3),
            'risk_status': 'EMERGENCY' if self.config.get('emergency_stop') else 'NORMAL'
        }
