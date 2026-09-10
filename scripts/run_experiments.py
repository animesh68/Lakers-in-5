"""
Master Experiment Runner for Lakers in 5 - Phase 3.
Executes Time-Series Walk-Forward Cross-Validation, Model Selection,
Untouched Final Test Set Evaluation (Season 2025-26), and Production Model Persistence.
"""

import os
import sys
import time
from typing import Tuple, Dict, Any, List, Optional
import joblib
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.models.preprocessing import (
    get_feature_columns,
    DifferentialFeatureTransformer,
    METADATA_COLUMNS,
    TARGET_COLUMNS
)
from src.models.validation import load_modeling_dataset, TimeSeriesWalkForwardCV
from src.models.baselines import NaiveHomeBaseline, EloBaseline
from src.models.classification import get_classifier, train_evaluate_classifier_fold
from src.models.regression import get_regressor, train_evaluate_regressor_fold
from src.models.evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    compute_calibration_curve,
    compute_expected_calibration_error
)
from src.models.tracking import ExperimentTracker
from src.utils.logging import logger

def run_classification_experiments(
    folds: list,
    feature_cols: list
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Runs walk-forward CV across all candidate classifiers.
    """
    logger.info("=" * 70)
    logger.info("STARTING CLASSIFICATION EXPERIMENTS (TARGET_HOME_WIN)")
    logger.info("=" * 70)
    
    candidate_configs = [
        {"model_name": "naive_home", "use_differentials": False, "label": "Naive Home Baseline"},
        {"model_name": "elo_baseline", "use_differentials": False, "label": "Elo Baseline"},
        {"model_name": "logistic_regression", "use_differentials": False, "label": "Logistic Regression (Standard)"},
        {"model_name": "logistic_regression", "use_differentials": True, "diff_mode": "concat", "label": "Logistic Regression (Diff Concat)"},
        {"model_name": "logistic_regression", "use_differentials": True, "diff_mode": "diff_only", "label": "Logistic Regression (Diff Only)"},
        {"model_name": "lightgbm", "use_differentials": False, "label": "LightGBM (Standard)"},
        {"model_name": "lightgbm", "use_differentials": True, "diff_mode": "concat", "label": "LightGBM (Diff Concat)"},
        {"model_name": "xgboost", "use_differentials": False, "label": "XGBoost (Standard)"},
        {"model_name": "xgboost", "use_differentials": True, "diff_mode": "concat", "label": "XGBoost (Diff Concat)"},
    ]
    
    fold_results = []
    all_oof_predictions = []
    trained_models_last_fold = {}
    
    for config in candidate_configs:
        model_label = config["label"]
        model_name = config["model_name"]
        use_diff = config.get("use_differentials", False)
        diff_mode = config.get("diff_mode", "concat")
        
        logger.info(f"\nEvaluating: {model_label} across {len(folds)} walk-forward folds...")
        
        for fold in folds:
            fold_idx = fold["fold_idx"]
            val_season = fold["val_season"]
            X_train = fold["X_train"]
            y_train = fold["y_train_win"]
            X_val = fold["X_val"]
            y_val = fold["y_val_win"]
            val_meta = fold["val_metadata"]
            
            # Construct model instance for this fold
            clf = get_classifier(
                model_name=model_name,
                use_differentials=use_diff,
                diff_mode=diff_mode,
                random_state=42
            )
            
            # Train and predict
            pred_probas, pred_labels, fitted_clf = train_evaluate_classifier_fold(
                clf, X_train, y_train, X_val, y_val
            )
            
            # Record last fold model for feature importance inspection
            if fold_idx == len(folds):
                trained_models_last_fold[model_label] = fitted_clf
                
            metrics = evaluate_classification_predictions(y_val, pred_probas, pred_labels)
            
            fold_results.append({
                "model": model_label,
                "model_type": model_name,
                "use_differentials": use_diff,
                "diff_mode": diff_mode if use_diff else "none",
                "fold": fold_idx,
                "train_start_season": fold["train_start_season"],
                "train_end_season": fold["train_end_season"],
                "val_season": val_season,
                "train_count": fold["train_count"],
                "val_count": fold["val_count"],
                "accuracy": metrics["accuracy"],
                "roc_auc": metrics["roc_auc"],
                "log_loss": metrics["log_loss"],
                "brier_score": metrics["brier_score"],
                "ece": metrics["ece"]
            })
            
            # Record OOF predictions
            oof_df = val_meta.copy()
            oof_df["model"] = model_label
            oof_df["fold"] = fold_idx
            oof_df["pred_prob_home_win"] = pred_probas[:, 1]
            oof_df["pred_home_win"] = pred_labels
            oof_df["actual_home_win"] = y_val
            all_oof_predictions.append(oof_df)
            
    df_fold_results = pd.DataFrame(fold_results)
    df_oof = pd.concat(all_oof_predictions, ignore_index=True)
    
    return df_fold_results, df_oof, trained_models_last_fold


def run_regression_experiments(
    folds: list,
    feature_cols: list
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Runs walk-forward CV across all candidate margin regressors.
    """
    logger.info("=" * 70)
    logger.info("STARTING MARGIN REGRESSION EXPERIMENTS (TARGET_POINT_MARGIN)")
    logger.info("=" * 70)
    
    candidate_configs = [
        {"model_name": "ridge", "use_differentials": False, "label": "Ridge Regression (Standard)"},
        {"model_name": "ridge", "use_differentials": True, "diff_mode": "concat", "label": "Ridge Regression (Diff Concat)"},
        {"model_name": "ridge", "use_differentials": True, "diff_mode": "diff_only", "label": "Ridge Regression (Diff Only)"},
        {"model_name": "lightgbm_regressor", "use_differentials": False, "label": "LightGBM Regressor (Standard)"},
        {"model_name": "lightgbm_regressor", "use_differentials": True, "diff_mode": "concat", "label": "LightGBM Regressor (Diff Concat)"},
        {"model_name": "xgboost_regressor", "use_differentials": False, "label": "XGBoost Regressor (Standard)"},
        {"model_name": "xgboost_regressor", "use_differentials": True, "diff_mode": "concat", "label": "XGBoost Regressor (Diff Concat)"},
    ]
    
    fold_results = []
    all_oof_predictions = []
    trained_models_last_fold = {}
    
    for config in candidate_configs:
        model_label = config["label"]
        model_name = config["model_name"]
        use_diff = config.get("use_differentials", False)
        diff_mode = config.get("diff_mode", "concat")
        
        logger.info(f"\nEvaluating: {model_label} across {len(folds)} walk-forward folds...")
        
        for fold in folds:
            fold_idx = fold["fold_idx"]
            val_season = fold["val_season"]
            X_train = fold["X_train"]
            y_train = fold["y_train_margin"]
            X_val = fold["X_val"]
            y_val = fold["y_val_margin"]
            val_meta = fold["val_metadata"]
            
            reg = get_regressor(
                model_name=model_name,
                use_differentials=use_diff,
                diff_mode=diff_mode,
                random_state=42
            )
            
            pred_margins, fitted_reg = train_evaluate_regressor_fold(
                reg, X_train, y_train, X_val, y_val
            )
            
            if fold_idx == len(folds):
                trained_models_last_fold[model_label] = fitted_reg
                
            metrics = evaluate_regression_predictions(y_val, pred_margins)
            
            fold_results.append({
                "model": model_label,
                "model_type": model_name,
                "use_differentials": use_diff,
                "diff_mode": diff_mode if use_diff else "none",
                "fold": fold_idx,
                "train_start_season": fold["train_start_season"],
                "train_end_season": fold["train_end_season"],
                "val_season": val_season,
                "train_count": fold["train_count"],
                "val_count": fold["val_count"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "bias": metrics["bias"]
            })
            
            oof_df = val_meta.copy()
            oof_df["model"] = model_label
            oof_df["fold"] = fold_idx
            oof_df["pred_margin"] = pred_margins
            oof_df["actual_margin"] = y_val
            all_oof_predictions.append(oof_df)
            
    df_fold_results = pd.DataFrame(fold_results)
    df_oof = pd.concat(all_oof_predictions, ignore_index=True)
    
    return df_fold_results, df_oof, trained_models_last_fold


def extract_feature_importances(
    trained_models: Dict[str, Any],
    feature_cols: list
) -> pd.DataFrame:
    """
    Extracts tree feature importances and standardized logistic coefficients.
    """
    records = []
    for model_label, model_obj in trained_models.items():
        # Handle Pipeline
        if hasattr(model_obj, "named_steps"):
            estimator = model_obj.named_steps["model"]
            if "diff" in model_obj.named_steps:
                cols = model_obj.named_steps["diff"].get_feature_names_out()
            else:
                cols = feature_cols
        else:
            estimator = model_obj
            cols = feature_cols
            
        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
            # Normalize to percentage
            norm_imp = importances / (np.sum(importances) + 1e-12)
            for col, imp, norm in zip(cols, importances, norm_imp):
                records.append({
                    "model": model_label,
                    "feature": col,
                    "importance_raw": float(imp),
                    "importance_normalized": float(norm),
                    "metric_type": "tree_split_or_gain"
                })
        elif hasattr(estimator, "coef_"):
            coefs = np.asarray(estimator.coef_).ravel()
            for col, coef in zip(cols, coefs):
                records.append({
                    "model": model_label,
                    "feature": col,
                    "importance_raw": float(coef),
                    "importance_normalized": float(abs(coef)),
                    "metric_type": "linear_or_logistic_coefficient"
                })
                
    return pd.DataFrame(records)


def main():
    start_total = time.time()
    logger.info("==================================================================")
    logger.info("LAKERS IN 5 — PHASE 3: MODEL EXPERIMENTATION & VALIDATION")
    logger.info("==================================================================")
    
    # 1. Load regular season modeling dataset (Seasons 2000 through 2025)
    df = load_modeling_dataset(start_season=2000, end_season=2025, regular_season_only=True)
    feature_cols = get_feature_columns(df)
    logger.info(f"Identified {len(feature_cols)} predictive feature columns.")
    
    # 2. Setup Walk-Forward Cross-Validation
    # Dev: 2000-2024, Val: 2015-2024 (10 folds). Test: 2025 (2025-26 season)
    cv = TimeSeriesWalkForwardCV(
        start_season=2000,
        val_start_season=2015,
        val_end_season=2024,
        test_season=2025
    )
    folds = cv.split_development_folds(df)
    
    # 3. Run Classification Experiments
    clf_fold_results, clf_oof, clf_last_models = run_classification_experiments(folds, feature_cols)
    
    # Summarize classification validation performance
    clf_summary = clf_fold_results.groupby("model").agg(
        mean_log_loss=("log_loss", "mean"),
        std_log_loss=("log_loss", "std"),
        mean_brier=("brier_score", "mean"),
        mean_accuracy=("accuracy", "mean"),
        mean_roc_auc=("roc_auc", "mean"),
        mean_ece=("ece", "mean"),
        model_type=("model_type", "first"),
        use_differentials=("use_differentials", "first"),
        diff_mode=("diff_mode", "first"),
    ).reset_index().sort_values(by="mean_log_loss")
    
    logger.info("\n" + "=" * 70)
    logger.info("CLASSIFICATION DEVELOPMENT VALIDATION SUMMARY (Ranked by Log Loss):")
    logger.info("=" * 70)
    for idx, row in clf_summary.iterrows():
        logger.info(f"{row['model']:<38} | LogLoss: {row['mean_log_loss']:.4f} (+/-{row['std_log_loss']:.4f}) | Brier: {row['mean_brier']:.4f} | Acc: {row['mean_accuracy']:.3f} | AUC: {row['mean_roc_auc']:.3f} | ECE: {row['mean_ece']:.4f}")
        
    # 4. Model Selection (Strictly on Development Data)
    best_clf_row = clf_summary.iloc[0]
    best_clf_label = best_clf_row["model"]
    logger.info("\n" + "*" * 70)
    logger.info(f"SELECTED CHAMPION CLASSIFIER (Based on Dev CV Log Loss): {best_clf_label}")
    logger.info(f"Mean Validation Log Loss: {best_clf_row['mean_log_loss']:.4f}")
    logger.info("*" * 70)

    # 5. Run Margin Regression Experiments
    reg_fold_results, reg_oof, reg_last_models = run_regression_experiments(folds, feature_cols)
    
    reg_summary = reg_fold_results.groupby("model").agg(
        mean_mae=("mae", "mean"),
        std_mae=("mae", "std"),
        mean_rmse=("rmse", "mean"),
        mean_bias=("bias", "mean"),
        model_type=("model_type", "first"),
        use_differentials=("use_differentials", "first"),
        diff_mode=("diff_mode", "first"),
    ).reset_index().sort_values(by="mean_mae")
    
    logger.info("\n" + "=" * 70)
    logger.info("MARGIN REGRESSION DEVELOPMENT VALIDATION SUMMARY (Ranked by MAE):")
    logger.info("=" * 70)
    for idx, row in reg_summary.iterrows():
        logger.info(f"{row['model']:<38} | MAE: {row['mean_mae']:.3f} (+/-{row['std_mae']:.3f}) | RMSE: {row['mean_rmse']:.3f} | Bias: {row['mean_bias']:+.3f}")
        
    best_reg_row = reg_summary.iloc[0]
    best_reg_label = best_reg_row["model"]
    logger.info("\n" + "*" * 70)
    logger.info(f"SELECTED CHAMPION REGRESSOR (Based on Dev CV MAE): {best_reg_label}")
    logger.info(f"Mean Validation MAE: {best_reg_row['mean_mae']:.3f}")
    logger.info("*" * 70)

    # 6. Evaluate Selected Champion Models ONCE on Isolated Final Test Set (Season 2025-26)
    logger.info("\n" + "=" * 70)
    logger.info("EVALUATING SELECTED CHAMPION ON UNTOUCHED 2025-26 TEST SET")
    logger.info("=" * 70)
    
    final_test_split = cv.get_final_test_split(df)
    X_dev = final_test_split["X_train"]
    y_dev_win = final_test_split["y_train_win"]
    y_dev_margin = final_test_split["y_train_margin"]
    X_test = final_test_split["X_test"]
    y_test_win = final_test_split["y_test_win"]
    y_test_margin = final_test_split["y_test_margin"]
    test_meta = final_test_split["test_metadata"]
    
    # Train champion classifier on development data (2000-2024)
    champion_clf = get_classifier(
        model_name=best_clf_row["model_type"],
        use_differentials=best_clf_row["use_differentials"],
        diff_mode=best_clf_row["diff_mode"],
        random_state=42
    )
    champion_clf.fit(X_dev, y_dev_win)
    test_pred_probas = champion_clf.predict_proba(X_test)
    test_pred_labels = champion_clf.predict(X_test)
    
    test_clf_metrics = evaluate_classification_predictions(y_test_win, test_pred_probas, test_pred_labels)
    logger.info(f"\nFinal Test (2025-26) Classifier Performance ({best_clf_label}):")
    logger.info(f"  Log Loss:    {test_clf_metrics['log_loss']:.4f}")
    logger.info(f"  Brier Score: {test_clf_metrics['brier_score']:.4f}")
    logger.info(f"  Accuracy:    {test_clf_metrics['accuracy']:.4f} ({test_clf_metrics['accuracy']*100:.1f}%)")
    logger.info(f"  ROC-AUC:     {test_clf_metrics['roc_auc']:.4f}")
    logger.info(f"  ECE:         {test_clf_metrics['ece']:.4f}")
    
    # Train champion regressor on development data (2000-2024)
    champion_reg = get_regressor(
        model_name=best_reg_row["model_type"],
        use_differentials=best_reg_row["use_differentials"],
        diff_mode=best_reg_row["diff_mode"],
        random_state=42
    )
    champion_reg.fit(X_dev, y_dev_margin)
    test_pred_margins = champion_reg.predict(X_test)
    
    test_reg_metrics = evaluate_regression_predictions(y_test_margin, test_pred_margins)
    logger.info(f"\nFinal Test (2025-26) Regressor Performance ({best_reg_label}):")
    logger.info(f"  MAE:         {test_reg_metrics['mae']:.3f} points")
    logger.info(f"  RMSE:        {test_reg_metrics['rmse']:.3f} points")
    logger.info(f"  Bias:        {test_reg_metrics['bias']:+.3f} points")
    
    # 7. Calibration Analysis for Champion Model
    cal_table = compute_calibration_curve(y_test_win, test_pred_probas[:, 1], n_bins=10)
    logger.info("\nFinal Test Calibration Analysis (Deciles):")
    for _, cal_row in cal_table.iterrows():
        logger.info(f"  Bin {cal_row['bin_range']:<7} | Count: {cal_row['sample_count']:<4} | Pred Prob: {cal_row['mean_predicted_prob']:.3f} | Actual Win Rate: {cal_row['actual_win_rate'] if pd.notna(cal_row['actual_win_rate']) else 0.0:.3f}")

    # 8. Feature Importances
    all_last_models = {**clf_last_models, **reg_last_models}
    df_importances = extract_feature_importances(all_last_models, feature_cols)
    
    # 9. Train Final Production Models on All Historical Data (2000-2025) for Future Inference
    logger.info("\n" + "=" * 70)
    logger.info("TRAINING FINAL PRODUCTION MODELS (2000-2025) FOR INFERENCE SERVING")
    logger.info("=" * 70)
    
    prod_data = cv.get_production_dataset(df)
    models_dir = os.path.join(BASE_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    prod_clf = get_classifier(
        model_name=best_clf_row["model_type"],
        use_differentials=best_clf_row["use_differentials"],
        diff_mode=best_clf_row["diff_mode"],
        random_state=42
    )
    prod_clf.fit(prod_data["X"], prod_data["y_win"])
    prod_clf_path = os.path.join(models_dir, "champion_classifier.joblib")
    joblib.dump({
        "model": prod_clf,
        "model_label": best_clf_label,
        "feature_names": feature_cols,
        "trained_seasons": (prod_data["start_season"], prod_data["end_season"]),
        "training_samples": prod_data["count"],
        "dev_cv_log_loss": float(best_clf_row["mean_log_loss"]),
        "final_test_log_loss": float(test_clf_metrics["log_loss"]),
    }, prod_clf_path)
    logger.info(f"Saved production classifier to: {prod_clf_path}")
    
    prod_reg = get_regressor(
        model_name=best_reg_row["model_type"],
        use_differentials=best_reg_row["use_differentials"],
        diff_mode=best_reg_row["diff_mode"],
        random_state=42
    )
    prod_reg.fit(prod_data["X"], prod_data["y_margin"])
    prod_reg_path = os.path.join(models_dir, "champion_regressor.joblib")
    joblib.dump({
        "model": prod_reg,
        "model_label": best_reg_label,
        "feature_names": feature_cols,
        "trained_seasons": (prod_data["start_season"], prod_data["end_season"]),
        "training_samples": prod_data["count"],
        "dev_cv_mae": float(best_reg_row["mean_mae"]),
        "final_test_mae": float(test_reg_metrics["mae"]),
    }, prod_reg_path)
    logger.info(f"Saved production regressor to: {prod_reg_path}")

    # 10. MLflow Experiment Logging & Artifact Export
    tracker = ExperimentTracker()
    
    # Log classification runs
    for model_label, group_df in clf_fold_results.groupby("model"):
        is_champion = (model_label == best_clf_label)
        t_metrics = test_clf_metrics if is_champion else None
        tracker.log_model_run(
            run_name=f"clf_{model_label.replace(' ', '_').lower()}",
            task_type="classification",
            params={
                "model_label": model_label,
                "model_type": group_df["model_type"].iloc[0],
                "use_differentials": group_df["use_differentials"].iloc[0],
                "diff_mode": group_df["diff_mode"].iloc[0],
                "n_features": len(feature_cols),
                "is_champion": is_champion
            },
            cv_metrics_df=group_df,
            test_metrics=t_metrics,
            tags={"phase": "phase3_experimentation"}
        )
        
    # Log regression runs
    for model_label, group_df in reg_fold_results.groupby("model"):
        is_champion = (model_label == best_reg_label)
        t_metrics = test_reg_metrics if is_champion else None
        tracker.log_model_run(
            run_name=f"reg_{model_label.replace(' ', '_').lower()}",
            task_type="regression",
            params={
                "model_label": model_label,
                "model_type": group_df["model_type"].iloc[0],
                "use_differentials": group_df["use_differentials"].iloc[0],
                "diff_mode": group_df["diff_mode"].iloc[0],
                "n_features": len(feature_cols),
                "is_champion": is_champion
            },
            cv_metrics_df=group_df,
            test_metrics=t_metrics,
            tags={"phase": "phase3_experimentation"}
        )
        
    # Save artifacts
    tracker.save_evaluation_artifacts(
        classification_results=clf_fold_results,
        regression_results=reg_fold_results,
        predictions=clf_oof,
        feature_importances=df_importances,
        calibration_df=cal_table
    )
    
    elapsed = time.time() - start_total
    logger.info("=" * 70)
    logger.info(f"PHASE 3 COMPLETE IN {elapsed:.1f}s.")
    logger.info("==================================================================")


if __name__ == "__main__":
    main()
