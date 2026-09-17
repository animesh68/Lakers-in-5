# Lakers in 5 — Phase 7.2 Matchup Predictor Production Investigation & Fix Report

## 1. Original Symptom
On the production dashboard (`https://lakers-in-5.onrender.com/`), selecting two teams on the **Matchup Predictor** page and clicking **Generate Prediction** resulted in no forecast being displayed:
- The UI remained stuck on the initial *"Ready to Simulate"* empty state.
- No prediction card was rendered, and no error banner was displayed to the user.

---

## 2. Root Cause Analysis
The failure was traced to a combination of frontend property mismatch and client-side exception handling:
1. **Frontend Property Name Deserialization Mismatch:**
   - The FastAPI backend endpoint (`POST /predict`) returns a `GamePredictionResponse` model where the predicted point spread field is named `predicted_home_margin`.
   - The React UI in `frontend/src/App.jsx` attempted to access `simResult.predicted_margin.toFixed(1)`.
   - Because `simResult.predicted_margin` was `undefined`, executing `.toFixed(1)` raised an uncaught JavaScript runtime exception:
     `TypeError: Cannot read properties of undefined (reading 'toFixed')`
   - In React's rendering lifecycle, this uncaught render error crashed the component render tree, unmounting the prediction card and resetting the view back to the fallback *"Ready to Simulate"* placeholder.
2. **Team Name vs Code Normalization in Quick Predict:**
   - In Schedule Explorer, `game.home_team` was populated with the full franchise name (e.g. `'Detroit Pistons'`). Clicking *"Simulate Matchup"* passed `'Detroit Pistons'` into `simHome`, which did not match the select dropdown value codes (`'DET'`), causing dropdown value misalignment.
3. **Missing Date Horizon & Distinct Team Guardrails:**
   - The backend did not previously reject selecting identical teams (e.g. `LAL vs LAL`) or dates far outside the 2026–27 season horizon.

---

## 3. Exact Failing Request
```http
POST /predict HTTP/1.1
Host: lakers-in-5.onrender.com
Content-Type: application/json
Accept: application/json

{
  "home_team": "LAL",
  "away_team": "GSW",
  "game_date": "2026-10-21",
  "persist": false
}
```

---

## 4. Backend Response
The backend returned HTTP 200 OK with the valid prediction payload:
```json
{
  "prediction_id": null,
  "game_id": null,
  "game_date": "2026-10-21",
  "home_team": "Los Angeles Lakers",
  "away_team": "Golden State Warriors",
  "home_team_id": "1610612747",
  "away_team_id": "1610612744",
  "home_win_probability": 0.717247,
  "away_win_probability": 0.282753,
  "predicted_home_margin": 6.162658,
  "model_version": "Logistic Regression (Standard) / Ridge Regression (Diff Only) (Phase 3 Production)",
  "classifier_name": "Logistic Regression (Standard)",
  "regressor_name": "Ridge Regression (Diff Only)",
  "feature_schema_version": "v1",
  "feature_snapshot_hash": "bbd8504312d1d467c73e1de9f909f9ff26afbba2951933e7a90e17cd087f1590",
  "feature_timestamp": "2026-09-17T05:54:34.638597Z",
  "features": null
}
```

---

## 5. Frontend Failure Point
In `frontend/src/App.jsx` (lines 656-658):
```jsx
// FAILING CODE:
<div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '4px', color: simResult.predicted_margin >= 0 ? '#34d399' : '#fb7185' }}>
  {simResult.predicted_margin >= 0 ? `+${simResult.predicted_margin.toFixed(1)} pts` : `${simResult.predicted_margin.toFixed(1)} pts`}
</div>
```
Because `simResult.predicted_margin` was undefined, `undefined.toFixed(1)` threw a `TypeError` during React render, silently aborting card presentation.

---

## 6. Date & Team Validation Behavior
- **Supported Season Horizon:** Target dates must fall within the official 2026–27 regular season & playoffs window: `2026-10-01` to `2027-06-30`. Dates outside this range return HTTP 400 with a descriptive error.
- **Distinct Teams:** Selecting identical home and away teams (`home_team == away_team`) returns HTTP 400 (`"Home team and away team must be distinct NBA teams."`).
- **Hypothetical & Scheduled Support:** The feature service computes strictly leakage-safe historical Elo, rolling metrics, and rest factors up to the selected date. If the matchup exists in the official 2026-27 schedule, schedule-aware contextual rest is used; if hypothetical, chronological pregame state is computed safely without future leakage.

---

## 7. Fix Implemented
1. **API Schema Contract Alignment:** Added `predicted_margin` convenience alias to `GamePredictionResponse` in `src/inference/schemas.py` and `src/inference/predictor.py` while maintaining strict `predicted_home_margin` contract integrity.
2. **Backend Validation Guardrails:** Added distinct team and season horizon validation in `src/inference/api.py` and `src/inference/predictor.py`.
3. **Frontend Defensive Rendering:** Updated `frontend/src/App.jsx` to safely parse `simResult.predicted_home_margin ?? simResult.predicted_margin ?? 0`, format percentages safely, and render a dedicated Lakers perspective banner when Lakers are home or road participants.
4. **API Client Resilience:** Added `AbortController` 30s timeout and enhanced JSON validation error message formatting in `frontend/src/api.js`.
5. **Team Normalization in Quick Predict:** Added `getTeamCode` mapping in `frontend/src/App.jsx` so Schedule Explorer cards smoothly transfer to the Matchup Predictor dropdowns.
6. **Frontend Rebuild:** Rebuilt production bundle into `frontend/dist`.

---

## 8. Tests Added
Created `tests/test_matchup_predictor.py` with 7 test cases:
1. `test_valid_matchup_prediction`: Tests valid matchup probability and margin computation ($P(\text{home}) + P(\text{away}) = 1.0$).
2. `test_matchup_prediction_same_team_rejected`: Tests HTTP 400 on identical teams.
3. `test_matchup_prediction_invalid_team_rejected`: Tests HTTP 400 on unknown team codes.
4. `test_matchup_prediction_date_outside_season_rejected`: Tests HTTP 400 on dates outside 2026–27 horizon.
5. `test_matchup_prediction_invalid_date_format`: Tests HTTP 422 on malformed date strings.
6. `test_matchup_prediction_persist_toggle`: Tests `persist=false` (transient) vs `persist=true` (persisted record).
7. `test_scheduled_matchup_prediction_via_schedule_lookup`: Tests end-to-end integration between schedule lookup and matchup prediction.

---

## 9. Full Pytest Result
```text
================== 78 passed, 4 warnings in 90.92s ==================
```
- Total test count: **78 passed / 0 failed** (71 baseline + 7 new tests).

---

## 10. Production Verification Plan
1. Commit and push changes to GitHub `master`.
2. Render automatic build triggers and compiles frontend assets into `/app/frontend/dist`.
3. Test endpoints:
   - `GET /health`
   - `POST /predict` (`{"home_team": "LAL", "away_team": "GSW", "game_date": "2026-10-21", "persist": false}`)
   - UI verification: Select teams, select date, click *"Generate Prediction"*, verify loading spinner, verify rendered forecast card, verify probabilities sum to 100%, verify projected margin, model version, and feature snapshot hash.
