"""
Smart Gym Member Onboarding & Progressive 1-Week+ Evolution Engine
- Freshers onboard with just: Goal (Bodybuilding, Weight Loss, Strength) & Time.
- The system automatically creates their smart 7-Day Plan.
- As members complete workouts, it auto-logs their history.
- After 1 Week, the AI intelligently evolves their workout and optimizes their gym schedule.
"""

from typing import Dict, List, Any, Optional

# Goal-based 7-Day Curriculum for Freshers
GOAL_PROTOCOLS = {
    "Bodybuilding (Muscle Gain)": [
        {"day": 1, "title": "Chest & Triceps (Push)", "muscle": "Chest", "focus": "Hypertrophy Volume"},
        {"day": 2, "title": "Back & Biceps (Pull)", "muscle": "Back", "focus": "Lats & Upper Back"},
        {"day": 3, "title": "Legs & Abs", "muscle": "Legs", "focus": "Quads & Hamstrings"},
        {"day": 4, "title": "Active Rest & Recovery", "muscle": "Rest", "focus": "Muscle Repair"},
        {"day": 5, "title": "Chest & Shoulders", "muscle": "Chest", "focus": "Upper Chest & Delts"},
        {"day": 6, "title": "Back & Legs Hybrid", "muscle": "Legs", "focus": "Lower Body & Posture"},
        {"day": 7, "title": "Full Rest Day", "muscle": "Rest", "focus": "CNS Reset"}
    ],
    "Weight Loss & Fat Burn": [
        {"day": 1, "title": "Full Body Circuit A", "muscle": "Full Body", "focus": "High Metabolic Calorie Burn"},
        {"day": 2, "title": "Legs & Core Burn", "muscle": "Legs", "focus": "Large Muscle Energy Expenditure"},
        {"day": 3, "title": "Upper Body & Cardio Tone", "muscle": "Back", "focus": "Lats & Heart Rate Elevation"},
        {"day": 4, "title": "Active Rest / Light Cardio", "muscle": "Rest", "focus": "Active Fat Oxidation"},
        {"day": 5, "title": "Full Body Circuit B", "muscle": "Chest", "focus": "Push Movements & Core"},
        {"day": 6, "title": "Lower Body & HIIT", "muscle": "Legs", "focus": "Leg Press & Calves"},
        {"day": 7, "title": "Rest Day", "muscle": "Rest", "focus": "Recovery"}
    ],
    "Strength & Power (Powerlifting)": [
        {"day": 1, "title": "Squat Foundation Day", "muscle": "Legs", "focus": "Olympic Squat Rack & Core"},
        {"day": 2, "title": "Bench Press Power Day", "muscle": "Chest", "focus": "Barbell Bench & Triceps"},
        {"day": 3, "title": "Rest & Mobility", "muscle": "Rest", "focus": "Joint Recovery"},
        {"day": 4, "title": "Posterior Chain & Row Day", "muscle": "Back", "focus": "Lat Pulldown & Rows"},
        {"day": 5, "title": "Secondary Squat & Leg Press", "muscle": "Legs", "focus": "Leg Press Volume"},
        {"day": 6, "title": "Incline Push & Cables", "muscle": "Chest", "focus": "Dumbbell Press & Accessories"},
        {"day": 7, "title": "Rest Day", "muscle": "Rest", "focus": "Full Recovery"}
    ]
}

# Initial realistic members with pre-populated multi-day progress
INITIAL_MEMBERS = [
    {
        "member_id": "M_01",
        "name": "Alex Miller",
        "goal": "Bodybuilding (Muscle Gain)",
        "experience": "Fresher (Week 1)",
        "preferred_time": "08:00 AM",
        "current_day_number": 3,  # Completed Day 1 (Chest), Day 2 (Back) -> Today is Day 3 (Legs)
        "completed_history": ["Chest & Triceps", "Back & Biceps"]
    },
    {
        "member_id": "M_02",
        "name": "Sarah Connor",
        "goal": "Strength & Power (Powerlifting)",
        "experience": "Active Member (Week 2+)",
        "preferred_time": "08:00 AM",
        "current_day_number": 8,  # Advanced to Week 2!
        "completed_history": [
            "Squat Day", "Bench Day", "Rest", "Posterior Chain", "Leg Press", "Incline Push", "Rest"
        ]
    },
    {
        "member_id": "M_03",
        "name": "David Kim",
        "goal": "Weight Loss & Fat Burn",
        "experience": "Fresher (Week 1)",
        "preferred_time": "08:15 AM",
        "current_day_number": 2,  # Completed Day 1 -> Today is Day 2 (Legs & Core Burn)
        "completed_history": ["Full Body Circuit A"]
    },
    {
        "member_id": "M_04",
        "name": "Elena Rostova",
        "goal": "Bodybuilding (Muscle Gain)",
        "experience": "Fresher (Week 1)",
        "preferred_time": "08:30 AM",
        "current_day_number": 1,  # Brand new fresher! Day 1 (Chest & Triceps)
        "completed_history": []
    },
    {
        "member_id": "M_05",
        "name": "Marcus Vance",
        "goal": "Strength & Power (Powerlifting)",
        "experience": "Fresher (Week 1)",
        "preferred_time": "08:00 AM",
        "current_day_number": 2,  # Day 2: Bench Press Power Day
        "completed_history": ["Squat Foundation Day"]
    }
]

# Master Equipment on the Gym Floor
GYM_FLOOR_EQUIPMENT = {
    "Barbell Bench Press": {"stations": ["Bench Press #1", "Bench Press #2"], "category": "Chest", "swap": "Incline Dumbbell Bench"},
    "Incline Dumbbell Bench": {"stations": ["Dumbbell Bench #1", "Dumbbell Bench #2", "Dumbbell Bench #3"], "category": "Chest", "swap": "Chest Press Machine"},
    "Chest Press Machine": {"stations": ["Chest Press Machine #1"], "category": "Chest", "swap": "Cable Crossover"},
    "Olympic Squat Rack": {"stations": ["Squat Rack #1", "Squat Rack #2"], "category": "Legs", "swap": "Leg Press"},
    "Leg Press Station": {"stations": ["Leg Press #1", "Leg Press #2"], "category": "Legs", "swap": "Hack Squat"},
    "Hack Squat": {"stations": ["Hack Squat #1"], "category": "Legs", "swap": "Leg Press"},
    "Lat Pulldown": {"stations": ["Lat Pulldown #1", "Lat Pulldown #2"], "category": "Back", "swap": "Seated Cable Row"},
    "Seated Cable Row": {"stations": ["Cable Row #1"], "category": "Back", "swap": "Lat Pulldown"},
    "Cable Crossover": {"stations": ["Cable Crossover #1", "Cable Crossover #2"], "category": "Chest", "swap": "Incline Dumbbell Bench"}
}


class SmartGymCoordinator:
    """Manages zero-manual-input onboarding, progressive week tracking, and floor timetable."""
    
    def __init__(self):
        self.members = list(INITIAL_MEMBERS)
        self.equipment = dict(GYM_FLOOR_EQUIPMENT)

    def register_fresher(self, name: str, goal: str, preferred_time: str) -> Dict[str, Any]:
        """Smart Onboarding: Registers a new fresher with just name, goal, and arrival time."""
        new_member = {
            "member_id": f"M_{len(self.members) + 1:02d}",
            "name": name,
            "goal": goal,
            "experience": "Fresher (Week 1)",
            "preferred_time": preferred_time,
            "current_day_number": 1,
            "completed_history": []
        }
        self.members.append(new_member)
        return new_member

    def get_today_routine_for_member(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart Progression Logic:
        Calculates today's exact workout automatically based on:
        - Their Goal
        - Whether they are in Week 1 (Days 1-7) or Week 2+ (Days 8+)
        """
        goal = member["goal"]
        protocol = GOAL_PROTOCOLS.get(goal, GOAL_PROTOCOLS["Bodybuilding (Muscle Gain)"])
        day_num = member["current_day_number"]

        # Week 1 vs Week 2+ progression
        week_num = ((day_num - 1) // 7) + 1
        day_of_week_idx = (day_num - 1) % 7
        routine_template = protocol[day_of_week_idx]

        is_week_2_plus = week_num >= 2

        # In Week 2+, AI adds progression notes (e.g. progressive overload, machine supersets)
        progression_status = (
            f"Week {week_num} - Day {day_of_week_idx + 1}"
            + (" (🔥 Progressive Overload Phase)" if is_week_2_plus else " (🌱 Foundational Form Phase)")
        )

        return {
            "week_number": week_num,
            "day_number": day_num,
            "day_of_week_idx": day_of_week_idx + 1,
            "title": routine_template["title"],
            "target_muscle": routine_template["muscle"],
            "focus": routine_template["focus"],
            "progression_status": progression_status,
            "is_rest_day": routine_template["muscle"] == "Rest",
            "is_advanced_week": is_week_2_plus
        }

    def complete_today_workout(self, member_name: str) -> Dict[str, Any]:
        """Simulates member finishing today's workout. Advances day count automatically."""
        for m in self.members:
            if m["name"].lower() == member_name.lower():
                today_info = self.get_today_routine_for_member(m)
                m["completed_history"].append(today_info["title"])
                m["current_day_number"] += 1
                if m["current_day_number"] > 7:
                    m["experience"] = "Active Member (Week 2+)"
                return m
        return None

    def build_daily_floor_schedule(self) -> Dict[str, Any]:
        """Coordinates all members arriving at clock times across the physical equipment floor."""
        time_slots = []
        for hour in range(6, 21):
            h_str = f"{hour:02d}"
            time_slots.append(f"{h_str}:00")
            time_slots.append(f"{h_str}:15")
            time_slots.append(f"{h_str}:30")
            time_slots.append(f"{h_str}:45")

        all_stations = []
        for eq_name, data in self.equipment.items():
            for stn in data["stations"]:
                all_stations.append((stn, eq_name, data["category"], data["swap"]))

        station_grid = {stn[0]: {slot: None for slot in time_slots} for stn in all_stations}
        member_itineraries = []
        ai_solutions = []

        for m in self.members:
            routine = self.get_today_routine_for_member(m)
            if routine["is_rest_day"]:
                member_itineraries.append({
                    "name": m["name"],
                    "goal": m["goal"],
                    "status": routine["progression_status"],
                    "today_title": "Rest & Recovery Day",
                    "steps": []
                })
                continue

            arr_time = m["preferred_time"]
            parts = arr_time.split(" ")
            t_part = parts[0]
            if parts[1] == "PM" and not t_part.startswith("12"):
                h, mi = t_part.split(":")
                start_slot = f"{int(h)+12:02d}:{mi}"
            elif parts[1] == "AM" and t_part.startswith("12"):
                start_slot = f"00:{t_part.split(':')[1]}"
            else:
                start_slot = t_part

            target_muscle = routine["target_muscle"]
            candidate_equip = [
                (eq_name, data) for eq_name, data in self.equipment.items()
                if (target_muscle == "Full Body" or data["category"].lower() == target_muscle.lower())
            ]

            member_steps = []
            slot_idx = time_slots.index(start_slot) if start_slot in time_slots else 8

            for ex_idx, (eq_name, eq_data) in enumerate(candidate_equip[:3]):
                curr_slot = time_slots[slot_idx + ex_idx]
                assigned_station = None
                is_swap = False

                # 1. Look for free station
                for stn in eq_data["stations"]:
                    if station_grid[stn][curr_slot] is None:
                        assigned_station = stn
                        break

                # 2. If full, intelligently swap to prevent line
                if assigned_station is None:
                    swap_equip_name = eq_data["swap"]
                    if swap_equip_name in self.equipment:
                        for stn in self.equipment[swap_equip_name]["stations"]:
                            if station_grid[stn][curr_slot] is None:
                                assigned_station = stn
                                is_swap = True
                                ai_solutions.append({
                                    "time": curr_slot,
                                    "member": m["name"],
                                    "original": eq_name,
                                    "assigned": stn,
                                    "reason": f"Both {eq_name} units busy at {curr_slot}. Rerouted {m['name']} to {stn} so zero waiting occurred."
                                })
                                break

                if assigned_station:
                    station_grid[assigned_station][curr_slot] = m["name"]
                    member_steps.append({
                        "step": ex_idx + 1,
                        "time_window": f"{curr_slot} - {time_slots[slot_idx + ex_idx + 1]}",
                        "station": assigned_station,
                        "muscle": target_muscle,
                        "is_swap": is_swap,
                        "instruction": "Walk right up (Reserved)" if not is_swap else f"Smart Alternative to skip line at {eq_name}"
                    })

            member_itineraries.append({
                "name": m["name"],
                "goal": m["goal"],
                "status": routine["progression_status"],
                "today_title": routine["title"],
                "arrival_time": m["preferred_time"],
                "steps": member_steps
            })

        return {
            "station_grid": station_grid,
            "member_itineraries": member_itineraries,
            "ai_solutions": ai_solutions
        }
