"""
Smart Gym Core Engine
- Gym Owner Configuration: Equipment Fleet & Operating Hours
- Member Biometric Assessment: Height, Weight, BMI, Goal, Experience
- Personalized Workout Prescriptions: Sets, Reps, Rest Intervals
- Novel Interleaved 'Working-In' Multi-User Set Sharing
"""

import json
from typing import Dict, List, Any, Optional, Tuple


def calculate_bmi(height_cm: float, weight_kg: float) -> Tuple[float, str, str]:
    """Calculates BMI and returns (BMI, category, color)."""
    if height_cm <= 0:
        return 0.0, "Unknown", "#94a3b8"
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = "Underweight (Focus on Lean Caloric Surplus & Strength)"
        color = "#38bdf8"
    elif 18.5 <= bmi <= 24.9:
        category = "Normal / Healthy Weight (Ideal for Muscle Hypertrophy)"
        color = "#10b981"
    elif 25.0 <= bmi <= 29.9:
        category = "Overweight (Focus on High-Turnover Circuit & Fat Loss)"
        color = "#f59e0b"
    else:
        category = "Obese Range (Focus on Joint-Safe Cardio & Conditioning)"
        color = "#ef4444"
        
    return bmi, category, color


# Default Gym Floor Equipment Catalog
DEFAULT_EQUIPMENT = [
    {
        "equipment_id": "EQ_01",
        "name": "Barbell Bench Press",
        "category": "Chest",
        "quantity": 2,
        "stations": ["Bench Press #1", "Bench Press #2"],
        "swap_alternative": "Incline Dumbbell Bench",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_02",
        "name": "Incline Dumbbell Bench",
        "category": "Chest",
        "quantity": 3,
        "stations": ["Dumbbell Bench #1", "Dumbbell Bench #2", "Dumbbell Bench #3"],
        "swap_alternative": "Seated Chest Press Machine",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_03",
        "name": "Seated Chest Press Machine",
        "category": "Chest",
        "quantity": 1,
        "stations": ["Chest Press Machine #1"],
        "swap_alternative": "Cable Crossover Station",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_04",
        "name": "Olympic Squat Rack",
        "category": "Legs",
        "quantity": 2,
        "stations": ["Squat Rack #1", "Squat Rack #2"],
        "swap_alternative": "45-Degree Leg Press",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_05",
        "name": "45-Degree Leg Press",
        "category": "Legs",
        "quantity": 2,
        "stations": ["Leg Press #1", "Leg Press #2"],
        "swap_alternative": "Plate-Loaded Hack Squat",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_06",
        "name": "Plate-Loaded Hack Squat",
        "category": "Legs",
        "quantity": 1,
        "stations": ["Hack Squat #1"],
        "swap_alternative": "45-Degree Leg Press",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_07",
        "name": "Lat Pulldown Machine",
        "category": "Back",
        "quantity": 2,
        "stations": ["Lat Pulldown #1", "Lat Pulldown #2"],
        "swap_alternative": "Seated Cable Row Station",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_08",
        "name": "Seated Cable Row Station",
        "category": "Back",
        "quantity": 1,
        "stations": ["Cable Row #1"],
        "swap_alternative": "Lat Pulldown Machine",
        "status": "Active"
    },
    {
        "equipment_id": "EQ_09",
        "name": "Cable Crossover Station",
        "category": "Full Body",
        "quantity": 2,
        "stations": ["Cable Crossover #1", "Cable Crossover #2"],
        "swap_alternative": "Incline Dumbbell Bench",
        "status": "Active"
    }
]

# Initial Gym Members with Real Biometrics & Assessment
INITIAL_MEMBERS = [
    {
        "member_id": "MEM_01",
        "name": "Alex Miller",
        "gender": "Male",
        "age": 24,
        "height_cm": 178,
        "weight_kg": 74.5,
        "goal": "Bodybuilding (Muscle Mass)",
        "experience": "Intermediate",
        "today_arrival_time": "08:00 AM",
        "duration_mins": 45,
        "focus_muscle": "Chest",
        "completed_sessions": 12
    },
    {
        "member_id": "MEM_02",
        "name": "Marcus Vance",
        "gender": "Male",
        "age": 27,
        "height_cm": 182,
        "weight_kg": 88.0,
        "goal": "Strength & Power (Powerlifting)",
        "experience": "Advanced",
        "today_arrival_time": "08:00 AM",
        "duration_mins": 45,
        "focus_muscle": "Chest",
        "completed_sessions": 24
    },
    {
        "member_id": "MEM_03",
        "name": "Sarah Connor",
        "gender": "Female",
        "age": 29,
        "height_cm": 168,
        "weight_kg": 62.0,
        "goal": "Fat Loss & Lean Definition",
        "experience": "Beginner (Fresher)",
        "today_arrival_time": "08:00 AM",
        "duration_mins": 45,
        "focus_muscle": "Legs",
        "completed_sessions": 3
    },
    {
        "member_id": "MEM_04",
        "name": "Elena Rostova",
        "gender": "Female",
        "age": 23,
        "height_cm": 165,
        "weight_kg": 55.0,
        "goal": "General Fitness & Toning",
        "experience": "Beginner (Fresher)",
        "today_arrival_time": "08:15 AM",
        "duration_mins": 45,
        "focus_muscle": "Legs",
        "completed_sessions": 2
    },
    {
        "member_id": "MEM_05",
        "name": "David Kim",
        "gender": "Male",
        "age": 31,
        "height_cm": 172,
        "weight_kg": 81.0,
        "goal": "Fat Loss & Lean Definition",
        "experience": "Intermediate",
        "today_arrival_time": "06:00 PM",
        "duration_mins": 45,
        "focus_muscle": "Back",
        "completed_sessions": 9
    }
]


class SmartGymSystem:
    """Complete backend for Gym Owner settings, Member biometrics, and Set-Sharing logic."""

    def __init__(self):
        # Gym Owner Configuration
        self.gym_name = "Iron Peak Fitness Club"
        self.open_time = "06:00 AM"
        self.close_time = "10:00 PM"
        self.equipment_fleet = list(DEFAULT_EQUIPMENT)
        self.members = list(INITIAL_MEMBERS)

    # -----------------------------------------------------------------------
    # Owner Management Methods
    # -----------------------------------------------------------------------
    def add_equipment(self, name: str, category: str, quantity: int, swap_alt: str) -> Dict[str, Any]:
        new_id = f"EQ_{len(self.equipment_fleet) + 1:02d}"
        stations = [f"{name} #{i}" for i in range(1, quantity + 1)]
        entry = {
            "equipment_id": new_id,
            "name": name,
            "category": category,
            "quantity": quantity,
            "stations": stations,
            "swap_alternative": swap_alt,
            "status": "Active"
        }
        self.equipment_fleet.append(entry)
        return entry

    def update_gym_schedule(self, open_time: str, close_time: str):
        self.open_time = open_time
        self.close_time = close_time

    # -----------------------------------------------------------------------
    # Member Biometrics & Prescription Engine
    # -----------------------------------------------------------------------
    def register_or_update_member(
        self,
        name: str,
        gender: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        goal: str,
        experience: str,
        arrival_time: str,
        duration_mins: int = 45,
        focus_muscle: str = "Chest"
    ) -> Dict[str, Any]:
        """Calculates BMI and registers or updates a member."""
        bmi, category, color = calculate_bmi(height_cm, weight_kg)
        
        for m in self.members:
            if m["name"].lower() == name.lower():
                m.update({
                    "gender": gender,
                    "age": age,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "goal": goal,
                    "experience": experience,
                    "today_arrival_time": arrival_time,
                    "duration_mins": duration_mins,
                    "focus_muscle": focus_muscle,
                    "bmi": bmi,
                    "bmi_category": category
                })
                return m

        new_member = {
            "member_id": f"MEM_{len(self.members) + 1:02d}",
            "name": name,
            "gender": gender,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "goal": goal,
            "experience": experience,
            "today_arrival_time": arrival_time,
            "duration_mins": duration_mins,
            "focus_muscle": focus_muscle,
            "bmi": bmi,
            "bmi_category": category,
            "completed_sessions": 0
        }
        self.members.append(new_member)
        return new_member

    def generate_reps_and_sets(self, member: Dict[str, Any], exercise_name: str) -> Dict[str, Any]:
        """
        Prescribes tailored sets, reps, and rest periods based on:
        - Goal (Bodybuilding, Fat Loss, Strength, Tone)
        - BMI & Fitness Level
        """
        goal = member["goal"]
        exp = member["experience"]
        bmi = member.get("bmi", 22.0)

        if "Bodybuilding" in goal:
            sets = 4 if exp == "Advanced" else 3
            reps = "8 - 12 Reps"
            rest_sec = 75
            guidance = "Moderate to Heavy weight. Control the lowering (eccentric) phase for 3 seconds."
        elif "Strength" in goal:
            sets = 5 if exp == "Advanced" else 4
            reps = "3 - 5 Heavy Reps"
            rest_sec = 120
            guidance = "Heavy progressive load. Focus on explosive concentric power and clean lockout."
        elif "Fat Loss" in goal:
            sets = 3
            reps = "12 - 15 Reps"
            rest_sec = 45
            guidance = "Continuous tempo with minimal rest to sustain elevated heart rate and metabolic burn."
        else: # General Fitness / Toning
            sets = 3
            reps = "10 - 12 Reps"
            rest_sec = 60
            guidance = "Smooth, continuous motion focusing on mind-muscle connection and full range of motion."

        # Extra safety recommendation if BMI is high (joint protection)
        if bmi >= 30.0:
            guidance += " (Note: Maintain strict knee & lower back alignment to preserve joint safety)."

        return {
            "sets": sets,
            "reps": reps,
            "rest_seconds": rest_sec,
            "coach_notes": guidance
        }

    # -----------------------------------------------------------------------
    # Multi-User Floor Scheduler with Interleaved "Working-In"
    # -----------------------------------------------------------------------
    def build_smart_floor_schedule(self) -> Dict[str, Any]:
        """
        Builds the global schedule across all stations and arrival times.
        CORE NOVELTY: If 2 members need the same station in the same time window,
        the system schedules them to 'Work In' together (alternating sets during rest)!
        """
        time_slots = [
            "06:00 AM", "06:15 AM", "06:30 AM", "06:45 AM",
            "07:00 AM", "07:15 AM", "07:30 AM", "07:45 AM",
            "08:00 AM", "08:15 AM", "08:30 AM", "08:45 AM",
            "09:00 AM", "09:15 AM", "09:30 AM", "09:45 AM",
            "05:00 PM", "05:15 PM", "05:30 PM", "05:45 PM",
            "06:00 PM", "06:15 PM", "06:30 PM", "06:45 PM",
            "07:00 PM", "07:15 PM", "07:30 PM", "07:45 PM"
        ]

        # Station map: { station_name: { time_slot: List[member_name] } }
        # Supports up to 2 concurrent lifters per station via "Working-In"
        all_stations = []
        for eq in self.equipment_fleet:
            if eq["status"] == "Active":
                for stn in eq["stations"]:
                    all_stations.append((stn, eq["name"], eq["category"], eq["swap_alternative"]))

        station_grid = {stn[0]: {slot: [] for slot in time_slots} for stn in all_stations}
        member_workout_plans = {}
        working_in_pairings = []

        # Sort members by arrival time
        for member in self.members:
            arr_time = member.get("today_arrival_time", "08:00 AM")
            target_muscle = member.get("focus_muscle", "Chest")

            # Filter relevant equipment for this muscle
            relevant_equip = [
                eq for eq in self.equipment_fleet 
                if eq["status"] == "Active" and (target_muscle == "Full Body" or eq["category"].lower() == target_muscle.lower())
            ]

            member_steps = []
            slot_idx = time_slots.index(arr_time) if arr_time in time_slots else 8

            # Prescribe 3 exercises for the 45-min workout
            for ex_idx, eq in enumerate(relevant_equip[:3]):
                curr_slot = time_slots[slot_idx + ex_idx]
                assigned_station = None
                is_working_in = False
                partner_name = None

                # 1. First priority: Find a completely empty station
                for stn in eq["stations"]:
                    if len(station_grid[stn][curr_slot]) == 0:
                        assigned_station = stn
                        break

                # 2. Second priority: If all stations have 1 person, activate NOVEL 'Working In' (Rest-Set Sharing)
                if assigned_station is None:
                    for stn in eq["stations"]:
                        if len(station_grid[stn][curr_slot]) == 1:
                            assigned_station = stn
                            is_working_in = True
                            partner_name = station_grid[stn][curr_slot][0]
                            working_in_pairings.append({
                                "time": curr_slot,
                                "station": stn,
                                "lifter_1": partner_name,
                                "lifter_2": member["name"],
                                "reason": f"Both need {eq['name']} at {curr_slot}. Alternating sets during rest intervals (Zero wait time!)."
                            })
                            break

                # 3. Third priority: If already 2 people working in, route to swap alternative
                if assigned_station is None:
                    alt_name = eq["swap_alternative"]
                    alt_eq = next((e for e in self.equipment_fleet if e["name"] == alt_name and e["status"] == "Active"), None)
                    if alt_eq:
                        for stn in alt_eq["stations"]:
                            if len(station_grid[stn][curr_slot]) < 2:
                                assigned_station = stn
                                if len(station_grid[stn][curr_slot]) == 1:
                                    is_working_in = True
                                    partner_name = station_grid[stn][curr_slot][0]
                                break

                # Book the station
                if assigned_station:
                    station_grid[assigned_station][curr_slot].append(member["name"])
                    reps_sets_info = self.generate_reps_and_sets(member, eq["name"])
                    
                    member_steps.append({
                        "step_num": ex_idx + 1,
                        "time_window": f"{curr_slot} - {time_slots[min(len(time_slots)-1, slot_idx + ex_idx + 1)]}",
                        "equipment_name": eq["name"],
                        "station": assigned_station,
                        "sets": reps_sets_info["sets"],
                        "reps": reps_sets_info["reps"],
                        "rest_seconds": reps_sets_info["rest_seconds"],
                        "coach_notes": reps_sets_info["coach_notes"],
                        "is_working_in": is_working_in,
                        "partner_name": partner_name
                    })

            member_workout_plans[member["name"]] = {
                "member_name": member["name"],
                "goal": member["goal"],
                "arrival_time": arr_time,
                "focus_muscle": target_muscle,
                "steps": member_steps
            }

        return {
            "time_slots": time_slots,
            "station_grid": station_grid,
            "member_workout_plans": member_workout_plans,
            "working_in_pairings": working_in_pairings
        }
