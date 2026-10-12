import duckdb
import json
import pandas as pd
from src.inference.roster_service import RosterService
from src.features.player_prediction_features import PlayerFeatureEngine
from src.models.player_models import PlayerPerformanceSuite

roster_svc = RosterService()
feat_engine = PlayerFeatureEngine()
suite = PlayerPerformanceSuite.load_artifacts("models")

print("=== 1. LAKERS ROSTER AS RESOLVED BY ROSTER SERVICE ===")
lal_roster = roster_svc.get_active_roster_universe(1610612747, "2026-10-21")
for p in lal_roster:
    print(f"  {p['player_name']} (ID: {p['person_id']}, Transfer: {p.get('is_transition_player')})")

print("\n=== 2. LUKA DONCIC FEATURE EXTRACTION & PREDICTION ===")
luka_meta = [p for p in lal_roster if "Luka" in p["player_name"] or "Doncic" in p["player_name"]]
if luka_meta:
    p_meta = luka_meta[0]
    print("Found Luka meta:", p_meta)
    feats = feat_engine.extract_pregame_player_features(
        person_id=p_meta["person_id"],
        team_id=1610612747,
        opponent_team_id=1610612744,
        target_game_date="2026-10-21",
        is_home=True,
        player_meta=p_meta
    )
    print("\nExtracted Features for Luka:")
    for k, v in sorted(feats.items()):
        print(f"  {k}: {v}")
    
    preds = suite.predict_player(feats)
    print("\nPredictions for Luka:", preds)

print("\n=== 3. ALL LAKERS PLAYERS PREDICTIONS & SUM OF MINUTES ===")
total_minutes = 0.0
for p_meta in lal_roster:
    f = feat_engine.extract_pregame_player_features(
        person_id=p_meta["person_id"],
        team_id=1610612747,
        opponent_team_id=1610612744,
        target_game_date="2026-10-21",
        is_home=True,
        player_meta=p_meta
    )
    pr = suite.predict_player(f)
    total_minutes += pr["expected_minutes"]
    print(f"  {p_meta['player_name']:<22} | Min: {pr['expected_minutes']:>4.1f} | Pts: {pr['predicted_points']:>4.1f} | Reb: {pr['predicted_rebounds']:>4.1f} | Ast: {pr['predicted_assists']:>4.1f}")

print(f"\nTotal Lakers Projected Minutes: {total_minutes:.1f} (Target NBA Regulation = 240.0)")

print("\n=== 4. LUKA HISTORICAL DATA IN PLAYER_GAME_STATS PARQUET ===")
con = duckdb.connect()
luka_stats = con.execute("""
    SELECT 
        season_year,
        COUNT(*) as games_played,
        ROUND(AVG(minutes), 2) as avg_minutes,
        ROUND(AVG(points), 2) as avg_points,
        ROUND(AVG(rebounds), 2) as avg_rebounds,
        ROUND(AVG(assists), 2) as avg_assists,
        MAX(game_date) as latest_game
    FROM 'data/processed/parquet/player_game_stats.parquet'
    WHERE person_id = 1629029 OR player_name ILIKE '%Doncic%'
    GROUP BY season_year
    ORDER BY season_year
""").df()
print(luka_stats)
