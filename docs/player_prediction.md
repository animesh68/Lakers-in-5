# Lakers in 5 — Phase 8: Player Performance Prediction Backend

**System**: Production NBA Player-Level Box Score Prediction Subsystem  
**Date**: September 27, 2026  
**Status**: Production Validated  

---

## 1. Overview & Objectives

Phase 8 introduces a deterministic, leakage-safe machine learning subsystem to predict individual player performance for upcoming scheduled NBA regular season games. 

### Initial Prediction Targets:
1. **Expected Minutes** (`actual_minutes` continuous regression, bounded $0.0 \dots 48.0$)
2. **Points** (`points` continuous regression, bounded $0.0 \dots 70.0$)
3. **Rebounds** (`reboundsTotal` continuous regression, bounded $0.0 \dots 35.0$)
4. **Assists** (`assists` continuous regression, bounded $0.0 \dots 30.0$)

Every projection displayed is computed strictly by trained regularized ML models using pregame information, with zero target-game leakage and full train/serve parity.

---

## 2. Information Architecture & Canonical Eligibility Rules

### A. Active Rotation Player Universe Resolution
To prevent predicting obsolete or fabricated players, the canonical pregame player universe is determined by:
1. **Recent Franchise History**: Selecting players who actively logged minutes for the franchise in recent season games prior to target game date $D$.
2. **2026 Offseason Transaction State**:
   - **Departures**: Players traded or departing in free agency are removed as of the transaction date ($2026\text{-}07\text{-}01$).
   - **Additions**: Players acquired via trade or signing are assigned to their new franchise.
   - **Re-signings**: Core rotation players re-signing with their team remain established.
3. **Validation Benchmark Case**:
   - *Kawhi Leonard*: As of $2026\text{-}10\text{-}21$, officially assigned to the Toronto Raptors (`is_transition_player = True`, `prior_team = "LA Clippers"`, `games_with_current_team = 0`).

---

## 3. Feature Definitions (24-Feature Canonical Contract)

All features are computed strictly prior to tip-off ($\text{game\_date} < D$):

| Feature Name | Description | Source / Formula |
| :--- | :--- | :--- |
| `player_min_avg_5` | 5-game rolling minutes average | Strictly preceding games |
| `player_min_avg_10` | 10-game rolling minutes average | Strictly preceding games |
| `player_min_season_avg` | Season average minutes | Cumulative preceding games |
| `player_pts_per_min_10` | Points per minute rate over last 10 games | $\sum \text{PTS}_{10} / \sum \text{MIN}_{10}$ |
| `player_reb_per_min_10` | Rebounds per minute rate over last 10 games | $\sum \text{REB}_{10} / \sum \text{MIN}_{10}$ |
| `player_ast_per_min_10` | Assists per minute rate over last 10 games | $\sum \text{AST}_{10} / \sum \text{MIN}_{10}$ |
| `player_ts_pct_10` | True Shooting percentage | $\text{PTS} / (2 \times (\text{FGA} + 0.44 \times \text{FTA}))$ |
| `player_usage_pct_10` | Possession load proxy | $(\text{FGA} + 0.44\text{FTA} + \text{TOV}) / (2 \times \text{MIN})$ |
| `is_starter_ratio_10` | Fraction of last 10 games started | Starting lineup indicator |
| `player_games_played_season` | Games played prior to target date | Game count |
| `is_home` | Home court venue flag | $1.0$ if Home, $0.0$ if Road |
| `days_since_last_game` | Rest recency | Target date minus prior game date |
| `is_b2b` | Back-to-back contest indicator | $1.0$ if $\text{rest} = 1\text{ day}$ |
| `team_pace_10` | Team rolling pace (possessions) | 10-game rolling average |
| `opponent_pace_10` | Opponent rolling pace | 10-game rolling average |
| `opponent_def_rating_10` | Opponent defensive rating | Points allowed per 100 poss |
| `team_off_rating_10` | Team offensive rating | Points scored per 100 poss |
| `is_team_change` | Offseason or in-season transfer flag | $1.0$ if new franchise |
| `days_since_team_change` | Days elapsed since transaction date | Elapsed calendar days |
| `games_with_current_team` | Prior games logged with current team | $0$ for new team opener |
| `prior_team_min_avg` | Minutes average with prior team | Fallback rate for trades |
| `prior_team_pts_per_min` | Prior team points per minute | Prior team history |
| `prior_team_reb_per_min` | Prior team rebounds per minute | Prior team history |
| `prior_team_ast_per_min` | Prior team assists per minute | Prior team history |

---

## 4. Cold-Start Strategy & Shrinkage

When a player has $0$ games with their current team (such as a traded player in season opener or a rookie):
1. **Zero Fabrication**: Fake current-team game stats are never invented.
2. **Principled Shrinkage**:
   - For traded players: Use prior-team per-minute production rates weighted against league position priors.
   - For rookies / untracked players: Fallback gracefully to league priors ($\text{MIN} = 18.5$, $\text{PTS/MIN} = 0.46$, $\text{REB/MIN} = 0.19$, $\text{AST/MIN} = 0.10$).

---

## 5. Model Architecture & Walk-Forward Validation Results

### Architecture:
- **Model 1 (Minutes)**: Ridge Regressor ($\alpha = 15.0$, feature scaling, bounded $[0.0, 48.0]$).
- **Models 2–4 (Points, Rebounds, Assists)**: Ridge Regressors ($\alpha = 10.0$) taking pregame features + `expected_minutes` from Model 1 as an anchor.

### Chronological Walk-Forward Split (Train: 2023–2025 [57,164 games], Test: 2025–2026 [29,982 games]):

| Target Metric | Overall Test MAE | Overall Test RMSE | Overall Bias | High-Minute MAE ($\ge 25$ mpg) | Low-Minute MAE ($< 15$ mpg) | Traded Players MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Minutes** | **5.271 min** | **6.828 min** | +0.309 min | 4.977 min | 7.200 min | 12.442 min |
| **Points** | **4.838 pts** | **6.271 pts** | +0.215 pts | 5.520 pts | 4.300 pts | 7.568 pts |
| **Rebounds** | **2.003 reb** | **2.612 reb** | +0.069 reb | 2.224 reb | 1.853 reb | 2.650 reb |
| **Assists** | **1.428 ast** | **1.922 ast** | +0.076 ast | 1.701 ast | 1.150 ast | 1.861 ast |

---

## 6. API Contract

### Endpoint: `POST /predict/players`
```json
{
  "home_team": "LAL",
  "away_team": "GSW",
  "game_date": "2026-10-21"
}
```

### Response:
```json
{
  "game_id": "5_LAL_GSW_2026-10-21",
  "game_date": "2026-10-21",
  "home_team": "Los Angeles Lakers",
  "away_team": "Golden State Warriors",
  "players": [
    {
      "player_id": "1630559",
      "player_name": "Austin Reaves",
      "team": "Los Angeles Lakers",
      "team_code": "LAL",
      "expected_minutes": 19.6,
      "predicted_points": 12.7,
      "predicted_rebounds": 3.2,
      "predicted_assists": 3.6,
      "is_transition_player": false
    },
    {
      "player_id": "1629012",
      "player_name": "Collin Sexton",
      "team": "Los Angeles Lakers",
      "team_code": "LAL",
      "expected_minutes": 15.2,
      "predicted_points": 11.1,
      "predicted_rebounds": 2.5,
      "predicted_assists": 2.0,
      "is_transition_player": true
    }
  ],
  "model_versions": {
    "minutes": "PlayerMinutes-Ridge-v1",
    "points": "PlayerPoints-Ridge-v1",
    "rebounds": "PlayerRebounds-Ridge-v1",
    "assists": "PlayerAssists-Ridge-v1"
  },
  "feature_schema_version": "v1.0-player",
  "prediction_timestamp": "2026-09-27T19:50:00Z"
}
```

---

## 7. Known Limitations & Future Work (Phase 8.1+)

1. **In-game Foul Trouble / Sudden Injuries**: Models predict expected pregame baseline rotation. Unexpected in-game ejections or early foul trouble cannot be anticipated before tip-off.
2. **Late Breaking Injury News**: When real-time injury reports confirm a player as OUT on game day, rotation minutes will redistribute across remaining active players via the availability handler in Phase 8.1.
