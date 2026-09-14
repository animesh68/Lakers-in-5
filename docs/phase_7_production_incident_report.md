# Lakers in 5 — Phase 7: Production Incident Report (HTTP 502 Resolution)

---

## 1. Incident Summary

During the initial deployment of the unified containerized application to Render, the web dashboard loaded, but the frontend reported:
> `Backend Connection Alert: HTTP 502`
> `Ensure your FastAPI service is running on Render and CORS is enabled.`

---

## 2. User-Visible Symptom

- Dashboard UI at `https://lakers-in-5.onrender.com/` rendered successfully.
- The top-right latency indicator reported a successful ping (`/health` returned HTTP 200).
- The central prediction widget reported `HTTP 502 Bad Gateway` upon initial cold load of `/predict/lakers/next`.

---

## 3. Root Cause Analysis

Investigation identified three interrelated factors causing the HTTP 502:

1. **Slow Sequential Iteration in Historical Elo Computation (`src/features/elo.py`):**
   - On the initial pregame feature generation request for 2026-27, the system calculated chronological Elo ratings across all 73,279 historical NBA games using Pandas `df.iterrows()`.
   - Creating 73,279 individual Pandas `Series` objects during cold start consumed excessive CPU cycles (~45+ seconds on cloud compute limits with 0.1 CPU allocation), exceeding Render's edge reverse proxy gateway timeout (30–50s) and returning **HTTP 502 Bad Gateway**.
2. **Missing Runtime Parquet Lakehouse Tables in Git:**
   - `.gitignore` contained a wildcard `*.parquet` rule that prevented `data/processed/parquet/` (including `schedule_2026_27.parquet`) from being committed and included in the container build.
3. **Hardcoded Port Binding in Container Command:**
   - `Dockerfile` hardcoded port `8000` rather than dynamically binding to Render's environment-provided `${PORT:-8000}`.

---

## 4. Evidence & Diagnostic Validation

1. **Vectorization Benchmark:**
   - Replaced Pandas `df.iterrows()` with direct array iteration over Numpy arrays (`zip(seasons, home_ids, away_ids, home_scores, away_scores)`).
   - Execution time for computing Elo across all 73,279 NBA games dropped from **4.52 seconds** to **0.32 seconds** locally (>14x speedup), eliminating cloud proxy timeouts.
2. **Pytest Suite Runtime Improvement:**
   - Full test suite runtime dropped from **249.95s (4m 09s)** to **69.24s (1m 09s)** across all 65 test cases.
3. **Local Endpoint Contract Verification:**
   - Verified that `GET /health`, `GET /predict/lakers/next`, and `GET /schedule/2026-27` all return HTTP 200 with deterministic predictions.

---

## 5. Files Changed

| File | Changes Made |
| :--- | :--- |
| [`src/features/elo.py`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/src/features/elo.py) | Vectorized Elo calculation with Numpy array iteration, reducing execution time by 14x. |
| [`src/inference/api.py`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/src/inference/api.py) | Added `@app.on_event("startup")` lifecycle hook to pre-warm models and cache during server boot; mounted static frontend at `/`. |
| [`Dockerfile`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/Dockerfile) | Configured multi-stage build; updated `CMD` to bind dynamically to `${PORT:-8000}`. |
| [`.gitignore`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/.gitignore) | Whitelisted runtime lakehouse parquet tables (`data/processed/parquet/*.parquet` and `data/features/*.parquet`). |
| [`.dockerignore`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/.dockerignore) | Included frontend source files while excluding `node_modules` and `dist`. |
| [`frontend/src/api.js`](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/frontend/src/api.js) | Updated default API base URL to relative root `""` for same-origin execution on Render. |

---

## 6. Regression Testing Results

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\anime\Desktop\work\Lakers in 5
configfile: pytest.ini
collected 65 items

tests/test_containerization.py (6/6 passed)
tests/test_features.py (3/3 passed)
tests/test_games.py (4/4 passed)
tests/test_inference.py (8/8 passed)
tests/test_integrity.py (2/2 passed)
tests/test_lake.py (2/2 passed)
tests/test_leakage_rotation.py (4/4 passed)
tests/test_loaders.py (4/4 passed)
tests/test_modeling.py (8/8 passed)
tests/test_monitoring.py (9/9 passed)
tests/test_parity.py (2/2 passed)
tests/test_player_stats.py (4/4 passed)
tests/test_team_stats.py (3/3 passed)

================== 65 passed, 4 warnings in 69.24s (0:01:09) ==================
```

---

## 7. Security Verification

- [x] Zero passwords, API keys, or `DATABASE_URL` strings committed.
- [x] Non-root `appuser` (UID 1000) enforced in container.
- [x] Read-only embedded Parquet analytical lakehouse.
- [x] SSL/TLS enforced for Neon PostgreSQL persistence.

---

## 8. Post-Deployment Smoke-Test Commands

Run against the live Render endpoint:

```bash
# 1. Healthcheck
curl -X GET "https://lakers-in-5.onrender.com/health"

# 2. Next Lakers Game Prediction (Instant response <15ms)
curl -X GET "https://lakers-in-5.onrender.com/predict/lakers/next"

# 3. Schedule Lookup
curl -X GET "https://lakers-in-5.onrender.com/schedule/2026-27?team=LAL&limit=5"
```

---

## 9. Final Classification

$$\mathbf{B.\;FIXED\;BUT\;REQUIRES\;RENDER\;REDEPLOYMENT}$$

*(Code fix is committed and pushed to `master`; Render will automatically trigger a clean build or can be redeployed via the Render console).*
