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
feats = feat_engine.extract_pregame_player_features(
    person_id=luka_meta["person_id"],
    team_id=1610612747,
    opponent_team_id=1610612744,
    target_game_date="2026-10-21",
    is_home=True,
    player_meta=luka_meta
)

min_pipe = suite.minutes_model.pipeline
scaler = min_pipe.named_steps["scaler"]
reg = min_pipe.named_steps["regressor"]

raw_vec = np.array([feats[col] for col in PLAYER_FEATURE_CONTRACT])
scaled_vec = (raw_vec - scaler.mean_) / scaler.scale_
contributions = scaled_vec * reg.coef_

df_contrib = pd.DataFrame({
    "feature": PLAYER_FEATURE_CONTRACT,
    "raw_value": raw_vec,
    "mean": scaler.mean_,
    "scale": scaler.scale_,
    "scaled_z": scaled_vec,
    "coef": reg.coef_,
    "contribution": contributions
}).sort_values("contribution")

print("=== LUKA DONCIC MINUTES PREDICTION BREAKDOWN ===")
print(df_contrib.to_string())
print(f"\nSum of contributions: {contributions.sum():.2f}")
print(f"Intercept: {reg.intercept_:.2f}")
print(f"Total Predicted Minutes: {reg.intercept_ + contributions.sum():.2f}")
