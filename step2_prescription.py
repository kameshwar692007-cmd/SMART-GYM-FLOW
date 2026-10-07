import pandas as pd

# Load the data generated in Step 1
df_equip = pd.read_csv("gym_equipment.csv")
df_users = pd.read_csv("user_profiles.csv")

def prescribe_workout(user_id, df_users, df_equip):
    # 1. Fetch user profile
    user = df_users[df_users['user_id'] == user_id].iloc[0]
    target = user['target_muscle']
    time_limit = user['available_mins']
    
    print(f"--- Generating Plan for {user_id} ---")
    print(f"Goal: {user['goal']} | Target: {target} | Time: {time_limit} mins")
    
    # 2. Filter equipment based on target muscle
    if target == "Full Body":
        relevant_machines = df_equip
    else:
        relevant_machines = df_equip[df_equip['category'] == target]
        
    # 3. Calculate how many exercises fit in their time window
    num_exercises = max(1, time_limit // 15) 
    
    # 4. Select the machines for the prescription
    # If the gym doesn't have enough machines for that muscle, just give them what is available
    if len(relevant_machines) < num_exercises:
        prescribed = relevant_machines['machine_id'].tolist()
    else:
        prescribed = relevant_machines.sample(num_exercises)['machine_id'].tolist()
        
    prescription = {
        "user_id": user_id,
        "prescribed_machines": prescribed,
        "total_workout_time": len(prescribed) * 15
    }
    
    return prescription

# Let's test it on the very first user in your CSV
test_user_id = df_users.iloc[0]['user_id']
workout_plan = prescribe_workout(test_user_id, df_users, df_equip)

print("\nFinal Prescription Output:")
print(workout_plan)
