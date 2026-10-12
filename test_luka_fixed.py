import pandas as pd
import numpy as np
from src.models.player_models import PlayerPerformanceSuite
from src.features.player_prediction_features import PlayerFeatureEngine, PLAYER_FEATURE_CONTRACT
from src.inference.roster_service import RosterService

feat_engine = PlayerFeatureEngine()
roster_svc = RosterService()
suite = PlayerPerformanceSuite.load_artifacts("models")

lal_roster = roster_svc.get_active_roster_universe(1610612747, "2026-10-21")
luka_meta = [p for p in lal_roster if "Luka" in p["player_name"]][0]

# Set days_since_team_change to 0.0 for established player
luka_meta_fixed = dict(luka_meta)
luka_meta_fixed["days_since_team_change"] = 0

feats_fixed = feat_engine.extract_pregame_player_features(
    person_id=luka_meta_fixed["person_id"],
    team_id=1610612747,
    opponent_team_id=1610612744,
    target_game_date="2026-10-21",
    is_home=True,
    player_meta=luka_meta_fixed
)

preds_fixed = suite.predict_player(feats_fixed)
print("=== FIXED LUKA DONCIC PREDICTION ===")
print("Features:")
print(f"  days_since_team_change: {feats_fixed['days_since_team_change']}")
print(f"  is_team_change: {feats_fixed['is_team_change']}")
print(f"  player_min_season_avg: {feats_fixed['player_min_season_avg']}")
print(f"  player_pts_per_min_10: {feats_fixed['player_pts_per_min_10']}")
print("\nPredictions:")
print(preds_fixed)
