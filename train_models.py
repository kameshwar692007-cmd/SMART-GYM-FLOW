from ml_utility_engine import GymUtilityMLForecaster, CrossElasticitySpilloverModel, calculate_fatigue_penalty

def main():
    print("--- 1. Training Multi-Output Random Forest Utility Model ---")
    forecaster = GymUtilityMLForecaster(model_dir=".")
    metrics = forecaster.train_and_save()
    print(f"Training Complete! R^2 Accuracy Score: {metrics['r2_score']} across {metrics['samples_trained']} synthetic operational sessions.")

    print("\n--- 2. Testing Cross-Elasticity Spillover Analysis (Novelty Test) ---")
    cesm = CrossElasticitySpilloverModel()
    
    # Simulate a high-demand chest day (e.g. 25 members training Chest)
    equipment_counts = {
        "bench_press": 2,          # Undersupplied (Trigger bottleneck)
        "dumbbell_bench": 4,       # Absorbs spillover
        "chest_press_machine": 2,  # Absorbs secondary spillover
        "squat_rack": 3,
        "leg_press": 2
    }
    demographic_demand = {
        "Chest": 25,  # High demand
        "Legs": 10
    }
    category_map = {
        "bench_press": "Chest",
        "dumbbell_bench": "Chest",
        "chest_press_machine": "Chest",
        "squat_rack": "Legs",
        "leg_press": "Legs"
    }

    spillover_results = cesm.analyze_spillover(equipment_counts, demographic_demand, category_map)
    
    print("\nRoot Cause Bottlenecks Detected:")
    for b in spillover_results["root_cause_trigger_bottlenecks"]:
        print(f"  [TRIGGER] {b['equipment']} | Overflow Severity: {b['overflow_severity']} | Spillover Caused: {b['spillover_caused']} users displaced")

    print("\nEquipment Breakdown (Intrinsic vs Phantom Spillover):")
    for eq in spillover_results["equipment_breakdown"]:
        print(f"  * {eq['equipment_type']} (qty={eq['quantity']}): Intrinsic={eq['intrinsic_demand']} | Phantom Spillover={eq['phantom_spillover_demand']} | Phantom Share={eq['phantom_load_share_pct']}%")

    print("\n--- 3. Testing Biomechanical Fatigue Penalty ---")
    safe_routine = ["bench_press", "squat_rack", "lat_pulldown"]
    dangerous_fatigue_routine = ["squat_rack", "hack_squat", "leg_press"]
    print(f"Safe Balanced Routine Fatigue Penalty: {calculate_fatigue_penalty(safe_routine)}")
    print(f"Severe Pre-exhaustion Fatigue Penalty: {calculate_fatigue_penalty(dangerous_fatigue_routine)}")

    print("\n--- 4. Testing What-If Counterfactual Rebalancer ---")
    current_fleet = {"bench_press": 2, "dumbbell_bench": 4, "squat_rack": 3, "hack_squat": 2}
    # Manager tests adding 1 bench press and removing 1 hack squat
    proposed_mod = {"bench_press": 3, "hack_squat": 1}
    whatif_res = forecaster.counterfactual_what_if(current_fleet, proposed_mod, crowd_size=30)
    print(f"Current Avg Queue Risk: {whatif_res['current_avg_queue_risk']} -> Projected: {whatif_res['projected_avg_queue_risk']}")
    print(f"Bottleneck Relief: {whatif_res['bottleneck_relief_pct']}% | ROI Assessment: {whatif_res['capital_efficiency_gain']}")

if __name__ == "__main__":
    main()
