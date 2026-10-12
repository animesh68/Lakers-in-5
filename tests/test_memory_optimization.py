import pytest
import numpy as np
from src.features.player_prediction_features import PlayerFeatureEngine
from src.inference.player_predictor import PlayerPredictor
from src.inference.schedule_service import normalize_team


def test_batch_feature_extraction_parity():
    engine = PlayerFeatureEngine()
    home_info = normalize_team("LAL")
    opp_info = normalize_team("GSW")
    game_date = "2026-10-21"
    
    team_context = engine.get_team_rolling_context(
        team_id=home_info["id"],
        opponent_team_id=opp_info["id"],
        cutoff_date=game_date
    )
    
    player_ids = [1629029, 201939, 1630559]  # Luka Doncic, Stephen Curry, Austin Reaves
    
    player_requests = [
        {
            "person_id": pid,
            "team_id": home_info["id"],
            "opponent_team_id": opp_info["id"],
            "is_home": True,
            "team_context": team_context
        }
        for pid in player_ids
    ]
    
    # Batch extraction
    batch_features = engine.extract_pregame_batch_player_features(
        player_requests=player_requests,
        target_game_date=game_date
    )
    
    # Single extraction for each
    for i, pid in enumerate(player_ids):
        single_feat = engine.extract_pregame_player_features(
            person_id=pid,
            team_id=home_info["id"],
            opponent_team_id=opp_info["id"],
            target_game_date=game_date,
            is_home=True,
            team_context=team_context
        )
        b_feat = batch_features[i]
        for key, val in single_feat.items():
            if isinstance(val, (int, float)):
                assert np.isclose(b_feat[key], val, atol=1e-5), f"Mismatch in {key} for player {pid}"
            else:
                assert b_feat[key] == val


def test_player_predictor_batch_inference_determinism():
    predictor = PlayerPredictor()
    
    res1 = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21",
        model_version="prod"
    )
    
    res2 = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21",
        model_version="prod"
    )
    
    assert len(res1.players) == len(res2.players)
    assert len(res1.players) > 0
    
    for p1, p2 in zip(res1.players, res2.players):
        assert p1.player_id == p2.player_id
        assert p1.player_name == p2.player_name
        assert np.isclose(p1.predicted_points, p2.predicted_points, atol=1e-5)
        assert np.isclose(p1.predicted_rebounds, p2.predicted_rebounds, atol=1e-5)
        assert np.isclose(p1.predicted_assists, p2.predicted_assists, atol=1e-5)
        assert np.isclose(p1.expected_minutes, p2.expected_minutes, atol=1e-5)
