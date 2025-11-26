"""
ML Model Evaluation Module

Provides comprehensive evaluation metrics and performance analysis for ML models.
Includes financial metrics and prediction quality assessment.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
    log_loss
)
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Handles comprehensive model evaluation and performance analysis.
    
    Features:
    - Classification metrics (accuracy, precision, recall, F1, ROC-AUC)
    - Financial metrics (win rate, Sharpe ratio, returns)
    - Confusion matrix and classification reports
    - ROC curves and calibration plots
    - Prediction quality over time
    """
    
    def __init__(self, db_path: str = "data/duckdb/economic_dashboard.duckdb"):
        """
        Initialize the model evaluator.
        
        Args:
            db_path: Path to DuckDB database
        """
        self.db_path = db_path
        
    def evaluate_predictions(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Calculate comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (for ROC-AUC, log loss)
            
        Returns:
            Dictionary of evaluation metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'support': len(y_true)
        }
        
        # Add probabilistic metrics if probabilities provided
        if y_proba is not None and len(np.unique(y_true)) > 1:
            try:
                # For binary classification, use positive class probabilities
                if y_proba.ndim > 1:
                    y_proba_positive = y_proba[:, 1]
                else:
                    y_proba_positive = y_proba
                
                metrics['roc_auc'] = roc_auc_score(y_true, y_proba_positive)
                metrics['log_loss'] = log_loss(y_true, y_proba)
            except Exception as e:
                logger.warning(f"Could not calculate probabilistic metrics: {e}")
                metrics['roc_auc'] = 0.0
                metrics['log_loss'] = 0.0
        
        return metrics
    
    def get_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Calculate confusion matrix and extract key values.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Tuple of (confusion matrix, dictionary of TN/FP/FN/TP)
        """
        cm = confusion_matrix(y_true, y_pred)
        
        # Extract values (assuming binary classification)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            cm_dict = {
                'true_negatives': int(tn),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp)
            }
        else:
            cm_dict = {}
        
        return cm, cm_dict
    
    def calculate_financial_metrics(
        self,
        predictions_df: pd.DataFrame,
        actual_returns: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate financial performance metrics.
        
        Assumes predictions_df has 'prediction' column (1=up, 0=down)
        and actual_returns are the realized returns.
        
        Args:
            predictions_df: DataFrame with predictions
            actual_returns: Series of actual returns
            
        Returns:
            Dictionary of financial metrics
        """
        # Align predictions with returns
        aligned_df = predictions_df.copy()
        aligned_df['actual_return'] = actual_returns
        aligned_df = aligned_df.dropna()
        
        if len(aligned_df) == 0:
            return {
                'win_rate': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0,
                'total_return': 0.0,
                'num_trades': 0
            }
        
        # Calculate strategy returns (go long if prediction=1, cash if prediction=0)
        aligned_df['strategy_return'] = aligned_df['actual_return'] * aligned_df['prediction']
        
        # Win rate: proportion of correct directional predictions
        aligned_df['correct'] = (
            ((aligned_df['prediction'] == 1) & (aligned_df['actual_return'] > 0)) |
            ((aligned_df['prediction'] == 0) & (aligned_df['actual_return'] <= 0))
        )
        win_rate = aligned_df['correct'].mean()
        
        # Average return per trade
        avg_return = aligned_df['strategy_return'].mean()
        
        # Sharpe ratio (assuming 252 trading days, 0% risk-free rate)
        returns_std = aligned_df['strategy_return'].std()
        sharpe_ratio = (avg_return / returns_std * np.sqrt(252)) if returns_std > 0 else 0.0
        
        # Total cumulative return
        total_return = (1 + aligned_df['strategy_return']).prod() - 1
        
        metrics = {
            'win_rate': float(win_rate),
            'avg_return': float(avg_return),
            'sharpe_ratio': float(sharpe_ratio),
            'total_return': float(total_return),
            'num_trades': len(aligned_df)
        }
        
        return metrics
    
    def evaluate_model_predictions(
        self,
        ticker: str,
        prediction_type: str = 'ensemble',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate historical predictions for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            prediction_type: Type of predictions to evaluate
            start_date: Start date for evaluation period
            end_date: End date for evaluation period
            
        Returns:
            Dictionary with comprehensive evaluation results
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        
        try:
            # Get predictions and actual outcomes
            query = f"""
            WITH predictions AS (
                SELECT
                    p.ticker,
                    p.date as prediction_date,
                    p.prediction,
                    p.probability_up,
                    p.probability_down,
                    p.confidence
                FROM ml_predictions p
                WHERE p.ticker = '{ticker}'
                AND p.prediction_type = '{prediction_type}'
            ),
            outcomes AS (
                SELECT
                    ticker,
                    date,
                    close,
                    LEAD(close, 5) OVER (PARTITION BY ticker ORDER BY date) as future_close
                FROM yfinance_ohlcv
                WHERE ticker = '{ticker}'
            ),
            combined AS (
                SELECT
                    p.*,
                    o.close as price_at_prediction,
                    o.future_close,
                    CASE
                        WHEN o.future_close > o.close THEN 1
                        ELSE 0
                    END as actual_outcome,
                    (o.future_close - o.close) / o.close as actual_return
                FROM predictions p
                JOIN outcomes o ON p.ticker = o.ticker AND p.prediction_date = o.date
                WHERE o.future_close IS NOT NULL
            )
            SELECT * FROM combined
            """
            
            if start_date:
                query += f" WHERE prediction_date >= '{start_date}'"
            if end_date:
                conjunction = "AND" if start_date else "WHERE"
                query += f" {conjunction} prediction_date <= '{end_date}'"
            
            query += " ORDER BY prediction_date"
            
            df = conn.execute(query).df()
            
            if df.empty:
                raise ValueError(f"No predictions found for {ticker} ({prediction_type})")
            
            # Calculate classification metrics
            y_true = df['actual_outcome'].values
            y_pred = df['prediction'].values
            y_proba = df[['probability_down', 'probability_up']].values
            
            classification_metrics = self.evaluate_predictions(y_true, y_pred, y_proba)
            
            # Get confusion matrix
            cm, cm_dict = self.get_confusion_matrix(y_true, y_pred)
            
            # Calculate financial metrics
            financial_metrics = self.calculate_financial_metrics(
                df[['prediction']],
                df['actual_return']
            )
            
            # Prediction quality over time
            df['correct'] = (df['prediction'] == df['actual_outcome']).astype(int)
            
            # Rolling accuracy (30-day window)
            if len(df) >= 30:
                df['rolling_accuracy'] = df['correct'].rolling(window=30, min_periods=10).mean()
            
            results = {
                'ticker': ticker,
                'prediction_type': prediction_type,
                'evaluation_period': {
                    'start': df['prediction_date'].min().isoformat() if hasattr(df['prediction_date'].min(), 'isoformat') else str(df['prediction_date'].min()),
                    'end': df['prediction_date'].max().isoformat() if hasattr(df['prediction_date'].max(), 'isoformat') else str(df['prediction_date'].max()),
                    'num_predictions': len(df)
                },
                'classification_metrics': classification_metrics,
                'confusion_matrix': cm_dict,
                'financial_metrics': financial_metrics,
                'predictions_df': df
            }
            
            logger.info(f"Evaluation for {ticker}: Accuracy={classification_metrics['accuracy']:.2%}, "
                       f"Win Rate={financial_metrics['win_rate']:.2%}, "
                       f"Sharpe={financial_metrics['sharpe_ratio']:.2f}")
            
            return results
            
        finally:
            conn.close()
    
    def generate_classification_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        target_names: List[str] = ['DOWN', 'UP']
    ) -> str:
        """
        Generate detailed classification report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            target_names: Names for classes
            
        Returns:
            Formatted classification report string
        """
        return classification_report(
            y_true,
            y_pred,
            target_names=target_names,
            zero_division=0
        )
    
    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        title: str = "ROC Curve",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot ROC curve.
        
        Args:
            y_true: True labels
            y_proba: Predicted probabilities for positive class
            title: Plot title
            save_path: Optional path to save plot
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_proba)
        roc_auc = roc_auc_score(y_true, y_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(title)
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"ROC curve saved to {save_path}")
        
        plt.close()
    
    def plot_confusion_matrix(
        self,
        cm: np.ndarray,
        labels: List[str] = ['DOWN', 'UP'],
        title: str = "Confusion Matrix",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot confusion matrix heatmap.
        
        Args:
            cm: Confusion matrix
            labels: Class labels
            title: Plot title
            save_path: Optional path to save plot
        """
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=labels,
            yticklabels=labels,
            cbar_kws={'label': 'Count'}
        )
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.title(title)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Confusion matrix saved to {save_path}")
        
        plt.close()
    
    def plot_prediction_timeline(
        self,
        predictions_df: pd.DataFrame,
        title: str = "Prediction Accuracy Over Time",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot prediction accuracy timeline.
        
        Args:
            predictions_df: DataFrame with predictions and outcomes
            title: Plot title
            save_path: Optional path to save plot
        """
        if 'rolling_accuracy' not in predictions_df.columns:
            logger.warning("No rolling_accuracy column found")
            return
        
        plt.figure(figsize=(12, 6))
        plt.plot(
            predictions_df['prediction_date'],
            predictions_df['rolling_accuracy'],
            label='30-day Rolling Accuracy',
            linewidth=2
        )
        plt.axhline(y=0.5, color='r', linestyle='--', label='Random (50%)', alpha=0.7)
        plt.xlabel('Date')
        plt.ylabel('Accuracy')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Timeline plot saved to {save_path}")
        
        plt.close()
    
    def compare_models(
        self,
        ticker: str,
        model_types: List[str] = ['xgboost', 'lightgbm', 'ensemble'],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Compare performance of different models.
        
        Args:
            ticker: Stock ticker symbol
            model_types: List of model types to compare
            start_date: Start date for comparison
            end_date: End date for comparison
            
        Returns:
            DataFrame with comparison metrics
        """
        results = []
        
        for model_type in model_types:
            try:
                eval_results = self.evaluate_model_predictions(
                    ticker, model_type, start_date, end_date
                )
                
                row = {
                    'model_type': model_type,
                    'num_predictions': eval_results['evaluation_period']['num_predictions'],
                    **eval_results['classification_metrics'],
                    **eval_results['financial_metrics']
                }
                
                results.append(row)
                
            except Exception as e:
                logger.error(f"Error evaluating {model_type}: {e}")
        
        comparison_df = pd.DataFrame(results)
        
        if not comparison_df.empty:
            # Sort by F1 score (or another metric)
            comparison_df = comparison_df.sort_values('f1', ascending=False)
            logger.info(f"Model comparison completed for {ticker}")
        
        return comparison_df
    
    def generate_evaluation_report(
        self,
        ticker: str,
        prediction_type: str = 'ensemble',
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report with plots.
        
        Args:
            ticker: Stock ticker symbol
            prediction_type: Type of predictions to evaluate
            output_dir: Directory to save plots
            
        Returns:
            Dictionary with evaluation results and plot paths
        """
        # Evaluate predictions
        results = self.evaluate_model_predictions(ticker, prediction_type)
        
        # Generate classification report
        df = results['predictions_df']
        y_true = df['actual_outcome'].values
        y_pred = df['prediction'].values
        
        results['classification_report'] = self.generate_classification_report(y_true, y_pred)
        
        # Generate plots if output directory provided
        if output_dir:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            # ROC curve
            y_proba = df['probability_up'].values
            roc_path = os.path.join(output_dir, f'{ticker}_{prediction_type}_roc.png')
            self.plot_roc_curve(y_true, y_proba, f"ROC Curve - {ticker}", roc_path)
            results['roc_plot'] = roc_path
            
            # Confusion matrix
            cm, _ = self.get_confusion_matrix(y_true, y_pred)
            cm_path = os.path.join(output_dir, f'{ticker}_{prediction_type}_cm.png')
            self.plot_confusion_matrix(cm, title=f"Confusion Matrix - {ticker}", save_path=cm_path)
            results['cm_plot'] = cm_path
            
            # Timeline
            if 'rolling_accuracy' in df.columns:
                timeline_path = os.path.join(output_dir, f'{ticker}_{prediction_type}_timeline.png')
                self.plot_prediction_timeline(
                    df,
                    f"Prediction Accuracy - {ticker}",
                    timeline_path
                )
                results['timeline_plot'] = timeline_path
        
        logger.info(f"Evaluation report generated for {ticker}")
        
        return results
