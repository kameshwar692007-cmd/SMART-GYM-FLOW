import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("[MODEL A] Training Station Dwell-Time Regressor (t_dwell)...")

# Reproducibility
np.random.seed(42)
N_SAMPLES = 3000

# 1. Feature Generation based on real gym biomechanics & sensor tracking data
# Equipment categories:
# 0: Plate-Loaded Barbell (Olympic Bench, Squat Rack - requires plate loading/unloading, collar clamping)
# 1: Plate-Loaded Machine (Leg Press, Hack Squat - pin & plate loading)
# 2: Selectorized Pin Machine (Lat Pulldown, Chest Press - fast pin selection)
# 3: Cable Column Station (Cable Crossover - height & attachment adjustment)
# 4: Free-Weight Dumbbells (Benches, Dumbbell arena - rack re-racking)
equip_categories = np.random.choice([0, 1, 2, 3, 4], size=N_SAMPLES, p=[0.25, 0.20, 0.20, 0.20, 0.15])

# Muscle Groups: 0: Chest, 1: Legs, 2: Back, 3: Full Body
muscle_groups = np.random.choice([0, 1, 2, 3], size=N_SAMPLES)

# Set Volume: 3, 4, or 5 sets
set_volumes = np.random.choice([3, 4, 5], size=N_SAMPLES, p=[0.6, 0.3, 0.1])

# Rep Range Type:
# 0: Heavy Compound / Strength (3-5 reps, higher rest)
# 1: Hypertrophy (8-12 reps, moderate rest)
# 2: Endurance / High Turnover (12-15 reps, minimal rest)
rep_range_types = np.random.choice([0, 1, 2], size=N_SAMPLES, p=[0.3, 0.5, 0.2])

# Lifter Experience Level: 1: Novice, 2: Intermediate, 3: Advanced
experience_levels = np.random.choice([1, 2, 3], size=N_SAMPLES, p=[0.35, 0.45, 0.20])

# Sharing Mode on station: 1: Solo (C=1), 2: 2-Way Interleaved (C=2), 3: 3-Way Cyclic (C=3)
sharing_modes = np.random.choice([1, 2, 3], size=N_SAMPLES, p=[0.45, 0.35, 0.20])

# 2. Physics & Biomechanical Dwell Formulation (Ground Truth Generation):
# Base setup time (minutes) per equipment type
setup_times = np.array([3.5, 2.5, 1.2, 1.8, 1.5])[equip_categories]
# Novices take longer to adjust pins/weights; advanced lifters are faster
setup_adjustments = np.where(experience_levels == 1, 1.0, np.where(experience_levels == 3, -0.6, 0.0))

# Active time per set (minutes): ~40-50 seconds = 0.75 mins
active_time_per_set = np.where(rep_range_types == 0, 0.6, np.where(rep_range_types == 1, 0.75, 0.9))

# Rest time per set (minutes) based on rep range
rest_time_per_set = np.where(rep_range_types == 0, 2.0, np.where(rep_range_types == 1, 1.25, 0.75))

# Dwell duration = Setup + Set_Volume * (Active_Time + Rest_Time)
# If 2-way or 3-way interleaved, the station stays occupied across the combined athlete sets
sharing_multiplier = np.where(sharing_modes == 1, 1.0, np.where(sharing_modes == 2, 1.45, 1.85))

noise = np.random.normal(0, 0.6, size=N_SAMPLES)

dwell_durations_mins = (setup_times + setup_adjustments + set_volumes * (active_time_per_set + rest_time_per_set)) * sharing_multiplier + noise
dwell_durations_mins = np.clip(dwell_durations_mins, 4.0, 32.0)

# Build DataFrame
df = pd.DataFrame({
    'equip_cat': equip_categories,
    'muscle_group': muscle_groups,
    'set_volume': set_volumes,
    'rep_range_type': rep_range_types,
    'experience': experience_levels,
    'sharing_mode': sharing_modes,
    'dwell_time_mins': dwell_durations_mins
})

X = df[['equip_cat', 'muscle_group', 'set_volume', 'rep_range_type', 'experience', 'sharing_mode']]
y = df['dwell_time_mins']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Gradient Boosting Regressor
reg = GradientBoostingRegressor(n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42)
reg.fit(X_train, y_train)

pred = reg.predict(X_test)
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
rmse = root_mean_squared_error(y_test, pred)

print(f"[SUCCESS] Model A (Station Dwell Time) R^2: {r2:.4f}")
print(f"[SUCCESS] Model A MAE: {mae:.2f} minutes | RMSE: {rmse:.2f} minutes")

# Fit Ridge for zero-latency parameter extraction
ridge = Ridge().fit(X_train, y_train)

model_artifact = {
    "model_name": "StationDwellRegressor_v2",
    "features": list(X.columns),
    "metrics": {
        "r2_score": round(float(r2), 4),
        "mae_minutes": round(float(mae), 3),
        "rmse_minutes": round(float(rmse), 3)
    },
    "feature_importances": {
        feat: round(float(imp), 4) for feat, imp in zip(X.columns, reg.feature_importances_)
    },
    "coefficients": {
        "intercept": round(float(ridge.intercept_), 3),
        "weights": {feat: round(float(coef), 4) for feat, coef in zip(X.columns, ridge.coef_)}
    }
}

os.makedirs(os.path.dirname(__file__), exist_ok=True)
output_path = os.path.join(os.path.dirname(__file__), 'dwell_model.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(model_artifact, f, indent=2)

print(f"Saved Model A parameters to {output_path}")
