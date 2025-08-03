"""Feature processing pipeline combining OpenBB and custom features."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .openbb_technical import OpenBBTechnicalFeatures
from .custom_features import CustomFeatureEngineer
from ..utils.openbb_helpers import OpenBBHelpers

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """Complete feature engineering pipeline for cryptocurrency trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the feature pipeline.
        
        Args:
            config: Configuration dictionary for feature engineering
        """
        self.config = config or self._get_default_config()
        
        # Initialize feature engineers
        self.openbb_features = OpenBBTechnicalFeatures(self.config.get('openbb', {}))
        self.custom_features = CustomFeatureEngineer(self.config.get('custom', {}))
        
        # Feature selection configuration
        self.feature_groups = self.config.get('feature_groups', {
            'core': True,
            'extended': True,
            'custom': True,
            'time': True
        })
        
        self.max_features = self.config.get('max_features', None)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for feature pipeline."""
        return {
            'openbb': {
                'indicators': {
                    'sma': {'periods': [20, 50, 200]},
                    'ema': {'periods': [12, 26, 50]},
                    'rsi': {'period': 14},
                    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                    'bbands': {'period': 20, 'std': 2},
                    'atr': {'period': 14}
                }
            },
            'custom': {
                'volatility_periods': [5, 10, 20, 50],
                'momentum_periods': [5, 10, 20, 50],
                'volume_periods': [5, 10, 20, 50]
            },
            'feature_groups': {
                'core': True,
                'extended': True,
                'custom': True,
                'time': True
            },
            'preprocessing': {
                'fill_method': 'forward',
                'normalize': False,
                'remove_outliers': True,
                'outlier_threshold': 3.0
            }
        }
    
    def process_features(
        self,
        data: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process all features through the complete pipeline.
        
        Args:
            data: Raw OHLCV DataFrame
            target_column: Optional target column name for supervised learning
            
        Returns:
            Tuple of (processed_features_df, metadata_dict)
        """
        logger.info("Starting feature processing pipeline...")
        
        # Validate input data
        self._validate_input_data(data)
        
        # Initialize processing metadata
        metadata = {
            'input_shape': data.shape,
            'processing_timestamp': datetime.now(),
            'feature_groups_used': [],
            'total_features_created': 0,
            'processing_steps': []
        }
        
        # Start with original data
        df = data.copy()
        original_columns = set(df.columns)
        
        # Step 1: OpenBB Technical Indicators
        if self.feature_groups.get('core', True) or self.feature_groups.get('extended', True):
            logger.info("Adding OpenBB technical indicators...")
            df = self.openbb_features.add_all_indicators(df)
            metadata['feature_groups_used'].append('openbb_technical')
            metadata['processing_steps'].append('openbb_technical_indicators')
        
        # Step 2: Custom Features
        if self.feature_groups.get('custom', True):
            logger.info("Adding custom features...")
            df = self.custom_features.add_all_custom_features(df)
            metadata['feature_groups_used'].append('custom_features')
            metadata['processing_steps'].append('custom_features')
        
        # Step 3: Feature Selection (if max_features is specified)
        if self.max_features and len(df.columns) > self.max_features:
            logger.info(f"Selecting top {self.max_features} features...")
            df, feature_importance = self._select_features(df, target_column)
            metadata['feature_selection'] = feature_importance
            metadata['processing_steps'].append('feature_selection')
        
        # Step 4: Preprocessing
        logger.info("Applying preprocessing...")
        df = self._preprocess_features(df)
        metadata['processing_steps'].append('preprocessing')
        
        # Update metadata
        new_columns = set(df.columns) - original_columns
        metadata['total_features_created'] = len(new_columns)
        metadata['output_shape'] = df.shape
        metadata['new_features'] = list(new_columns)
        
        logger.info(f"Feature pipeline completed: {metadata['input_shape']} -> {metadata['output_shape']}")
        
        return df, metadata
    
    def _validate_input_data(self, data: pd.DataFrame):
        """Validate input data format and requirements."""
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        if data.empty:
            raise ValueError("Input data is empty")
        
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.warning("Index is not DatetimeIndex, some time-based features may not work correctly")
    
    def _select_features(
        self,
        data: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Select most important features using various methods.
        
        Args:
            data: DataFrame with all features
            target_column: Target column for supervised feature selection
            
        Returns:
            Tuple of (selected_features_df, feature_importance_dict)
        """
        from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
        from sklearn.ensemble import RandomForestRegressor
        
        # Separate features from target
        feature_columns = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        if target_column and target_column in data.columns:
            # Supervised feature selection
            X = data[feature_columns].fillna(0)
            y = data[target_column].fillna(0)
            
            # Remove rows where target is NaN
            valid_idx = ~y.isna()
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) > 0:
                # Random Forest feature importance
                rf = RandomForestRegressor(n_estimators=100, random_state=42)
                rf.fit(X, y)
                
                feature_importance = dict(zip(feature_columns, rf.feature_importances_))
                
                # Select top features
                top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                selected_features = [feat[0] for feat in top_features[:self.max_features]]
                
                # Keep original OHLCV columns
                final_columns = ['open', 'high', 'low', 'close', 'volume'] + selected_features
                final_columns = [col for col in final_columns if col in data.columns]
                
                return data[final_columns], feature_importance
        
        # Unsupervised feature selection (variance-based)
        logger.info("Using variance-based feature selection")
        
        X = data[feature_columns].fillna(0)
        
        # Calculate variance for each feature
        variances = X.var()
        
        # Select features with highest variance
        top_variance_features = variances.nlargest(self.max_features).index.tolist()
        
        # Keep original OHLCV columns
        final_columns = ['open', 'high', 'low', 'close', 'volume'] + top_variance_features
        final_columns = [col for col in final_columns if col in data.columns]
        
        feature_importance = variances.to_dict()
        
        return data[final_columns], feature_importance
    
    def _preprocess_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing steps to features.
        
        Args:
            data: DataFrame with features
            
        Returns:
            Preprocessed DataFrame
        """
        df = data.copy()
        preprocessing_config = self.config.get('preprocessing', {})
        
        # Handle missing values
        fill_method = preprocessing_config.get('fill_method', 'forward')
        if fill_method == 'forward':
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif fill_method == 'backward':
            df = df.fillna(method='bfill').fillna(method='ffill')
        elif fill_method == 'zero':
            df = df.fillna(0)
        elif fill_method == 'mean':
            df = df.fillna(df.mean())
        
        # Remove outliers
        if preprocessing_config.get('remove_outliers', True):
            threshold = preprocessing_config.get('outlier_threshold', 3.0)
            df = self._remove_outliers(df, threshold)
        
        # Normalize features
        if preprocessing_config.get('normalize', False):
            df = self._normalize_features(df)
        
        return df
    
    def _remove_outliers(self, data: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """Remove outliers using z-score method.
        
        Args:
            data: Input DataFrame
            threshold: Z-score threshold for outlier detection
            
        Returns:
            DataFrame with outliers removed
        """
        df = data.copy()
        
        # Only apply to numeric columns (exclude OHLCV)
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        feature_columns = [col for col in numeric_columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        for col in feature_columns:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df.loc[z_scores > threshold, col] = df[col].median()
        
        return df
    
    def _normalize_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize features using min-max scaling.
        
        Args:
            data: Input DataFrame
            
        Returns:
            DataFrame with normalized features
        """
        from sklearn.preprocessing import MinMaxScaler
        
        df = data.copy()
        
        # Only normalize feature columns (not OHLCV)
        feature_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        if feature_columns:
            scaler = MinMaxScaler()
            df[feature_columns] = scaler.fit_transform(df[feature_columns])
        
        return df
    
    def get_feature_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of processed features.
        
        Args:
            data: Processed features DataFrame
            
        Returns:
            Dictionary with feature summary statistics
        """
        summary = {
            'total_features': len(data.columns),
            'total_samples': len(data),
            'missing_values': data.isnull().sum().sum(),
            'feature_types': {},
            'feature_groups': {}
        }
        
        # Categorize features by type
        for col in data.columns:
            if col in ['open', 'high', 'low', 'close', 'volume']:
                summary['feature_types'][col] = 'price_volume'
            elif any(indicator in col for indicator in ['sma', 'ema', 'rsi', 'macd', 'bb']):
                summary['feature_types'][col] = 'technical_indicator'
            elif any(pattern in col for pattern in ['returns', 'volatility', 'momentum']):
                summary['feature_types'][col] = 'custom_feature'
            elif any(time_feat in col for time_feat in ['hour', 'day', 'month', 'session']):
                summary['feature_types'][col] = 'time_feature'
            else:
                summary['feature_types'][col] = 'other'
        
        # Count features by group
        for feature_type in ['price_volume', 'technical_indicator', 'custom_feature', 'time_feature', 'other']:
            count = sum(1 for ft in summary['feature_types'].values() if ft == feature_type)
            summary['feature_groups'][feature_type] = count
        
        return summary
