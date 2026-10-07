from multi_user_scheduler import MultiUserGymScheduler, GymCatalog

def test_multi_user():
    catalog = GymCatalog("gym_catalogs.json")
    scheduler = MultiUserGymScheduler(catalog=catalog, num_slots=8)

    # 1. Test across 3 different gym types
    gym_ids = catalog.get_gym_ids()
    print(f"Loaded Gym Types: {gym_ids}")
    assert "commercial_gym" in gym_ids
    assert "hotel_gym" in gym_ids
    assert "powerlifting_box" in gym_ids

    # 2. Simulate Rush Hour with 12 concurrent users arriving at Commercial Gym
    # All wanting Chest or Legs to induce heavy machine contention!
    mock_users = [
        {"user_id": f"Member_{i:02d}", "target_muscle": "Chest" if i % 2 == 0 else "Legs", "available_mins": 45}
        for i in range(1, 13)
    ]

    sim_res = scheduler.batch_simulate("commercial_gym", mock_users)
    print("\n--- Commercial Gym 12-User Simulation Results ---")
    print(f"Gym: {sim_res['gym_name']}")
    print(f"Users routed: {sim_res['total_users_simulated']}")
    print(f"Equipment units: {sim_res['total_equipment_units']}")
    print(f"Utilization: {sim_res['overall_utilization_pct']}%")
    print(f"Collisions (Double-bookings): {sim_res['collision_count']}")

    assert sim_res['collision_count'] == 0, "No user should be double booked or assigned to occupied gear!"

    # 3. Test Hotel Gym with 4 users (low equipment scenario)
    hotel_users = [
        {"user_id": f"Guest_{i:02d}", "target_muscle": "Full Body", "available_mins": 30}
        for i in range(1, 5)
    ]
    hotel_res = scheduler.batch_simulate("hotel_gym", hotel_users)
    print("\n--- Hotel Gym 4-Guest Simulation Results ---")
    print(f"Gym: {hotel_res['gym_name']}")
    print(f"Collisions: {hotel_res['collision_count']}")
    assert hotel_res['collision_count'] == 0

    print("\nALL MULTI-USER SCHEDULER TESTS PASSED!")

if __name__ == "__main__":
    test_multi_user()
