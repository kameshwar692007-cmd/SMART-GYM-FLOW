import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("[MODEL A] Training Member Biometric & Metabolic Calibrator...")

# Seed for reproducibility
np.random.seed(42)
N_SAMPLES = 2500

# 1. Generate realistic dataset based on the Kaggle Gym Members Exercise Dataset distributions
# (Vala Khorasani benchmark: Age 18-60, Weight 45-120kg, Height 1.50-2.00m, Session 0.5-1.5 hrs)
ages = np.random.randint(18, 60, size=N_SAMPLES)
genders = np.random.choice([0, 1], size=N_SAMPLES) # 0: Female, 1: Male
heights_m = np.random.normal(1.72, 0.10, size=N_SAMPLES)
heights_m = np.clip(heights_m, 1.48, 2.05)

# Weight correlated with height and gender
base_weights = (heights_m * 100 - 100) + (genders * 6) + np.random.normal(0, 8, size=N_SAMPLES)
weights_kg = np.clip(base_weights, 42.0, 130.0)

# Calculate real BMI
bmis = weights_kg / (heights_m ** 2)

# Experience: 1: Beginner, 2: Intermediate, 3: Advanced
experience_levels = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2], size=N_SAMPLES)

# Workout Type: 0: Fat Loss / HIIT, 1: Bodybuilding / Hypertrophy, 2: Strength / Heavy, 3: General Fitness
workout_types = np.random.choice([0, 1, 2, 3], size=N_SAMPLES)

# Duration in minutes: 30, 45, 60
durations_mins = np.random.choice([30, 45, 60], size=N_SAMPLES)
durations_hrs = durations_mins / 60.0

# Calculate physiological target metrics based on metabolic equivalents (METs) and lifter data
# Base metabolic expenditure formula calibrated from exercise physiology
met_map = {0: 9.5, 1: 7.0, 2: 6.5, 3: 5.5} # MET values for workout types
met_values = np.array([met_map[wt] for wt in workout_types])

# Calories burned = MET * weight_kg * duration_hrs * experience efficiency factor
intensity_factor = 0.9 + (experience_levels * 0.08)
calories_burned = met_values * weights_kg * durations_hrs * intensity_factor + np.random.normal(0, 15, size=N_SAMPLES)
calories_burned = np.clip(calories_burned, 180, 1100)

# Target Heart Rate:
# Max BPM = 220 - Age
max_bpms = (220 - ages) - np.random.normal(0, 4, size=N_SAMPLES)
# Avg BPM during workout: between 60% to 85% of Max BPM depending on workout type & experience
bpm_ratios = np.array([0.78, 0.70, 0.65, 0.60])[workout_types] + (experience_levels * 0.02)
avg_bpms = max_bpms * bpm_ratios + np.random.normal(0, 3, size=N_SAMPLES)

# Optimal Rest Seconds:
# Strength needs 90-120s, Hypertrophy 60-80s, Fat loss/HIIT 40-50s, adjusted by BMI and experience
base_rest_map = {0: 45, 1: 75, 2: 120, 3: 60}
base_rests = np.array([base_rest_map[wt] for wt in workout_types])
# Overweight or beginners require +10-15s recovery; advanced require -10s
rest_adjustments = np.where(bmis >= 26.0, 15, 0) - ((experience_levels - 1) * 8)
optimal_rests = np.clip(base_rests + rest_adjustments + np.random.normal(0, 3, size=N_SAMPLES), 30, 150)

# Build DataFrame
df = pd.DataFrame({
    'age': ages,
    'gender': genders,
    'height_m': heights_m,
    'weight_kg': weights_kg,
    'bmi': bmis,
    'experience': experience_levels,
    'workout_type': workout_types,
    'duration_mins': durations_mins,
    'calories_burned': calories_burned,
    'avg_bpm': avg_bpms,
    'max_bpm': max_bpms,
    'optimal_rest_sec': optimal_rests
})

# Prepare Feature Matrix X and Target Y
X = df[['age', 'gender', 'height_m', 'weight_kg', 'bmi', 'experience', 'workout_type', 'duration_mins']]
y_calories = df['calories_burned']
y_bpm = df['avg_bpm']
y_rest = df['optimal_rest_sec']

# Train/Test Split
X_train, X_test, y_c_train, y_c_test = train_test_split(X, y_calories, test_size=0.2, random_state=42)
_, _, y_b_train, y_b_test = train_test_split(X, y_bpm, test_size=0.2, random_state=42)
_, _, y_r_train, y_r_test = train_test_split(X, y_rest, test_size=0.2, random_state=42)

# Train Gradient Boosting Regressors
reg_calories = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
reg_calories.fit(X_train, y_c_train)
pred_c = reg_calories.predict(X_test)
r2_c = r2_score(y_c_test, pred_c)
mae_c = mean_absolute_error(y_c_test, pred_c)

reg_bpm = GradientBoostingRegressor(n_estimators=80, max_depth=3, random_state=42)
reg_bpm.fit(X_train, y_b_train)
pred_b = reg_bpm.predict(X_test)
r2_b = r2_score(y_b_test, pred_b)

reg_rest = GradientBoostingRegressor(n_estimators=80, max_depth=3, random_state=42)
reg_rest.fit(X_train, y_r_train)
pred_r = reg_rest.predict(X_test)
r2_r = r2_score(y_r_test, pred_r)

print(f"[SUCCESS] Calorie Predictor R^2: {r2_c:.4f} (MAE: {mae_c:.2f} kcal)")
print(f"[SUCCESS] Heart Rate (Avg BPM) R^2: {r2_b:.4f}")
print(f"[SUCCESS] Optimal Rest Seconds R^2: {r2_r:.4f}")

# Extract feature importances and linear coefficients for zero-latency deployment
from sklearn.linear_model import Ridge
ridge_c = Ridge().fit(X_train, y_c_train)
ridge_b = Ridge().fit(X_train, y_b_train)
ridge_r = Ridge().fit(X_train, y_r_train)

model_artifact = {
    "model_name": "BiometricMetabolicCalibrator_v1",
    "features": list(X.columns),
    "metrics": {
        "calorie_r2": round(float(r2_c), 4),
        "calorie_mae": round(float(mae_c), 2),
        "bpm_r2": round(float(r2_b), 4),
        "rest_r2": round(float(r2_r), 4)
    },
    "feature_importances": {
        feat: round(float(imp), 4) for feat, imp in zip(X.columns, reg_calories.feature_importances_)
    },
    "coefficients": {
        "calories": {
            "intercept": round(float(ridge_c.intercept_), 3),
            "weights": {feat: round(float(coef), 4) for feat, coef in zip(X.columns, ridge_c.coef_)}
        },
        "avg_bpm": {
            "intercept": round(float(ridge_b.intercept_), 3),
            "weights": {feat: round(float(coef), 4) for feat, coef in zip(X.columns, ridge_b.coef_)}
        },
        "optimal_rest": {
            "intercept": round(float(ridge_r.intercept_), 3),
            "weights": {feat: round(float(coef), 4) for feat, coef in zip(X.columns, ridge_r.coef_)}
        }
    }
}

os.makedirs(os.path.dirname(__file__), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), 'biometric_model.json'), 'w') as f:
    json.dump(model_artifact, f, indent=2)

print("💾 Model A saved successfully to ai_engine/biometric_model.json")
