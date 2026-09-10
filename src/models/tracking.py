"""
MLflow Experiment Tracking and Artifact Persistence Module for Lakers in 5.
"""

from typing import Dict, Any, Optional, List
import os
import pandas as pd
import numpy as np
import mlflow
from src.utils.logging import logger

class ExperimentTracker:
    """
    Manages experiment tracking via MLflow and persists evaluation tables.
    """
    def __init__(
        self,
        experiment_name: str = "lakers_in_5_phase3",
        tracking_uri: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = output_dir or os.path.join(base_dir, "data", "evaluation")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure MLflow tracking with robust SQLite backend
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
        
        db_path = os.path.join(self.output_dir, "mlflow.db")
        db_uri = f"sqlite:///{os.path.abspath(db_path).replace(os.sep, '/')}"
        self.tracking_uri = tracking_uri or db_uri
        
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow tracking initialized: experiment='{experiment_name}', uri='{self.tracking_uri}'")

    def log_model_run(
        self,
        run_name: str,
        task_type: str,
        params: Dict[str, Any],
        cv_metrics_df: pd.DataFrame,
        test_metrics: Optional[Dict[str, float]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Logs a full model run with CV metrics and optional final test metrics to MLflow.
        """
        with mlflow.start_run(run_name=run_name):
            # 1. Log tags
            mlflow.set_tag("task_type", task_type)
            if tags:
                for k, v in tags.items():
                    mlflow.set_tag(k, v)
                    
            # 2. Log parameters
            for param_key, param_val in params.items():
                mlflow.log_param(param_key, param_val)
                
            # 3. Log mean and std of cross-validation metrics for numeric columns only
            exclude_cols = {"fold", "train_start_season", "train_end_season", "val_season"}
            num_cols = [c for c in cv_metrics_df.select_dtypes(include=[np.number]).columns if c not in exclude_cols]
            for col in num_cols:
                vals = cv_metrics_df[col].dropna()
                if len(vals) > 0:
                    mlflow.log_metric(f"mean_cv_{col}", float(np.mean(vals)))
                    mlflow.log_metric(f"std_cv_{col}", float(np.std(vals)))
                    
            # 4. Log final test metrics if evaluated
            if test_metrics:
                for k, v in test_metrics.items():
                    mlflow.log_metric(f"final_test_{k}", float(v))
                    
        logger.info(f"Logged run '{run_name}' to MLflow.")

    def save_evaluation_artifacts(
        self,
        classification_results: pd.DataFrame,
        regression_results: pd.DataFrame,
        predictions: pd.DataFrame,
        feature_importances: Optional[pd.DataFrame] = None,
        calibration_df: Optional[pd.DataFrame] = None
    ):
        """
        Saves all tabular evaluation artifacts to data/evaluation/.
        """
        clf_path = os.path.join(self.output_dir, "classification_results.csv")
        reg_path = os.path.join(self.output_dir, "regression_results.csv")
        pred_path = os.path.join(self.output_dir, "predictions.parquet")
        
        classification_results.to_csv(clf_path, index=False)
        regression_results.to_csv(reg_path, index=False)
        predictions.to_parquet(pred_path, index=False)
        
        logger.info(f"Saved classification results to: {clf_path}")
        logger.info(f"Saved regression results to: {reg_path}")
        logger.info(f"Saved predictions parquet to: {pred_path}")
        
        if feature_importances is not None:
            fi_path = os.path.join(self.output_dir, "feature_importances.csv")
            feature_importances.to_csv(fi_path, index=False)
            logger.info(f"Saved feature importances to: {fi_path}")
            
        if calibration_df is not None:
            cal_path = os.path.join(self.output_dir, "calibration_summary.csv")
            calibration_df.to_csv(cal_path, index=False)
            logger.info(f"Saved calibration summary to: {cal_path}")
