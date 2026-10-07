import pandas as pd

# Load the equipment catalog
df_equip = pd.read_csv("gym_equipment.csv")

# 1. Simulate the Real-Time Gym State
# True = Machine is OCCUPIED. False = Machine is FREE.
# Let's pretend the gym is crowded right now.
current_gym_state = {
    "BP_01": True,  # Barbell Bench is OCCUPIED
    "DB_01": False, # Dumbbell Bench is FREE
    "SQ_01": True,  # Squat Rack is OCCUPIED
    "LP_01": True,  # Leg Press is ALSO OCCUPIED
    "CB_01": False, # Cable Crossover is FREE
    "PD_01": False  # Lat Pulldown is FREE
}

# 2. A mock prescription from Step 2
# This user wants to do Bench Press, Squats, and Cables.
prescribed_machines = ["BP_01", "SQ_01", "CB_01"]

def optimize_route(prescribed, gym_state, df_equip):
    print("--- Starting Smart Gym Routing Engine ---\n")
    final_schedule = []
    wait_queue = []

    for machine in prescribed:
        # 3. Check if the primary machine is free
        if not gym_state.get(machine, True): 
            print(f"[AVAILABLE] Routing directly to: {machine}")
            final_schedule.append(machine)
        else:
            print(f"[OCCUPIED] {machine} is full. Searching for alternatives...")
            
            # Fetch the alternative machine (swap_id) from the catalog
            swap_id = df_equip.loc[df_equip['machine_id'] == machine, 'swap_id'].values[0]
            
            # 4. Swap Logic: If the alternative exists and is free, swap it!
            if swap_id != "None" and not gym_state.get(swap_id, True):
                print(f"  -> [SWAP SUCCESS] Alternative found! Rerouting to: {swap_id}")
                final_schedule.append(swap_id)
            else:
                # 5. Reorder Logic: If alternative is also full, move it to the end.
                print(f"  -> [NO ALTERNATIVES FREE] Adding {machine} to the wait queue.")
                wait_queue.append(machine)
    
    # Add the machines they have to wait for to the very end of their session
    if wait_queue:
        print("\n[REORDERING] Pushing busy machines to the end of the workout.")
        final_schedule.extend(wait_queue)
        
    return final_schedule

# Run the algorithm
optimized_workout = optimize_route(prescribed_machines, current_gym_state, df_equip)

print("\n--- Final Optimized Customer Schedule ---")
for step_num, machine in enumerate(optimized_workout, 1):
    print(f"Step {step_num}: Go to {machine}")
