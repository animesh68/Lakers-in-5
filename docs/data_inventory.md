# Lakers in 5 — Data Inventory

This document provides a comprehensive inventory of all raw datasets currently stored in `data/raw/` for the **Lakers in 5** project.

---

## 1. Summary Inventory Table

| Dataset Name | Current Location | Original Filename | Format | Granularity | Rows | Cols | Date Range | Primary Purpose in Lakers in 5 |
| :--- | :--- | :--- | :---: | :---: | ---: | ---: | :---: | :--- |
| **Games** | `data/raw/games/Games.csv` | `Games.csv` | CSV | Game-level | 73,279 | 23 | 1946-11-26 to 2026-06-13 | Matchup outcomes, final scores, home/away status, location, attendance, officials |
| **Team Statistics** | `data/raw/games/TeamStatistics.csv` | `TeamStatistics.csv` | CSV | Team-Game | 146,560 | 59 | 1946-11-26 to 2026-06-13 | Traditional team box scores (points by quarter, shooting %, rebounds, assists, turnovers) |
| **Team Statistics Extended** | `data/raw/games/TeamStatisticsExtended.csv` | `TeamStatisticsExtended.csv` | CSV | Team-Game | 79,724 | 104 | 1996-11-01 to 2026-06-13 | Advanced & tracking team metrics (Off/Def/Net ratings, Pace, True Shooting %, Four Factors) |
| **Player Statistics** | `data/raw/players/PlayerStatistics.csv` | `PlayerStatistics.csv` | CSV | Player-Game | 1,669,922 | 40 | 1946-11-26 to 2026-06-13 | Historical individual player game logs (points, assists, rebounds, minutes, +/-) |
| **Player Statistics Extended** | `data/raw/players/PlayerStatisticsExtended.csv` | `PlayerStatisticsExtended.csv` | CSV | Player-Game | 838,803 | 110 | 1996-11-01 to 2026-06-13 | Advanced player metrics (PIE, Usage %, True Shooting %, assisted/unassisted shot breakdown) |
| **Player Profiles** | `data/raw/players/Players.csv` | `Players.csv` | CSV | Player bio | 6,692 | 20 | Static bio / Drafts | Bio metadata (height, weight, draft year/round/pick, position, active career span) |
| **Playoffs Season Stats** | `data/raw/players/Playoffs.csv` | `Playoffs.csv` | CSV | Player-Season | 2,576 | 31 | 2012-13 to 2023-24 | Scraped seasonal playoff player leaderboards & rate stats from NBA.com |
| **Regular Season Stats** | `data/raw/players/Regular_Season.csv` | `Regular_Season.csv` | CSV | Player-Season | 6,259 | 31 | 2012-13 to 2023-24 | Scraped seasonal regular season player leaderboards & rate stats from NBA.com |
| **NBA Combined Season Stats** | `data/raw/players/nba.csv` | `nba.csv` | CSV | Player-Season | 8,835 | 30 | 2012-13 to 2023-24 | Consolidated seasonal regular season + playoff player totals (contains `EFF` column) |
| **Schedule (By Date)** | `data/raw/schedules/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf` | `2026-27-NBA-Regular-Season-Schedule-By-Date.pdf` | PDF | Game schedule | ~1,230 games | N/A | 2026-10-20 to 2027-04-11 | Chronological 2026-27 regular season fixtures for future outcome prediction |
| **Schedule (By Team)** | `data/raw/schedules/2026-27-NBA-Regular-Season-Schedule-By-Team.pdf` | `2026-27-NBA-Regular-Season-Schedule-By-Team.pdf` | PDF | Team schedule | 30 teams × 82 | N/A | 2026-10-20 to 2027-04-11 | Team-by-team 82-game schedule (including Lakers full 82-game campaign & rest days) |
| **2026 Offseason Transactions** | `data/raw/transactions/nba_2026_offseason_transactions.csv` | `nba_2026_offseason_transactions.csv` | CSV | Transaction | 259 | 5 | Offseason 2026 | Player movement (signings, trades, waivers, extensions) for 2026-27 roster state |
| **Team Histories** | `data/raw/other/TeamHistories.csv` | `TeamHistories.csv` | CSV | Franchise | 140 | 7 | 1946 to Present | Historical franchise tracking (city relocations, name changes, BAA/NBA continuity) |
| **Scraper Notes** | `data/raw/other/README.txt` | `README.txt` | TXT | Reference | 65 lines | N/A | N/A | Reference for abbreviations (`GP`, `MIN`, `PTS`, `AST_TOV`) and franchise 3-letter codes |

---

## 2. Detailed Dataset Profiles

### 2.1. Games (`data/raw/games/Games.csv`)
* **Original Filename:** `Games.csv`
* **File Size:** ~10.69 MB
* **Total Rows:** 73,279
* **Total Columns:** 23
* **Date Range:** November 26, 1946 to June 13, 2026 (Game 5 of 2026 NBA Finals)
* **Granularity:** Game-level (one row per game)
* **Key Columns:** `gameId`, `gameDateTimeEst`, `hometeamId`, `awayteamId`, `hometeamCity`, `hometeamName`, `awayteamCity`, `awayteamName`, `homeScore`, `awayScore`, `winner`, `gameType`, `gameLabel`, `attendance`, `arenaName`
* **Project Role:** Serves as the primary ground-truth target table for historical match outcomes (who won, score margin, home court advantage).
* **Notes & Observations:**
  * Contains games across all eras: regular season, playoffs, and play-in tournaments.
  * `winner` directly indicates winning team name/id.

---

### 2.2. Team Statistics (`data/raw/games/TeamStatistics.csv`)
* **Original Filename:** `TeamStatistics.csv`
* **File Size:** ~34.35 MB
* **Total Rows:** 146,560 (exactly 2 rows per game for 73,279 games)
* **Total Columns:** 59
* **Date Range:** November 26, 1946 to June 13, 2026
* **Granularity:** Team-Game level (one record per team per game)
* **Key Columns:** `gameId`, `gameDateTimeEst`, `teamId`, `teamName`, `opponentTeamId`, `home`, `win`, `teamScore`, `opponentScore`, `assists`, `blocks`, `steals`, `fieldGoalsMade`, `fieldGoalsAttempted`, `threePointersMade`, `threePointersAttempted`, `freeThrowsMade`, `freeThrowsAttempted`, `reboundsTotal`, `turnovers`, `plusMinusPoints`, `q1Points`-`q4Points`, `benchPoints`, `pointsFastBreak`, `pointsInThePaint`
* **Project Role:** Provides traditional box score metrics and quarter-by-quarter scoring breakdowns per team.
* **Notes & Observations:**
  * Box score stats like three-pointers and turnovers are available from the eras when the NBA began recording them (3PT recorded starting 1979-80). Earlier eras naturally contain null/zero values for modern metrics.

---

### 2.3. Team Statistics Extended (`data/raw/games/TeamStatisticsExtended.csv`)
* **Original Filename:** `TeamStatisticsExtended.csv`
* **File Size:** ~36.42 MB
* **Total Rows:** 79,724
* **Total Columns:** 104
* **Date Range:** November 1, 1996 to June 13, 2026
* **Granularity:** Team-Game level (advanced era)
* **Key Columns:** `gameId`, `teamId`, `offensiveRating`, `defensiveRating`, `netRating`, `pace`, `possessions`, `effectiveFieldGoalPercentage`, `trueShootingPercentage`, `assistPercentage`, `assistToTurnoverRatio`, `offensiveReboundPercentage`, `defensiveReboundPercentage`, `teamTurnoverPercentage`, `freeThrowAttemptRate`, `playerImpactEstimate`, `opponentPointsOffTurnovers`, `opponentPointsInPaint`
* **Project Role:** Rich source for team-level Dean Oliver "Four Factors" (eFG%, TOV%, OREB%, FT Rate) and possession-adjusted efficiency ratings (Off/Def/Net Rating, Pace).
* **Notes & Observations:**
  * Begins in the 1996-97 season when the NBA officially instituted play-by-play and advanced box tracking.

---

### 2.4. Player Statistics (`data/raw/players/PlayerStatistics.csv`)
* **Original Filename:** `PlayerStatistics.csv`
* **File Size:** ~371.62 MB
* **Total Rows:** 1,669,922
* **Total Columns:** 40
* **Date Range:** November 26, 1946 to June 13, 2026
* **Granularity:** Individual Player-Game level
* **Key Columns:** `personId`, `firstName`, `lastName`, `gameId`, `gameDateTimeEst`, `playerteamId`, `opponentteamId`, `win`, `home`, `numMinutes`, `points`, `assists`, `blocks`, `steals`, `fieldGoalsAttempted`, `fieldGoalsMade`, `fieldGoalsPercentage`, `threePointersAttempted`, `threePointersMade`, `threePointersPercentage`, `freeThrowsAttempted`, `freeThrowsMade`, `freeThrowsPercentage`, `reboundsDefensive`, `reboundsOffensive`, `reboundsTotal`, `foulsPersonal`, `turnovers`, `plusMinusPoints`, `startingPosition`, `comment`
* **Project Role:** Foundation for individual player performance aggregation, starter identification, player availability, and rolling form.
* **Notes & Observations:**
  * `comment` contains Did Not Play (DNP) reasons like "DNP - Coach's Decision", "DND - Injury", etc., which will be crucial for modeling player availability and injury impact.

---

### 2.5. Player Statistics Extended (`data/raw/players/PlayerStatisticsExtended.csv`)
* **Original Filename:** `PlayerStatisticsExtended.csv`
* **File Size:** ~432.32 MB
* **Total Rows:** 838,803
* **Total Columns:** 110
* **Date Range:** November 1, 1996 to June 13, 2026
* **Granularity:** Individual Player-Game level (advanced era)
* **Key Columns:** `personId`, `gameId`, `offensiveRating`, `defensiveRating`, `netRating`, `usagePercentage`, `effectiveFieldGoalPercentage`, `trueShootingPercentage`, `playerImpactEstimate`, `assistPercentage`, `assistToTurnoverRatio`, `reboundPercentage`, `pointsOffTurnovers`, `pointsInPaint`, `percentTeamPoints`, `percentTeamAssists`, `percentTeamRebounds`, `percentAssisted2PointMade`, `percentUnassisted2PointMade`
* **Project Role:** Provides player-level usage share, true shooting efficiency, and team dependency ratios (% of team points, assists, rebounds).
* **Notes & Observations:**
  * Covers 1996-97 onwards. Ideal for computing modern player value metrics and weighted impact on team ratings.

---

### 2.6. Player Profiles (`data/raw/players/Players.csv`)
* **Original Filename:** `Players.csv`
* **File Size:** ~524 KB
* **Total Rows:** 6,692
* **Total Columns:** 20
* **Granularity:** Player profile (one row per player in NBA history)
* **Key Columns:** `personId`, `firstName`, `lastName`, `birthDate`, `school`, `country`, `heightInches`, `bodyWeightLbs`, `jersey`, `guard`, `forward`, `center`, `draftYear`, `draftRound`, `draftNumber`, `fromYear`, `toYear`
* **Project Role:** Dimension table for player physical attributes, positions, age, draft pedigree, and career span.

---

### 2.7. Seasonal Player Datasets (`Playoffs.csv`, `Regular_Season.csv`, `nba.csv`)
* **Locations:**
  * `data/raw/players/Playoffs.csv` (2,576 rows, 31 cols, 2012-13 to 2023-24)
  * `data/raw/players/Regular_Season.csv` (6,259 rows, 31 cols, 2012-13 to 2023-24)
  * `data/raw/players/nba.csv` (8,835 rows, 30 cols, 2012-13 to 2023-24)
* **Granularity:** Player-Season aggregated totals/averages
* **Key Columns:** `year`, `Season_type`, `PLAYER_ID`, `RANK`, `PLAYER`, `TEAM_ID`, `TEAM`, `GP`, `MIN`, `PTS`, `FGM`, `FGA`, `FG_PCT`, `FG3M`, `FG3A`, `FG3_PCT`, `FTM`, `FTA`, `FT_PCT`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `AST_TOV`, `STL_TOV`, `EFF` (in `nba.csv`)
* **Relationship & Duplication Analysis:**
  * `Playoffs.csv` (2,576 rows) and `Regular_Season.csv` (6,259 rows) sum exactly to 8,835 rows.
  * `nba.csv` is the union of `Regular_Season.csv` and `Playoffs.csv`, formatted with an additional `EFF` (Efficiency) rating column and without pandas index artifacts (`Unnamed: 0`).
  * **Preservation Policy:** All three files are preserved in `data/raw/players/` to adhere to raw data immutability.

---

### 2.8. NBA 2026-27 Schedules (`data/raw/schedules/*.pdf`)
* **Files:**
  1. `2026-27-NBA-Regular-Season-Schedule-By-Date.pdf` (~541 KB)
  2. `2026-27-NBA-Regular-Season-Schedule-By-Team.pdf` (~1.27 MB)
* **Format:** PDF document
* **Content:** Official 2026-27 NBA Regular Season Schedule released by the NBA.
  * By Date: All 1,230 regular season games arranged chronologically starting October 20, 2026 through April 11, 2027, including national TV broadcast info (ESPN, ABC, TNT, NBA TV).
  * By Team: 82 regular season games broken down by each of the 30 franchises (specifically including the Los Angeles Lakers).
* **Project Role:** Provides the forward-looking inference targets (upcoming Lakers matchups, opponents, home/away status, travel days, back-to-back rest days).

---

### 2.9. 2026 Offseason Transactions (`data/raw/transactions/nba_2026_offseason_transactions.csv`)
* **Original Filename:** `nba_2026_offseason_transactions.csv`
* **File Size:** ~20.8 KB
* **Total Rows:** 259
* **Total Columns:** 5
* **Date Range:** Summer 2026 Offseason
* **Key Columns:** `Team`, `Category` (`Additions`, `Departures`, `Re-signing`, `Draft`), `Player`, `Transaction`, `Status` (`Officially announced`, `Multiple reports`)
* **Project Role:** Informs roster updates going into the 2026-27 season (e.g. new signings, traded players, departures) so that pre-season team strength can be updated before 2026-27 games begin.

---

### 2.10. Team Histories & Reference Docs (`data/raw/other/`)
* **`data/raw/other/TeamHistories.csv`:**
  * **Rows:** 140 | **Cols:** 7
  * **Columns:** `teamId`, `teamCity`, `teamName`, `teamAbbrev`, `seasonFounded`, `seasonActiveTill`, `league`
  * **Purpose:** Maps historical franchise relocations (e.g., Minneapolis Lakers $\to$ Los Angeles Lakers, Tri-Cities Blackhawks $\to$ Milwaukee $\to$ St. Louis $\to$ Atlanta Hawks) to stable `teamId` keys.
* **`data/raw/other/README.txt`:**
  * **Lines:** 65
  * **Purpose:** Original reference document mapping scraped column abbreviations and NBA team 3-letter codes to full team names.

---

## 3. Storage & Versioning Notes

* **Large Files:** `PlayerStatistics.csv` (371.6 MB) and `PlayerStatisticsExtended.csv` (432.3 MB) exceed GitHub's standard 100MB file limit. In production, these should be managed via Git LFS or object storage (S3 / GCS / DVC).
* **Data Immutability:** No files in `data/raw/` have been altered, sampled, or truncated. All hash signatures match their original sources.
