# Lakers in 5

> **"Lakers in 5"** is a production-oriented NBA prediction system and MLOps platform engineered to forecast upcoming Los Angeles Lakers games with strict temporal leakage prevention, train/serve feature parity, automated outcome logging, data drift monitoring, and retraining governance.

---

## 1. System Architecture

```text
RAW HISTORICAL NBA DATA (1946–2026)
                ↓
    DuckDB / Parquet Analytical Lakehouse (data/processed/parquet/)
                ↓
    Leakage-Safe Feature Engineering (src/features/)
    ├── Rolling Team Form & Efficiency (L5, L10)
    ├── Chronological Pregame Elo Ratings
    ├── Schedule Density & Rest Days
    └── Canonical Pregame Player Rotation Aggregates
                ↓
    Time-Series Walk-Forward Cross-Validation (10 Folds, 2015–2025)
                ↓
    Champion Production ML Models (models/)
    ├── Logistic Regression (Win Probability)
    └── Ridge Regression (Point Spread)
                ↓
    Production Inference & Feature Service (src/inference/)
    ├── Deterministic SHA-256 Feature Snapshot Hashing
    ├── 2026–27 Schedule & Offseason Roster Ingestion
    └── Fast Pre-Game Prediction Engine
                ↓
    ┌───────────────────────────┴───────────────────────────┐
    ▼                                                       ▼
FastAPI Serving API (src/inference/api.py)     Prediction Store (PostgreSQL / DuckDB)
    │                                                       │
    │                                       ┌───────────────┴───────────────┐
    │                                       ▼                               ▼
    │                            Outcome Settlement Service      Data Drift & PSI Engine
    │                            (src/monitoring/outcomes.py)    (src/monitoring/drift.py)
    │                                       │                               │
    └───────────────────────────────────────┼───────────────────────────────┘
                                            ▼
                                Streamlit MLOps Dashboard
                                  (src/dashboard/app.py)
                                            │
                                            ▼
                              Model Health & Retraining Governance
                                  (src/monitoring/health.py)
```

---

## 2. Directory Structure

```text
Lakers in 5/
│
├── data/
│   ├── raw/                  # Immutable original raw datasets (Games, Box scores, Logs)
│   ├── processed/parquet/    # Analytical Lakehouse (games, team stats, player stats)
│   ├── features/             # ML-ready feature matrices (73,279 rows x 61 cols)
│   ├── evaluation/           # Model validation predictions, calibration, importances
│   └── monitoring/           # Local persistent prediction store (fallback)
│
├── src/
│   ├── ingestion/            # Raw data loading, schema, and Lakehouse converters
│   ├── features/             # Leakage-safe feature pipelines (Elo, form, rotation)
│   ├── models/               # Model factories, preprocessing, evaluation metrics
│   ├── inference/            # Production prediction engine, schedule & roster services
│   ├── monitoring/           # Prediction repository, metrics, PSI drift, health diagnostics
│   ├── dashboard/            # Streamlit interactive UI application
│   └── utils/                # Database engine, connection pool, logging
│
├── models/                   # Serialized champion artifacts (.joblib)
├── tests/                    # 57 automated unit, parity, leakage, and monitoring tests
├── scripts/                  # Executable CLI tools
│   ├── build_features.py     # Feature dataset builder
│   ├── run_experiments.py    # Walk-forward cross-validation trainer
│   ├── predict_game.py       # Pre-game prediction CLI runner
│   ├── update_prediction_outcomes.py # Outcome settlement runner
│   └── run_dashboard.py      # Streamlit dashboard launcher
└── docs/                     # Full architecture & operational documentation
```

---

## 3. Quickstart & Operational Commands

### 3.1. Install Dependencies & Activate Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2. Run Pre-Game Prediction (CLI)
```bash
# Predict next upcoming Lakers game
python scripts/predict_game.py --lakers-next

# Predict with persistent logging to database
python scripts/predict_game.py --lakers-next --persist

# Predict arbitrary matchup
python scripts/predict_game.py --home-team LAL --away-team GSW --date 2026-10-21 --persist
```

### 3.3. Launch FastAPI Prediction & Monitoring Server
```bash
uvicorn src.inference.api:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`

### 3.4. Launch Streamlit Monitoring Dashboard
```bash
python scripts/run_dashboard.py
# or: streamlit run src/dashboard/app.py
```

### 3.5. Sync Completed Game Outcomes
```bash
python scripts/update_prediction_outcomes.py
```

### 3.6. Run with Docker Compose (Production Stack)
```bash
# Set database environment variable (optional, falls back to local Parquet)
export DATABASE_URL="postgresql://user:password@ep-cool-lake-12345.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Build and start FastAPI and Streamlit dashboard
docker compose up -d --build

# Access services:
# - API & Healthcheck:  http://localhost:8000 (Docs: http://localhost:8000/docs)
# - Monitoring UI:      http://localhost:8501
```

### 3.7. Run Complete Test Suite
```bash
python -m pytest tests/ -v
# 65 passing tests covering integrity, parity, leakage, inference, monitoring, and containerization
```

---

## 4. Key Documentation Links
- [Feature Engineering & Leakage Guardrails](file:///docs/feature_engineering.md)
- [Model Experimentation & Validation Benchmarks](file:///docs/model_experimentation.md)
- [Production Inference Pipeline](file:///docs/production_inference.md)
- [Monitoring, Drift & Retraining Governance](file:///docs/monitoring.md)
- [Containerization & Deployment Guide](file:///docs/deployment.md)

