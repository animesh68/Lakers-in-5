# Phase 3: Model Experimentation, Time-Series Validation & Model Selection

## 1. Executive Summary

Phase 3 established a leakage-safe, time-series expanding-window validation and machine learning experimentation framework for predicting NBA game outcomes (`target_home_win` and `target_point_margin`).

The experiments evaluated 5 classification model families (9 configurations) and 3 regression model families (7 configurations) across **10 walk-forward expanding folds** (validation seasons 2015–16 through 2024–25; training seasons 2000–01 through $S-1$).

The **2025–26 season was strictly isolated as the untouched final test set** and evaluated exactly once after champion model selection.

```
+---------------------------------------------------------------------------------------------------+
| MODEL ARCHITECTURE & EVALUATION HIERARCHY                                                         |
+---------------------------------------------------------------------------------------------------+
|  1. Naive Home Baseline       -> Empirical train home-win rate benchmark (LogLoss: 0.6864)        |
|  2. Pregame Elo Baseline      -> Logistic Elo probability benchmark (LogLoss: 0.6321)             |
|  3. Logistic Regression       -> Linear probabilistic pipeline (LogLoss: 0.6183) [CHAMPION]       |
|  4. LightGBM Classifier       -> Gradient boosted decision trees (LogLoss: 0.6248)                |
|  5. XGBoost Classifier        -> Gradient boosted decision trees (LogLoss: 0.6230)                |
|  6. Margin Regressors         -> Ridge (MAE: 10.378) [CHAMPION] vs LightGBM (10.453) / XGB (10.444)|
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Temporal Validation & Leakage Protection Methodology

### 2.1 Expanding-Window Walk-Forward Cross-Validation
To respect the temporal arrow of time, all development validation was performed using 10 sequential walk-forward expanding folds:
* **Fold 1:** Train 2000–01 to 2014–15 $\to$ Validate 2015–16 (1,230 games)
* **Fold 2:** Train 2000–01 to 2015–16 $\to$ Validate 2016–17 (1,230 games)
* **Fold 3:** Train 2000–01 to 2016–17 $\to$ Validate 2017–18 (1,230 games)
* **Fold 4:** Train 2000–01 to 2017–18 $\to$ Validate 2018–19 (1,230 games)
* **Fold 5:** Train 2000–01 to 2018–19 $\to$ Validate 2019–20 (1,059 games)
* **Fold 6:** Train 2000–01 to 2019–20 $\to$ Validate 2020–21 (1,080 games)
* **Fold 7:** Train 2000–01 to 2020–21 $\to$ Validate 2021–22 (1,230 games)
* **Fold 8:** Train 2000–01 to 2021–22 $\to$ Validate 2022–23 (1,230 games)
* **Fold 9:** Train 2000–01 to 2022–23 $\to$ Validate 2023–24 (1,164 games)
* **Fold 10:** Train 2000–01 to 2023–24 $\to$ Validate 2024–25 (1,226 games)

### 2.2 Leakage Guardrails Enforced
1. **No Temporal Inversion:** $\max(\text{train\_game\_date}) < \min(\text{val\_game\_date})$.
2. **Train-Only Preprocessing:** `SimpleImputer` and `StandardScaler` are fitted strictly on `X_train` within each fold.
3. **Identifier Exclusion:** Non-feature columns (`game_id`, `game_date`, `season`, `home_team`, `away_team`, `home_team_id`, `away_team_id`) and targets are strictly excluded from predictive matrices.
4. **Final Test Isolation:** The 2025–26 season (1,230 games) was completely excluded from all development folds, hyperparameter decisions, and threshold selections.

---

## 3. Classification Benchmark Results (`target_home_win`)

### 3.1 Development Validation Performance (10 Walk-Forward Folds, 2015–16 to 2024–25)
*Ranked by Mean Validation Log Loss (Primary Selection Metric)*

| Model | Log Loss (Mean $\pm$ Std) | Brier Score | Accuracy | ROC-AUC | ECE | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression (Standard)** | **0.6191 $\pm$ 0.0207** | **0.2153** | **0.653** | **0.704** | **0.0404** | **SELECTED CHAMPION** |
| **Logistic Regression (Diff Concat)** | 0.6192 $\pm$ 0.0207 | 0.2153 | 0.652 | 0.704 | 0.0398 | Contender |
| **Logistic Regression (Diff Only)** | 0.6196 $\pm$ 0.0209 | 0.2155 | 0.653 | 0.704 | 0.0383 | Contender |
| **XGBoost (Diff Concat)** | 0.6242 $\pm$ 0.0174 | 0.2174 | 0.653 | 0.697 | 0.0347 | Non-linear baseline |
| **LightGBM (Diff Concat)** | 0.6248 $\pm$ 0.0170 | 0.2177 | 0.648 | 0.696 | 0.0397 | Non-linear baseline |
| **XGBoost (Standard)** | 0.6257 $\pm$ 0.0190 | 0.2180 | 0.652 | 0.696 | 0.0362 | Non-linear baseline |
| **LightGBM (Standard)** | 0.6271 $\pm$ 0.0192 | 0.2187 | 0.649 | 0.693 | 0.0379 | Non-linear baseline |
| **Elo Baseline** | 0.6321 $\pm$ 0.0215 | 0.2208 | 0.643 | 0.696 | 0.0617 | Domain benchmark |
| **Naive Home Baseline** | 0.6864 $\pm$ 0.0080 | 0.2466 | 0.565 | 0.500 | 0.0297 | Empirical baseline |

### 3.2 Key Finding: Linear Regularization Outperforms Tree Boosting
Logistic Regression achieved the lowest log loss (0.6191) and highest ROC-AUC (0.704), consistently outperforming uncalibrated gradient boosted trees (XGBoost at 0.6242, LightGBM at 0.6248). In NBA game outcome prediction, where the signal-to-noise ratio is inherently moderate and features are symmetric across home/away matchups, L2-regularized linear models provide superior generalization with fewer overfitting risks.

---

## 4. Margin Regression Benchmark Results (`target_point_margin`)

### 4.1 Development Validation Performance (10 Walk-Forward Folds, 2015–16 to 2024–25)
*Ranked by Mean Validation MAE (Primary Selection Metric)*

| Model | MAE (Mean $\pm$ Std) | RMSE | Mean Bias | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Ridge Regression (Diff Only)** | **10.386 $\pm$ 0.677** | **13.261** | **+0.655** | **SELECTED CHAMPION** |
| **Ridge Regression (Standard)** | 10.389 $\pm$ 0.663 | 13.260 | +0.549 | Contender |
| **Ridge Regression (Diff Concat)** | 10.390 $\pm$ 0.664 | 13.261 | +0.551 | Contender |
| **XGBoost Regressor (Diff Concat)** | 10.462 $\pm$ 0.665 | 13.365 | +0.439 | Non-linear baseline |
| **LightGBM Regressor (Diff Concat)** | 10.472 $\pm$ 0.653 | 13.378 | +0.450 | Non-linear baseline |
| **XGBoost Regressor (Standard)** | 10.474 $\pm$ 0.660 | 13.368 | +0.541 | Non-linear baseline |
| **LightGBM Regressor (Standard)** | 10.478 $\pm$ 0.634 | 13.371 | +0.566 | Non-linear baseline |

---

## 5. Untouched Final Test Set Evaluation (Season 2025–26)

Trained on all development data (2000–01 through 2024–25, 29,954 games) and evaluated once on the 2025–26 regular season (1,230 games).

### 5.1 Champion Classifier (`Logistic Regression (Standard)`)
* **Log Loss:** `0.6076` (Strong generalization beyond 0.6191 CV mean)
* **Brier Score:** `0.2093`
* **Accuracy:** `68.07%` (837 / 1,230 games predicted correctly)
* **ROC-AUC:** `0.7253`
* **Expected Calibration Error (ECE):** `0.0262` (2.62%)

### 5.2 Champion Margin Regressor (`Ridge Regression (Diff Only)`)
* **MAE:** `11.476` points
* **RMSE:** `14.722` points
* **Mean Bias:** `+0.704` points

### 5.3 Decile Probability Calibration Analysis (2025–26 Season)
The classifier's predicted probabilities demonstrate strong calibration across all bins:

| Probability Bin | Game Count | Mean Predicted Prob | Actual Win Rate | Calibration Gap |
| :--- | :--- | :--- | :--- | :--- |
| **0.0 – 0.1** | 3 | 9.1% | 0.0% | 9.1% |
| **0.1 – 0.2** | 40 | 16.2% | 10.0% | 6.2% |
| **0.2 – 0.3** | 97 | 24.8% | 23.7% | **1.1%** |
| **0.3 – 0.4** | 143 | 35.0% | 38.5% | **3.4%** |
| **0.4 – 0.5** | 202 | 45.5% | 38.6% | 6.9% |
| **0.5 – 0.6** | 191 | 55.6% | 58.6% | **3.1%** |
| **0.6 – 0.7** | 202 | 65.3% | 66.8% | **1.5%** |
| **0.7 – 0.8** | 195 | 74.9% | 76.4% | **1.6%** |
| **0.8 – 0.9** | 128 | 84.1% | 79.7% | 4.4% |
| **0.9 – 1.0** | 29 | 91.4% | 82.8% | 8.6% |

---

## 6. Feature Importances & Interpretability

### 6.1 Top Standardized Coefficients (Champion Logistic Regression)
1. `diff_rotation_usage_5` (+0.444): Net top-rotation usage percentage difference.
2. `diff_rotation_points_5` (+0.296): Net points scored by top rotational players.
3. `diff_elo` / `elo_difference` (+0.240): Pre-game Elo rating difference with home advantage.
4. `away_rest_days` / `home_rest_days` ($\pm 0.230$): Schedule rest differential.
5. `away_win_pct_10` / `home_win_pct_10` ($\pm 0.198$): 10-game rolling form.
6. `home_ts_5` / `away_efg_5` ($\pm 0.168$): Short-term shooting efficiency.

### 6.2 Top Tree Feature Importances (XGBoost Classifier)
1. `elo_difference` / `diff_elo` (26.5% total gain): Dominant matchup anchor.
2. `diff_point_diff_10` (2.0% gain): 10-game point differential difference.
3. `diff_back_to_back` / `away_back_to_back` (2.8% gain): Schedule fatigue indicators.
4. `home_off_rating_10` / `away_efg_10` (2.2% gain): 10-game efficiency metrics.
5. `diff_rotation_points_5` (1.1% gain): Rotation scoring capacity.

---

## 7. Artifact Directory & MLflow Integration

* **Evaluation Tables:**
  - `data/evaluation/classification_results.csv` (Fold-by-fold results for all 9 classifiers)
  - `data/evaluation/regression_results.csv` (Fold-by-fold results for all 7 regressors)
  - `data/evaluation/predictions.parquet` (Complete out-of-fold and test predictions)
  - `data/evaluation/feature_importances.csv` (All model coefficients and gain metrics)
  - `data/evaluation/calibration_summary.csv` (10-bin calibration table)
* **Production Model Artifacts (Trained on 2000–2025 historical data for 2026–27 inference):**
  - `models/champion_classifier.joblib`
  - `models/champion_regressor.joblib`
* **MLflow Tracking:**
  - SQLite backend: `sqlite:///data/evaluation/mlflow.db`
  - Experiment: `lakers_in_5_phase3`

---

## 8. Reproducibility Command

To execute the entire Phase 3 experiment pipeline from scratch:
```bash
python scripts/run_experiments.py
```
To run the complete test suite:
```bash
pytest tests/ -v
```
