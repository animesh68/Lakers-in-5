# Phase 9 — Player Performance Projections: Frontend Integration

## Overview

This document details the frontend integration of the player performance prediction system into the production **Lakers in 5** React application. The integration seamlessly surfaces individual player projections (Minutes, Points, Rebounds, Assists) within the existing Forecast and Matchup Predictor views, strictly adhering to the design language, responsive grid layout, and circular player image specifications.

---

## 1. Feature Placement and User Access

The player performance projections are integrated into two primary views in the existing application:

1. **Forecast View (`/`)**:
   - Rendered directly below the primary `ForecastHero` prediction card.
   - Automatically loads player rotation projections for the upcoming scheduled Lakers game (`lakersNext.data.home_team`, `lakersNext.data.away_team`, `lakersNext.data.game_date`).
2. **NBA Matchup Predictor View (`/matchups`)**:
   - Rendered immediately below the matchup prediction result card upon generating a simulation.
   - Updates dynamically whenever the user simulates an official scheduled 2026-27 NBA contest.

---

## 2. API Endpoints & Request / Response Contract

### Endpoints Used

* **`POST /predict/players`**:
  ```json
  {
    "home_team": "LAL",
    "away_team": "GSW",
    "game_date": "2026-10-21",
    "game_id": "1"
  }
  ```
* **`GET /predict/{game_id}/players`**:
  - Direct schedule number lookup for scheduled games.

### Response Schema (`PlayerPredictionResponse`)

```json
{
  "game_id": "1",
  "game_date": "2026-10-21",
  "home_team": "Los Angeles Lakers",
  "away_team": "Golden State Warriors",
  "players": [
    {
      "player_id": "2544",
      "player_name": "LeBron James",
      "team": "Los Angeles Lakers",
      "team_code": "LAL",
      "expected_minutes": 34.5,
      "predicted_points": 25.2,
      "predicted_rebounds": 7.8,
      "predicted_assists": 8.4,
      "is_transition_player": false
    }
  ],
  "model_versions": {
    "minutes": "ridge-v1",
    "stats": "gb-multi-v1"
  },
  "feature_schema_version": "v1.0-player",
  "prediction_timestamp": "2026-09-30T10:00:00Z"
}
```

---

## 3. UI Component Structure & Design

### Section Header

- **Heading**: `PLAYER PROJECTIONS`
- **Supporting text**: `Projected performance for players in this matchup.`
- **Badges & Actions**: `Expected Rotation` badge with an in-place `Retry Projections` button if an error occurs.

### Player Card (`PlayerCard.jsx`)

Each card exhibits a hierarchical information layout:

1. **Mandatory Circular Profile Image Area**:
   - Fixed dimension: `56px × 56px` on desktop, `48px × 48px` on mobile.
   - Shape: `border-radius: 50%` with `overflow: hidden`, `flex-shrink: 0`.
   - Never collapses under any condition (missing URL, synthetic ID, or failed image fetch).
2. **Player Identity & Offseason Transfer Badge**:
   - Player full name with ellipsis overflow protection.
   - Team code (`LAL`, `GSW`, etc.).
   - `Offseason Transfer` tag if `is_transition_player === true`.
3. **Prominent Expected Minutes**:
   - Bold, callout minutes figure (`expected_minutes.toFixed(1)`) highlighted in gold for primary rotation players (≥ 25 mins).
4. **Statistical Projections Row**:
   - Compact 3-column row displaying **PTS**, **REB**, and **AST** to 1 decimal place (`toFixed(1)`).
   - No fabricated or unsupported metrics (e.g. FG%, 3PT%, PER).

### Image Resolution & Fallback Strategy

1. **Numeric NBA Person ID**:
   - Resolves to official CDN: `https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png`.
   - Rendered with `object-fit: cover` and `border-radius: 50%`.
2. **Synthetic or Missing ID / Load Failure**:
   - On `onError` or synthetic IDs (`R-xxxxxx`), dynamically renders an initials avatar (e.g., `LJ`, `AD`) centered over a Lakers purple/gold gradient or neutral dark glass styling.
   - Dimensions (`56px` / `48px`) and circular shape remain strictly intact.

### Team Separation & Sorting

- Two distinct columns for **Away Team** and **Home Team**.
- Each column header shows team name, home/away designation, and total projected rotation players.
- Player cards preserve the backend's descending order by projected minutes.

---

## 4. State Handling

| State | UI Behavior |
| --- | --- |
| **Loading** | Renders 6 skeleton cards across two columns with pulsing circular avatar skeletons (`56px` circle), minutes skeleton, and stat row skeleton. |
| **Error** | Shows `"Player projections are temporarily unavailable."` with error details and a dedicated **Retry** action. Does not break game-level prediction. |
| **Empty** | Shows `"No player projections available for this matchup."` with clean empty-state icon. |
| **Disclaimer** | Subtle footer disclaimer: *"These are statistical projections, not confirmed lineups or guaranteed outcomes."* |

---

## 5. Responsive Design

- **Desktop (≥ 1024px)**: 2-column side-by-side team roster grid with full `56px` circular avatars.
- **Tablet (768px – 1023px)**: Auto-fit fluid grid maintaining card proportions.
- **Mobile (< 768px)**: Vertically stacked single-column team layout with compact `48px` circular avatars and no horizontal page overflow.

---

## 6. Verification & Test Suite

The integration test suite was executed via `npm test` (`frontend/run_tests.js` with Vite SSR Loader):

```
🚀 Initializing Vite Dev Server for Component SSR Tests...
✓ Successfully loaded PlayerCard and PlayerProjections modules.

--- Running 15 Verification Tests ---
  PASS: 1. Player projections render for both teams
  PASS: 2. Player name and team are displayed correctly
  PASS: 3. PTS, REB, AST, and projected minutes use exact API values with proper formatting
  PASS: 4. Every player card has a circular image container
  PASS: 5. Valid NBA player ID produces headshot URL and circular img
  PASS: 6. Missing or non-numeric image IDs render circular placeholder with initials without collapsing
  PASS: 7. Transition player badge is displayed for offseason transfer
  PASS: 8. Loading state renders skeleton with circular avatar placeholders
  PASS: 9. Empty response displays clean empty state message
  PASS: 10. Disclaimer is visible in the section
  PASS: 11. Heading and supporting text match specifications
  PASS: 12. No fabricated statistical metrics are rendered
  PASS: 13. Roster sorting preserves backend order
  PASS: 14. Player avatar container dimensions consistent (56px fixed circular container)
  PASS: 15. Fallback avatar retains initials without collapse when player_id is null

========================================
Result: 15/15 tests PASSED
========================================
```

### Production Build

`npm run build`:
```
vite v8.3.0 building client environment for production...
transforming...
✓ 1882 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.31 kB │ gzip:  0.70 kB
dist/assets/index-DJuyjebi.css    5.36 kB │ gzip:  1.85 kB
dist/assets/index-PUdbgny-.js   296.88 kB │ gzip: 86.73 kB
✓ built in 625ms
```

---

## 7. Remaining Limitations & Production Notes

1. **Headshot CDN Availability**:
   - Official NBA CDN headshots depend on active internet connectivity and valid NBA numeric IDs. Synthetic IDs (`R-xxxxxxx`) for unmapped offseason additions automatically fallback gracefully to the styled initials avatar.
2. **Environment URL**:
   - The frontend connects via `VITE_API_URL` or defaults to relative endpoints (`/predict/players`) when deployed on the same origin (Vercel / Render).
