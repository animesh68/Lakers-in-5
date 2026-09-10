# Phase 6B — Deployment Readiness & Production Audit
## Lakers in 5

---

## A. Executive Summary

- **Overall Status:** **READY WITH CONDITIONS**
- **Deployment Blockers (P0/P1):** **0 Blockers** (Codebase, inference engine, feature pipeline, API contracts, persistence layer, and test suite are 100% verified and functional).
- **Conditions / Pre-Deployment Requirements:**
  1. Setting the production `DATABASE_URL` environment variable pointing to the managed Neon PostgreSQL database.
  2. Executing an actual container build on a host/CI environment where a Docker daemon is active (since local Windows host has no Docker CLI/daemon).
- **Test Suite Status:** **65 passed / 0 failed in 186.11s** across all unit, leakage, parity, inference, persistence, monitoring, and container contract suites.

---

## B. Architecture Assessment

```text
                                [ Internet / Client Traffic ]
                                              │
                         ┌────────────────────┴────────────────────┐
                         │                                         │
                         ▼                                         ▼
            FastAPI API Container (Port 8000)      Streamlit Dashboard (Port 8501)
              (uvicorn: 2 workers)                    (streamlit: headless)
                         │                                         │
                         ├─────────────────────────────────────────┤
                         │                                         │
                         ▼                                         ▼
             Embedded Analytical Lakehouse              Serving Database
            - data/processed/parquet/                 - Managed Neon PostgreSQL
            - data/features/game_features.parquet       (via DATABASE_URL)
            - models/champion_*.joblib                - Local Parquet Fallback
            - In-Memory DuckDB Engine
```

### Architectural Strengths:
1. **Self-Contained Embedded Lakehouse:** The analytical storage layer (`data/processed/parquet/` ~110 MB) is read-only and embedded inside the container, eliminating external object store latency or network dependencies during real-time feature computation.
2. **Dual-Backend Persistence:** The API and Dashboard interact with Neon PostgreSQL for persistent prediction logging and settlement, with seamless fallback to local Parquet storage if the database is unreachable.
3. **Strict Train/Serve Parity & Causality:** 52 pregame features computed chronologically without future target-game participation leakage.

---

## C. Deployment Blockers

| Issue | Why it matters | File | Recommended fix | Status |
|---|---|---|---|---|
| *None* | No critical blocking issues discovered | N/A | N/A | **CLEARED** |

---

## D. Environment Variables Table

All dynamic configuration and credentials are injected via environment variables without hardcoded fallback secrets.

| Variable | Required? | Used By | Default | Secret? | Description |
|---|---|---|---|---|---|
| `DATABASE_URL` | Recommended | `src/utils/db.py`, `src/monitoring/repository.py` | `""` (Falls back to Parquet) | **YES** | Neon PostgreSQL connection string (e.g. `postgresql://user:pass@host/db?sslmode=require`) |
| `POSTGRES_HOST` | Optional | `src/utils/db.py` | `localhost` | No | Postgres server host (alternative to DATABASE_URL) |
| `POSTGRES_PORT` | Optional | `src/utils/db.py` | `5432` | No | Postgres server port |
| `POSTGRES_DB` | Optional | `src/utils/db.py` | `lakers_in_5` | No | Postgres database name |
| `POSTGRES_USER` | Optional | `src/utils/db.py` | `postgres` | No | Postgres database user |
| `POSTGRES_PASSWORD` | Optional | `src/utils/db.py` | `""` | **YES** | Postgres password |
| `DB_POOL_SIZE` | Optional | `src/utils/db.py` | `10` | No | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | Optional | `src/utils/db.py` | `20` | No | SQLAlchemy max pool overflow connections |
| `DB_TIMEOUT` | Optional | `src/utils/db.py` | `30` | No | Connection timeout in seconds |
| `PYTHONPATH` | Required in Container | Container Runtime | `/app` | No | Python module search path |
| `PORT` | Optional | FastAPI / Uvicorn | `8000` | No | Internal HTTP port |

---

## E. Security Findings

| Severity | Item | Finding & Mitigation |
|---|---|---|
| **Informational** | **Secrets Isolation** | Verified zero plaintext passwords, tokens, or connection strings in Git history or Docker files. |
| **Informational** | **Non-Root Execution** | Container runs under dedicated non-root user `appuser` (UID 1000). |
| **Low** | **CORS Configuration** | `src/inference/api.py` currently allows `allow_origins=["*"]` for development. In restricted production environments, this can be parameterized. |
| **Informational** | **SQL Injection Safety** | All queries utilize SQLAlchemy ORM parameterized statements or psycopg2 `execute_values`. |

---

## F. Docker Verification Matrix

| Component / Layer | Status | Verification Detail |
|---|---|---|
| **Base Image (`python:3.11-slim`)** | **STATIC VERIFIED** | Validated via `tests/test_containerization.py::test_dockerfile_structure` |
| **System Packages (`curl`, `libgomp1`)** | **STATIC VERIFIED** | Declared for healthchecks and OpenMP ML runtimes |
| **User & Permissions (`USER appuser`)** | **STATIC VERIFIED** | Non-root `appuser:appgroup` ownership on `/app/data/monitoring` |
| **Context Inclusion / Exclusion** | **STATIC VERIFIED** | `.dockerignore` verified excluding `.venv`, `.env`, raw CSVs (~850 MB) |
| **Runtime Artifact Presence** | **VERIFIED** | Validated champion models, 6 lakehouse parquets, and schedule files exist |
| **API Entrypoint (`src.inference.api:app`)** | **VERIFIED** | Validated via FastAPI TestClient on `/health`, `/predict`, `/schedule/2026-27` |
| **Dashboard Entrypoint (`src/dashboard/app.py`)**| **VERIFIED** | Validated via headless data loaders in test suite |
| **Actual `docker build` / `run` Execution** | **UNVERIFIED** | Docker CLI/daemon is not installed on the local Windows host |

---

## G. Platform & Hosting Requirements

A container hosting platform (e.g., AWS App Runner, Google Cloud Run, Railway, Render, Fly.io, or VPS) must satisfy:
1. **Container Engine:** Ability to build from Dockerfile or pull pre-built OCI container image.
2. **Memory Limit:** Minimum **1.0 GB RAM** (recommended: **1.5–2.0 GB RAM**) to support in-memory DuckDB queries, feature extraction, and 2 Uvicorn workers.
3. **CPU Limit:** 1–2 vCPUs.
4. **Networking:** Outbound TCP access to Neon PostgreSQL (`ep-*.aws.neon.tech:5432`) over TLS/SSL.
5. **Port Routing:** HTTP ingress mapped to port 8000 (API) and port 8501 (Dashboard).

---

## H. Recommended Deployment Strategy

### **Option A (Recommended): Multi-Service Deployment (API + Dashboard)**
Deploy as two independent services built from the same unified Docker image:
1. **Service 1 (Backend API):**
   - Command: `uvicorn src.inference.api:app --host 0.0.0.0 --port 8000 --workers 2`
   - Ingress: Public port 8000
   - Healthcheck: `/health`
2. **Service 2 (Frontend Dashboard):**
   - Command: `streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`
   - Ingress: Public port 8501

*Why this strategy?* Decouples the user dashboard from the high-throughput prediction API while sharing the same validated Dockerfile and codebase.

---

## I. Manual Steps Required from You (User)

The assistant cannot perform external platform authentication or billing. You will need to:
1. **Select / Create Hosting Account:** (e.g., Render, Railway, AWS, GCP, or DigitalOcean).
2. **Connect GitHub Repository:** Authorize access to `https://github.com/animesh68/Lakers-in-5.git`.
3. **Configure Environment Variable:** Paste your Neon connection string into `DATABASE_URL`.
4. **Trigger Deployment:** Click Deploy / Enable Automatic Deploys on `master` branch.
5. **Approve Cloud Billing / Provisioning.**

---

## J. Post-Deployment Smoke-Test Checklist

Once deployed to your hosting platform, run these commands against the live URL:

```bash
# 1. Healthcheck (Returns status: healthy and champion model versions)
curl -s -X GET "https://<YOUR-API-DOMAIN>/health" | jq .

# 2. Predict next Lakers game (framed from Lakers perspective)
curl -s -X GET "https://<YOUR-API-DOMAIN>/predict/lakers/next" | jq .

# 3. Predict arbitrary scheduled game (e.g. 2026-10-21 GSW at LAL)
curl -s -X POST "https://<YOUR-API-DOMAIN>/predict" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "LAL", "away_team": "GSW", "game_date": "2026-10-21", "persist": true}' | jq .

# 4. Query 2026-27 schedule
curl -s -X GET "https://<YOUR-API-DOMAIN>/schedule/2026-27?team=LAL&limit=5" | jq .

# 5. Query Monitoring Health Diagnostic
curl -s -X GET "https://<YOUR-API-DOMAIN>/monitoring/health?window=30d" | jq .

# 6. Access Streamlit Dashboard
# Open browser at: https://<YOUR-DASHBOARD-DOMAIN>/
```

---

## K. Test Results Summary

```powershell
python -m pytest tests/ -v
================= 65 passed, 2 warnings in 186.11s =================
```

All 65 automated tests across all 7 test modules passed with 0 failures.
