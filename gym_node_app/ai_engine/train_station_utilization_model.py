import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("[MODEL B] Training Machine-Level Spatial-Temporal Utilization Forecaster (U_k,t)...")

np.random.seed(42)

# Machine groups
MACHINE_GROUPS = [
    "Barbell_Bench_Press",
    "Olympic_Squat_Rack",
    "Cable_Crossover_Columns",
    "Incline_Dumbbell_Area",
    "Leg_Press_45Deg"
]

N_DAYS = 365
hours = list(range(6, 23)) # 06:00 to 22:00
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

records = []

for day_idx in range(N_DAYS):
    dow = day_idx % 7
    day_name = days[dow]
    is_weekend = 1 if dow in [5, 6] else 0

    for hr in hours:
        # Base hourly demand shape: Morning peak (7:30 - 9:00), Midday low, Evening peak (17:30 - 19:30)
        if 7 <= hr <= 9:
            base_load = 0.78 if not is_weekend else 0.40
        elif 11 <= hr <= 14:
            base_load = 0.38 if not is_weekend else 0.55
        elif 17 <= hr <= 20:
            base_load = 0.92 if not is_weekend else 0.48
        elif hr >= 21:
            base_load = 0.28
        else:
            base_load = 0.20

        # SPATIAL-TEMPORAL MACHINE SPECIALIZATION:
        # 1. Bench Press: Extreme surge on Monday ("International Chest Day") & Tuesday
        bench_bias = 1.35 if dow == 0 else (1.20 if dow == 1 else (0.80 if is_weekend else 0.95))
        u_bench = np.clip(base_load * bench_bias + np.random.normal(0, 0.04), 0.05, 0.98)

        # 2. Squat Rack: Peak on Wednesday (Leg Day) and Saturday
        squat_bias = 1.30 if dow == 2 else (1.15 if is_weekend else 0.90)
        u_squat = np.clip(base_load * squat_bias + np.random.normal(0, 0.04), 0.05, 0.98)

        # 3. Cable Columns: High consistent utility across all workout splits
        cable_bias = 1.10 if (17 <= hr <= 20) else 0.95
        u_cables = np.clip(base_load * cable_bias + np.random.normal(0, 0.03), 0.08, 0.96)

        # 4. Dumbbells: Universal usage across all days
        u_dumbbells = np.clip(base_load * 1.05 + np.random.normal(0, 0.03), 0.10, 0.97)

        # 5. Leg Press: High during leg days & as squat backup
        legpress_bias = 1.25 if dow in [2, 5] else 0.85
        u_legpress = np.clip(base_load * legpress_bias + np.random.normal(0, 0.04), 0.05, 0.95)

        records.append({
            'day_of_week': dow,
            'hour_24': hr,
            'is_weekend': is_weekend,
            'u_bench': u_bench,
            'u_squat': u_squat,
            'u_cables': u_cables,
            'u_dumbbells': u_dumbbells,
            'u_legpress': u_legpress
        })

df = pd.DataFrame(records)
X = df[['day_of_week', 'hour_24', 'is_weekend']]
y = df[['u_bench', 'u_squat', 'u_cables', 'u_dumbbells', 'u_legpress']]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
rf.fit(X_train, y_train)

pred = rf.predict(X_test)
r2_macro = r2_score(y_test, pred)
mae_macro = mean_absolute_error(y_test, pred)

# Compute WAPE: sum(|actual - pred|) / sum(actual)
wape = np.sum(np.abs(y_test.values - pred)) / np.sum(y_test.values)

print(f"[SUCCESS] Model B (Spatial-Temporal Machine Utilization) Macro R^2: {r2_macro:.4f}")
print(f"[SUCCESS] Model B WAPE: {wape * 100:.2f}% | MAE: {mae_macro:.3f} utilization index")

# Precompute spatial-temporal weekly matrix for instant microsecond serving
station_forecast_matrix = {}

for d_idx, day_name in enumerate(days):
    station_forecast_matrix[day_name] = {}
    is_w = 1 if d_idx in [5, 6] else 0
    for h in hours:
        period = "AM" if h < 12 else "PM"
        h12 = h if h <= 12 else h - 12
        if h12 == 0: h12 = 12
        time_slot = f"{h12:02d}:00 {period}"

        row_input = pd.DataFrame([[d_idx, h, is_w]], columns=['day_of_week', 'hour_24', 'is_weekend'])
        preds = rf.predict(row_input)[0]

        station_forecast_matrix[day_name][time_slot] = {
            "Barbell_Bench_Press": round(float(preds[0]), 3),
            "Olympic_Squat_Rack": round(float(preds[1]), 3),
            "Cable_Crossover_Columns": round(float(preds[2]), 3),
            "Incline_Dumbbell_Area": round(float(preds[3]), 3),
            "Leg_Press_45Deg": round(float(preds[4]), 3)
        }

model_b_artifact = {
    "model_name": "MachineSpatialTemporalUtilForecaster_v2",
    "metrics": {
        "r2_score": round(float(r2_macro), 4),
        "wape_percent": round(float(wape * 100), 2),
        "mae_index": round(float(mae_macro), 3)
    },
    "machine_groups": MACHINE_GROUPS,
    "spatial_forecast_matrix": station_forecast_matrix
}

os.makedirs(os.path.dirname(__file__), exist_ok=True)
out_b = os.path.join(os.path.dirname(__file__), 'station_utilization_model.json')
with open(out_b, 'w', encoding='utf-8') as f:
    json.dump(model_b_artifact, f, indent=2)

print(f"Saved Model B parameters to {out_b}")
