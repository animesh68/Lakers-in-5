"""
High-performance chunked ingestion module for player game statistics.
Processes PlayerStatistics.csv (1.67M rows) and PlayerStatisticsExtended.csv (838K rows)
using streaming chunked batches to keep memory usage minimal.
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

def load_player_stats(engine: Engine, raw_data_dir: str, chunk_size: int = 50000) -> int:
    """
    Ingests PlayerStatistics.csv in memory-safe chunks into player_game_stats table.
    """
    stats_csv = os.path.join(raw_data_dir, "players", "PlayerStatistics.csv")
    if not os.path.exists(stats_csv):
        logger.error(f"PlayerStatistics.csv not found at {stats_csv}")
        return 0

    logger.info(f"Starting chunked ingestion of player box scores from {stats_csv} (chunk_size={chunk_size:,})...")
    total_loaded = 0
    chunk_records: List[Dict[str, Any]] = []

    from src.utils.db import bulk_insert_records
    columns = [
        "game_id", "person_id", "first_name", "last_name", "game_datetime_est", "game_date",
        "player_team_id", "player_team_city", "player_team_name",
        "opponent_team_id", "opponent_team_city", "opponent_team_name",
        "game_type", "game_label", "game_sub_label", "series_game_number",
        "win", "home", "num_minutes", "points", "assists", "blocks", "steals",
        "field_goals_attempted", "field_goals_made", "field_goals_percentage",
        "three_pointers_attempted", "three_pointers_made", "three_pointers_percentage",
        "free_throws_attempted", "free_throws_made", "free_throws_percentage",
        "rebounds_defensive", "rebounds_offensive", "rebounds_total",
        "fouls_personal", "turnovers", "plus_minus_points", "comment", "starting_position"
    ]
    on_conflict = """ON CONFLICT (game_id, person_id) DO UPDATE SET
        points = EXCLUDED.points,
        assists = EXCLUDED.assists,
        rebounds_total = EXCLUDED.rebounds_total,
        plus_minus_points = EXCLUDED.plus_minus_points"""

    with open(stats_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            p_id = parse_int(row.get("personId"))
            if not g_id or p_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))
            d_date = parse_date(row.get("gameDate")) or (dt_est[:10] if dt_est else None)

            record = {
                "game_id": g_id,
                "person_id": p_id,
                "first_name": row.get("firstName", "").strip() or None,
                "last_name": row.get("lastName", "").strip() or None,
                "game_datetime_est": dt_est,
                "game_date": d_date,
                "player_team_id": parse_int(row.get("playerteamId")),
                "player_team_city": row.get("playerteamCity", "").strip() or None,
                "player_team_name": row.get("playerteamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentteamId")),
                "opponent_team_city": row.get("opponentteamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentteamName", "").strip() or None,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "win": parse_int(row.get("win")),
                "home": parse_int(row.get("home")),
                "num_minutes": row.get("numMinutes", "").strip() or None,
                "points": parse_int(row.get("points")),
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
                "fouls_personal": parse_int(row.get("foulsPersonal")),
                "turnovers": parse_int(row.get("turnovers")),
                "plus_minus_points": parse_int(row.get("plusMinusPoints")),
                "comment": row.get("comment", "").strip() or None,
                "starting_position": row.get("startingPosition", "").strip() or None,
            }
            chunk_records.append(record)

            if len(chunk_records) >= chunk_size:
                bulk_insert_records(engine, "player_game_stats", columns, chunk_records, on_conflict=on_conflict, batch_size=chunk_size)
                total_loaded += len(chunk_records)
                chunk_records.clear()
                logger.info(f"Loaded {total_loaded:,} player game records...")

    if chunk_records:
        bulk_insert_records(engine, "player_game_stats", columns, chunk_records, on_conflict=on_conflict, batch_size=chunk_size)
        total_loaded += len(chunk_records)

    logger.info(f"Successfully finished loading {total_loaded:,} player game records.")
    return total_loaded

def load_player_stats_extended(engine: Engine, raw_data_dir: str, chunk_size: int = 50000) -> int:
    """
    Ingests PlayerStatisticsExtended.csv in memory-safe chunks into player_game_stats_extended table.
    """
    ext_csv = os.path.join(raw_data_dir, "players", "PlayerStatisticsExtended.csv")
    if not os.path.exists(ext_csv):
        logger.error(f"PlayerStatisticsExtended.csv not found at {ext_csv}")
        return 0

    logger.info(f"Starting chunked ingestion of extended player tracking logs from {ext_csv} (chunk_size={chunk_size:,})...")
    total_loaded = 0
    chunk_records: List[Dict[str, Any]] = []

    from src.utils.db import bulk_insert_records
    columns = [
        "game_id", "person_id", "first_name", "last_name", "game_datetime_est",
        "game_type", "game_label", "game_sub_label", "series_game_number",
        "win", "home", "player_team_id", "player_team_city", "player_team_name",
        "opponent_team_id", "opponent_team_city", "opponent_team_name",
        "comment", "starting_position", "num_minutes", "points", "assists",
        "rebounds_total", "rebounds_offensive", "rebounds_defensive",
        "field_goals_made", "field_goals_attempted", "field_goals_percentage",
        "three_pointers_made", "three_pointers_attempted", "three_pointers_percentage",
        "free_throws_made", "free_throws_attempted", "free_throws_percentage",
        "steals", "blocks", "blocks_against", "turnovers", "fouls_personal", "fouls_against",
        "plus_minus_points", "double_double", "triple_double",
        "offensive_rating", "estimated_offensive_rating", "defensive_rating", "estimated_defensive_rating",
        "net_rating", "estimated_net_rating", "assist_percentage", "assist_to_turnover_ratio",
        "assist_ratio", "offensive_rebound_percentage", "defensive_rebound_percentage",
        "rebound_percentage", "team_turnover_percentage", "estimated_turnover_percentage",
        "effective_field_goal_percentage", "true_shooting_percentage",
        "usage_percentage", "estimated_usage_percentage",
        "pace", "estimated_pace", "pace_per40", "player_impact_estimate", "possessions",
        "points_off_turnovers", "points_second_chance", "points_fast_break", "points_in_paint",
        "percent_team_points", "percent_team_assists", "percent_team_rebounds",
        "percent_team_turnovers", "percent_team_steals", "percent_team_blocks",
        "percent_assisted_2point_made", "percent_unassisted_2point_made",
        "percent_assisted_3point_made", "percent_unassisted_3point_made",
        "percent_assisted_field_goals_made", "percent_unassisted_field_goals_made"
    ]
    on_conflict = """ON CONFLICT (game_id, person_id) DO UPDATE SET
        offensive_rating = EXCLUDED.offensive_rating,
        defensive_rating = EXCLUDED.defensive_rating,
        usage_percentage = EXCLUDED.usage_percentage,
        player_impact_estimate = EXCLUDED.player_impact_estimate"""

    with open(ext_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            p_id = parse_int(row.get("personId"))
            if not g_id or p_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))

            record = {
                "game_id": g_id,
                "person_id": p_id,
                "first_name": row.get("firstName", "").strip() or None,
                "last_name": row.get("lastName", "").strip() or None,
                "game_datetime_est": dt_est,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "win": parse_int(row.get("win")),
                "home": parse_int(row.get("home")),
                "player_team_id": parse_int(row.get("playerteamId")),
                "player_team_city": row.get("playerteamCity", "").strip() or None,
                "player_team_name": row.get("playerteamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentteamId")),
                "opponent_team_city": row.get("opponentteamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentteamName", "").strip() or None,
                "comment": row.get("comment", "").strip() or None,
                "starting_position": row.get("startingPosition", "").strip() or None,
                "num_minutes": parse_float(row.get("numMinutes")),
                "points": parse_int(row.get("points")),
                "assists": parse_int(row.get("assists")),
                "rebounds_total": parse_int(row.get("reboundsTotal")),
                "rebounds_offensive": parse_int(row.get("reboundsOffensive")),
                "rebounds_defensive": parse_int(row.get("reboundsDefensive")),
                "field_goals_made": parse_int(row.get("fieldGoalsMade")),
                "field_goals_attempted": parse_int(row.get("fieldGoalsAttempted")),
                "field_goals_percentage": parse_float(row.get("fieldGoalsPercentage")),
                "three_pointers_made": parse_int(row.get("threePointersMade")),
                "three_pointers_attempted": parse_int(row.get("threePointersAttempted")),
                "three_pointers_percentage": parse_float(row.get("threePointersPercentage")),
                "free_throws_made": parse_int(row.get("freeThrowsMade")),
                "free_throws_attempted": parse_int(row.get("freeThrowsAttempted")),
                "free_throws_percentage": parse_float(row.get("freeThrowsPercentage")),
                "steals": parse_int(row.get("steals")),
                "blocks": parse_int(row.get("blocks")),
                "blocks_against": parse_int(row.get("blocksAgainst")),
                "turnovers": parse_int(row.get("turnovers")),
                "fouls_personal": parse_int(row.get("foulsPersonal")),
                "fouls_against": parse_int(row.get("foulsAgainst")),
                "plus_minus_points": parse_int(row.get("plusMinusPoints")),
                "double_double": parse_int(row.get("doubleDouble")),
                "triple_double": parse_int(row.get("tripleDouble")),
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
                "estimated_turnover_percentage": parse_float(row.get("estimatedTurnoverPercentage")),
                "effective_field_goal_percentage": parse_float(row.get("effectiveFieldGoalPercentage")),
                "true_shooting_percentage": parse_float(row.get("trueShootingPercentage")),
                "usage_percentage": parse_float(row.get("usagePercentage")),
                "estimated_usage_percentage": parse_float(row.get("estimatedUsagePercentage")),
                "pace": parse_float(row.get("pace")),
                "estimated_pace": parse_float(row.get("estimatedPace")),
                "pace_per40": parse_float(row.get("pacePer40")),
                "player_impact_estimate": parse_float(row.get("playerImpactEstimate")),
                "possessions": parse_int(row.get("possessions")),
                "points_off_turnovers": parse_float(row.get("pointsOffTurnovers")),
                "points_second_chance": parse_float(row.get("pointsSecondChance")),
                "points_fast_break": parse_float(row.get("pointsFastBreak")),
                "points_in_paint": parse_float(row.get("pointsInPaint")),
                "percent_team_points": parse_float(row.get("percentTeamPoints")),
                "percent_team_assists": parse_float(row.get("percentTeamAssists")),
                "percent_team_rebounds": parse_float(row.get("percentTeamRebounds")),
                "percent_team_turnovers": parse_float(row.get("percentTeamTurnovers")),
                "percent_team_steals": parse_float(row.get("percentTeamSteals")),
                "percent_team_blocks": parse_float(row.get("percentTeamBlocks")),
                "percent_assisted_2point_made": parse_float(row.get("percentAssisted2PointMade")),
                "percent_unassisted_2point_made": parse_float(row.get("percentUnassisted2PointMade")),
                "percent_assisted_3point_made": parse_float(row.get("percentAssisted3PointMade")),
                "percent_unassisted_3point_made": parse_float(row.get("percentUnassisted3PointMade")),
                "percent_assisted_field_goals_made": parse_float(row.get("percentAssistedFieldGoalsMade")),
                "percent_unassisted_field_goals_made": parse_float(row.get("percentUnassistedFieldGoalsMade")),
            }
            chunk_records.append(record)

            if len(chunk_records) >= chunk_size:
                bulk_insert_records(engine, "player_game_stats_extended", columns, chunk_records, on_conflict=on_conflict, batch_size=chunk_size)
                total_loaded += len(chunk_records)
                chunk_records.clear()
                logger.info(f"Loaded {total_loaded:,} extended player game records...")

    if chunk_records:
        bulk_insert_records(engine, "player_game_stats_extended", columns, chunk_records, on_conflict=on_conflict, batch_size=chunk_size)
        total_loaded += len(chunk_records)

    logger.info(f"Successfully finished loading {total_loaded:,} extended player game records.")
    return total_loaded

    with open(ext_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            p_id = parse_int(row.get("personId"))
            if not g_id or p_id is None:
                continue

            dt_est = parse_datetime(row.get("gameDateTimeEst"))

            record = {
                "game_id": g_id,
                "person_id": p_id,
                "first_name": row.get("firstName", "").strip() or None,
                "last_name": row.get("lastName", "").strip() or None,
                "game_datetime_est": dt_est,
                "game_type": row.get("gameType", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "win": parse_int(row.get("win")),
                "home": parse_int(row.get("home")),
                "player_team_id": parse_int(row.get("playerteamId")),
                "player_team_city": row.get("playerteamCity", "").strip() or None,
                "player_team_name": row.get("playerteamName", "").strip() or None,
                "opponent_team_id": parse_int(row.get("opponentteamId")),
                "opponent_team_city": row.get("opponentteamCity", "").strip() or None,
                "opponent_team_name": row.get("opponentteamName", "").strip() or None,
                "comment": row.get("comment", "").strip() or None,
                "starting_position": row.get("startingPosition", "").strip() or None,
                "num_minutes": parse_float(row.get("numMinutes")),
                "points": parse_int(row.get("points")),
                "assists": parse_int(row.get("assists")),
                "rebounds_total": parse_int(row.get("reboundsTotal")),
                "rebounds_offensive": parse_int(row.get("reboundsOffensive")),
                "rebounds_defensive": parse_int(row.get("reboundsDefensive")),
                "field_goals_made": parse_int(row.get("fieldGoalsMade")),
                "field_goals_attempted": parse_int(row.get("fieldGoalsAttempted")),
                "field_goals_percentage": parse_float(row.get("fieldGoalsPercentage")),
                "three_pointers_made": parse_int(row.get("threePointersMade")),
                "three_pointers_attempted": parse_int(row.get("threePointersAttempted")),
                "three_pointers_percentage": parse_float(row.get("threePointersPercentage")),
                "free_throws_made": parse_int(row.get("freeThrowsMade")),
                "free_throws_attempted": parse_int(row.get("freeThrowsAttempted")),
                "free_throws_percentage": parse_float(row.get("freeThrowsPercentage")),
                "steals": parse_int(row.get("steals")),
                "blocks": parse_int(row.get("blocks")),
                "blocks_against": parse_int(row.get("blocksAgainst")),
                "turnovers": parse_int(row.get("turnovers")),
                "fouls_personal": parse_int(row.get("foulsPersonal")),
                "fouls_against": parse_int(row.get("foulsAgainst")),
                "plus_minus_points": parse_int(row.get("plusMinusPoints")),
                "double_double": parse_int(row.get("doubleDouble")),
                "triple_double": parse_int(row.get("tripleDouble")),
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
                "estimated_turnover_percentage": parse_float(row.get("estimatedTurnoverPercentage")),
                "effective_field_goal_percentage": parse_float(row.get("effectiveFieldGoalPercentage")),
                "true_shooting_percentage": parse_float(row.get("trueShootingPercentage")),
                "usage_percentage": parse_float(row.get("usagePercentage")),
                "estimated_usage_percentage": parse_float(row.get("estimatedUsagePercentage")),
                "pace": parse_float(row.get("pace")),
                "estimated_pace": parse_float(row.get("estimatedPace")),
                "pace_per40": parse_float(row.get("pacePer40")),
                "player_impact_estimate": parse_float(row.get("playerImpactEstimate")),
                "possessions": parse_int(row.get("possessions")),
                "points_off_turnovers": parse_float(row.get("pointsOffTurnovers")),
                "points_second_chance": parse_float(row.get("pointsSecondChance")),
                "points_fast_break": parse_float(row.get("pointsFastBreak")),
                "points_in_paint": parse_float(row.get("pointsInPaint")),
                "percent_team_points": parse_float(row.get("percentTeamPoints")),
                "percent_team_assists": parse_float(row.get("percentTeamAssists")),
                "percent_team_rebounds": parse_float(row.get("percentTeamRebounds")),
                "percent_team_turnovers": parse_float(row.get("percentTeamTurnovers")),
                "percent_team_steals": parse_float(row.get("percentTeamSteals")),
                "percent_team_blocks": parse_float(row.get("percentTeamBlocks")),
                "percent_assisted_2point_made": parse_float(row.get("percentAssisted2PointMade")),
                "percent_unassisted_2point_made": parse_float(row.get("percentUnassisted2PointMade")),
                "percent_assisted_3point_made": parse_float(row.get("percentAssisted3PointMade")),
                "percent_unassisted_3point_made": parse_float(row.get("percentUnassisted3PointMade")),
                "percent_assisted_field_goals_made": parse_float(row.get("percentAssistedFieldGoalsMade")),
                "percent_unassisted_field_goals_made": parse_float(row.get("percentUnassistedFieldGoalsMade")),
            }
            chunk_records.append(record)

            if len(chunk_records) >= chunk_size:
                with engine.begin() as conn:
                    conn.execute(sql_to_use, chunk_records)
                total_loaded += len(chunk_records)
                chunk_records.clear()
                logger.info(f"Loaded {total_loaded:,} extended player game records...")

    if chunk_records:
        with engine.begin() as conn:
            conn.execute(sql_to_use, chunk_records)
        total_loaded += len(chunk_records)

    logger.info(f"Successfully finished loading {total_loaded:,} extended player game records.")
    return total_loaded
