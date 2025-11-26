"""
ML Prediction Engine

Generates predictions for stock movements using trained models.
Provides confidence scoring and ensemble agreement metrics.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import pickle

from .models import BaseModel, XGBoostModel, LightGBMModel, EnsembleModel

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Handles prediction generation for stock movements.
    
    Features:
    - Load trained models
    - Generate predictions with confidence scores
    - Multi-model ensemble predictions
    - Prediction persistence to database
    - Historical prediction tracking
    """
    
    def __init__(
        self,
        db_path: str = "data/duckdb/economic_dashboard.duckdb",
        models_dir: str = "data/models"
    ):
        """
        Initialize the prediction engine.
        
        Args:
            db_path: Path to DuckDB database
            models_dir: Directory containing trained models
        """
        self.db_path = db_path
        self.models_dir = Path(models_dir)
        self.loaded_models: Dict[str, BaseModel] = {}
        
    def load_model(self, model_path: str, cache_key: Optional[str] = None) -> BaseModel:
        """
        Load a trained model from disk.
        
        Args:
            model_path: Path to saved model file
            cache_key: Optional key to cache the model
            
        Returns:
            Loaded model instance
        """
        if cache_key and cache_key in self.loaded_models:
            logger.info(f"Using cached model: {cache_key}")
            return self.loaded_models[cache_key]
        
        logger.info(f"Loading model from {model_path}")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        if cache_key:
            self.loaded_models[cache_key] = model
        
        return model
    
    def get_latest_features(
        self,
        ticker: str,
        as_of_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get the latest feature values for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            as_of_date: Optional date to get features as of (YYYY-MM-DD)
            
        Returns:
            DataFrame with latest features (single row)
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        
        try:
            # Build query to get latest features
            date_filter = f"AND date <= '{as_of_date}'" if as_of_date else ""
            
            query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date
                FROM technical_features
                WHERE ticker = '{ticker}'
                {date_filter}
            ),
            combined_features AS (
                SELECT 
                    t.date,
                    t.ticker,
                    t.*,
                    d.*,
                    o.pcr_volume,
                    o.pcr_open_interest,
                    o.iv_rank,
                    o.iv_percentile,
                    o.iv_skew
                FROM technical_features t
                CROSS JOIN latest_date ld
                LEFT JOIN derived_features d
                    ON t.ticker = d.ticker AND t.date = d.date
                LEFT JOIN options_data o
                    ON t.ticker = o.ticker AND t.date = o.date
                WHERE t.ticker = '{ticker}'
                AND t.date = ld.max_date
            )
            SELECT * FROM combined_features
            """
            
            df = conn.execute(query).df()
            
            if df.empty:
                raise ValueError(f"No features found for {ticker}")
            
            # Drop non-feature columns
            feature_cols = df.columns.difference(['date', 'ticker'])
            X = df[feature_cols].copy()
            
            # Handle missing values
            X = X.fillna(X.median())
            
            logger.info(f"Retrieved features for {ticker} as of {df['date'].iloc[0]}")
            
            return X
            
        finally:
            conn.close()
    
    def predict(
        self,
        ticker: str,
        model_path: Optional[str] = None,
        model_type: str = 'ensemble',
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate prediction for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            model_path: Path to trained model (auto-detected if None)
            model_type: Type of model if auto-detecting
            as_of_date: Date to generate prediction as of
            
        Returns:
            Dictionary with prediction results
        """
        # Auto-detect model path if not provided
        if model_path is None:
            pattern = f"{ticker}_{model_type}_*.pkl"
            model_files = list(self.models_dir.glob(pattern))
            
            if not model_files:
                raise FileNotFoundError(f"No trained model found for {ticker} ({model_type})")
            
            # Use most recent model
            model_path = str(sorted(model_files)[-1])
            logger.info(f"Auto-selected model: {model_path}")
        
        # Load model
        cache_key = f"{ticker}_{model_type}"
        model = self.load_model(model_path, cache_key)
        
        # Get latest features
        X = self.get_latest_features(ticker, as_of_date)
        
        # Generate prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        # Calculate confidence (max probability)
        confidence = float(max(probabilities))
        
        # Get feature importance if available
        feature_importance = None
        try:
            importance = model.get_feature_importance()
            if importance is not None:
                # Get top 10 features
                top_features = sorted(
                    importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                feature_importance = dict(top_features)
        except Exception as e:
            logger.warning(f"Could not get feature importance: {e}")
        
        result = {
            'ticker': ticker,
            'prediction': int(prediction),
            'prediction_label': 'UP' if prediction == 1 else 'DOWN',
            'probability_down': float(probabilities[0]),
            'probability_up': float(probabilities[1]),
            'confidence': confidence,
            'model_type': model_type,
            'model_path': model_path,
            'prediction_date': datetime.now().isoformat(),
            'as_of_date': as_of_date or datetime.now().date().isoformat(),
            'feature_importance': feature_importance
        }
        
        logger.info(f"{ticker} prediction: {result['prediction_label']} "
                   f"(confidence: {confidence:.2%})")
        
        return result
    
    def predict_ensemble(
        self,
        ticker: str,
        model_types: List[str] = ['xgboost', 'lightgbm', 'ensemble'],
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate predictions using multiple models and combine results.
        
        Args:
            ticker: Stock ticker symbol
            model_types: List of model types to use
            as_of_date: Date to generate prediction as of
            
        Returns:
            Dictionary with ensemble prediction results
        """
        predictions = []
        model_results = {}
        
        for model_type in model_types:
            try:
                result = self.predict(ticker, model_type=model_type, as_of_date=as_of_date)
                predictions.append(result)
                model_results[model_type] = result
            except Exception as e:
                logger.error(f"Error getting prediction from {model_type}: {e}")
        
        if not predictions:
            raise ValueError(f"No predictions available for {ticker}")
        
        # Calculate ensemble metrics
        avg_prob_up = np.mean([p['probability_up'] for p in predictions])
        avg_prob_down = np.mean([p['probability_down'] for p in predictions])
        
        # Majority vote
        votes_up = sum(1 for p in predictions if p['prediction'] == 1)
        votes_down = len(predictions) - votes_up
        
        ensemble_prediction = 1 if votes_up > votes_down else 0
        
        # Agreement score (proportion of models that agree)
        agreement = max(votes_up, votes_down) / len(predictions)
        
        result = {
            'ticker': ticker,
            'ensemble_prediction': ensemble_prediction,
            'ensemble_label': 'UP' if ensemble_prediction == 1 else 'DOWN',
            'avg_probability_up': float(avg_prob_up),
            'avg_probability_down': float(avg_prob_down),
            'votes_up': votes_up,
            'votes_down': votes_down,
            'agreement_score': float(agreement),
            'num_models': len(predictions),
            'model_predictions': model_results,
            'prediction_date': datetime.now().isoformat(),
            'as_of_date': as_of_date or datetime.now().date().isoformat()
        }
        
        logger.info(f"{ticker} ensemble: {result['ensemble_label']} "
                   f"(agreement: {agreement:.2%}, {votes_up}/{len(predictions)} models)")
        
        return result
    
    def save_prediction(self, prediction: Dict[str, Any]) -> None:
        """
        Save prediction to database.
        
        Args:
            prediction: Prediction dictionary from predict() or predict_ensemble()
        """
        conn = duckdb.connect(self.db_path)
        
        try:
            # Determine if this is ensemble or single model prediction
            is_ensemble = 'ensemble_prediction' in prediction
            
            if is_ensemble:
                # Save ensemble prediction
                query = """
                INSERT INTO ml_predictions (
                    ticker, date, prediction_type, prediction,
                    probability_up, probability_down, confidence,
                    model_agreement, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    prediction['ticker'],
                    prediction['as_of_date'],
                    'ensemble',
                    prediction['ensemble_prediction'],
                    prediction['avg_probability_up'],
                    prediction['avg_probability_down'],
                    prediction['agreement_score'],
                    prediction['agreement_score'],
                    str(prediction['model_predictions']),
                    prediction['prediction_date']
                )
            else:
                # Save single model prediction
                query = """
                INSERT INTO ml_predictions (
                    ticker, date, prediction_type, prediction,
                    probability_up, probability_down, confidence,
                    model_path, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    prediction['ticker'],
                    prediction['as_of_date'],
                    prediction['model_type'],
                    prediction['prediction'],
                    prediction['probability_up'],
                    prediction['probability_down'],
                    prediction['confidence'],
                    prediction['model_path'],
                    str(prediction.get('feature_importance', {})),
                    prediction['prediction_date']
                )
            
            conn.execute(query, params)
            conn.commit()
            
            logger.info(f"Saved prediction for {prediction['ticker']} to database")
            
        finally:
            conn.close()
    
    def batch_predict(
        self,
        tickers: List[str],
        use_ensemble: bool = True,
        save_to_db: bool = True,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate predictions for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            use_ensemble: Whether to use ensemble predictions
            save_to_db: Whether to save predictions to database
            **kwargs: Additional arguments for predict/predict_ensemble
            
        Returns:
            Dictionary mapping tickers to prediction results
        """
        results = {}
        
        for ticker in tickers:
            try:
                logger.info(f"Generating prediction for {ticker}")
                
                if use_ensemble:
                    prediction = self.predict_ensemble(ticker, **kwargs)
                else:
                    prediction = self.predict(ticker, **kwargs)
                
                results[ticker] = prediction
                
                if save_to_db:
                    self.save_prediction(prediction)
                    
            except Exception as e:
                logger.error(f"Error predicting {ticker}: {e}")
                results[ticker] = {'error': str(e)}
        
        return results
    
    def get_historical_predictions(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        prediction_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical predictions for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            prediction_type: Filter by prediction type
            
        Returns:
            DataFrame with historical predictions
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        
        try:
            query = f"""
            SELECT *
            FROM ml_predictions
            WHERE ticker = '{ticker}'
            """
            
            if start_date:
                query += f" AND date >= '{start_date}'"
            if end_date:
                query += f" AND date <= '{end_date}'"
            if prediction_type:
                query += f" AND prediction_type = '{prediction_type}'"
            
            query += " ORDER BY date DESC"
            
            df = conn.execute(query).df()
            
            return df
            
        finally:
            conn.close()
