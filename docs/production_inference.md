# Production Inference Pipeline Architecture & Operations

## 1. Overview & Architecture

The **Lakers in 5** Production Inference Pipeline delivers deterministic, leakage-safe pregame predictions for upcoming NBA games (specifically the 2026–27 regular season). It couples historical performance data stored in the Parquet/DuckDB analytical lakehouse with future schedules and offseason transactions to compute pregame feature vectors and evaluate champion ML models.

```text
2026-27 NBA Schedule (PDF) ──> ScheduleService ──> schedule_2026_27.parquet
                                                          │
2026 Offseason Transactions CSV ──> RosterService ───────┼─┐
                                                          │ │
Analytical Lakehouse (DuckDB/Parquet) ───────────────────┼─┼──> FeatureService (Pregame Features)
                                                          │ │         │
                                                          │ │         ▼ (52 features)
                                                          │ │   Champion Models (Joblib)
                                                          │ │   ├── Logistic Regression (Win Prob)
                                                          │ │   └── Ridge Regression (Margin)
                                                          │ │         │
                                                          │ │         ▼
                                                    GamePredictor (Inference Core)
                                                          │
                                           ┌──────────────┴──────────────┐
                                           ▼                             ▼
                                   FastAPI Service               CLI Prediction Tool
                           (`src/inference/api.py`)         (`scripts/predict_game.py`)
```

---

## 2. Temporal Leakage & Integrity Guarantees

Inference requires strictly causal data processing. To guarantee zero temporal leakage:

1. **Strict Date Cutoff in SQL Views:**
   Every query to the analytical lakehouse applies `WHERE game_date < ?` with the target game's calendar date.
2. **Target Game Exclusion:**
   If a future game record already exists with partial or placeholder stats, it is excluded via `AND game_id != ?`.
3. **Pregame Elo Evaluation:**
   Team Elo ratings are retrieved from the pre-game state of the most recent historical game prior to `target_game_date`, correctly rolled over across season boundaries (mean regression factor $0.75 \times \text{Elo} + 0.25 \times 1500$).
4. **Schedule & Rest Feature Calculation:**
   Rest days and back-to-back flags are calculated dynamically by comparing the target game date against the team's most recent prior game in the lakehouse or the 2026–27 schedule up to `target_game_date`.
5. **Cold Start & Season Boundary Handling:**
   For early-season games with fewer than 5 games played in the current season, the rolling window queries up to 5 games from the end of the previous season (2025–26) to ensure dense, non-empty rolling stat averages.
6. **Player Team Transition Awareness:**
   Offseason transactions (`nba_2026_offseason_transactions.csv`) are incorporated to map players to their new 2026–27 franchises, ensuring player-level rotation stats reflect the current roster rather than stale historical affiliations.

---

## 3. Model Feature Contract

The inference service generates a 52-column feature vector that strictly matches `MODEL_FEATURE_CONTRACT`:

| Feature Group | Column Count | Features |
| :--- | :--- | :--- |
| **Team Rolling Form (5-Game)** | 24 | `home_win_pct_5`, `away_win_pct_5`, `home_avg_points_5`, `away_avg_points_5`, `home_avg_points_allowed_5`, `away_avg_points_allowed_5`, `home_avg_margin_5`, `away_avg_margin_5`, `home_avg_fg_pct_5`, `away_avg_fg_pct_5`, `home_avg_fg3_pct_5`, `away_avg_fg3_pct_5`, `home_avg_ft_pct_5`, `away_avg_ft_pct_5`, `home_avg_rebounds_5`, `away_avg_rebounds_5`, `home_avg_assists_5`, `away_avg_assists_5`, `home_avg_steals_5`, `away_avg_steals_5`, `home_avg_blocks_5`, `away_avg_blocks_5`, `home_avg_turnovers_5`, `away_avg_turnovers_5` |
| **Team Rolling Form (10-Game)** | 8 | `home_win_pct_10`, `away_win_pct_10`, `home_avg_points_10`, `away_avg_points_10`, `home_avg_points_allowed_10`, `away_avg_points_allowed_10`, `home_avg_margin_10`, `away_avg_margin_10` |
| **Elo Ratings** | 3 | `home_elo`, `away_elo`, `elo_difference` |
| **Schedule & Rest** | 7 | `home_rest_days`, `away_rest_days`, `rest_difference`, `home_back_to_back`, `away_back_to_back`, `home_games_last_7`, `away_games_last_7` |
| **Player Rotation Aggregates** | 6 | `home_rotation_points_5`, `away_rotation_points_5`, `home_rotation_ts_5`, `away_rotation_ts_5`, `home_rotation_usage_5`, `away_rotation_usage_5` |
| **Total** | **52** | Strict column order and dtype matching Phase 3 training pipelines |

---

## 4. Champion Models

The production pipeline utilizes the models selected during Phase 3 walk-forward evaluation:

1. **Classification (Win Probability):**
   - **Artifact:** `models/champion_classifier.joblib`
   - **Model:** Logistic Regression with `SimpleImputer`, `StandardScaler`.
   - **Outputs:** Home Win Probability ($P \in [0, 1]$), Away Win Probability ($1 - P$).
2. **Regression (Point Margin):**
   - **Artifact:** `models/champion_regressor.joblib`
   - **Model:** Ridge Regression with `DifferentialFeatureTransformer(mode='diff_only')`, `SimpleImputer`, `StandardScaler`.
   - **Outputs:** Predicted Home Margin ($\hat{y} \in \mathbb{R}$, positive = home win margin, negative = away win margin).

---

## 5. Lakers-Specific Perspective Layer

The core prediction service is strictly team-agnostic (predicting from the Home vs. Away perspective). To serve Lakers fans and analysts, a specialized Lakers wrapper interprets the predictions relative to Los Angeles:

| Scenario | Win Probability Calculation | Margin Calculation |
| :--- | :--- | :--- |
| **Lakers at Home** (e.g. `GSW @ LAL`) | `lakers_win_prob = home_win_prob` | `predicted_lakers_margin = predicted_home_margin` |
| **Lakers on Road** (e.g. `LAL @ BOS`) | `lakers_win_prob = away_win_prob` | `predicted_lakers_margin = -predicted_home_margin` |

---

## 6. CLI Usage

The prediction CLI (`scripts/predict_game.py`) supports multiple operation modes:

### A. Next Upcoming Lakers Game
```bash
python scripts/predict_game.py --lakers-next --as-of-date 2026-10-20
```

### B. Specific Scheduled Game ID
```bash
python scripts/predict_game.py --game-id 2026-10-21-GSW-LAL
```

### C. Arbitrary Matchup & Date
```bash
python scripts/predict_game.py --home-team "Los Angeles Lakers" --away-team "Golden State Warriors" --date 2026-10-21
```

---

## 7. FastAPI Service Endpoints

The API is served via FastAPI in `src/inference/api.py`.

### Start API Server
```bash
uvicorn src.inference.api:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints

- **`GET /health`**
  - Health check verifying loaded models and DuckDB lakehouse connectivity.
- **`POST /predict`**
  - Predict any scheduled or custom matchup.
  - Body: `{"home_team": "Los Angeles Lakers", "away_team": "Golden State Warriors", "game_date": "2026-10-21"}`
- **`GET /predict/{game_id}`**
  - Predict a game by its schedule ID (e.g., `/predict/2026-10-21-GSW-LAL`).
- **`GET /predict/lakers/next?as_of_date=2026-10-20`**
  - Automatically fetches the next upcoming Lakers game and formats output from the Lakers perspective.
- **`GET /schedule/2026-27?team=LAL&limit=10`**
  - Lists 2026–27 regular season scheduled games with optional team filtering.

---

## 8. Verified 2026–27 Predictions
 
| Game ID | Date | Matchup | Lakers Win Prob | Predicted Margin | Key Context Factors |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `2026-10-21-GSW-LAL` | 2026-10-21 | Golden State Warriors @ Los Angeles Lakers | **71.7%** | **+6.2 pts** | Season opener at Crypto.com Arena, Lakers high baseline Elo. |
| `2026-10-24-LAL-PHX` | 2026-10-24 | Los Angeles Lakers @ Phoenix Suns | **50.8%** | **+0.1 pts** | First road test; 2 days rest for both teams. |
| `2026-10-29-LAL-MIN` | 2026-10-29 | Los Angeles Lakers @ Minnesota Timberwolves | **41.3%** | **-2.3 pts** | Road game against top Western contender; tight margin. |

---

## 9. Limitations & Edge Cases

1. **Early-Season Roster Continuity:**
   In the absence of early-season games, player-level stats rely on the previous season's per-minute averages combined with updated roster transaction affiliations.
2. **In-Game Live Adjustments:**
   Predictions represent pre-game expectations only; live in-game injury scratches occurring minutes before tip-off require updating player availability flags.
3. **Schedule Parsing Dependencies:**
   Schedule parsing is verified against the official NBA 2026–27 PDF structure; future schedule format changes will require parser validation.
