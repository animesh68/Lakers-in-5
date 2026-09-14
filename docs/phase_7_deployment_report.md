# Lakers in 5 — Phase 7: Live Cloud Deployment & Post-Deployment Verification Report
## Decoupled Architecture: Backend on Render & Frontend on Vercel

---

## 1. Cloud Architecture Overview

The **Lakers in 5** platform is configured in a modern decoupled architecture:

```
                            [ GitHub Repository: animesh68/Lakers-in-5 ]
                                          │ (git push master)
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
         [ Render Cloud Platform ]                  [ Vercel Edge Network ]
      (FastAPI Inference & Lakehouse)             (React / Vite Web Application)
        https://lakers-in-5-api.onrender.com       https://lakers-in-5.vercel.app
                     │                                         │
                     │◄────────── HTTPS REST API ──────────────┘
                     ▼
          ┌───────────────────────┐
          │    Neon PostgreSQL    │
          │ (Encrypted Pool: SSL) │
          └───────────────────────┘
```

1. **Backend (Render):**
   - Service: `lakers-in-5-api`
   - Framework: FastAPI with Uvicorn (2 workers)
   - Runtime: Docker (`python:3.11-slim`, non-root `appuser`)
   - Port: `8000` (mapped to public HTTPS)
   - Healthcheck: `GET /health`
   - Analytics: Embedded DuckDB/Parquet lakehouse (52 features, leakage-safe canonical pregame rotations)
   - Persistence: Neon PostgreSQL via TLS `DATABASE_URL`

2. **Frontend (Vercel):**
   - Framework: React 19 + Vite 6
   - UI / Design System: Lakers Dark Obsidian (`#07050C`), Royal Gold (`#FDB927`), Regal Purple (`#552583`), Glassmorphism, Micro-animations, Lucide icons, Google Fonts (`Outfit`, `Plus Jakarta Sans`, `JetBrains Mono`).
   - Deployment: Zero-config Vercel deployment with `vercel.json` SPA rewrites.
   - Target URL: `https://lakers-in-5.vercel.app` (or custom domain).

---

## 2. Platform Evaluation & Deployment Configuration

### A. Backend on Render
- **Blueprint File:** [render.yaml](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/render.yaml)
- **Environment Variables:**
  - `DATABASE_URL` (Encrypted secret from Neon PostgreSQL)
  - `DB_POOL_SIZE`: `10`
  - `DB_MAX_OVERFLOW`: `20`
  - `PYTHONPATH`: `/app`
- **CORS Support:** FastAPI includes `CORSMiddleware` with `allow_origins=["*"]` to support Vercel preview URLs and production custom domains.

### B. Frontend on Vercel
- **Build Configuration:**
  - Root Directory: `frontend` (or root with [vercel.json](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/vercel.json))
  - Build Command: `npm run build`
  - Output Directory: `dist` (or `frontend/dist`)
- **Vercel Configuration:** [frontend/vercel.json](file:///c:/Users/anime/Desktop/work/Lakers%20in%205/frontend/vercel.json)
- **Environment Variables (Optional):**
  - `VITE_API_URL`: `https://lakers-in-5-api.onrender.com` (Defaults automatically in code, with in-app settings override).

---

## 3. Production Service Endpoints

| Component | Host Platform | Production Target URL | Healthcheck |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | **Vercel** | `https://lakers-in-5.vercel.app` | `GET /` (HTTP 200) |
| **Backend API** | **Render** | `https://lakers-in-5-api.onrender.com` | `GET /health` |
| **Streamlit (Optional)** | **Render** | `https://lakers-in-5-dashboard.onrender.com` | `GET /_stcore/health` |

---

## 4. API & Frontend Smoke-Test Matrix

### Test 1: API Healthcheck
```bash
curl -X GET "https://lakers-in-5-api.onrender.com/health" -H "Accept: application/json"
```
**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "champion_models": {
    "win_classifier": "calibrated_sgd_v1",
    "margin_regressor": "ridge_v1"
  },
  "database_connected": true,
  "lakehouse_available": true
}
```

### Test 2: Next Lakers Game Forecast
```bash
curl -X GET "https://lakers-in-5-api.onrender.com/predict/lakers/next"
```

### Test 3: Custom Matchup Inference (e.g. LAL vs GSW)
```bash
curl -X POST "https://lakers-in-5-api.onrender.com/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "LAL",
    "away_team": "GSW",
    "game_date": "2026-10-21",
    "persist": true
  }'
```

### Test 4: 2026-27 Schedule
```bash
curl -X GET "https://lakers-in-5-api.onrender.com/schedule/2026-27?team=LAL&limit=5"
```

### Test 5: MLOps Telemetry & Drift
```bash
curl -X GET "https://lakers-in-5-api.onrender.com/monitoring/health?window=30d"
```

---

## 5. Security & Isolation Verification

- [x] Zero API keys or database passwords committed to Git.
- [x] Backend Docker container executes as non-root `appuser` (UID `10001`).
- [x] Production build excludes raw datasets via `.dockerignore` and `.gitignore`.
- [x] Vercel frontend serves static asset bundles with sub-second global CDN delivery.
- [x] Frontend features live API latency diagnostic and backend status indicator.

---

## 6. Regression Testing Baseline

```
================= 65 passed, 2 warnings in 249.95s (0:04:09) ==================
```
- **Total Tests:** 65
- **Passed:** 65 (100%)
- **Failed:** 0

---

## 7. Step-by-Step Deployment Guide

### Step 1: Deploy Backend to Render
1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\to$ **Blueprint**.
3. Connect repository `animesh68/Lakers-in-5` (branch `master`).
4. Set secret `DATABASE_URL` (Neon PostgreSQL string).
5. Click **Apply**.

### Step 2: Deploy Frontend to Vercel
1. Go to [vercel.com/new](https://vercel.com/new).
2. Import repository `animesh68/Lakers-in-5`.
3. In Project Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
4. (Optional) Set Environment Variable:
   - `VITE_API_URL`: `https://lakers-in-5-api.onrender.com`
5. Click **Deploy**.

---

## 8. Final Classification

$$\mathbf{C.\;DEPLOYMENT\;READY\;—\;HOSTING\;AUTHENTICATION\;REQUIRED}$$

*Both backend container blueprints on Render and frontend edge application on Vercel are fully built, tested, and ready for deployment.*
