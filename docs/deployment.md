# Deployment & Containerization Guide — Lakers in 5

## 1. Production Architecture Overview

The *Lakers in 5* production deployment packages the FastAPI inference service and Streamlit monitoring dashboard into a reproducible, slim container environment.

```text
                            Docker Compose
                                   |
                  +----------------+----------------+
                  |                                 |
                  v                                 v
          FastAPI API Container          Streamlit Dashboard Container
             (Port 8000)                        (Port 8501)
                  |                                 |
                  +----------------+----------------+
                                   |
                  +----------------+----------------+
                  |                                 |
                  v                                 v
         Embedded Lakehouse            External Managed Serving DB
          (DuckDB / Parquet)                (Neon PostgreSQL)
```

### Core Architecture Components
1. **FastAPI Inference Container (`api`):** Production ASGI server (`uvicorn`) exposing prediction, schedule, and monitoring endpoints on port `8000`.
2. **Streamlit Dashboard Container (`dashboard`):** Real-time monitoring and Lakers forecasting dashboard exposing UI on port `8501`.
3. **Embedded Analytical Storage:** In-container read-only DuckDB engine querying `/app/data/processed/parquet/` and `/app/data/features/game_features.parquet`.
4. **External PostgreSQL Database:** Neon cloud PostgreSQL serving database for persistent prediction logging and settlement (configured via `DATABASE_URL`).

---

## 2. Docker Image Specifications

- **Base Image:** `python:3.11-slim` (minimal Debian bookworm runtime with system `curl` and `libgomp1`).
- **Security:** Executes as a non-root system user (`appuser`, UID 1000, GID 1000).
- **Working Directory:** `/app`
- **Environment Flags:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PYTHONPATH=/app`.
- **Image Size Optimization:** Excludes raw CSV data (~850 MB), test caches, virtual environments, and intermediate experiment runs via `.dockerignore`.

---

## 3. Environment Variables & Secrets

All credentials and dynamic configurations are injected via environment variables. **No credentials or secrets are baked into the Docker image.**

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Optional | `""` | Full SQLAlchemy connection string for Neon PostgreSQL |
| `POSTGRES_HOST` | Optional | `localhost` | Neon / Postgres database host |
| `POSTGRES_PORT` | Optional | `5432` | Postgres database port |
| `POSTGRES_DB` | Optional | `lakers_in_5` | Postgres database name |
| `POSTGRES_USER` | Optional | `postgres` | Postgres user |
| `POSTGRES_PASSWORD` | Optional | `""` | Postgres password |
| `DB_POOL_SIZE` | Optional | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | Optional | `20` | SQLAlchemy max pool overflow connections |
| `DB_TIMEOUT` | Optional | `30` | Connection timeout in seconds |

> **Fallback Mode:** If `DATABASE_URL` is empty or unreachable, the system automatically uses `/app/data/monitoring/predictions.parquet` for local prediction logging.

---

## 4. Building the Production Image

Build the container image using Docker:

```bash
docker build -t lakers-in-5:latest .
```

---

## 5. Running the Containers Individually

### A. Run FastAPI Inference Service (Port 8000)
```bash
docker run -d \
  --name lakers_api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@ep-cool-lake-12345.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  lakers-in-5:latest
```

### B. Run Streamlit Monitoring Dashboard (Port 8501)
```bash
docker run -d \
  --name lakers_dashboard \
  -p 8501:8501 \
  -e DATABASE_URL="postgresql://user:password@ep-cool-lake-12345.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  lakers-in-5:latest \
  streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

---

## 6. Docker Compose Orchestration

Use `docker-compose.yml` to launch both the API and Dashboard simultaneously:

```bash
# 1. Provide database credentials via environment or .env file
export DATABASE_URL="postgresql://user:password@ep-cool-lake-12345.us-east-2.aws.neon.tech/neondb?sslmode=require"

# 2. Build and run in detached mode
docker compose up -d --build

# 3. View service logs
docker compose logs -f

# 4. Tear down services
docker compose down
```

---

## 7. Container Health Check

The image defines a Docker `HEALTHCHECK`:
- **Command:** `curl -f http://localhost:8000/health || exit 1`
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start Period:** 15 seconds
- **Retries:** 3

The `/health` endpoint loads the champion classifier and regressor and reports active model versions. If artifacts are corrupted or missing, the health check returns non-zero and marks the container unhealthy.

---

## 8. Runtime Artifact Strategy

The production image bundles the minimal runtime artifacts:
1. **Champion Models (`/app/models/`):**
   - `champion_classifier.joblib` (~6 KB)
   - `champion_regressor.joblib` (~5 KB)
2. **Lakehouse Parquet Tables (`/app/data/processed/parquet/`):**
   - `games.parquet` (0.9 MB)
   - `team_game_stats.parquet` (3.9 MB)
   - `team_game_stats_extended.parquet` (6.3 MB)
   - `player_game_stats.parquet` (27.9 MB)
   - `player_game_stats_extended.parquet` (64.5 MB)
   - `schedule_2026_27.parquet` (0.02 MB)
3. **Drift Reference Distribution (`/app/data/features/`):**
   - `game_features.parquet` (7.3 MB)

Total bundled artifact size is **~110 MB**, keeping the final container image lightweight while self-contained for inference.

---

## 9. What is Intentionally NOT Containerized

To maintain a lightweight and focused architecture:
- **Raw Historical CSVs (`data/raw/` ~850 MB):** Not copied into the container.
- **Local PostgreSQL Server:** Not run as a container; Neon cloud PostgreSQL is used directly.
- **Model Training / Hyperparameter Search:** Training and experimentation are offline batch jobs.
- **Heavy Orchestration (Kubernetes / Kafka / Airflow / Redis):** Excluded intentionally to avoid unnecessary operational overhead.

---

## 10. Troubleshooting & Common Issues

| Symptom | Cause | Resolution |
|---|---|---|
| Container fails healthcheck | Missing model files or invalid working directory | Check `docker logs lakers_api` to ensure `models/champion_*.joblib` are present. |
| DB connection timeout | Neon PostgreSQL sleep state or SSL requirement | Ensure `?sslmode=require` is appended to `DATABASE_URL`. |
| Port already in use | Host port 8000 or 8501 bound by another process | Map to alternate host ports (e.g. `-p 8080:8000`). |
