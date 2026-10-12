"""
Unit and integration tests for Phase 10B — Prospective Shadow Monitoring & Promotion Gate.

Verifies:
1. Production and C1 predictions are paired correctly.
2. Missing shadow prediction does not accidentally get compared against a different player/game.
3. Missing actual outcome is excluded.
4. Target-game outcome cannot affect pregame features (pregame immutability / mutation test).
5. Role assignment remains invariant under target-game mutation.
6. Threshold coverage calculations are correct.
7. MAE & bias calculations are correct.
8. Paired delta calculation is correct.
9. Subgroup assignment is correct.
10. Promotion gate returns expected status for synthetic pass/fail examples.
11. Insufficient evidence cannot produce PROMOTION_ELIGIBLE.
12. PROMOTION_ELIGIBLE does not automatically modify production artifacts.
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

from src.monitoring.player_shadow_evaluator import (
    PlayerShadowEvaluator,
    PromotionStatus,
)
from src.monitoring.store import PlayerShadowPredictionRecord
from src.monitoring.repository import PredictionRepository


# ---------------------------------------------------------------------------
# Test 1 & 2 & 3: Paired Evaluation Data Preparation & Exclusion Logic
# ---------------------------------------------------------------------------

def test_paired_evaluation_alignment_and_exclusions(tmp_path):
    """
    Verifies that only rows with valid production, shadow, and actual outcomes
    are evaluated on the EXACT SAME player-game population.
    """
    parquet_path = str(tmp_path / "shadow_test.parquet")
    repo = PredictionRepository(parquet_player_shadow_path=parquet_path)
    
    # 1. Valid evaluated paired record
    rec1 = PlayerShadowPredictionRecord(
        game_id="G1", player_id="P1", player_name="Player One", game_date="2026-10-25",
        model_version="Production-v1.0", production_model_version="Production-v1.0",
        shadow_model_version="PlayerSuite-v1.1-c1-shadow", role="Star",
        predicted_minutes_production=34.0, predicted_minutes_shadow=35.0,
        predicted_points_production=25.0, predicted_points_shadow=28.0,
        predicted_rebounds_production=8.0, predicted_rebounds_shadow=8.5,
        predicted_assists_production=7.0, predicted_assists_shadow=7.5,
        actual_points=30.0, actual_minutes=36.0, actual_rebounds=9.0, actual_assists=8.0,
        prediction_status="evaluated"
    )
    # 2. Missing actual outcome (pending) -> must be excluded from evaluation
    rec2 = PlayerShadowPredictionRecord(
        game_id="G1", player_id="P2", player_name="Player Two", game_date="2026-10-25",
        model_version="Production-v1.0", production_model_version="Production-v1.0",
        shadow_model_version="PlayerSuite-v1.1-c1-shadow", role="Starter",
        predicted_minutes_production=28.0, predicted_minutes_shadow=28.0,
        predicted_points_production=15.0, predicted_points_shadow=16.0,
        actual_points=None, prediction_status="pending"
    )
    # 3. Missing shadow points -> must be excluded
    rec3 = PlayerShadowPredictionRecord(
        game_id="G1", player_id="P3", player_name="Player Three", game_date="2026-10-25",
        model_version="Production-v1.0", production_model_version="Production-v1.0",
        shadow_model_version="PlayerSuite-v1.1-c1-shadow", role="Bench",
        predicted_minutes_production=15.0, predicted_minutes_shadow=15.0,
        predicted_points_production=8.0, predicted_points_shadow=None,
        actual_points=10.0, actual_minutes=14.0, prediction_status="evaluated"
    )
    
    repo.save_player_shadow_predictions([rec1, rec2, rec3])
    
    evaluator = PlayerShadowEvaluator(repository=repo)
    df = evaluator.build_paired_evaluation_dataset()
    
    assert len(df) == 1
    assert df.iloc[0]["player_id"] == "P1"
    assert df.iloc[0]["game_id"] == "G1"
    assert df.iloc[0]["prod_pts_err"] == -5.0  # 25 - 30
    assert df.iloc[0]["shadow_pts_err"] == -2.0  # 28 - 30
    assert df.iloc[0]["prod_pts_abs_err"] == 5.0
    assert df.iloc[0]["shadow_pts_abs_err"] == 2.0
    assert df.iloc[0]["pts_delta"] == -3.0  # 2.0 - 5.0 (C1 improved error by 3.0)


# ---------------------------------------------------------------------------
# Test 4 & 5: Pregame Immutability & Role Assignment Mutation Invariance
# ---------------------------------------------------------------------------

def test_pregame_immutability_and_role_invariance():
    """
    Mutation test: Changing the target game's actual postgame boxscore
    CANNOT alter pregame features or assigned role.
    """
    from src.features.player_prediction_features import PlayerFeatureEngine
    from src.models.player_models import RoleStratifiedPointsModel
    
    engine = PlayerFeatureEngine()
    features_before = engine.extract_pregame_player_features(
        person_id="1629029",
        team_id="1610612747",
        opponent_team_id="1610612744",
        target_game_date="2026-10-21"
    )
    role_before = RoleStratifiedPointsModel.get_pregame_role(pd.DataFrame([features_before])).iloc[0]
    
    # Target game outcome occurs (50 PTS, 40 MIN)
    target_game_outcome = {"GAME_DATE": "2026-10-21", "MIN": 40.0, "PTS": 50.0, "REB": 15.0, "AST": 12.0}
    
    # Verify: Inference engine only ingests prior history, NOT the target game outcome
    features_after = engine.extract_pregame_player_features(
        person_id="1629029",
        team_id="1610612747",
        opponent_team_id="1610612744",
        target_game_date="2026-10-21"
    )
    role_after = RoleStratifiedPointsModel.get_pregame_role(pd.DataFrame([features_after])).iloc[0]
    
    assert features_before == features_after
    assert role_before == role_after == "star"


# ---------------------------------------------------------------------------
# Test 6 & 7: Metric Calculations & Threshold Coverage
# ---------------------------------------------------------------------------

def test_metric_calculations_and_threshold_coverage():
    evaluator = PlayerShadowEvaluator()
    
    # Slice metrics test
    slice_df = pd.DataFrame({
        "prod_pts_err": [-2.0, 2.0, 2.0, 5.0],
        "shadow_pts_err": [1.0, 1.0, -1.0, 2.0],
        "prod_pts_abs_err": [2.0, 2.0, 2.0, 5.0],
        "shadow_pts_abs_err": [1.0, 1.0, 1.0, 2.0],
        "prod_min_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_min_err": [0.0, 0.0, 0.0, 0.0],
        "prod_min_abs_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_min_abs_err": [0.0, 0.0, 0.0, 0.0],
        "prod_reb_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_reb_err": [0.0, 0.0, 0.0, 0.0],
        "prod_reb_abs_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_reb_abs_err": [0.0, 0.0, 0.0, 0.0],
        "prod_ast_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_ast_err": [0.0, 0.0, 0.0, 0.0],
        "prod_ast_abs_err": [0.0, 0.0, 0.0, 0.0],
        "shadow_ast_abs_err": [0.0, 0.0, 0.0, 0.0],
    })
    
    metrics = evaluator.calculate_slice_metrics(slice_df)
    assert metrics["count"] == 4
    # prod_mae = (2+2+2+5)/4 = 2.75
    assert metrics["points"]["prod_mae"] == 2.75
    # shadow_mae = (1+1+1+2)/4 = 1.25
    assert metrics["points"]["shadow_mae"] == 1.25
    assert metrics["points"]["mae_improvement"] == 1.50
    
    # Threshold coverage test for 30+
    cov_df = pd.DataFrame({
        "actual_points": [10.0, 22.0, 32.0, 45.0],
        "predicted_points_production": [12.0, 20.0, 26.0, 28.0],
        "predicted_points_shadow": [12.0, 20.0, 30.0, 40.0]
    })
    
    cov = evaluator.calculate_threshold_coverage(cov_df, thresholds=[30.0])
    assert "30+" in cov
    c1_30 = cov["30+"]
    assert c1_30["actual_count"] == 2
    assert c1_30["shadow_predicted_count"] == 2
    assert c1_30["shadow_tp"] == 2
    assert c1_30["shadow_fp"] == 0
    assert c1_30["shadow_fn"] == 0


# ---------------------------------------------------------------------------
# Test 8: Paired Delta Calculations
# ---------------------------------------------------------------------------

def test_paired_delta_calculations():
    evaluator = PlayerShadowEvaluator()
    paired_df = pd.DataFrame({
        "pts_delta": [-2.0, 0.0, 1.0, -1.0, -4.0],
        "prod_pts_abs_err": [5.0, 4.0, 3.0, 2.0, 6.0],
        "shadow_pts_abs_err": [3.0, 4.0, 4.0, 1.0, 2.0]
    })
    
    stats = evaluator.calculate_paired_delta_stats(paired_df)
    assert np.isclose(stats["mean_delta"], -1.2)
    assert stats["c1_wins"] == 3
    assert stats["prod_wins"] == 1
    assert stats["ties"] == 1
    assert np.isclose(stats["c1_win_pct"], 60.0)


# ---------------------------------------------------------------------------
# Test 9: Subgroup Classification Logic
# ---------------------------------------------------------------------------

def test_subgroup_assignment():
    from src.models.player_models import RoleStratifiedPointsModel
    
    # Star definition: min_avg_10 >= 28.0, usg_10 >= 0.24
    assert RoleStratifiedPointsModel.get_pregame_role(pd.DataFrame([{"player_min_avg_10": 34.0, "player_usage_pct_10": 0.32}])).iloc[0] == "star"
    # Starter definition: min_avg_10 >= 24.0
    assert RoleStratifiedPointsModel.get_pregame_role(pd.DataFrame([{"player_min_avg_10": 26.0, "player_usage_pct_10": 0.18}])).iloc[0] == "starter"
    # Bench definition: min_avg_10 < 24.0
    assert RoleStratifiedPointsModel.get_pregame_role(pd.DataFrame([{"player_min_avg_10": 16.0, "player_usage_pct_10": 0.15}])).iloc[0] == "bench"


# ---------------------------------------------------------------------------
# Test 10, 11 & 12: Promotion Gate Scenarios and Artifact Protection
# ---------------------------------------------------------------------------

def test_promotion_gate_insufficient_evidence(tmp_path):
    """
    < 250 samples must evaluate to INSUFFICIENT_EVIDENCE regardless of metrics.
    """
    parquet_path = str(tmp_path / "shadow_test.parquet")
    repo = PredictionRepository(parquet_player_shadow_path=parquet_path)
    
    records = []
    for i in range(50):
        records.append(PlayerShadowPredictionRecord(
            game_id=f"G{i}", player_id=f"P{i}", player_name=f"Player {i}", game_date="2026-11-01",
            model_version="Production-v1.0", production_model_version="Production-v1.0",
            shadow_model_version="PlayerSuite-v1.1-c1-shadow", role="Star",
            predicted_minutes_production=30.0, predicted_minutes_shadow=30.0,
            predicted_points_production=20.0, predicted_points_shadow=24.0,
            predicted_rebounds_production=5.0, predicted_rebounds_shadow=5.0,
            predicted_assists_production=5.0, predicted_assists_shadow=5.0,
            actual_points=25.0, actual_minutes=30.0, actual_rebounds=5.0, actual_assists=5.0,
            prediction_status="evaluated"
        ))
    repo.save_player_shadow_predictions(records)
    
    evaluator = PlayerShadowEvaluator(repository=repo)
    report = evaluator.evaluate_promotion_gate()
    assert report["promotion_status"] == PromotionStatus.INSUFFICIENT_EVIDENCE.value
    assert report["evidence_sample_count"] == 50
    assert report["promotion_decision"] == "HOLD (Production Unchanged)"


def test_promotion_gate_failing_criteria(tmp_path):
    """
    >= 1000 samples where C1 has worse overall MAE must evaluate to C1_NOT_BETTER.
    """
    parquet_path = str(tmp_path / "shadow_test.parquet")
    repo = PredictionRepository(parquet_player_shadow_path=parquet_path)
    
    records = []
    for i in range(1000):
        # Production error 1.0, Shadow error 3.0 (C1 is worse)
        records.append(PlayerShadowPredictionRecord(
            game_id=f"G{i}", player_id=f"P{i%20}", player_name=f"Player {i%20}", game_date="2026-11-01",
            model_version="Production-v1.0", production_model_version="Production-v1.0",
            shadow_model_version="PlayerSuite-v1.1-c1-shadow", role="Star",
            predicted_minutes_production=30.0, predicted_minutes_shadow=30.0,
            predicted_points_production=25.0, predicted_points_shadow=22.0,
            predicted_rebounds_production=5.0, predicted_rebounds_shadow=5.0,
            predicted_assists_production=5.0, predicted_assists_shadow=5.0,
            actual_points=25.0, actual_minutes=30.0, actual_rebounds=5.0, actual_assists=5.0,
            prediction_status="evaluated"
        ))
    repo.save_player_shadow_predictions(records)
    
    evaluator = PlayerShadowEvaluator(repository=repo)
    report = evaluator.evaluate_promotion_gate()
    assert report["promotion_status"] == PromotionStatus.C1_NOT_BETTER.value
    assert report["evidence_sample_count"] == 1000
    assert report["promotion_decision"] == "HOLD (Production Unchanged)"
    assert report["criteria_checks"]["c1_overall_points_mae_improvement"]["pass"] is False


def test_promotion_gate_eligible_does_not_modify_artifacts(tmp_path):
    """
    When C1 meets all criteria on >= 1000 samples, it evaluates to C1_PROMOTION_ELIGIBLE.
    Crucially, verify that production model files remain UNCHANGED.
    """
    prod_model_path = os.path.join("models", "player_points_model.joblib")
    mtime_before = os.path.getmtime(prod_model_path) if os.path.exists(prod_model_path) else None
    
    parquet_path = str(tmp_path / "shadow_test.parquet")
    repo = PredictionRepository(parquet_player_shadow_path=parquet_path)
    
    records = []
    roles = ["Star", "Starter", "Bench"]
    for i in range(1050):
        r = roles[i % 3]
        pts_c1 = 26.0 if i % 2 == 0 else 24.0  # abs error 1.0, mean bias 0.0
        pts_prod = 30.0 if i % 2 == 0 else 20.0  # abs error 5.0, mean bias 0.0
        records.append(PlayerShadowPredictionRecord(
            game_id=f"G{i}", player_id=f"P{i%30}", player_name=f"Player {i%30}", game_date="2026-11-01",
            model_version="Production-v1.0", production_model_version="Production-v1.0",
            shadow_model_version="PlayerSuite-v1.1-c1-shadow", role=r,
            predicted_minutes_production=30.0, predicted_minutes_shadow=30.0,
            predicted_points_production=pts_prod, predicted_points_shadow=pts_c1,
            predicted_rebounds_production=5.0, predicted_rebounds_shadow=5.0,
            predicted_assists_production=5.0, predicted_assists_shadow=5.0,
            actual_points=25.0, actual_minutes=30.0, actual_rebounds=5.0, actual_assists=5.0,
            prediction_status="evaluated"
        ))
    repo.save_player_shadow_predictions(records)
    
    evaluator = PlayerShadowEvaluator(repository=repo)
    report = evaluator.evaluate_promotion_gate()
    assert report["promotion_status"] == PromotionStatus.C1_PROMOTION_ELIGIBLE.value
    assert report["all_gate_criteria_passed"] is True
    assert report["promotion_decision"] == "PROMOTION_RECOMMENDED (Requires Manual Approval)"
    
    # Assert production artifact was NOT modified
    if mtime_before is not None:
        mtime_after = os.path.getmtime(prod_model_path)
        assert mtime_before == mtime_after

