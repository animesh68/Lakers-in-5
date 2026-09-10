"""
Command-Line Prediction Runner for Lakers in 5 Production Inference.

Usage examples:
    # 1. Predict next upcoming Lakers game:
    python scripts/predict_game.py --lakers-next

    # 2. Predict next Lakers game and persist prediction record:
    python scripts/predict_game.py --lakers-next --persist

    # 3. Predict specific scheduled game by official number:
    python scripts/predict_game.py --game-id 5

    # 4. Predict arbitrary custom matchup:
    python scripts/predict_game.py --home-team LAL --away-team GSW --date 2026-10-21 --persist
"""

import os
import sys
import argparse
from datetime import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.inference.predictor import GamePredictor
from src.inference.schedule_service import ScheduleService

def format_date_human(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date[:10], "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except Exception:
        return iso_date

def print_game_prediction(res):
    print("\n" + "=" * 50)
    print("Lakers in 5 — NBA Game Prediction")
    print("-" * 50)
    print(f"{res.away_team} at {res.home_team}")
    print(f"{format_date_human(res.game_date)}")
    print("-" * 50)
    print(f"{res.home_team} Win Probability: {res.home_win_probability * 100:.1f}%")
    print(f"{res.away_team} Win Probability: {res.away_win_probability * 100:.1f}%")
    print()
    if res.predicted_home_margin >= 0:
        print(f"Predicted Margin: {res.home_team} +{res.predicted_home_margin:.1f}")
    else:
        print(f"Predicted Margin: {res.away_team} +{abs(res.predicted_home_margin):.1f}")
    print("-" * 50)
    print(f"Model:                 {res.model_version}")
    print(f"Feature Schema:        {res.feature_schema_version}")
    print(f"Feature Hash:          {res.feature_snapshot_hash[:16]}...")
    if res.prediction_id:
        print(f"Persisted Record ID:   {res.prediction_id}")
    print(f"Feature Timestamp:     {res.feature_timestamp}")
    print("=" * 50 + "\n")

def print_lakers_prediction(res):
    print("\n" + "=" * 50)
    print("Lakers in 5 — Los Angeles Lakers Forecast")
    print("-" * 50)
    print(f"{res.matchup}")
    print(f"{format_date_human(res.game_date)}")
    print("-" * 50)
    print(f"Lakers Win Probability:   {res.lakers_win_probability * 100:.1f}%")
    print(f"{res.opponent_team} Win Probability: {res.opponent_win_probability * 100:.1f}%")
    print()
    if res.predicted_lakers_margin >= 0:
        print(f"Predicted Margin: Lakers +{res.predicted_lakers_margin:.1f}")
    else:
        print(f"Predicted Margin: {res.opponent_team} +{abs(res.predicted_lakers_margin):.1f}")
    print("-" * 50)
    print(f"Model:                 {res.model_version}")
    print(f"Feature Schema:        {res.feature_schema_version}")
    print(f"Feature Hash:          {res.feature_snapshot_hash[:16]}...")
    if res.prediction_id:
        print(f"Persisted Record ID:   {res.prediction_id}")
    print(f"Feature Timestamp:     {res.feature_timestamp}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Lakers in 5 Production Game Predictor CLI")
    
    parser.add_argument("--lakers-next", action="store_true", help="Predict the next scheduled Lakers game")
    parser.add_argument("--as-of-date", type=str, default=None, help="Reference date for --lakers-next (YYYY-MM-DD)")
    parser.add_argument("--game-id", "--game-num", type=int, default=None, help="Predict a game by official schedule number")
    parser.add_argument("--home-team", type=str, default=None, help="Home team name or code (e.g. LAL, Celtics)")
    parser.add_argument("--away-team", type=str, default=None, help="Away team name or code (e.g. GSW, Warriors)")
    parser.add_argument("--date", type=str, default=None, help="Game date (YYYY-MM-DD)")
    parser.add_argument("--persist", action="store_true", help="Persist prediction record to the prediction repository")
    
    args = parser.parse_args()
    predictor = GamePredictor()
    
    if args.lakers_next or (args.game_id is None and args.home_team is None):
        res = predictor.predict_lakers_next(as_of_date=args.as_of_date, persist=args.persist)
        print_lakers_prediction(res)
    elif args.game_id is not None:
        res = predictor.predict_by_game_num(game_num=args.game_id, persist=args.persist)
        print_game_prediction(res)
    elif args.home_team and args.away_team and args.date:
        res = predictor.predict_game(
            home_team=args.home_team,
            away_team=args.away_team,
            game_date=args.date,
            persist=args.persist
        )
        print_game_prediction(res)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
