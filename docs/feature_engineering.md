# Lakers in 5 — Phase 2A: Feature Engineering & Leakage Prevention Document

This document outlines the architecture, mathematical specifications, rolling window methodologies, temporal leakage guardrails, and schema definitions for the **Lakers in 5** game-level ML feature dataset.

---

## 1. Feature Engineering Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │       data/raw/ (Immutable Raw CSVs)         │
                               │  73k Games, 146k Team Stats, 1.67M Players   │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                      ┌───────────────────────────────────────────────────────────────┐
                      │            ANALYTICAL LAKEHOUSE (DuckDB / Parquet)            │
                      │                    data/processed/parquet/                    │
                      │                                                               │
                      │  • games.parquet (73,279 official games)                      │
                      │  • team_game_stats.parquet (146,560 records)                  │
                      │  • team_game_stats_extended.parquet (79,724 records)          │
                      │  • player_game_stats.parquet (1.67M records)                  │
                      │  • player_game_stats_extended.parquet (838k records)          │
                      └──────────────────────┬────────────────────────────────────────┘
                                             │
                                             ▼ (Vectorized SQL Window Functions)
                      ┌───────────────────────────────────────────────────────────────┐
                      │           LEAKAGE-SAFE FEATURE ENGINEERING PIPELINE           │
                      │                        src/features/                          │
                      │                                                               │
                      │  • Team Form & Advanced Efficiency (team_features.py)         │
                      │  • Chronological Pregame Elo (elo.py)                         │
                      │  • Schedule Density & Rest Days (schedule_features.py)        │
                      │  • Team-Aware Player Rotation Form (player_features.py)       │
                      │  • Leakage Verification Suite (leakage_checks.py)             │
                      └──────────────────────┬────────────────────────────────────────┘
                                             │
                                             ▼
                      ┌───────────────────────────────────────────────────────────────┐
                      │              ML-READY GAME FEATURE MATRIX (73,279 rows)       │
                      │               data/features/game_features.parquet             │
                      │               data/features/feature_metadata.json             │
                      └───────────────────────────────────────────────────────────────┘
```

---

## 2. Core Principle: Temporal Leakage Prevention

> [!CAUTION]
> **Strict Axiom:** For a game taking place on date $D$, **EVERY SINGLE FEATURE** must represent information that was known **strictly before that game's tip-off**.
> 
> $$\text{source\_game\_date} < D$$
> 
> Under no circumstances may the current game's result, box score, plus/minus, points, or player statistics influence its own feature representation.

### Guardrails Implemented:
1. **Strict Window Offsets:** SQL window functions use `ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING` (and `10 PRECEDING AND 1 PRECEDING`), strictly excluding the current row ($0\text{ PRECEDING}$).
2. **Cold-Start Season Openers:** In the first game of a season for any team, prior same-season history is non-existent. These features are strictly assigned `NaN` / `NULL` instead of looking backward into future games or guessing values.
3. **Pregame Elo Ratings:** Elo ratings are recorded *before* the match is simulated/evaluated, and updated *afterwards*.
4. **Calendar-Bound Schedule Intervals:** Back-to-back flags and games in the last 7 days only look at games in the range $[D - 7\text{ days}, D - 1\text{ day}]$.
5. **Separation of Targets:** `target_home_win` and `target_point_margin` are strictly labeled as prediction targets and excluded from feature inputs.

---

## 3. Feature Groups & Mathematical Definitions

### 3.1. Basic Game Information
* `game_id`: Official NBA match identifier (e.g. `'0022300123'`).
* `game_date`: Calendar date of tip-off.
* `season`: Starting year of the NBA season (e.g., 2025 for 2025–26 season).
* `home_team_id`, `away_team_id`: NBA franchise unique numerical IDs.
* `home_team`, `away_team`: Full franchise display name.

### 3.2. Team Recent Form (Last 5 & Last 10 Same-Season Games)
Calculated separately for both Home and Away franchises over preceding games in the current season:
* `win_pct_5`, `win_pct_10`: Proportion of victories over the last $N$ games ($\frac{\sum \text{wins}}{N}$).
* `avg_points_5`, `avg_points_10`: Mean points scored over the last $N$ games.
* `avg_points_allowed_5`, `avg_points_allowed_10`: Mean points conceded over the last $N$ games.
* `point_diff_5`, `point_diff_10`: Average net scoring margin (`avg_points` - `avg_points_allowed`).

### 3.3. Advanced Team Strength & Efficiency (Tracking Era 1996+)
Calculated separately for both Home and Away franchises over preceding same-season games from `team_game_stats_extended`:
* `off_rating_5`, `off_rating_10`: Offensive rating (points scored per 100 possessions).
* `def_rating_5`, `def_rating_10`: Defensive rating (points allowed per 100 possessions).
* `efg_5`, `efg_10`: Effective Field Goal Percentage ($\frac{\text{FGM} + 0.5 \times \text{3PM}}{\text{FGA}}$).
* `ts_5`, `ts_10`: True Shooting Percentage ($\frac{\text{PTS}}{2 \times (\text{FGA} + 0.44 \times \text{FTA})}$).
* `pace_5`, `pace_10`: Number of possessions per 48 minutes.

### 3.4. Elo Rating System
Chronological Elo tracking across NBA franchise history (1946–2026):
* **Initial Rating:** $R_0 = 1500.0$
* **K-Factor:** $K = 20.0$
* **Home Court Advantage:** $H = 100.0\text{ Elo points}$
* **Season Mean Reversion:** $R_{\text{new\_season}} = 0.75 \times R_{\text{old}} + 0.25 \times 1500.0$
* **Expected Win Probability:**
  $$E_H = \frac{1}{1 + 10^{-( (R_H + H) - R_A ) / 400}}$$
* **Features:**
  * `home_elo`: Pregame Elo rating of Home team.
  * `away_elo`: Pregame Elo rating of Away team.
  * `elo_difference`: $(R_H + H) - R_A$.

### 3.5. Schedule & Rest Features
* `home_rest_days`, `away_rest_days`: Calendar days elapsed since the team's previous game in the same season.
* `rest_difference`: `home_rest_days` - `away_rest_days`.
* `home_back_to_back`, `away_back_to_back`: Boolean flag ($1$ if `rest_days == 1`, else $0$).
* `home_games_last_7`, `away_games_last_7`: Total games played by the team in the 7 days prior $[D - 7, D - 1]$.

### 3.6. Player Rotation Aggregates (Pregame Canonical Definition)
Aggregated performance of core rotation players prior to target game tip-off:
* **Canonical Pregame Definition:** For team $T$ as of target date $D$ in season $S$, the rotation comprises all players on team $T$ who played in at least one game for team $T$ in season $S$ with $\text{game\_date} < D$ and averaged $\ge 10.0$ minutes/game over their last $\le 5$ appearances for team $T$.
* **Target-Game Participation Leakage Elimination:** Feature generation strictly avoids conditioning on which players actually stepped onto the court in game $G$ (which is unknowable pregame). Instead, rotation stats are constructed strictly from prior appearances.
* **Aggregated Metrics:**
  * `rotation_points_5`: Average points scored by active rotation players over their last 5 games with that team.
  * `rotation_ts_5`: Average true shooting % of active rotation players.
  * `rotation_usage_5`: Average usage % of active rotation players.
* **Team-Awareness Rule:** If Player $P$ was traded from Team $A$ to Team $B$, Player $P$'s games on Team $A$ are never counted toward Team $B$'s metrics.

---

## 4. Target Variables (Prediction Targets)

* `target_home_win`: Binary indicator ($1$ if `home_score > away_score`, else $0$).
* `target_point_margin`: Continuous integer (`home_score - away_score`).

---

## 5. Execution & Verification

To execute the feature engineering pipeline and run automated leakage verification:

```bash
# Generate features and metadata
python scripts/build_features.py

# Run unit tests
pytest tests/test_features.py -v
```
