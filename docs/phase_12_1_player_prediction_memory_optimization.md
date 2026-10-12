# Phase 12.1 — Player Prediction Memory Optimization & Hardening Audit

## Executive Summary

During the Phase 12 production readiness audit, local profiling revealed a severe memory bottleneck in the player-level prediction serving path (`/predict/players` and `/predict/scheduled_game_players`). While the base application and team-level match prediction endpoints operated within safe margins (~328 MB RSS), executing player performance projections across 20 rotation players caused transient memory spikes up to **1056.91 MB RSS** during repeated bursts, posing an immediate Out-Of-Memory (OOM) risk on a 512 MB Render deployment instance.

**Phase 12.1 successfully resolved this memory bottleneck without modifying any machine learning model artifacts, coefficients, feature definitions, or prediction semantics.**

Through zero-copy DuckDB streaming, predicate pushdown, vectorized single-query batch extraction, and per-request team context reuse, peak working set memory was slashed by **67.0%** down to **348.58 MB**, establishing a healthy **163.42 MB (31.9%) headroom margin** under a 512 MB deployment budget.

---

## 1. Root Cause Analysis

Profiling and memory inspection identified three primary architectural causes for memory bloat:

1. **Full-Table Polars DataFrame Retention & Inefficient Conversion**:
   - `PlayerFeatureEngine` loaded historical player game logs (`data/processed/parquet/player_game_stats.parquet`, ~1.5M rows) into in-memory Polars DataFrames and performed 20 `.to_pandas()` conversions per request.
   - Polars-to-Pandas zero-copy conversions triggered large memory reallocations in Python process space.

2. **Per-Player Redundant Scans & Intermediate Frame Allocations**:
   - `extract_pregame_player_features` was invoked in an unvectorized loop across all 20 players.
   - For every player, `team_game_stats.parquet` was queried repeatedly to compute identical rolling pace/offensive ratings.
   - Pregame role assignment created temporary `pd.DataFrame([feature_dict])` instances inside inner loops.

3. **Unbounded DuckDB Query Buffering & Roster Lookups**:
   - `RosterService.get_active_roster_universe` performed full parquet scans per team (home + away), adding +317 MB per request.
   - Unconstrained DuckDB thread counts and memory limits allowed temporary buffer pools to expand unchecked.

---

## 2. Engineering Optimizations Implemented

All optimizations strictly adhere to zero retraining, zero model coefficient modification, and 100% deterministic output parity constraints.

### 2.1 DuckDB Streaming with Strict Memory Bounds
- Configured DuckDB runtime parameters:
  ```sql
  SET memory_limit = '64MB';
  SET threads = 1;
  ```
- Replaced in-memory Polars DataFrame persistence with DuckDB streaming queries reading directly from parquet lakehouse storage (`read_parquet`).
- Enforced predicate pushdown (`WHERE CAST(personId AS VARCHAR) IN (...) AND substr(CAST(gameDateTimeEst AS VARCHAR), 1, 10) < cutoff_date LIMIT 25`) so that only the exact required historical rows are materialized.

### 2.2 Vectorized Batch Player Feature Extraction
- Implemented `extract_pregame_batch_player_features(player_requests, target_game_date)` in `PlayerFeatureEngine`.
- Consolidates 20 distinct database queries into a single unified SQL query with `IN (...)` filtering.
- Groups retrieved rows in memory and feeds each player's recent historical slice to `_compute_features_from_df`.

### 2.3 Team Rolling Context Precomputation & Reuse
- Added `get_team_rolling_context(team_id, opponent_team_id, cutoff_date)` to precompute home/away rolling pace, offensive rating, and defensive rating once per game request.
- Passes the precomputed context into all 20 player feature generations, eliminating 38 redundant team parquet reads per game.

### 2.4 Streamlined Roster Resolution & Inference Loop
- Refactored `RosterService` to stream active roster universes via DuckDB aggregate window queries rather than loading full tables into Polars.
- Streamlined `PlayerPredictor` to avoid redundant dictionary-to-DataFrame conversions during role stratification.

---

## 3. Empirical Verification & Parity Audit

### 3.1 Deterministic Prediction Parity
Parity testing on Game 5 (Los Angeles Lakers vs Golden State Warriors, `2026-10-21`) confirmed **exact mathematical equality** across all 20 rotation players across all target metrics (minutes, points, rebounds, assists, role assignment).

| Metric Target | Discrepancy Count | Max Absolute Diff | Parity Status |
|:---|:---:|:---:|:---:|
| **Expected Minutes** | 0 / 20 | 0.00000 | **EXACT MATCH** |
| **Predicted Points** | 0 / 20 | 0.00000 | **EXACT MATCH** |
| **Predicted Rebounds** | 0 / 20 | 0.00000 | **EXACT MATCH** |
| **Predicted Assists** | 0 / 20 | 0.00000 | **EXACT MATCH** |
| **Role Assignment** | 0 / 20 | 0.00000 | **EXACT MATCH** |

### 3.2 Memory Profiling & Benchmark Comparison

Measurements taken on local runtime using `psutil` Process Working Set (RSS):

```
========================================================================================
LAKERS IN 5 - PHASE 12.1 MEMORY BENCHMARK (512 MB DEPLOYMENT BUDGET)
========================================================================================
Target Budget:                               512.00 MB
----------------------------------------------------------------------------------------
Runtime Checkpoint                           Pre-Opt RSS      Post-Opt RSS     Reduction
----------------------------------------------------------------------------------------
Baseline Python Runtime                      14.75 MB         14.77 MB         +0.02 MB
Post-Import / Module Load                    276.19 MB        276.25 MB        +0.06 MB
Idle Server Post-Warmup                      308.11 MB        308.07 MB        -0.04 MB
Matchup Prediction (/predict/lakers/next)    328.61 MB        329.73 MB        +1.12 MB
Single 20-Player Prediction Peak             855.87 MB        340.00 MB        -515.87 MB (-60.3%)
10-Batch Burst Stress Peak                   1056.91 MB       348.58 MB        -708.33 MB (-67.0%)
Final Steady-State RSS                       631.90 MB        341.16 MB        -290.74 MB (-46.0%)
----------------------------------------------------------------------------------------
512 MB Target Headroom Margin                -544.91 MB       +163.42 MB       +708.33 MB
========================================================================================
Budget Verdict: PASS - HEALTHY HEADROOM (68.1% of 512 MB budget utilized at peak burst)
========================================================================================
```

---

## 4. Test & Verification Coverage

1. **Observability & Reliability Suite (`tests/test_phase11_observability.py`)**:
   - 33/33 tests PASSED (structured logging, correlation IDs, Prometheus metrics, `/health/models`, drift checks).
2. **Shadow Monitoring & C1 Role-Stratified Suites (`tests/test_phase10b_shadow_monitoring.py`, `tests/test_role_stratified_verification.py`)**:
   - 14/14 tests PASSED (shadow isolation, paired deltas, model gating).
3. **Core Prediction & Containerization Suites (`tests/test_inference.py`, `tests/test_matchup_predictor.py`, `tests/test_player_prediction.py`, `tests/test_containerization.py`)**:
   - 40/40 tests PASSED (temporal leakage guards, orientation parity, container configs).
4. **Dedicated Memory Optimization Suite (`tests/test_memory_optimization.py`)**:
   - 2/2 tests PASSED (batch feature parity against single extraction, repeated deterministic inference).

---

## 5. Deployment Recommendation

With a peak memory footprint of **348.58 MB** under 10 consecutive full-game player prediction bursts, the application is **fully production-ready for deployment on a 512 MB Render instance**.
