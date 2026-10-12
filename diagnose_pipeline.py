import duckdb
import pandas as pd
import numpy as np
from datetime import datetime
from src.features.player_prediction_features import PlayerFeatureEngine, PLAYER_FEATURE_CONTRACT, LEAGUE_PRIORS
from src.models.player_models import PlayerPerformanceSuite, PlayerTargetRegressor
from src.inference.roster_service import RosterService

con = duckdb.connect()
p_sql = "data/processed/parquet/player_game_stats.parquet"
t_sql = "data/processed/parquet/team_game_stats.parquet"

print("=== 1. AUDIT OF DNP / ZERO-MINUTE GAMES IN DATASET ===")
dnp_summary = con.execute(f"""
    SELECT 
        COUNT(*) as total_rows,
        SUM(CASE WHEN TRY_CAST(numMinutes AS DOUBLE) = 0 OR numMinutes IS NULL THEN 1 ELSE 0 END) as zero_min_rows,
        ROUND(AVG(TRY_CAST(numMinutes AS DOUBLE)), 2) as avg_min_all,
        ROUND(AVG(CASE WHEN TRY_CAST(numMinutes AS DOUBLE) >= 1.0 THEN TRY_CAST(numMinutes AS DOUBLE) END), 2) as avg_min_active
    FROM '{p_sql}'
""").df()
print(dnp_summary)

print("\n=== 2. STAR PLAYERS TEST FIXTURE (Lakers vs Warriors 2026-10-21) ===")
roster_svc = RosterService()
feat_engine = PlayerFeatureEngine()
suite = PlayerPerformanceSuite.load_artifacts("models")

for team_id, team_name in [(1610612747, "Los Angeles Lakers"), (1610612744, "Golden State Warriors")]:
    print(f"\n--- {team_name} ---")
    roster = roster_svc.get_active_roster_universe(team_id, "2026-10-21")
    team_mins = 0.0
    for p in roster:
        # Correct days_since_team_change for established players
        p_clean = dict(p)
        if not p_clean.get("is_transition_player"):
            p_clean["days_since_team_change"] = 0
            
        f = feat_engine.extract_pregame_player_features(
            person_id=p_clean["person_id"],
            team_id=team_id,
            opponent_team_id=1610612744 if team_id == 1610612747 else 1610612747,
            target_game_date="2026-10-21",
            is_home=(team_id == 1610612747),
            player_meta=p_clean
        )
        pr = suite.predict_player(f)
        team_mins += pr["expected_minutes"]
        print(f"  {p_clean['player_name']:<22} (ID: {p_clean['person_id']:>8}) | Exp Min: {pr['expected_minutes']:>4.1f} | Season Avg: {f['player_min_season_avg']:>4.1f} | PTS: {pr['predicted_points']:>4.1f} | REB: {pr['predicted_rebounds']:>4.1f} | AST: {pr['predicted_assists']:>4.1f}")
    print(f"Total Team Minutes: {team_mins:.1f}")
