"""Data validation module for multi-provider crypto data."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    quality_score: float
    issues: List[str]
    metrics: Dict[str, Any]
    recommendations: List[str]


class DataValidator:
    """Validates cryptocurrency data quality across multiple providers."""
    
    def __init__(self, config: Dict):
        """Initialize the data validator.
        
        Args:
            config: Validation configuration from YAML
        """
        self.config = config.get('validation', {})
        self.quality_config = config.get('data_quality', {})
        
    def validate_single_provider(self, df: pd.DataFrame, provider: str) -> ValidationResult:
        """Validate data from a single provider.
        
        Args:
            df: DataFrame with OHLCV data
            provider: Provider name
            
        Returns:
            ValidationResult with quality metrics
        """
        issues = []
        metrics = {}
        recommendations = []
        
        # Basic data checks
        if df.empty:
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=["No data available"],
                metrics={},
                recommendations=["Check provider connection and symbol format"]
            )
        
        # Check data completeness
        completeness = self._check_completeness(df)
        metrics['completeness_percent'] = completeness
        
        if completeness < self.quality_config.get('min_completeness_percent', 95.0):
            issues.append(f"Low data completeness: {completeness:.1f}%")
            recommendations.append("Consider using alternative provider or filling missing data")
        
        # Check for duplicates
        duplicate_percent = (df.duplicated().sum() / len(df)) * 100
        metrics['duplicate_percent'] = duplicate_percent
        
        if duplicate_percent > self.quality_config.get('max_duplicate_percent', 1.0):
            issues.append(f"High duplicate rate: {duplicate_percent:.1f}%")
            recommendations.append("Remove duplicate records")
        
        # Check volume data
        if 'volume' in df.columns:
            zero_volume_percent = ((df['volume'] == 0).sum() / len(df)) * 100
            metrics['zero_volume_percent'] = zero_volume_percent
            
            if zero_volume_percent > self.quality_config.get('max_zero_volume_percent', 5.0):
                issues.append(f"High zero volume rate: {zero_volume_percent:.1f}%")
                recommendations.append("Investigate volume data quality")
        
        # Check price consistency
        price_issues = self._check_price_consistency(df)
        issues.extend(price_issues)
        
        # Check temporal consistency
        temporal_issues = self._check_temporal_consistency(df)
        issues.extend(temporal_issues)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(metrics, issues)
        
        # Add provider-specific metrics
        metrics.update({
            'provider': provider,
            'record_count': len(df),
            'date_range_days': (df.index[-1] - df.index[0]).days if len(df) > 1 else 0,
            'validation_time': datetime.now().isoformat()
        })
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            metrics=metrics,
            recommendations=recommendations
        )
    
    def validate_cross_provider(
        self, 
        provider_data: Dict[str, pd.DataFrame]
    ) -> ValidationResult:
        """Validate data consistency across multiple providers.
        
        Args:
            provider_data: Dictionary mapping provider names to DataFrames
            
        Returns:
            ValidationResult for cross-provider validation
        """
        if len(provider_data) < 2:
            return ValidationResult(
                is_valid=True,
                quality_score=1.0,
                issues=[],
                metrics={'providers_count': len(provider_data)},
                recommendations=["Add more providers for cross-validation"]
            )
        
        issues = []
        metrics = {}
        recommendations = []
        
        # Find common date range
        common_dates = self._find_common_dates(provider_data)
        if len(common_dates) == 0:
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=["No overlapping dates between providers"],
                metrics={},
                recommendations=["Check date ranges and data availability"]
            )
        
        # Compare prices across providers
        price_comparison = self._compare_prices_across_providers(provider_data, common_dates)
        metrics.update(price_comparison['metrics'])
        issues.extend(price_comparison['issues'])
        recommendations.extend(price_comparison['recommendations'])
        
        # Calculate consensus metrics
        consensus_metrics = self._calculate_consensus_metrics(provider_data, common_dates)
        metrics.update(consensus_metrics)
        
        quality_score = self._calculate_cross_provider_quality_score(metrics, issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            metrics=metrics,
            recommendations=recommendations
        )
    
    def _check_completeness(self, df: pd.DataFrame) -> float:
        """Check data completeness percentage."""
        if df.empty:
            return 0.0
        
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        return ((total_cells - missing_cells) / total_cells) * 100
    
    def _check_price_consistency(self, df: pd.DataFrame) -> List[str]:
        """Check for price consistency issues."""
        issues = []
        
        if 'close' not in df.columns:
            return ["Missing close price column"]
        
        # Check for negative prices
        if (df['close'] <= 0).any():
            issues.append("Found negative or zero prices")
        
        # Check for extreme price changes
        if len(df) > 1:
            price_changes = df['close'].pct_change().abs()
            outlier_threshold = self.quality_config.get('price_change_outlier_threshold', 0.20)
            
            extreme_changes = price_changes > outlier_threshold
            if extreme_changes.any():
                count = extreme_changes.sum()
                max_change = price_changes.max()
                issues.append(f"Found {count} extreme price changes (max: {max_change:.1%})")
        
        # Check OHLC consistency
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # High should be >= Open, Close
            if ((df['high'] < df['open']) | (df['high'] < df['close'])).any():
                issues.append("High price lower than Open/Close in some records")
            
            # Low should be <= Open, Close
            if ((df['low'] > df['open']) | (df['low'] > df['close'])).any():
                issues.append("Low price higher than Open/Close in some records")
        
        return issues
    
    def _check_temporal_consistency(self, df: pd.DataFrame) -> List[str]:
        """Check for temporal consistency issues."""
        issues = []
        
        if len(df) < 2:
            return issues
        
        # Check for gaps in time series
        if hasattr(df.index, 'freq') and df.index.freq:
            expected_periods = pd.date_range(
                start=df.index[0], 
                end=df.index[-1], 
                freq=df.index.freq
            )
            missing_periods = len(expected_periods) - len(df)
            if missing_periods > 0:
                issues.append(f"Missing {missing_periods} time periods")
        
        # Check for duplicate timestamps
        if df.index.duplicated().any():
            issues.append("Found duplicate timestamps")
        
        return issues
    
    def _find_common_dates(self, provider_data: Dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
        """Find common dates across all providers."""
        date_indices = [df.index for df in provider_data.values() if not df.empty]
        
        if not date_indices:
            return pd.DatetimeIndex([])
        
        # Find intersection of all date indices
        common_dates = date_indices[0]
        for dates in date_indices[1:]:
            common_dates = common_dates.intersection(dates)
        
        return common_dates
    
    def _compare_prices_across_providers(
        self, 
        provider_data: Dict[str, pd.DataFrame], 
        common_dates: pd.DatetimeIndex
    ) -> Dict:
        """Compare prices across providers for common dates."""
        issues = []
        recommendations = []
        metrics = {}
        
        if len(common_dates) == 0:
            return {
                'issues': ["No common dates for comparison"],
                'recommendations': [],
                'metrics': {}
            }
        
        # Extract close prices for common dates
        price_data = {}
        for provider, df in provider_data.items():
            if not df.empty and 'close' in df.columns:
                common_df = df.loc[common_dates]
                price_data[provider] = common_df['close']
        
        if len(price_data) < 2:
            return {
                'issues': ["Insufficient price data for comparison"],
                'recommendations': [],
                'metrics': {}
            }
        
        # Calculate price deviations
        price_df = pd.DataFrame(price_data)
        price_mean = price_df.mean(axis=1)
        
        max_deviation = 0.0
        tolerance = self.config.get('cross_provider_tolerance', 0.02)
        
        for provider in price_df.columns:
            deviation = abs(price_df[provider] - price_mean) / price_mean
            max_provider_deviation = deviation.max()
            max_deviation = max(max_deviation, max_provider_deviation)
            
            if max_provider_deviation > tolerance:
                issues.append(f"{provider} has price deviation up to {max_provider_deviation:.1%}")
        
        metrics.update({
            'max_price_deviation': max_deviation,
            'common_dates_count': len(common_dates),
            'providers_compared': list(price_data.keys())
        })
        
        if max_deviation > tolerance:
            recommendations.append("Investigate price discrepancies between providers")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'metrics': metrics
        }
    
    def _calculate_consensus_metrics(
        self, 
        provider_data: Dict[str, pd.DataFrame], 
        common_dates: pd.DatetimeIndex
    ) -> Dict:
        """Calculate consensus metrics across providers."""
        metrics = {}
        
        # Count providers with data
        providers_with_data = sum(1 for df in provider_data.values() if not df.empty)
        metrics['providers_with_data'] = providers_with_data
        
        # Calculate data overlap percentage
        if common_dates is not None and len(common_dates) > 0:
            total_possible_dates = max(len(df) for df in provider_data.values() if not df.empty)
            overlap_percentage = (len(common_dates) / total_possible_dates) * 100
            metrics['data_overlap_percent'] = overlap_percentage
        else:
            metrics['data_overlap_percent'] = 0.0
        
        return metrics
    
    def _calculate_quality_score(self, metrics: Dict, issues: List[str]) -> float:
        """Calculate overall quality score for single provider."""
        base_score = 100.0
        
        # Deduct points for issues
        base_score -= len(issues) * 10
        
        # Adjust based on completeness
        completeness = metrics.get('completeness_percent', 100.0)
        base_score *= (completeness / 100.0)
        
        # Adjust based on duplicates
        duplicate_percent = metrics.get('duplicate_percent', 0.0)
        base_score *= (1 - duplicate_percent / 100.0)
        
        return max(0.0, min(100.0, base_score)) / 100.0
    
    def _calculate_cross_provider_quality_score(self, metrics: Dict, issues: List[str]) -> float:
        """Calculate quality score for cross-provider validation."""
        base_score = 100.0
        
        # Deduct points for issues
        base_score -= len(issues) * 15
        
        # Adjust based on data overlap
        overlap_percent = metrics.get('data_overlap_percent', 0.0)
        base_score *= (overlap_percent / 100.0)
        
        # Bonus for multiple providers
        providers_count = metrics.get('providers_with_data', 1)
        provider_bonus = min(20, (providers_count - 1) * 10)
        base_score += provider_bonus
        
        return max(0.0, min(100.0, base_score)) / 100.0
