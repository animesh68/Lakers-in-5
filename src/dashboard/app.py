"""
Streamlit Production Dashboard for Lakers in 5.
Presents real-time Lakers match forecasts, league-wide predictions, rolling model evaluation,
probability calibration curves, feature PSI drift analytics, and retraining governance.
"""

import os
import sys
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.inference.predictor import GamePredictor
from src.inference.schedule_service import ScheduleService, LAKERS_TEAM_ID
from src.monitoring.repository import PredictionRepository
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector
from src.monitoring.health import ModelHealthService, RetrainingDecisionEngine
from src.monitoring.outcomes import OutcomeIngestionService

# ==============================================================================
# DATA LOADERS (Cached & Testable)
# ==============================================================================

@st.cache_resource
def get_services():
    repo = PredictionRepository()
    predictor = GamePredictor(repository=repo)
    schedule = ScheduleService()
    metrics_svc = MonitoringMetricsService(repository=repo)
    drift_detector = DataDriftDetector(repository=repo)
    health_svc = ModelHealthService(repository=repo, metrics_service=metrics_svc, drift_detector=drift_detector)
    retrain_engine = RetrainingDecisionEngine(repository=repo, health_service=health_svc)
    outcome_svc = OutcomeIngestionService(repository=repo)
    return {
        "repo": repo,
        "predictor": predictor,
        "schedule": schedule,
        "metrics_svc": metrics_svc,
        "drift_detector": drift_detector,
        "health_svc": health_svc,
        "retrain_engine": retrain_engine,
        "outcome_svc": outcome_svc,
    }

def load_next_lakers_game(predictor: GamePredictor, as_of_date: Optional[str] = None):
    try:
        return predictor.predict_lakers_next(as_of_date=as_of_date, persist=True)
    except Exception as e:
        return None

def load_recent_predictions(repo: PredictionRepository, team: Optional[str] = None, status: Optional[str] = None):
    preds = repo.get_predictions(team=team, status=status, limit=100)
    if not preds:
        return pd.DataFrame()
    
    rows = []
    for p in preds:
        rows.append({
            "Date": p.game_date,
            "Matchup": f"{p.away_team} @ {p.home_team}",
            "Home Team": p.home_team,
            "Away Team": p.away_team,
            "Home Win Prob": f"{p.home_win_probability * 100:.1f}%",
            "Away Win Prob": f"{p.away_win_probability * 100:.1f}%",
            "Pred Margin": f"{p.predicted_home_margin:+.1f}",
            "Status": p.status.upper(),
            "Actual Result": f"{p.actual_away_score} - {p.actual_home_score}" if p.actual_home_score is not None else "Pending",
            "Winner": ("Home" if p.actual_home_win == 1 else "Away") if p.actual_home_win is not None else "-",
            "Prediction ID": p.prediction_id,
            "Feature Hash": p.feature_snapshot_hash[:8] + "...",
        })
    return pd.DataFrame(rows)

# ==============================================================================
# STREAMLIT UI LAYOUT
# ==============================================================================

def main():
    st.set_page_config(
        page_title="Lakers in 5 — Prediction & Monitoring Center",
        page_icon="🏀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    svcs = get_services()
    repo = svcs["repo"]
    predictor = svcs["predictor"]
    metrics_svc = svcs["metrics_svc"]
    drift_detector = svcs["drift_detector"]
    health_svc = svcs["health_svc"]
    retrain_engine = svcs["retrain_engine"]

    # Header
    st.title("🏀 Lakers in 5 — MLOps & Prediction Center")
    st.caption("Production Machine Learning Forecasts, Temporal Monitoring & Data Drift Governance")

    # Sidebar Filters & Actions
    st.sidebar.header("⚙️ Configuration & Controls")
    selected_window = st.sidebar.selectbox("Monitoring Time Window", ["30d", "7d", "season", "all_time"], index=0)
    
    if st.sidebar.button("🔄 Sync Completed Outcomes"):
        out_res = svcs["outcome_svc"].update_pending_outcomes()
        st.sidebar.success(f"Settled {out_res.get('updated_count', 0)} completed predictions!")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        f"**Active Model:**\n{predictor.clf_label}\n\n"
        f"**Regressor:**\n{predictor.reg_label}\n\n"
        f"**Feature Contract:** 52 Pregame Features\n\n"
        f"**Analytical Lakehouse:** DuckDB / Parquet"
    )

    # --------------------------------------------------------------------------
    # SECTION A: LAKERS NEXT GAME FORECAST
    # --------------------------------------------------------------------------
    st.header("1. 🌟 Next Lakers Matchup Forecast")
    lakers_pred = load_next_lakers_game(predictor, as_of_date="2026-10-20")
    
    if lakers_pred:
        col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.5])
        with col1:
            st.subheader(f"📅 {lakers_pred.game_date}")
            st.markdown(f"### **{lakers_pred.matchup}**")
            loc = "Home (Crypto.com Arena)" if lakers_pred.is_lakers_home else f"Road (vs {lakers_pred.opponent_team})"
            st.write(f"**Venue:** {loc}")

        with col2:
            st.metric(
                label="Lakers Win Probability",
                value=f"{lakers_pred.lakers_win_probability * 100:.1f}%",
                delta=f"{(lakers_pred.lakers_win_probability - 0.5) * 100:+.1f}% vs 50/50"
            )

        with col3:
            st.metric(
                label="Predicted Lakers Margin",
                value=f"{lakers_pred.predicted_lakers_margin:+.1f} pts",
                delta="Win" if lakers_pred.predicted_lakers_margin > 0 else "Loss"
            )

        with col4:
            st.caption(f"**Model Version:** `{lakers_pred.model_version}`")
            st.caption(f"**Feature Snapshot Hash:** `{lakers_pred.feature_snapshot_hash[:16]}...`")
            st.caption(f"**Feature Schema:** `{lakers_pred.feature_schema_version}`")
            st.caption(f"**Inference Generated:** `{lakers_pred.feature_timestamp}`")
    else:
        st.info("No upcoming Lakers regular season games found on schedule.")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # SECTION F & G: MODEL HEALTH & RETRAINING RECOMMENDATION
    # --------------------------------------------------------------------------
    st.header("2. 🩺 Model Health & Retraining Governance")
    health_report = health_svc.evaluate_health(window=selected_window)
    retrain_report = retrain_engine.evaluate_retraining_decision(window=selected_window)

    h_col1, h_col2 = st.columns(2)

    with h_col1:
        status = health_report.get("status", "HEALTHY")
        if status == "HEALTHY":
            st.success(f"### Status: 🟢 {status}")
        elif status == "WARNING":
            st.warning(f"### Status: 🟡 {status}")
        else:
            st.error(f"### Status: 🔴 {status}")

        st.markdown("**Health Diagnostic Findings:**")
        for r in health_report.get("reasons", []):
            st.write(f"- {r}")

    with h_col2:
        decision = retrain_report.get("decision", "NO_RETRAIN_NEEDED")
        if decision == "NO_RETRAIN_NEEDED":
            st.info(f"### Recommendation: 🛡️ {decision}")
        else:
            st.warning(f"### Recommendation: ⚠️ {decision}")

        st.markdown("**Governance Evaluation Details:**")
        for r in retrain_report.get("reasons", []):
            st.write(f"- {r}")
        st.caption("🔒 *Retraining is an engineer-directed operational process. No automatic model replacement occurs.*")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # SECTION C: MODEL PERFORMANCE BENCHMARKS
    # --------------------------------------------------------------------------
    st.header(f"3. 📈 Rolling Model Performance ({selected_window.upper()})")
    perf = metrics_svc.compute_performance_metrics(window=selected_window)
    clf = perf.get("classification", {})
    reg = perf.get("regression", {})
    sample_count = perf.get("sample_count", 0)

    st.write(f"Evaluated on **{sample_count} completed games** (Total logged in window: {perf.get('total_predictions', 0)})")

    p_col1, p_col2, p_col3, p_col4, p_col5, p_col6 = st.columns(6)
    with p_col1:
        st.metric("Accuracy", f"{clf.get('accuracy', 0.0) * 100:.1f}%" if clf.get('accuracy') is not None else "N/A")
    with p_col2:
        st.metric("Log Loss", f"{clf.get('log_loss', 0.0):.4f}" if clf.get('log_loss') is not None else "N/A")
    with p_col3:
        st.metric("Brier Score", f"{clf.get('brier_score', 0.0):.4f}" if clf.get('brier_score') is not None else "N/A")
    with p_col4:
        st.metric("ROC-AUC", f"{clf.get('roc_auc', 0.0):.4f}" if clf.get('roc_auc') is not None else "N/A")
    with p_col5:
        st.metric("Margin MAE", f"{reg.get('mae', 0.0):.2f} pts" if reg.get('mae') is not None else "N/A")
    with p_col6:
        st.metric("Margin RMSE", f"{reg.get('rmse', 0.0):.2f} pts" if reg.get('rmse') is not None else "N/A")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # SECTION D: PROBABILITY CALIBRATION
    # --------------------------------------------------------------------------
    st.header("4. 🎯 Probability Calibration Monitoring")
    cal_df = metrics_svc.compute_calibration_table(window=selected_window)
    
    cal_col1, cal_col2 = st.columns([1.5, 1])
    with cal_col1:
        st.subheader("Predicted Probability vs. Empirical Win Rate")
        # Plot calibration curve using Altair / Streamlit line chart
        plot_df = cal_df.dropna(subset=["actual_win_rate"]).copy()
        if not plot_df.empty:
            plot_df["Perfect Calibration"] = plot_df["mean_predicted_prob"]
            st.line_chart(
                plot_df.set_index("mean_predicted_prob")[["actual_win_rate", "Perfect Calibration"]],
                use_container_width=True
            )
        else:
            st.info("Awaiting completed game outcomes to render empirical calibration curve.")

    with cal_col2:
        st.subheader("Decile Breakdown")
        st.dataframe(cal_df, use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # SECTION E: DATA DRIFT & PSI MONITORING
    # --------------------------------------------------------------------------
    st.header("5. 📊 Feature Data Drift (Population Stability Index)")
    drift_data = drift_detector.compute_feature_drift(window=selected_window)
    
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    with d_col1:
        st.metric("High Drift Features (PSI > 0.25)", drift_data.get("features_high_drift", 0))
    with d_col2:
        st.metric("Moderate Drift Features (PSI 0.10–0.25)", drift_data.get("features_moderate_drift", 0))
    with d_col3:
        st.metric("Low Drift Features (PSI < 0.10)", drift_data.get("features_low_drift", 0))
    with d_col4:
        st.metric("Features Evaluated", drift_data.get("total_features_evaluated", 0))

    drift_features = drift_data.get("features", [])
    if drift_features:
        drift_df = pd.DataFrame(drift_features)
        st.dataframe(
            drift_df[["feature", "psi", "mean_shift", "std_shift", "missing_rate_shift", "status", "ref_mean", "curr_mean"]],
            use_container_width=True
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # SECTION B: RECENT PREDICTIONS LOG
    # --------------------------------------------------------------------------
    st.header("6. 📋 Prediction Store & Historical Log")
    
    f_col1, f_col2, _ = st.columns([1, 1, 2])
    with f_col1:
        filter_team = st.selectbox("Team Filter", ["All Teams", "Los Angeles Lakers"], index=0)
    with f_col2:
        filter_status = st.selectbox("Status Filter", ["All Statuses", "completed", "pending"], index=0)

    team_arg = "Los Angeles Lakers" if filter_team == "Los Angeles Lakers" else None
    status_arg = None if filter_status == "All Statuses" else filter_status

    preds_table = load_recent_predictions(repo, team=team_arg, status=status_arg)
    if not preds_table.empty:
        st.dataframe(preds_table, use_container_width=True)
    else:
        st.info("No predictions found matching the selected filters.")

if __name__ == "__main__":
    main()
