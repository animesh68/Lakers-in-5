"""
Ingestion module for traditional and extended team game statistics.
Loads TeamStatistics.csv and TeamStatisticsExtended.csv in chunked batches.
"""

import os
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def parse_datetime(val: Optional[str]) -> Optional[str]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

def parse_date(val: Optional[str]) -> Optional[str]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def parse_int(val: Optional[str]) -> Optional[int]:
    if not val or not str(val).strip():
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None

def parse_float(val: Optional[str]) -> Optional[float]:
    if not val or not str(val).strip():
        return None
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None

def load_team_stats(engine: Engine, raw_data_dir: str, batch_size: int = 10000) -> int:
    """
    Loads TeamStatistics.csv into team_game_stats table.
    """
    stats_csv = os.path.join(raw_data_dir, "games", "TeamStatistics.csv")
    if not os.path.exists(stats_csv):
        logger.error(f"TeamStatistics.csv not found at {stats_csv}")
        return 0

    logger.info(f"Ingesting team game box scores from {stats_csv}...")
    records: List[Dict[str, Any]] = []
    total_processed = 0

    from src.utils.db import bulk_insert_records
    columns = [
        "game_id", "team_id", "game_datetime_est", "game_date",
        "team_city", "team_name", "opponent_team_id", "opponent_team_city", "opponent_team_name",
        "home", "win", "team_score", "opponent_score", "assists", "blocks", "steals",
        "field_goals_attempted", "field_goals_made", "field_goals_percentage",
        "three_pointers_attempted", "three_pointers_made", "three_pointers_percentage",
        "free_throws_attempted", "free_throws_made", "free_throws_percentage",
        "rebounds_defensive", "rebounds_offensive", "rebounds_total", "rebounds_team",
        "fouls_personal", "turnovers", "turnovers_team", "plus_minus_points", "num_minutes",
        "q1_points", "q2_points", "q3_points", "q4_points", "ot1_points", "ot2_points", "ot_all_points",
        "bench_points", "biggest_lead", "biggest_scoring_run", "lead_changes",
        "points_fast_break", "points_from_turnovers", "points_in_the_paint", "points_second_chance",
        "times_tied", "timeouts_remaining", "season_wins", "season_losses", "coach_id",
        "game_type", "game_label", "game_sub_label", "series_game_number", "seed"
    ]
    on_conflict = """ON CONFLICT (game_id, team_id) DO UPDATE SET
        win = EXCLUDED.win,
        team_score = EXCLUDED.team_score,
        opponent_score = EXCLUDED.opponent_score,
        plus_minus_points = EXCLUDED.plus_minus_points"""

    with open(stats_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            t_id = parse_int(row.get("teamId"))
            if not g_id or t_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))
            d_date = parse_date(row.get("gameDate")) or (dt_est[:10] if dt_est else None)

            record = {
                "game_id": g_id,
                "team_id": t_id,
                "game_datetime_est": dt_est,
                "game_date": d_date,
                "team_city": row.get("teamCity", "").strip() or None,
                "team_name": row.get("teamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentTeamId")),
                "opponent_team_city": row.get("opponentTeamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentTeamName", "").strip() or None,
                "home": parse_int(row.get("home")) or 0,
                "win": parse_int(row.get("win")) or 0,
                "team_score": parse_int(row.get("teamScore")),
                "opponent_score": parse_int(row.get("opponentScore")),
                "assists": parse_int(row.get("assists")),
                "blocks": parse_int(row.get("blocks")),
                "steals": parse_int(row.get("steals")),
                "field_goals_attempted": parse_int(row.get("fieldGoalsAttempted")),
                "field_goals_made": parse_int(row.get("fieldGoalsMade")),
                "field_goals_percentage": parse_float(row.get("fieldGoalsPercentage")),
                "three_pointers_attempted": parse_int(row.get("threePointersAttempted")),
                "three_pointers_made": parse_int(row.get("threePointersMade")),
                "three_pointers_percentage": parse_float(row.get("threePointersPercentage")),
                "free_throws_attempted": parse_int(row.get("freeThrowsAttempted")),
                "free_throws_made": parse_int(row.get("freeThrowsMade")),
                "free_throws_percentage": parse_float(row.get("freeThrowsPercentage")),
                "rebounds_defensive": parse_int(row.get("reboundsDefensive")),
                "rebounds_offensive": parse_int(row.get("reboundsOffensive")),
                "rebounds_total": parse_int(row.get("reboundsTotal")),
                "rebounds_team": parse_int(row.get("reboundsTeam")),
                "fouls_personal": parse_int(row.get("foulsPersonal")),
                "turnovers": parse_int(row.get("turnovers")),
                "turnovers_team": parse_int(row.get("turnoversTeam")),
                "plus_minus_points": parse_int(row.get("plusMinusPoints")),
                "num_minutes": parse_float(row.get("numMinutes")),
                "q1_points": parse_int(row.get("q1Points")),
                "q2_points": parse_int(row.get("q2Points")),
                "q3_points": parse_int(row.get("q3Points")),
                "q4_points": parse_int(row.get("q4Points")),
                "ot1_points": parse_int(row.get("ot1Points")),
                "ot2_points": parse_int(row.get("ot2Points")),
                "ot_all_points": parse_int(row.get("otAllPoints")),
                "bench_points": parse_int(row.get("benchPoints")),
                "biggest_lead": parse_int(row.get("biggestLead")),
                "biggest_scoring_run": parse_int(row.get("biggestScoringRun")),
                "lead_changes": parse_int(row.get("leadChanges")),
                "points_fast_break": parse_int(row.get("pointsFastBreak")),
                "points_from_turnovers": parse_int(row.get("pointsFromTurnovers")),
                "points_in_the_paint": parse_int(row.get("pointsInThePaint")),
                "points_second_chance": parse_int(row.get("pointsSecondChance")),
                "times_tied": parse_int(row.get("timesTied")),
                "timeouts_remaining": parse_int(row.get("timeoutsRemaining")),
                "season_wins": parse_int(row.get("seasonWins")),
                "season_losses": parse_int(row.get("seasonLosses")),
                "coach_id": row.get("coachId", "").strip() or None,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "seed": parse_int(row.get("seed")),
            }
            records.append(record)

            if len(records) >= batch_size:
                bulk_insert_records(engine, "team_game_stats", columns, records, on_conflict=on_conflict, batch_size=batch_size)
                total_processed += len(records)
                records.clear()
                logger.info(f"Loaded {total_processed:,} team game stats...")

    if records:
        bulk_insert_records(engine, "team_game_stats", columns, records, on_conflict=on_conflict, batch_size=batch_size)
        total_processed += len(records)

    logger.info(f"Successfully loaded {total_processed:,} team game stats.")
    return total_processed

def load_team_stats_extended(engine: Engine, raw_data_dir: str, batch_size: int = 10000) -> int:
    """
    Loads TeamStatisticsExtended.csv into team_game_stats_extended table.
    """
    ext_csv = os.path.join(raw_data_dir, "games", "TeamStatisticsExtended.csv")
    if not os.path.exists(ext_csv):
        logger.error(f"TeamStatisticsExtended.csv not found at {ext_csv}")
        return 0

    logger.info(f"Ingesting extended team tracking statistics from {ext_csv}...")
    records: List[Dict[str, Any]] = []
    total_processed = 0

    from src.utils.db import bulk_insert_records
    columns = [
        "game_id", "team_id", "game_datetime_est", "game_type", "game_label", "game_sub_label",
        "series_game_number", "team_city", "team_name", "opponent_team_id", "opponent_team_city",
        "opponent_team_name", "home", "win", "team_score", "opponent_score", "seed", "num_minutes",
        "offensive_rating", "estimated_offensive_rating", "defensive_rating", "estimated_defensive_rating",
        "net_rating", "estimated_net_rating", "assist_percentage", "assist_to_turnover_ratio",
        "assist_ratio", "offensive_rebound_percentage", "defensive_rebound_percentage",
        "rebound_percentage", "team_turnover_percentage", "effective_field_goal_percentage",
        "true_shooting_percentage", "pace", "estimated_pace", "pace_per40", "possessions",
        "player_impact_estimate", "points_off_turnovers", "opponent_points_off_turnovers",
        "opponent_points_second_chance", "opponent_points_fast_break", "opponent_points_in_paint",
        "percent_field_goal_attempts_2point", "percent_field_goal_attempts_3point",
        "percent_points_2point", "percent_points_2point_mid_range", "percent_points_3point",
        "percent_points_fast_break", "percent_points_free_throw", "percent_points_off_turnovers",
        "percent_points_in_paint", "percent_assisted_2point_made", "percent_unassisted_2point_made",
        "percent_assisted_3point_made", "percent_unassisted_3point_made",
        "percent_assisted_field_goals_made", "percent_unassisted_field_goals_made",
        "free_throw_attempt_rate", "opponent_effective_field_goal_percentage",
        "opponent_free_throw_attempt_rate", "opponent_turnover_percentage",
        "opponent_offensive_rebound_percentage"
    ]
    on_conflict = """ON CONFLICT (game_id, team_id) DO UPDATE SET
        offensive_rating = EXCLUDED.offensive_rating,
        defensive_rating = EXCLUDED.defensive_rating,
        net_rating = EXCLUDED.net_rating,
        pace = EXCLUDED.pace"""

    with open(ext_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            t_id = parse_int(row.get("teamId"))
            if not g_id or t_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))

            record = {
                "game_id": g_id,
                "team_id": t_id,
                "game_datetime_est": dt_est,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "team_city": row.get("teamCity", "").strip() or None,
                "team_name": row.get("teamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentTeamId")),
                "opponent_team_city": row.get("opponentTeamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentTeamName", "").strip() or None,
                "home": parse_int(row.get("home")),
                "win": parse_int(row.get("win")),
                "team_score": parse_int(row.get("teamScore")),
                "opponent_score": parse_int(row.get("opponentScore")),
                "seed": parse_int(row.get("seed")),
                "num_minutes": parse_float(row.get("numMinutes")),
                "offensive_rating": parse_float(row.get("offensiveRating")),
                "estimated_offensive_rating": parse_float(row.get("estimatedOffensiveRating")),
                "defensive_rating": parse_float(row.get("defensiveRating")),
                "estimated_defensive_rating": parse_float(row.get("estimatedDefensiveRating")),
                "net_rating": parse_float(row.get("netRating")),
                "estimated_net_rating": parse_float(row.get("estimatedNetRating")),
                "assist_percentage": parse_float(row.get("assistPercentage")),
                "assist_to_turnover_ratio": parse_float(row.get("assistToTurnoverRatio")),
                "assist_ratio": parse_float(row.get("assistRatio")),
                "offensive_rebound_percentage": parse_float(row.get("offensiveReboundPercentage")),
                "defensive_rebound_percentage": parse_float(row.get("defensiveReboundPercentage")),
                "rebound_percentage": parse_float(row.get("reboundPercentage")),
                "team_turnover_percentage": parse_float(row.get("teamTurnoverPercentage")),
                "effective_field_goal_percentage": parse_float(row.get("effectiveFieldGoalPercentage")),
                "true_shooting_percentage": parse_float(row.get("trueShootingPercentage")),
                "pace": parse_float(row.get("pace")),
                "estimated_pace": parse_float(row.get("estimatedPace")),
                "pace_per40": parse_float(row.get("pacePer40")),
                "possessions": parse_int(row.get("possessions")),
                "player_impact_estimate": parse_float(row.get("playerImpactEstimate")),
                "points_off_turnovers": parse_float(row.get("pointsOffTurnovers")),
                "opponent_points_off_turnovers": parse_float(row.get("opponentPointsOffTurnovers")),
                "opponent_points_second_chance": parse_float(row.get("opponentPointsSecondChance")),
                "opponent_points_fast_break": parse_float(row.get("opponentPointsFastBreak")),
                "opponent_points_in_paint": parse_float(row.get("opponentPointsInPaint")),
                "percent_field_goal_attempts_2point": parse_float(row.get("percentFieldGoalAttempts2Point")),
                "percent_field_goal_attempts_3point": parse_float(row.get("percentFieldGoalAttempts3Point")),
                "percent_points_2point": parse_float(row.get("percentPoints2Point")),
                "percent_points_2point_mid_range": parse_float(row.get("percentPoints2PointMidRange")),
                "percent_points_3point": parse_float(row.get("percentPoints3Point")),
                "percent_points_fast_break": parse_float(row.get("percentPointsFastBreak")),
                "percent_points_free_throw": parse_float(row.get("percentPointsFreeThrow")),
                "percent_points_off_turnovers": parse_float(row.get("percentPointsOffTurnovers")),
                "percent_points_in_paint": parse_float(row.get("percentPointsInPaint")),
                "percent_assisted_2point_made": parse_float(row.get("percentAssisted2PointMade")),
                "percent_unassisted_2point_made": parse_float(row.get("percentUnassisted2PointMade")),
                "percent_assisted_3point_made": parse_float(row.get("percentAssisted3PointMade")),
                "percent_unassisted_3point_made": parse_float(row.get("percentUnassisted3PointMade")),
                "percent_assisted_field_goals_made": parse_float(row.get("percentAssistedFieldGoalsMade")),
                "percent_unassisted_field_goals_made": parse_float(row.get("percentUnassistedFieldGoalsMade")),
                "free_throw_attempt_rate": parse_float(row.get("freeThrowAttemptRate")),
                "opponent_effective_field_goal_percentage": parse_float(row.get("opponentEffectiveFieldGoalPercentage")),
                "opponent_free_throw_attempt_rate": parse_float(row.get("opponentFreeThrowAttemptRate")),
                "opponent_turnover_percentage": parse_float(row.get("opponentTurnoverPercentage")),
                "opponent_offensive_rebound_percentage": parse_float(row.get("opponentOffensiveReboundPercentage")),
            }
            records.append(record)

            if len(records) >= batch_size:
                bulk_insert_records(engine, "team_game_stats_extended", columns, records, on_conflict=on_conflict, batch_size=batch_size)
                total_processed += len(records)
                records.clear()
                logger.info(f"Loaded {total_processed:,} extended team stats...")

    if records:
        bulk_insert_records(engine, "team_game_stats_extended", columns, records, on_conflict=on_conflict, batch_size=batch_size)
        total_processed += len(records)

    logger.info(f"Successfully loaded {total_processed:,} extended team stats.")
    return total_processed

    with open(ext_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            t_id = parse_int(row.get("teamId"))
            if not g_id or t_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))

            record = {
                "game_id": g_id,
                "team_id": t_id,
                "game_datetime_est": dt_est,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "team_city": row.get("teamCity", "").strip() or None,
                "team_name": row.get("teamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentTeamId")),
                "opponent_team_city": row.get("opponentTeamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentTeamName", "").strip() or None,
                "home": parse_int(row.get("home")),
                "win": parse_int(row.get("win")),
                "team_score": parse_int(row.get("teamScore")),
                "opponent_score": parse_int(row.get("opponentScore")),
                "seed": parse_int(row.get("seed")),
                "num_minutes": parse_float(row.get("numMinutes")),
                "offensive_rating": parse_float(row.get("offensiveRating")),
                "estimated_offensive_rating": parse_float(row.get("estimatedOffensiveRating")),
                "defensive_rating": parse_float(row.get("defensiveRating")),
                "estimated_defensive_rating": parse_float(row.get("estimatedDefensiveRating")),
                "net_rating": parse_float(row.get("netRating")),
                "estimated_net_rating": parse_float(row.get("estimatedNetRating")),
                "assist_percentage": parse_float(row.get("assistPercentage")),
                "assist_to_turnover_ratio": parse_float(row.get("assistToTurnoverRatio")),
                "assist_ratio": parse_float(row.get("assistRatio")),
                "offensive_rebound_percentage": parse_float(row.get("offensiveReboundPercentage")),
                "defensive_rebound_percentage": parse_float(row.get("defensiveReboundPercentage")),
                "rebound_percentage": parse_float(row.get("reboundPercentage")),
                "team_turnover_percentage": parse_float(row.get("teamTurnoverPercentage")),
                "effective_field_goal_percentage": parse_float(row.get("effectiveFieldGoalPercentage")),
                "true_shooting_percentage": parse_float(row.get("trueShootingPercentage")),
                "pace": parse_float(row.get("pace")),
                "estimated_pace": parse_float(row.get("estimatedPace")),
                "pace_per40": parse_float(row.get("pacePer40")),
                "possessions": parse_int(row.get("possessions")),
                "player_impact_estimate": parse_float(row.get("playerImpactEstimate")),
                "points_off_turnovers": parse_float(row.get("pointsOffTurnovers")),
                "opponent_points_off_turnovers": parse_float(row.get("opponentPointsOffTurnovers")),
                "opponent_points_second_chance": parse_float(row.get("opponentPointsSecondChance")),
                "opponent_points_fast_break": parse_float(row.get("opponentPointsFastBreak")),
                "opponent_points_in_paint": parse_float(row.get("opponentPointsInPaint")),
                "percent_field_goal_attempts_2point": parse_float(row.get("percentFieldGoalAttempts2Point")),
                "percent_field_goal_attempts_3point": parse_float(row.get("percentFieldGoalAttempts3Point")),
                "percent_points_2point": parse_float(row.get("percentPoints2Point")),
                "percent_points_2point_mid_range": parse_float(row.get("percentPoints2PointMidRange")),
                "percent_points_3point": parse_float(row.get("percentPoints3Point")),
                "percent_points_fast_break": parse_float(row.get("percentPointsFastBreak")),
                "percent_points_free_throw": parse_float(row.get("percentPointsFreeThrow")),
                "percent_points_off_turnovers": parse_float(row.get("percentPointsOffTurnovers")),
                "percent_points_in_paint": parse_float(row.get("percentPointsInPaint")),
                "percent_assisted_2point_made": parse_float(row.get("percentAssisted2PointMade")),
                "percent_unassisted_2point_made": parse_float(row.get("percentUnassisted2PointMade")),
                "percent_assisted_3point_made": parse_float(row.get("percentAssisted3PointMade")),
                "percent_unassisted_3point_made": parse_float(row.get("percentUnassisted3PointMade")),
                "percent_assisted_field_goals_made": parse_float(row.get("percentAssistedFieldGoalsMade")),
                "percent_unassisted_field_goals_made": parse_float(row.get("percentUnassistedFieldGoalsMade")),
                "free_throw_attempt_rate": parse_float(row.get("freeThrowAttemptRate")),
                "opponent_effective_field_goal_percentage": parse_float(row.get("opponentEffectiveFieldGoalPercentage")),
                "opponent_free_throw_attempt_rate": parse_float(row.get("opponentFreeThrowAttemptRate")),
                "opponent_turnover_percentage": parse_float(row.get("opponentTurnoverPercentage")),
                "opponent_offensive_rebound_percentage": parse_float(row.get("opponentOffensiveReboundPercentage")),
            }
            records.append(record)

            if len(records) >= batch_size:
                with engine.begin() as conn:
                    conn.execute(sql_to_use, records)
                total_processed += len(records)
                records.clear()
                logger.info(f"Loaded {total_processed:,} extended team stats...")

    if records:
        with engine.begin() as conn:
            conn.execute(sql_to_use, records)
        total_processed += len(records)

    logger.info(f"Successfully loaded {total_processed:,} extended team stats.")
    return total_processed
