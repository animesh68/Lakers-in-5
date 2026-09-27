# Lakers in 5 — UI/UX Redesign & Information Architecture

## 1. Overview & Redesign Philosophy
The **Lakers in 5** frontend has been redesigned from an engineering/debug dashboard into a polished sports-analytics prediction product. The user experience is structured around the core principle:

$$\text{PREDICT} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{EXPLORE}$$

### Key Improvements:
- **Hero-First Next Game Experience:** The home landing screen immediately answers the user's primary question: *"What does the model think will happen in the Lakers' next game?"*
- **Primary Visual Focal Point:** Prominent display of win probability (e.g., `71.7% LAKERS WIN`), projected point margin (`+6.2 pts`), and matchup confidence without overwhelming implementation clutter.
- **Honest Pregame Context:** "Factors reflected in this prediction" displays pregame feature state (Home venue advantage, Rest & travel density, Pregame Elo rating, Regularized differential form) without making false causal claims.
- **Short Horizon Schedule:** Presents the next 4–5 Lakers contests with 1-click `Predict` buttons to immediately run inference on any upcoming scheduled game.
- **Dedicated Technical Isolation:** Moved deep MLOps diagnostics (Brier score, ECE, PSI drift metrics, Retraining Advisory Engine, 52-column feature parity, and Lakehouse architecture) into a dedicated **Model** tab.

---

## 2. Information Architecture & Navigation

The primary navigation has been streamlined to 4 primary tabs:
```
[ L ] LAKERS IN 5      Forecast    Matchups    Schedule    Model      ● System Operational  ⚙
```

1. **Forecast (`/`)**:
   - Next Lakers game hero card with dominant win probability and margin.
   - Key pregame feature factors.
   - Short upcoming Lakers horizon with 1-click simulation.
2. **Matchups**:
   - Focused matchup builder.
   - Home team, Away team, and schedule-backed game selector (dynamically filtered against official 2026-27 regular season).
   - Clear forecast output with probability bars and expandable technical metadata.
3. **Schedule**:
   - Clean chronological timeline of official regular season games.
   - Filterable by team with quick limit options.
   - 1-click `Predict` action leading directly into inference.
4. **Model & Engineering**:
   - Multi-metric diagnostics: Brier score, ECE, Max PSI drift, and overall health status.
   - Retraining decision advisory with guardrail thresholds.
   - Expandable technical deep-dives into Champion models, feature parity contracts, and DuckDB lakehouse architecture.

---

## 3. Design System & Tokens
- **Theme:** Dark, premium sports-analytics palette.
- **Background:** Deep graphite charcoal (`#08060D`) with subtle elevated surfaces (`#100C1B` / `#161224`).
- **Accents:** Lakers Gold (`#FDB927`) as primary highlight/action, restrained Lakers Purple (`#552583`), and emerald green (`#10B981`) for nominal system health.
- **Typography:** `Outfit` (Display & Titles), `Plus Jakarta Sans` (Body), and `JetBrains Mono` (Numeric metrics & hashes).
- **Component Primitives:** Clean reusable modules (`StatusBadge`, `MetricCard`, `ProbabilityBar`, `Header`, `Footer`, `SettingsModal`).

---

## 4. Verification & Testing
- **Automated Tests:** All **82/82 pytest tests passed** with 0 regressions.
- **Frontend Build:** `npm run build` executed in 563ms with 0 warnings/errors.
- **Backend API Integration:** Verified `/predict/lakers/next`, `/predict`, `/schedule/matchup`, `/schedule/2026-27`, and `/monitoring/health`.
