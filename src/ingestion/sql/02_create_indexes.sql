-- =============================================================================
-- Lakers in 5 — Index Creation DDL (02_create_indexes.sql)
-- Optimizes temporal queries, player tracking, and team performance rollups
-- =============================================================================

-- Games Indexes
CREATE INDEX IF NOT EXISTS idx_games_date ON games (game_date);
CREATE INDEX IF NOT EXISTS idx_games_datetime ON games (game_datetime_est);
CREATE INDEX IF NOT EXISTS idx_games_home_away ON games (home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_winner ON games (winner);

-- Team Game Stats Indexes
CREATE INDEX IF NOT EXISTS idx_team_stats_team_date ON team_game_stats (team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_team_stats_opponent ON team_game_stats (opponent_team_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_ext_team ON team_game_stats_extended (team_id);

-- Player Game Stats Indexes
CREATE INDEX IF NOT EXISTS idx_player_stats_person_date ON player_game_stats (person_id, game_date);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_game_stats (player_team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_player_stats_ext_person ON player_game_stats_extended (person_id);

-- Dimension Table Indexes
CREATE INDEX IF NOT EXISTS idx_players_name ON players (last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_team_histories_id ON team_histories (team_id);
