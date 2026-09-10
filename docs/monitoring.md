# Lakers in 5 — Phase 5: Monitoring, Prediction Logging & Dashboard

## 1. System Architecture Overview

Phase 5 establishes a production-grade MLOps monitoring and prediction logging layer around the *Lakers in 5* forecasting system. It tracks live predictions, settles completed game outcomes, monitors rolling time-windowed metrics and probability calibration, detects input feature and output prediction drift (via PSI), evaluates holistic model health, and provides deterministic retraining recommendations.

```text
                               Prediction Request (FastAPI / CLI)
                                              │
                                              ▼
                                   ProductionFeatureService
                                              │ (52-column vector + deterministic hash)
                                              ▼
                                    Champion ML Pipelines
                                    ├── Logistic Regression (Standard)
                                    └── Ridge Regression (Diff Only)
                                              │
                                              ▼
                                        GamePredictor
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                    Prediction API / CLI            PredictionRepository
                                                              │
                                               ┌──────────────┴──────────────┐
                                               ▼                             ▼
                                      PostgreSQL (Neon)              DuckDB / Parquet Store
                                       (`predictions`)               (`data/monitoring/`)
                                               │
                   ┌───────────────────────────┼───────────────────────────┐
                   ▼                           ▼                           ▼
          OutcomeIngestionService     MonitoringMetricsService     DataDriftDetector
           (Autoruns on completed)      (7d, 30d, season, all)      (PSI & Shift stats)
                   │                           │                           │
                   └───────────────────────────┼───────────────────────────┘
                                               ▼
                                      ModelHealthService
                               (HEALTHY / WARNING / CRITICAL)
                                               │
                                               ▼
                                 RetrainingDecisionEngine
                           (RETRAIN_RECOMMENDED / NO_RETRAIN_NEEDED)
                                               │
                              ┌────────────────┴────────────────┐
                              ▼                                 ▼
                     FastAPI Monitoring API            Streamlit Dashboard
                      (`src/inference/api.py`)          (`src/dashboard/app.py`)
```

---

## 2. Prediction Logging & Store Schema

Predictions are persisted via the `PredictionRepository` abstraction (`src/monitoring/repository.py`), supporting PostgreSQL with automatic local DuckDB/Parquet fallback.

### Database Schema (`predictions` table)
| Column Name | Data Type | Constraints / Index | Description |
| :--- | :--- | :--- | :--- |
| `prediction_id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique prediction UUID |
| `game_id` | `VARCHAR(64)` | `INDEX` | Official NBA schedule / game number |
| `game_date` | `DATE` | `INDEX` | Match calendar date (YYYY-MM-DD) |
| `home_team`, `away_team` | `VARCHAR(100)` | `NOT NULL` | Franchise names |
| `home_team_id`, `away_team_id` | `VARCHAR(32)` | `NOT NULL` | Unique franchise IDs |
| `prediction_created_at` | `TIMESTAMP` | `INDEX` | UTC timestamp of prediction creation |
| `model_version` | `VARCHAR(128)` | `INDEX` | Deterministic model version string |
| `classifier_model_version` | `VARCHAR(128)` | `NOT NULL` | Champion classifier identifier |
| `regressor_model_version` | `VARCHAR(128)` | `NOT NULL` | Champion regressor identifier |
| `home_win_probability` | `FLOAT` | `NOT NULL` | Calibrated home win probability ($P \in [0, 1]$) |
| `away_win_probability` | `FLOAT` | `NOT NULL` | Away win probability ($1 - P$) |
| `predicted_home_margin` | `FLOAT` | `NOT NULL` | Expected point spread (home - away) |
| `feature_schema_version` | `VARCHAR(32)` | `NOT NULL` | Feature definition version (e.g. `"v1"`) |
| `feature_snapshot_hash` | `VARCHAR(64)` | `INDEX` | Deterministic SHA-256 hash of pregame feature vector |
| `status` | `VARCHAR(32)` | `INDEX` | `"pending"` \| `"completed"` \| `"cancelled"` |
| `actual_home_score` | `INTEGER` | `NULLABLE` | Final home team points |
| `actual_away_score` | `INTEGER` | `NULLABLE` | Final away team points |
| `actual_home_win` | `INTEGER` | `NULLABLE` | Final win indicator ($1$ = home win, $0$ = away win) |
| `actual_home_margin` | `FLOAT` | `NULLABLE` | Final point margin (`home_score - away_score`) |
| `outcome_recorded_at` | `TIMESTAMP` | `NULLABLE` | UTC timestamp when outcome was settled |
| `created_at`, `updated_at` | `TIMESTAMP` | `NOT NULL` | Audit timestamps |

---

## 3. Deterministic Feature Snapshot Hashing

To guarantee reproducibility and trace which exact feature state was fed to the models without storing 52 duplicate floating-point columns per prediction, the system canonicalizes and hashes the feature vector:

$$\text{feature\_snapshot\_hash} = \text{SHA-256}\left( \text{JSON\_SERIALIZE}(\text{SORTED\_KEYS}(\{k: \text{round}(v, 6)\})) \right)$$

- **Invariance:** Independent of dictionary insertion order or Python version.
- **Sensitivity:** Any change to prior rolling stats or Elo produces a distinct hash.

---

## 4. Outcome Ingestion Workflow

`OutcomeIngestionService` (`src/monitoring/outcomes.py` / `scripts/update_prediction_outcomes.py`):
1. Queries `pending` predictions from the prediction repository.
2. Matches `game_id` or `(home_team_id, away_team_id, game_date)` against official completed box scores in the DuckDB lakehouse (`data/processed/parquet/games.parquet`).
3. Updates `actual_home_score`, `actual_away_score`, `actual_home_win`, `actual_home_margin`, sets `status = 'completed'`, and records `outcome_recorded_at`.
4. **Idempotency:** Future unplayed games remain `pending`; re-running the script is safe and non-destructive.

---

## 5. Monitoring Metrics & Time Windows

`MonitoringMetricsService` (`src/monitoring/metrics.py`) supports time-aware filtering:
- **`7d`**: Predictions within the last 7 calendar days.
- **`30d`**: Predictions within the last 30 calendar days.
- **`season`**: Predictions in the current active NBA season (October 1 to present).
- **`all_time`**: All historical settled predictions.

### Metrics Computed:
- **Classification:** Accuracy, Log Loss, Brier Score, ROC-AUC, Expected Calibration Error (ECE).
- **Regression:** Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Prediction Bias ($\hat{y} - y$).
- **Decile Calibration:** 10 uniform probability buckets (`0.0–0.1`, ..., `0.9–1.0`) comparing mean predicted probability vs. empirical actual win rate.

---

## 6. Data Drift & Prediction Distribution Monitoring

`DataDriftDetector` (`src/monitoring/drift.py`) computes drift between the Phase 3 historical baseline feature distribution and recent production features:

### Population Stability Index (PSI) Formulation
$$\text{PSI} = \sum_{b=1}^{B} \left( P_b - Q_b \right) \ln\left(\frac{P_b}{Q_b}\right)$$
- $Q_b$: Proportion of observations in quantile bin $b$ from the baseline training distribution.
- $P_b$: Proportion of observations in bin $b$ from recent production prediction features.

### Operational Heuristic Thresholds:
| PSI Range | Drift Status | Actionable Meaning |
| :--- | :--- | :--- |
| $\text{PSI} < 0.10$ | `Low Drift` (Healthy) | Feature distribution matches baseline; no action required. |
| $0.10 \le \text{PSI} \le 0.25$ | `Moderate Drift` (Warning) | Slight shift in team/player stats; monitor closely. |
| $\text{PSI} > 0.25$ | `Significant Drift` (High) | Major shift (e.g. trade deadline, rule changes); flag for retraining. |

### Output Prediction Drift:
Monitors `home_win_probability` variance, mean entropy, and point margin shifts to detect probability collapse or extreme bias.

---

## 7. Model Health & Retraining Governance

### Model Health Status Logic (`ModelHealthService`)
- **`HEALTHY`**: Log Loss $\le 0.630$, MAE $\le 11.2$, ECE $\le 0.050$, $< 3$ high-drift features.
- **`WARNING`**: Log Loss $0.630–0.660$, or MAE $11.2–12.5$, or ECE $0.050–0.090$, or $3–5$ high-drift features.
- **`CRITICAL`**: Log Loss $> 0.660$, or MAE $> 12.5$, or ECE $> 0.090$, or $> 5$ high-drift features.

### Retraining Recommendation Logic (`RetrainingDecisionEngine`)
Outputs `RETRAIN_RECOMMENDED` or `NO_RETRAIN_NEEDED` based on:
1. **Sample Size Gate:** Requires at least $N \ge 50$ newly completed games.
2. **Performance Degradation Trigger:** $\text{Log Loss} > \text{Baseline} + 0.020$ OR $\text{MAE} > \text{Baseline} + 1.0\text{ pts}$.
3. **Calibration Decay Trigger:** $\text{ECE} > 0.060$.
4. **Drift Trigger:** $\ge 4$ features with $\text{PSI} > 0.25$.

> [!IMPORTANT]
> **Strict Governance Principle:** The retraining engine provides a **decision-support advisory only**. It will **never automatically overwrite or promote models**. Model retraining and deployment remain deliberate, engineer-controlled operations.

---

## 8. Operational Commands & API

### Start FastAPI Server
```bash
uvicorn src.inference.api:app --host 0.0.0.0 --port 8000 --reload
```

### Launch Streamlit Dashboard
```bash
python scripts/run_dashboard.py
# or: streamlit run src/dashboard/app.py
```

### Generate Predictions with Persistence
```bash
# Predict next Lakers game and persist
python scripts/predict_game.py --lakers-next --persist

# Predict arbitrary matchup and persist
python scripts/predict_game.py --home-team LAL --away-team GSW --date 2026-10-21 --persist
```

### Sync Completed Outcomes
```bash
python scripts/update_prediction_outcomes.py
```

### Key REST Monitoring Endpoints
- `GET /monitoring/health` — Full health report (`HEALTHY` / `WARNING` / `CRITICAL`).
- `GET /monitoring/performance?window=30d` — Rolling Log Loss, Brier, Accuracy, MAE, RMSE.
- `GET /monitoring/calibration?window=season` — Decile calibration curve data.
- `GET /monitoring/drift?window=30d` — Feature PSI table and output prediction distribution.
- `GET /monitoring/predictions?status=pending` — Query prediction records.
- `GET /monitoring/retraining-decision` — Retraining advisory recommendation.
