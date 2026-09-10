# Lakers in 5 — Data Dictionary

This document defines the schema, data types, and semantic definitions for all key fields present across the datasets in the **Lakers in 5** project.

---

## 1. Player Game Statistics (`PlayerStatistics.csv` & `PlayerStatisticsExtended.csv`)

### 1.1. Core Identifiers & Contextual Attributes

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `personId` | Integer / String | Unique official NBA identifier for the player (e.g. `2544` for LeBron James, `1628404` for Josh Hart). Primary key join to `Players.csv`. |
| `firstName` | String | Player's first name. |
| `lastName` | String | Player's last name. |
| `gameId` | String / Integer | Unique official NBA identifier for the game. Primary key join to `Games.csv` and `TeamStatistics.csv`. |
| `gameDateTimeEst` | Timestamp | Scheduled start date and time of the game in Eastern Standard Time (EST) formatted as `YYYY-MM-DD HH:MM:SS`. |
| `gameDate` | Date / Timestamp | Calendar date of the game. |
| `playerteamId` | Integer | Unique identifier for the player's team in this specific contest. |
| `playerteamCity` | String | City or location name of the player's team (e.g., `Los Angeles`). |
| `playerteamName` | String | Nickname / franchise name of the player's team (e.g., `Lakers`). |
| `opponentteamId` | Integer | Unique identifier of the opposing team. |
| `opponentteamCity`| String | City or location name of the opposing team. |
| `opponentteamName`| String | Nickname / franchise name of the opposing team. |
| `gameType` | String | Competition category: `Regular Season`, `Playoffs`, `Play-In Tournament`, or `Pre-Season`. |
| `gameLabel` | String | Specific tournament/series label (e.g., `NBA Finals`, `First Round`, `Regular Season`). |
| `gameSubLabel` | String | Specific matchup sub-label (e.g., `Game 1`, `Game 5`). |
| `seriesGameNumber` | Integer | Sequence number of the game within a multi-game playoff series (1 through 7). |
| `win` | Integer (0/1) | Binary indicator of game outcome for the player's team (`1` = Win, `0` = Loss). |
| `home` | Integer (0/1) | Binary indicator of venue (`1` = Home game, `0` = Away / Neutral game). |
| `startingPosition`| String | Starting lineup position: `G` (Guard), `F` (Forward), `C` (Center), or empty if the player came off the bench. |
| `comment` | String | Status notes for players who did not play (e.g., `DNP - Coach's Decision`, `DND - Injury`, `NWT - Personal`). Empty if player entered game. |

### 1.2. Box Score Counting & Shooting Statistics

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `numMinutes` | Decimal / String | Minutes played by the player during the game (e.g. `34.5` or `34:30`). |
| `points` | Integer | Total points scored by the player. |
| `fieldGoalsMade` | Integer | Total 2-point and 3-point field goals successfully made ($FGM$). |
| `fieldGoalsAttempted`| Integer | Total field goals attempted ($FGA$). |
| `fieldGoalsPercentage`| Decimal (0.0–1.0)| Field goal percentage ($FGM / FGA$). |
| `threePointersMade`| Integer | 3-point field goals made ($3PM$). |
| `threePointersAttempted`| Integer | 3-point field goals attempted ($3PA$). |
| `threePointersPercentage`| Decimal (0.0–1.0)| 3-point field goal percentage ($3PM / 3PA$). |
| `freeThrowsMade` | Integer | Free throws made ($FTM$). |
| `freeThrowsAttempted`| Integer | Free throws attempted ($FTA$). |
| `freeThrowsPercentage`| Decimal (0.0–1.0)| Free throw shooting percentage ($FTM / FTA$). |
| `reboundsOffensive`| Integer | Offensive rebounds collected ($OREB$). |
| `reboundsDefensive`| Integer | Defensive rebounds collected ($DREB$). |
| `reboundsTotal` | Integer | Total rebounds collected ($REB = OREB + DREB$). |
| `assists` | Integer | Direct assists leading to field goals ($AST$). |
| `steals` | Integer | Defensive steals ($STL$). |
| `blocks` | Integer | Blocked shots ($BLK$). |
| `turnovers` | Integer | Ball possession turnovers ($TOV$). |
| `foulsPersonal` | Integer | Personal fouls committed ($PF$). |
| `plusMinusPoints` | Integer | Net team point differential while the player was on the court ($+/-$). |

### 1.3. Advanced & Tracking Metrics (`PlayerStatisticsExtended.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `offensiveRating` | Decimal | Points produced by the team per 100 possessions while player is on the court. |
| `defensiveRating` | Decimal | Points allowed by the team per 100 possessions while player is on the court. |
| `netRating` | Decimal | Difference between Offensive Rating and Defensive Rating ($NetRtg = OffRtg - DefRtg$). |
| `usagePercentage` | Decimal | Percentage of team plays used by the player while on floor ($USG\% = \frac{FGA + 0.44 \times FTA + TOV}{Possessions}$). |
| `effectiveFieldGoalPercentage` | Decimal | Shooting percentage adjusted for 3-pointers ($eFG\% = \frac{FGM + 0.5 \times 3PM}{FGA}$). |
| `trueShootingPercentage` | Decimal | Comprehensive shooting efficiency metric ($TS\% = \frac{PTS}{2 \times (FGA + 0.44 \times FTA)}$). |
| `playerImpactEstimate` | Decimal | Metric measuring a player's overall statistical contribution relative to total game events ($PIE$). |
| `assistPercentage` | Decimal | Percentage of teammate field goals the player assisted while on floor. |
| `assistToTurnoverRatio` | Decimal | Ratio of assists created to turnovers committed ($AST / TOV$). |
| `reboundPercentage` | Decimal | Percentage of available rebounds grabbed while on the court. |
| `pace` | Decimal | Estimated possessions per 48 minutes while player was on the court. |
| `possessions` | Integer | Number of possessions player participated in during court time. |
| `pointsOffTurnovers`| Decimal | Points scored by player directly following opponent turnovers. |
| `pointsInPaint` | Decimal | Points scored inside the key / painted area. |
| `pointsFastBreak` | Decimal | Points scored in fast-break transition situations. |
| `percentTeamPoints` | Decimal | Proportion of the team's total points scored by this player. |
| `percentTeamAssists` | Decimal | Proportion of the team's total assists credited to this player. |
| `percentAssisted2PointMade` | Decimal | Percentage of player's made 2-pointers that were assisted by a teammate. |
| `percentUnassisted2PointMade` | Decimal | Percentage of player's made 2-pointers created independently (unassisted). |

---

## 2. Team Game Statistics (`TeamStatistics.csv` & `TeamStatisticsExtended.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `gameId` | String / Integer | Unique official NBA game ID. |
| `gameDateTimeEst` | Timestamp | Start timestamp in EST. |
| `teamId` | Integer | Unique identifier of the team. |
| `teamName` | String | Team name (e.g., `Lakers`). |
| `opponentTeamId` | Integer | Identifier of the opposing team. |
| `home` | Integer (0/1) | Home court indicator (`1` = Home, `0` = Away). |
| `win` | Integer (0/1) | Game outcome (`1` = Win, `0` = Loss). |
| `teamScore` | Integer | Total points scored by the team in this game. |
| `opponentScore` | Integer | Total points allowed by the team in this game. |
| `q1Points` – `q4Points` | Integer | Points scored by quarter (1st through 4th). |
| `ot1Points` – `otAllPoints` | Integer | Overtime period points. |
| `benchPoints` | Integer | Total points contributed by non-starters. |
| `biggestLead` | Integer | Largest point margin held by the team during the game. |
| `leadChanges` | Integer | Total number of lead changes in the matchup. |
| `timesTied` | Integer | Number of times the score was tied during regulation and OT. |
| `seasonWins` | Integer | Cumulative wins by the team prior to or after this game. |
| `seasonLosses` | Integer | Cumulative losses by the team prior to or after this game. |
| `fourFactorsEffectiveFieldGoalPercentage` | Decimal | Team effective shooting efficiency ($eFG\%$). |
| `fourFactorsTurnoverPercentage` | Decimal | Percentage of team possessions ending in a turnover ($TOV\%$). |
| `fourFactorsOffensiveReboundPercentage` | Decimal | Percentage of available offensive rebounds captured ($OREB\%$). |
| `fourFactorsFreeThrowRate` | Decimal | Free throw attempts per field goal attempt ($FTA / FGA$). |
| `pace` | Decimal | Pace of play: total possessions per 48 minutes. |
| `offensiveRating` | Decimal | Offensive efficiency: points scored per 100 possessions. |
| `defensiveRating` | Decimal | Defensive efficiency: points allowed per 100 possessions. |
| `netRating` | Decimal | Point differential per 100 possessions ($OffRtg - DefRtg$). |

---

## 3. Game Matchup Metadata (`Games.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `gameId` | String / Integer | Unique official NBA game ID. |
| `gameDateTimeEst` | Timestamp | Scheduled tip-off date and time (EST). |
| `hometeamId` / `awayteamId` | Integer | Team IDs for home and away competitors. |
| `hometeamCity` / `hometeamName` | String | Location and franchise name for home team. |
| `awayteamCity` / `awayteamName` | String | Location and franchise name for visiting team. |
| `homeScore` / `awayScore` | Integer | Final score for each team. |
| `winner` | String / Integer | Winning franchise name or ID. |
| `gameType` | String | Regular Season, Playoffs, Play-In Tournament, Pre-Season. |
| `attendance` | Integer | Number of fans in attendance. |
| `arenaName` | String | Name of the venue / arena (e.g., `Crypto.com Arena`). |
| `arenaCity` / `arenaState` | String | Arena location. |
| `officials` | String | Officiating crew referee names. |

---

## 4. Player Bio Profiles (`Players.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `personId` | Integer | Unique player identifier. |
| `firstName` / `lastName` | String | Player full legal name. |
| `birthDate` | Date | Player date of birth (`YYYY-MM-DD`). |
| `school` | String | College, university, or high school attended before NBA draft. |
| `country` | String | Country of origin / nationality. |
| `heightInches` | Integer | Height in inches. |
| `bodyWeightLbs` | Integer | Weight in pounds. |
| `jersey` | String | Primary jersey number. |
| `guard` / `forward` / `center` | Integer (0/1) | Positional eligibility flags. |
| `draftYear` | Integer | Year selected in NBA draft. |
| `draftRound` / `draftNumber` | Integer | Draft round (1 or 2) and overall pick number (1–60). |
| `fromYear` / `toYear` | Integer | First and last active seasons in the NBA. |

---

## 5. Offseason Transactions (`nba_2026_offseason_transactions.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `Team` | String | Franchise associated with the transaction (e.g. `Los Angeles Lakers`). |
| `Category` | String | Type of movement: `Additions`, `Departures`, `Re-signing`, `Draft`, `Extension`, `Waiver`. |
| `Player` | String | Full name of the involved player. |
| `Transaction` | String | Contract details, trade terms, or draft pick info (e.g. `Trade with Kings`, `1-year deal`). |
| `Status` | String | Official reporting status (`Officially announced`, `Multiple reports`). |

---

## 6. Historical Franchise Lineage (`TeamHistories.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `teamId` | Integer | Stable franchise identifier across city/name rebrandings. |
| `teamCity` | String | City name during this historical tenure (e.g. `Minneapolis`, `Los Angeles`). |
| `teamName` | String | Nickname during this tenure (e.g. `Lakers`). |
| `teamAbbrev` | String | 3- or 4-letter box score abbreviation (e.g. `LAL`, `MNL`). |
| `seasonFounded` | Integer | First season active in the league. |
| `seasonActiveTill` | Integer / String | Last season under this specific city/name designation. |
| `league` | String | League governing body (`NBA`, `BAA`, `ABA`). |
