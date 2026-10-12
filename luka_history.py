import duckdb
import pandas as pd
from src.features.player_prediction_features import PlayerFeatureEngine
from src.models.player_models import PlayerPerformanceSuite
from src.inference.roster_service import RosterService

feat_engine = PlayerFeatureEngine()
roster_svc = RosterService()
suite = PlayerPerformanceSuite.load_artifacts("models")

con = duckdb.connect()
p_sql = "data/processed/parquet/player_game_stats.parquet"

print("=== LUKA DONCIC LAST 10 HISTORICAL GAMES ===")
luka_recent = con.execute(f"""
    SELECT 
        gameDateTimeEst,
        playerteamId,
        numMinutes,
        points,
        reboundsTotal,
        assists
    FROM '{p_sql}'
    WHERE personId = 1629029
    ORDER BY TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) DESC
    LIMIT 10
""").df()
print(luka_recent)

print("\n=== LUKA HISTORICAL CAREER TOTALS BY SEASON ===")
luka_seasons = con.execute(f"""
    SELECT 
        season_year,
        COUNT(*) as g,
        ROUND(AVG(TRY_CAST(numMinutes AS DOUBLE)), 1) as mpg,
        ROUND(AVG(TRY_CAST(points AS DOUBLE)), 1) as ppg,
        ROUND(AVG(TRY_CAST(reboundsTotal AS DOUBLE)), 1) as rpg,
        ROUND(AVG(TRY_CAST(assists AS DOUBLE)), 1) as apg,
        ROUND(SUM(TRY_CAST(points AS DOUBLE)) / NULLIF(SUM(TRY_CAST(numMinutes AS DOUBLE)), 0), 3) as pts_per_min
    FROM '{p_sql}'
    WHERE personId = 1629029
    GROUP BY season_year
    ORDER BY season_year
""").df()
print(luka_seasons)
