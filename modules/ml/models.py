"""
ML Models for Stock Price Prediction

Implements XGBoost, LightGBM, and Ensemble models for binary classification:
- Target: Will stock price be higher at week-end? (1=up, 0=down)
- Features: Technical indicators, options metrics, derived features
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import xgboost as xgb
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path


class BaseModel:
    """Base class for ML models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BaseModel':
        """Train the model."""
        raise NotImplementedError
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        raise NotImplementedError
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities."""
        raise NotImplementedError
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_name': self.model_name
            }, f)
    
    def load(self, path: str) -> None:
        """Load model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.model_name = data['model_name']
            self.is_trained = True


class XGBoostModel(BaseModel):
    """XGBoost classifier for stock prediction."""
    
    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        **kwargs
    ):
        super().__init__('XGBoost')
        
        self.params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'random_state': 42,
            'n_jobs': -1,
            **kwargs
        }
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None,
        early_stopping_rounds: int = 50,
        verbose: bool = False
    ) -> 'XGBoostModel':
        """
        Train XGBoost model.
        
        Args:
            X: Feature DataFrame
            y: Target series
            eval_set: Optional validation set for early stopping
            early_stopping_rounds: Rounds without improvement before stopping
            verbose: Print training progress
            
        Returns:
            Self (trained model)
        """
        self.feature_names = X.columns.tolist()
        
        # Initialize model
        self.model = xgb.XGBClassifier(**self.params)
        
        # Fit model (simplified - no early stopping in this version)
        if eval_set:
            self.model.fit(X, y, eval_set=eval_set, verbose=verbose)
        else:
            self.model.fit(X, y, verbose=verbose)
        
        self.is_trained = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels (0 or 1)."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance scores."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance


class LightGBMModel(BaseModel):
    """LightGBM classifier for stock prediction."""
    
    def __init__(
        self,
        n_estimators: int = 200,
        num_leaves: int = 31,
        learning_rate: float = 0.05,
        feature_fraction: float = 0.8,
        bagging_fraction: float = 0.8,
        **kwargs
    ):
        super().__init__('LightGBM')
        
        self.params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'n_estimators': n_estimators,
            'num_leaves': num_leaves,
            'learning_rate': learning_rate,
            'feature_fraction': feature_fraction,
            'bagging_fraction': bagging_fraction,
            'bagging_freq': 5,
            'random_state': 42,
            'n_jobs': -1,
            'verbose': -1,
            **kwargs
        }
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None,
        early_stopping_rounds: int = 50,
        verbose: bool = False
    ) -> 'LightGBMModel':
        """
        Train LightGBM model.
        
        Args:
            X: Feature DataFrame
            y: Target series
            eval_set: Optional validation set for early stopping
            early_stopping_rounds: Rounds without improvement before stopping
            verbose: Print training progress
            
        Returns:
            Self (trained model)
        """
        self.feature_names = X.columns.tolist()
        
        # Initialize model
        self.model = lgb.LGBMClassifier(**self.params)
        
        # Prepare evaluation set
        eval_set_scaled = None
        if eval_set:
            eval_set_scaled = [
                (X_val, y_val)
                for X_val, y_val in eval_set
            ]
        
        # Fit model
        self.model.fit(
            X, y,
            eval_set=eval_set_scaled,
            callbacks=[
                lgb.early_stopping(early_stopping_rounds) if eval_set else None,
                lgb.log_evaluation(period=100 if verbose else 0)
            ]
        )
        
        self.is_trained = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels (0 or 1)."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance scores."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance


class EnsembleModel(BaseModel):
    """
    Ensemble model combining XGBoost and LightGBM predictions.
    
    Uses a logistic regression meta-learner to combine base model predictions.
    """
    
    def __init__(
        self,
        base_models: Optional[List[BaseModel]] = None
    ):
        super().__init__('Ensemble')
        
        if base_models:
            self.base_models = base_models
        else:
            # Default: XGBoost + LightGBM
            self.base_models = [
                XGBoostModel(),
                LightGBMModel()
            ]
        
        # Meta-learner (logistic regression)
        self.meta_learner = LogisticRegression(
            random_state=42,
            max_iter=1000
        )
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None,
        verbose: bool = False
    ) -> 'EnsembleModel':
        """
        Train ensemble model.
        
        Steps:
        1. Train each base model
        2. Generate meta-features (base model predictions)
        3. Train meta-learner on meta-features
        
        Args:
            X: Feature DataFrame
            y: Target series
            eval_set: Optional validation set
            verbose: Print training progress
            
        Returns:
            Self (trained model)
        """
        self.feature_names = X.columns.tolist()
        
        # Step 1: Train base models
        print(f"\n🔨 Training {len(self.base_models)} base models...")
        for i, model in enumerate(self.base_models, 1):
            print(f"  [{i}/{len(self.base_models)}] Training {model.model_name}...")
            model.fit(X, y, eval_set=eval_set, verbose=verbose)
        
        # Step 2: Generate meta-features
        print(f"\n🔀 Generating meta-features...")
        meta_features = self._generate_meta_features(X)
        
        # Step 3: Train meta-learner
        print(f"\n🎯 Training meta-learner...")
        self.meta_learner.fit(meta_features, y)
        
        self.is_trained = True
        print(f"✅ Ensemble model trained successfully")
        
        return self
    
    def _generate_meta_features(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate meta-features from base model predictions.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of shape (n_samples, n_base_models * 2)
            For each base model: [prob_class_0, prob_class_1]
        """
        meta_features_list = []
        
        for model in self.base_models:
            # Get probability predictions from each base model
            proba = model.predict_proba(X)
            meta_features_list.append(proba)
        
        # Concatenate all base model predictions
        meta_features = np.hstack(meta_features_list)
        
        return meta_features
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels using ensemble."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        meta_features = self._generate_meta_features(X)
        return self.meta_learner.predict(meta_features)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities using ensemble."""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        meta_features = self._generate_meta_features(X)
        return self.meta_learner.predict_proba(meta_features)
    
    def get_base_model_predictions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get predictions from each base model.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Dictionary mapping model names to probability predictions
        """
        predictions = {}
        
        for model in self.base_models:
            proba = model.predict_proba(X)
            predictions[model.model_name] = proba[:, 1]  # Probability of class 1
        
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get aggregated feature importance from base models.
        
        Returns:
            DataFrame with average importance across base models
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        importance_dfs = []
        
        for model in self.base_models:
            if hasattr(model, 'get_feature_importance'):
                imp = model.get_feature_importance()
                imp = imp.rename(columns={'importance': f'importance_{model.model_name}'})
                importance_dfs.append(imp)
        
        # Merge all importance DataFrames
        combined = importance_dfs[0]
        for imp_df in importance_dfs[1:]:
            combined = combined.merge(imp_df, on='feature', how='outer')
        
        # Calculate average importance
        importance_cols = [col for col in combined.columns if col.startswith('importance_')]
        combined['importance_avg'] = combined[importance_cols].mean(axis=1)
        combined = combined.sort_values('importance_avg', ascending=False)
        
        return combined
    
    def save(self, path: str) -> None:
        """Save ensemble model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save base models
        base_model_paths = []
        for i, model in enumerate(self.base_models):
            base_path = str(Path(path).parent / f"{Path(path).stem}_base_{i}.pkl")
            model.save(base_path)
            base_model_paths.append(base_path)
        
        # Save ensemble metadata and meta-learner
        with open(path, 'wb') as f:
            pickle.dump({
                'model_name': self.model_name,
                'meta_learner': self.meta_learner,
                'feature_names': self.feature_names,
                'base_model_paths': base_model_paths,
                'base_model_classes': [type(m).__name__ for m in self.base_models]
            }, f)
    
    def load(self, path: str) -> None:
        """Load ensemble model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            
            self.model_name = data['model_name']
            self.meta_learner = data['meta_learner']
            self.feature_names = data['feature_names']
            
            # Load base models
            self.base_models = []
            for base_path, model_class_name in zip(
                data['base_model_paths'],
                data['base_model_classes']
            ):
                # Instantiate the appropriate model class
                if model_class_name == 'XGBoostModel':
                    model = XGBoostModel()
                elif model_class_name == 'LightGBMModel':
                    model = LightGBMModel()
                else:
                    raise ValueError(f"Unknown model class: {model_class_name}")
                
                model.load(base_path)
                self.base_models.append(model)
            
            self.is_trained = True
