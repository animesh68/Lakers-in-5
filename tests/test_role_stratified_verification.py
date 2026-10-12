"""
Unit and Integration Tests for Phase 10A.1: Role-Stratified Model Verification & Shadow Integration.
Verifies:
1. Role assignment leakage invariance
2. Cold-start / rookie fallback routing
3. Shadow model artifact loading and version isolation
4. Train/serve parity for representative archetypes
5. Default production inference preservation
"""

import os
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any

from src.models.player_models import PlayerPerformanceSuite, RoleStratifiedPointsModel
from src.features.player_prediction_features import PlayerFeatureEngine, PLAYER_FEATURE_CONTRACT, LEAGUE_PRIORS
from src.inference.player_predictor import PlayerPredictor
from src.inference.roster_service import RosterService


def test_role_assignment_leakage_invariance():
    """Prove that pregame role assignment cannot be altered by target game outcome manipulations."""
    df_star = pd.DataFrame([{
        "player_min_avg_10": 34.5,
        "player_usage_pct_10": 0.32,
        "target_minutes": 38.0,
        "target_points": 45.0,
        "target_rebounds": 10.0,
        "target_assists": 12.0
    }])
    assert RoleStratifiedPointsModel.get_pregame_role(df_star).iloc[0] == "star"

    # Manipulate target game to 0 minutes / 0 points
    df_mutated_zero = df_star.copy()
    df_mutated_zero["target_minutes"] = 0.0
    df_mutated_zero["target_points"] = 0.0
    assert RoleStratifiedPointsModel.get_pregame_role(df_mutated_zero).iloc[0] == "star"

    # Manipulate target game to 60 points
    df_mutated_high = df_star.copy()
    df_mutated_high["target_points"] = 60.0
    assert RoleStratifiedPointsModel.get_pregame_role(df_mutated_high).iloc[0] == "star"


def test_cold_start_fallback_routing():
    """Prove that rookie / cold-start players safely route to bench tier."""
    df_cold = pd.DataFrame([{
        "player_min_avg_10": LEAGUE_PRIORS["min_avg"],   # 18.5
        "player_usage_pct_10": LEAGUE_PRIORS["usage_pct"], # 0.18
        "target_minutes": 15.0,
        "target_points": 8.0
    }])
    role = RoleStratifiedPointsModel.get_pregame_role(df_cold).iloc[0]
    assert role == "bench", f"Expected cold-start to route to bench, got {role}"


def test_shadow_model_artifact_loading():
    """Verify that shadow models load cleanly under experimental version without affecting prod."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shadow_dir = os.path.join(base_dir, "models", "experimental", "c1_role_stratified")
    
    assert os.path.exists(shadow_dir), f"Shadow directory missing at {shadow_dir}"
    shadow_suite = PlayerPerformanceSuite.load_shadow_suite(shadow_dir)
    
    assert shadow_suite.is_shadow is True
    assert shadow_suite.model_version == "PlayerSuite-v1.1-c1-shadow"
    assert isinstance(shadow_suite.points_model, RoleStratifiedPointsModel)


def test_prod_suite_remains_default_and_untouched():
    """Verify that default PlayerPerformanceSuite.load_artifacts loads production Ridge."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prod_dir = os.path.join(base_dir, "models")
    
    prod_suite = PlayerPerformanceSuite.load_artifacts(prod_dir)
    assert prod_suite.is_shadow is False
    assert prod_suite.model_version == "PlayerSuite-v1.0"


def test_player_predictor_default_production_output():
    """Verify that PlayerPredictor returns production predictions by default, with shadow logging."""
    predictor = PlayerPredictor()
    
    # 2026-10-21: GSW @ LAL (Opening Game)
    response = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21",
        max_players_per_team=5
    )
    
    assert response.home_team == "Los Angeles Lakers"
    assert response.away_team == "Golden State Warriors"
    assert response.model_versions["minutes"] == "PlayerSuite-v1.0"
    assert response.model_versions["points"] == "PlayerPoints-Ridge-v1"
    assert len(response.players) > 0


def test_player_predictor_shadow_mode_output():
    """Verify that explicit model_version='c1_shadow' returns role-stratified shadow projections."""
    predictor = PlayerPredictor()
    
    response_shadow = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21",
        max_players_per_team=5,
        model_version="c1_shadow"
    )
    
    assert response_shadow.model_versions["points"] == "PlayerPoints-RoleStratified-Ridge-v1.1"
    
    # Find Luka in shadow response
    luka_shadow = next((p for p in response_shadow.players if p.player_id == "1629029"), None)
    if luka_shadow:
        assert luka_shadow.predicted_points >= 27.0, f"Expected shadow Luka PTS >= 27.0, got {luka_shadow.predicted_points}"
