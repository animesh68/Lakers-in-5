import joblib
import pandas as pd
import numpy as np
from src.models.player_models import PlayerPerformanceSuite
from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT

suite = PlayerPerformanceSuite.load_artifacts("models")
min_pipe = suite.minutes_model.pipeline
scaler = min_pipe.named_steps["scaler"]
reg = min_pipe.named_steps["regressor"]

print("=== MINUTES MODEL COEFFICIENTS ===")
coefs = pd.DataFrame({
    "feature": PLAYER_FEATURE_CONTRACT,
    "mean": scaler.mean_,
    "scale": scaler.scale_,
    "coef": reg.coef_
})
print(coefs.to_string())
print(f"\nIntercept: {reg.intercept_}")

pts_pipe = suite.points_model.pipeline
pts_scaler = pts_pipe.named_steps["scaler"]
pts_reg = pts_pipe.named_steps["regressor"]
pts_features = list(PLAYER_FEATURE_CONTRACT) + ["expected_minutes"]
print("\n=== POINTS MODEL COEFFICIENTS ===")
pts_coefs = pd.DataFrame({
    "feature": pts_features,
    "mean": pts_scaler.mean_,
    "scale": pts_scaler.scale_,
    "coef": pts_reg.coef_
})
print(pts_coefs.to_string())
print(f"\nIntercept: {pts_reg.intercept_}")
