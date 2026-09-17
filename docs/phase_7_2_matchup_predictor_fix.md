# Phase 7.2 Matchup Predictor Fix: Schedule-Backed Validation & Ingestion Parity

## Executive Summary
In Phase 7.2, the Matchup Predictor was hardened to strictly enforce **schedule-backed validation** across both the frontend user interface and backend inference API. Arbitrary in-season date selection has been replaced by dynamic schedule querying, ensuring that predictions can only be executed for real matchups scheduled in the official 2026-27 NBA regular season.

---

## 1. Schedule Dataset Ingestion & Completeness Investigation

### 1.1 Root Cause of Missing Schedule Games
- **Observation:** Earlier parsing yielded 1,197 games whereas the initial 80-game regular season schedule for 30 NBA franchises represents $30 \times 80 / 2 = 1,200$ unique games.
- **Root Cause:** The schedule parser regex previously only matched `\s+at\s+`. Three neutral-site/international games (Denver vs Indiana, New Orleans vs San Antonio, and San Antonio vs New Orleans) used `vs` instead of `at` in the official NBA schedule PDF.
- **Fix:** The parsing regex in `ScheduleService.load_schedule()` was updated to `r"^(\d+)\s+([A-Za-z]+\.?)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+(?:at|vs)\s+(.+?)\s+(\d{1,2}:\d{2}\s+[AP]M)"`.
- **Validation:** 1,200 out of 1,200 scheduled games are now parsed with 0 drops and cached to `data/processed/parquet/schedule_2026_27.parquet`.

### 1.2 Canonical Schedule Schema
Each scheduled game record is canonically represented as:
- `game_num` (int, 1–1200): Official game number in the 2026-27 schedule.
- `game_date` (str, `YYYY-MM-DD`): ISO 8601 calendar date of the scheduled contest.
- `home_team` (str): Canonical full franchise name (e.g., `"Los Angeles Lakers"`).
- `away_team` (str): Canonical full franchise name (e.g., `"Golden State Warriors"`).
- `home_team_id` / `away_team_id` (str): Official NBA franchise IDs (e.g., `"1610612747"`).
- `home_team_code` / `away_team_code` (str): 3-letter uppercase NBA abbreviation (e.g., `"LAL"`, `"GSW"`).
- `game_time` (str): Scheduled local tip-off time (e.g., `"7:00 PM"`).
- `is_lakers_game` (bool): Boolean flag denoting whether the Lakers are a participant.

---

## 2. API Contract & Validation Rules

### 2.1 Backend Server-Side Validation (`POST /predict`)
The server enforces strict multi-stage validation:
1. **Team Identifier Normalization:** `home_team` and `away_team` are normalized using `normalize_team()`. Unknown team names/codes raise `HTTP 400 Bad Request` (`"Unknown NBA team identifier: '{team_str}'"`).
2. **Team Distinctness:** Matchups where `home_team_id == away_team_id` raise `HTTP 400 Bad Request` (`"Home team and away team must be distinct NBA teams."`).
3. **Date Format:** Malformed date strings fail Pydantic model validation with `HTTP 422 Unprocessable Entity`.
4. **Schedule Existence:** The backend queries `ScheduleService.find_game(home_team, away_team, game_date)`. If no record matches the exact home host, away visitor, and date, the endpoint returns `HTTP 400 Bad Request` with:
   ```json
   {
     "detail": "No scheduled 2026-27 game exists for LAL vs GSW on 2026-12-31."
   }
   ```
5. **Inference Execution:** For valid scheduled games, the official `game_num` is supplied as `game_id`, and deterministic chronological pregame features are computed without target-game leakage.

### 2.2 Matchup Schedule Lookup Endpoint (`GET /schedule/matchup`)
- **Query Parameters:** `home_team: str`, `away_team: str`
- **Response:** List of `ScheduledGame` objects for all contests where `home_team` hosts `away_team` during the 2026-27 regular season.

---

## 3. Frontend UI Interaction

1. **Dynamic Matchup Loading:** When the user selects Home and Away teams, the frontend invokes `api.getMatchupSchedule(simHome, simAway)`.
2. **Schedule-Backed Date Selector:** The generic `<input type="date">` is replaced with a contextual `<select>` dropdown containing only the valid scheduled game dates, game numbers, and tip-off times (e.g., `📅 2026-10-21 (Game #5 • 7:00 PM)`).
3. **Empty / Host Inversion State:** If no scheduled games exist with the chosen home/away configuration, the UI displays a warning:
   `"⚠️ No scheduled 2026-27 games found with [Home] as host vs [Away]. Try reversing the home/away teams."`
   and disables the `Generate Prediction` button.
4. **Quick-Predict Integration:** Clicking "Simulate" on any game in the Schedule tab loads the exact home team, away team, and scheduled date into the Matchup Predictor without error.

---

## 4. Test Verification Suite
All regression and contract tests pass with 0 failures:

| Test Case | Description | Expected Status | Result |
| :--- | :--- | :--- | :--- |
| `test_valid_matchup_prediction_lal_gsw` | Real scheduled game (LAL vs GSW on 2026-10-21) | 200 OK | PASSED |
| `test_valid_matchup_prediction_bos_nyk` | Real scheduled game (BOS vs NYK on 2026-10-23) | 200 OK | PASSED |
| `test_unscheduled_matchup_date_rejected` | Real teams, unscheduled date (LAL vs GSW on 2026-12-31) | 400 Bad Request | PASSED |
| `test_arbitrary_in_season_date_rejected` | Real teams, wrong date (BOS vs NYK on 2026-11-05) | 400 Bad Request | PASSED |
| `test_matchup_prediction_same_team_rejected` | LAL vs LAL | 400 Bad Request | PASSED |
| `test_matchup_prediction_invalid_team_rejected` | Unknown team identifier | 400 Bad Request | PASSED |
| `test_matchup_prediction_date_outside_season_rejected` | Past date (2025-05-15) | 400 Bad Request | PASSED |
| `test_matchup_prediction_invalid_date_format` | Malformed date string | 422 Unprocessable Entity | PASSED |
| `test_matchup_prediction_persist_toggle` | Transient vs persisted prediction records | 200 OK | PASSED |
| `test_get_matchup_schedule_endpoint` | Query scheduled games for LAL hosting GSW | 200 OK (2 games) | PASSED |
| `test_schedule_lookup_and_prediction_canonicalization_parity` | Alias matching ("celtics" vs "knicks") | 200 OK | PASSED |

Full test suite: **82 passed in 98.11s**.
Frontend production build: **Vite build completed in 634ms**.
