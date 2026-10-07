import pandas as pd
import random

# 1. Create the Gym Equipment Catalog
# 'swap_id' is crucial for your novelty—it tells the algorithm what to suggest if a machine is full.
equipment_data = [
    {"machine_id": "BP_01", "name": "Barbell Bench Press", "category": "Chest", "swap_id": "DB_01"},
    {"machine_id": "DB_01", "name": "Dumbbell Bench", "category": "Chest", "swap_id": "BP_01"},
    {"machine_id": "SQ_01", "name": "Squat Rack 1", "category": "Legs", "swap_id": "LP_01"},
    {"machine_id": "LP_01", "name": "Leg Press", "category": "Legs", "swap_id": "SQ_01"},
    {"machine_id": "CB_01", "name": "Cable Crossover", "category": "Full Body", "swap_id": "None"},
    {"machine_id": "PD_01", "name": "Lat Pulldown", "category": "Back", "swap_id": "CB_01"}
]
df_equip = pd.DataFrame(equipment_data)
df_equip.to_csv("gym_equipment.csv", index=False)

# 2. Create the User Profile Data
goals = ["Hypertrophy", "Strength", "Weight Loss"]
time_windows = [30, 45, 60, 90]
target_muscles = ["Chest", "Legs", "Back", "Full Body"]

users = []
for i in range(1, 51): # Generate 50 synthetic users
    users.append({
        "user_id": f"U_{i:03d}",
        "goal": random.choice(goals),
        "available_mins": random.choice(time_windows),
        "target_muscle": random.choice(target_muscles)
    })
    
df_users = pd.DataFrame(users)
df_users.to_csv("user_profiles.csv", index=False)

print("Step 1 Complete: Created gym_equipment.csv and user_profiles.csv")
