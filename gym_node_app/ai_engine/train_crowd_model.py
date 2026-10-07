import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.linear_model import Ridge
import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("[MODEL B] Training Gym Floor Crowdedness & Bottleneck Forecaster...")

np.random.seed(42)
N_DAYS = 365
RECORDS_PER_DAY = 17 # Operating hours: 6 AM to 10 PM (17 hours)
N_TOTAL = N_DAYS * RECORDS_PER_DAY

hours = []
day_of_weeks = []
is_weekends = []
is_semesters = []
crowd_counts = []

for day in range(N_DAYS):
    dow = day % 7 # 0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat, 6: Sun
    is_weekend = 1 if dow in [5, 6] else 0
    is_sem = 1 if (day % 120 < 90) else 0 # Semester vs break

    for hr in range(6, 23): # 6:00 to 22:00
        # Historical crowd patterns from Campus Gym dataset:
        # Peak 1: Morning Rush (07:30 - 09:30)
        # Low: Midday lull (11:00 - 15:00)
        # Peak 2: Evening Major Rush (17:00 - 20:30)
        if 7 <= hr <= 9:
            base_occupancy = 45 if not is_weekend else 20
        elif 11 <= hr <= 14:
            base_occupancy = 25 if not is_weekend else 35
        elif 17 <= hr <= 20:
            base_occupancy = 68 if not is_weekend else 30
        elif hr >= 21:
            base_occupancy = 18
        else:
            base_occupancy = 12

        # Monday & Tuesday have highest gym traffic
        dow_factor = 1.2 if dow == 0 else (1.15 if dow == 1 else (0.75 if is_weekend else 1.0))
        noise = np.random.normal(0, 5)

        count = int(np.clip(base_occupancy * dow_factor * (1.1 if is_sem else 0.85) + noise, 3, 95))
        
        hours.append(hr)
        day_of_weeks.append(dow)
        is_weekends.append(is_weekend)
        is_semesters.append(is_sem)
        crowd_counts.append(count)

df_crowd = pd.DataFrame({
    'hour': hours,
    'day_of_week': day_of_weeks,
    'is_weekend': is_weekends,
    'is_semester': is_semesters,
    'crowd_count': crowd_counts
})

X = df_crowd[['hour', 'day_of_week', 'is_weekend', 'is_semester']]
y = df_crowd['crowd_count']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
rf.fit(X_train, y_train)

pred = rf.predict(X_test)
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)

print(f"[SUCCESS] Gym Crowdedness Forecaster R^2: {r2:.4f} (MAE: {mae:.2f} people)")

# Precompute hourly profile per day-of-week for instant client lookup
hourly_profiles = {}
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

for d_idx, day_name in enumerate(days):
    hourly_profiles[day_name] = {}
    is_w = 1 if d_idx in [5, 6] else 0
    for h in range(6, 23):
        # Format time label
        period = "AM" if h < 12 else "PM"
        h12 = h if h <= 12 else h - 12
        if h12 == 0: h12 = 12
        time_label = f"{h12:02d}:00 {period}"

        sample = pd.DataFrame([[h, d_idx, is_w, 1]], columns=['hour', 'day_of_week', 'is_weekend', 'is_semester'])
        pred_val = int(round(float(rf.predict(sample)[0])))
        
        # Determine bottleneck risk and status
        if pred_val >= 55:
            status = "Bottleneck Alert (High Rush)"
            level = "high"
            color = "#ef4444"
        elif pred_val >= 35:
            status = "Moderate Traffic"
            level = "moderate"
            color = "#f59e0b"
        else:
            status = "Low Traffic (Ideal Flow)"
            level = "low"
            color = "#10b981"

        hourly_profiles[day_name][time_label] = {
            "hour_24": h,
            "predicted_crowd": pred_val,
            "capacity_percent": int(round((pred_val / 80.0) * 100)),
            "status": status,
            "level": level,
            "color": color
        }

model_b_artifact = {
    "model_name": "GymCrowdForecaster_v1",
    "metrics": {
        "r2_score": round(float(r2), 4),
        "mae": round(float(mae), 2)
    },
    "hourly_profiles": hourly_profiles
}

with open(os.path.join(os.path.dirname(__file__), 'crowd_model.json'), 'w') as f:
    json.dump(model_b_artifact, f, indent=2)

print("💾 Model B saved successfully to ai_engine/crowd_model.json")
