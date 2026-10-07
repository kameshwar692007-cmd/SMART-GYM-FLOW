"""
Multi-User Gym Floor Scheduling Engine
Solves multi-gym adaptation and multi-user resource contention using
discrete-time slot reservation, load-balancing, swapping, and dynamic reordering.
"""

import json
import random
from typing import Dict, List, Optional, Any
from pathlib import Path


class GymCatalog:
    """Manages multi-gym equipment inventories and instance generation."""
    def __init__(self, config_path: str = "gym_catalogs.json"):
        self.config_path = Path(config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.gyms_data = json.load(f)

    def get_gym_ids(self) -> List[str]:
        return list(self.gyms_data.keys())

    def get_gym_info(self, gym_id: str) -> Dict[str, Any]:
        if gym_id not in self.gyms_data:
            raise ValueError(f"Unknown gym_id: {gym_id}")
        return self.gyms_data[gym_id]

    def get_equipment_fleet(self, gym_id: str) -> List[Dict[str, Any]]:
        """Expands equipment types with quantities into concrete machine instances."""
        gym = self.get_gym_info(gym_id)
        fleet = []
        for eq in gym["equipment_types"]:
            qty = eq.get("quantity", 1)
            for i in range(1, qty + 1):
                instance_id = f"{eq['type_id']}_{i:02d}"
                fleet.append({
                    "instance_id": instance_id,
                    "type_id": eq["type_id"],
                    "name": f"{eq['name']} #{i}",
                    "base_name": eq["name"],
                    "category": eq["category"],
                    "swap_types": eq.get("swap_types", [])
                })
        return fleet

    def get_type_to_swaps_map(self, gym_id: str) -> Dict[str, List[str]]:
        gym = self.get_gym_info(gym_id)
        return {eq["type_id"]: eq.get("swap_types", []) for eq in gym["equipment_types"]}


class ReservationGrid:
    """
    Tracks discrete time-slot reservations for all machine instances in a gym.
    Slot 0 = 0-15 min, Slot 1 = 15-30 min, Slot 2 = 30-45 min, etc.
    """
    def __init__(self, fleet: List[Dict[str, Any]], num_slots: int = 12):
        self.fleet = fleet
        self.instance_map = {m["instance_id"]: m for m in fleet}
        self.num_slots = num_slots
        # grid: { instance_id: { slot: Optional[Dict[str, Any]] } }
        self.grid: Dict[str, Dict[int, Optional[Dict[str, Any]]]] = {
            m["instance_id"]: {s: None for s in range(num_slots)} for m in fleet
        }

    def is_free(self, instance_id: str, slot: int) -> bool:
        if instance_id not in self.grid or slot >= self.num_slots:
            return False
        return self.grid[instance_id].get(slot) is None

    def book(self, instance_id: str, slot: int, user_id: str, exercise_type: str, is_swap: bool = False):
        if not self.is_free(instance_id, slot):
            raise ValueError(f"Collision detected! Machine {instance_id} at slot {slot} is already booked.")
        self.grid[instance_id][slot] = {
            "user_id": user_id,
            "exercise_type": exercise_type,
            "machine_name": self.instance_map[instance_id]["name"],
            "is_swap": is_swap
        }

    def release(self, instance_id: str, slot: int):
        if instance_id in self.grid and slot in self.grid[instance_id]:
            self.grid[instance_id][slot] = None

    def get_available_instances_for_type(self, type_id: str, slot: int) -> List[str]:
        """Finds all free instances for a given machine type at a specific slot."""
        available = []
        for instance_id, info in self.instance_map.items():
            if info["type_id"] == type_id and self.is_free(instance_id, slot):
                available.append(instance_id)
        return available

    def get_matrix_view(self) -> Dict[str, Any]:
        """Returns visual matrix data for UI heatmap / Gantt display."""
        matrix = []
        for instance_id, slots in self.grid.items():
            m_info = self.instance_map[instance_id]
            row = {
                "instance_id": instance_id,
                "name": m_info["name"],
                "category": m_info["category"],
                "slots": {s: (slots[s]["user_id"] if slots[s] else None) for s in range(self.num_slots)}
            }
            matrix.append(row)
        return matrix


class MultiUserGymScheduler:
    """
    Orchestrates collision-free multi-user workout scheduling across diverse gym types.
    Features:
    - Multi-instance load balancing
    - Dynamic exercise swapping
    - Step reordering to prevent peak-time bottlenecks
    """
    def __init__(self, catalog: Optional[GymCatalog] = None, num_slots: int = 8):
        self.catalog = catalog or GymCatalog()
        self.num_slots = num_slots
        self.gym_grids: Dict[str, ReservationGrid] = {}
        self.user_schedules: Dict[str, Dict[str, Any]] = {}
        self._init_all_gyms()

    def _init_all_gyms(self):
        for gym_id in self.catalog.get_gym_ids():
            fleet = self.catalog.get_equipment_fleet(gym_id)
            self.gym_grids[gym_id] = ReservationGrid(fleet, num_slots=self.num_slots)

    def reset_gym(self, gym_id: str):
        fleet = self.catalog.get_equipment_fleet(gym_id)
        self.gym_grids[gym_id] = ReservationGrid(fleet, num_slots=self.num_slots)

    def prescribe_exercises(self, gym_id: str, target_muscle: str, available_mins: int) -> List[str]:
        """Prescribes required exercise types tailored to what the specific gym actually owns."""
        gym = self.catalog.get_gym_info(gym_id)
        equip_types = gym["equipment_types"]

        if target_muscle == "Full Body":
            relevant = [eq["type_id"] for eq in equip_types]
        else:
            relevant = [eq["type_id"] for eq in equip_types if eq["category"].lower() == target_muscle.lower()]

        if not relevant:
            # Fallback to all equipment if target muscle has no matching equipment in a compact gym
            relevant = [eq["type_id"] for eq in equip_types]

        num_needed = max(1, min(available_mins // 15, len(relevant)))
        # Sample distinct exercise types
        selected = random.sample(relevant, num_needed)
        return selected

    def schedule_user(
        self,
        gym_id: str,
        user_id: str,
        target_muscle: str,
        available_mins: int,
        start_slot: int = 0
    ) -> Dict[str, Any]:
        """
        Dynamically routes an individual user into the shared gym floor grid without collisions.
        Uses greedy load balancing, alternative swapping, and reordering.
        """
        grid = self.gym_grids[gym_id]
        swaps_map = self.catalog.get_type_to_swaps_map(gym_id)
        prescribed_types = self.prescribe_exercises(gym_id, target_muscle, available_mins)

        steps = []
        pending_types = list(prescribed_types)
        current_slot = start_slot

        while pending_types and current_slot < self.num_slots:
            scheduled_step = False

            # Try to schedule one of the pending exercises in this time slot
            for candidate_type in list(pending_types):
                # 1. Check primary equipment instances
                free_instances = grid.get_available_instances_for_type(candidate_type, current_slot)
                if free_instances:
                    # Pick least utilized or first available instance
                    chosen_instance = free_instances[0]
                    grid.book(chosen_instance, current_slot, user_id, candidate_type, is_swap=False)
                    steps.append({
                        "step_num": len(steps) + 1,
                        "slot": current_slot,
                        "time_window": f"{current_slot*15}-{(current_slot+1)*15}m",
                        "instance_id": chosen_instance,
                        "machine_name": grid.instance_map[chosen_instance]["name"],
                        "category": grid.instance_map[chosen_instance]["category"],
                        "status": "PRIMARY_ASSIGNED",
                        "note": "Scheduled at preferred equipment"
                    })
                    pending_types.remove(candidate_type)
                    scheduled_step = True
                    break

            # 2. If no primary equipment was free at this slot, try swap alternatives
            if not scheduled_step:
                for candidate_type in list(pending_types):
                    possible_swaps = swaps_map.get(candidate_type, [])
                    for swap_type in possible_swaps:
                        free_swaps = grid.get_available_instances_for_type(swap_type, current_slot)
                        if free_swaps:
                            chosen_instance = free_swaps[0]
                            grid.book(chosen_instance, current_slot, user_id, swap_type, is_swap=True)
                            steps.append({
                                "step_num": len(steps) + 1,
                                "slot": current_slot,
                                "time_window": f"{current_slot*15}-{(current_slot+1)*15}m",
                                "instance_id": chosen_instance,
                                "machine_name": grid.instance_map[chosen_instance]["name"],
                                "category": grid.instance_map[chosen_instance]["category"],
                                "status": "SWAP_ASSIGNED",
                                "note": f"Primary {candidate_type} busy; routed to alternative {grid.instance_map[chosen_instance]['base_name']}"
                            })
                            pending_types.remove(candidate_type)
                            scheduled_step = True
                            break
                    if scheduled_step:
                        break

            # 3. If everything suitable in this slot is congested, advance slot (reordering/wait buffer)
            current_slot += 1

        # Check if any exercise couldn't fit within time horizon
        unfulfilled = list(pending_types)

        user_result = {
            "gym_id": gym_id,
            "user_id": user_id,
            "target_muscle": target_muscle,
            "available_mins": available_mins,
            "prescribed_types": prescribed_types,
            "schedule": steps,
            "total_slots": len(steps),
            "unfulfilled_exercises": unfulfilled,
            "collision_count": 0  # Mathematically guaranteed 0 by reservation grid
        }
        self.user_schedules[user_id] = user_result
        return user_result

    def batch_simulate(
        self,
        gym_id: str,
        users: List[Dict[str, Any]],
        start_slot: int = 0
    ) -> Dict[str, Any]:
        """
        Simulates Rush Hour: Multiple users arriving concurrently.
        Routes all users in real time, distributing them across fleet duplicates and swaps.
        """
        self.reset_gym(gym_id)
        results = []
        for u in users:
            res = self.schedule_user(
                gym_id=gym_id,
                user_id=u["user_id"],
                target_muscle=u.get("target_muscle", "Chest"),
                available_mins=u.get("available_mins", 45),
                start_slot=start_slot
            )
            results.append(res)

        grid = self.gym_grids[gym_id]
        fleet = self.catalog.get_equipment_fleet(gym_id)
        total_slots_available = len(fleet) * self.num_slots
        occupied_slots = sum(
            1 for inst in grid.grid.values() for s in inst.values() if s is not None
        )
        utilization_rate = (occupied_slots / total_slots_available * 100) if total_slots_available else 0

        # Verify collision absence
        collisions = 0
        for slot in range(self.num_slots):
            seen_users = set()
            for inst_id, slots in grid.grid.items():
                b = slots[slot]
                if b:
                    u_id = b["user_id"]
                    # A user cannot physically be on two machines at once
                    if u_id in seen_users:
                        collisions += 1
                    seen_users.add(u_id)

        return {
            "gym_id": gym_id,
            "gym_name": self.catalog.get_gym_info(gym_id)["name"],
            "total_users_simulated": len(users),
            "total_equipment_units": len(fleet),
            "total_slots_horizon": self.num_slots,
            "occupied_slots": occupied_slots,
            "overall_utilization_pct": round(utilization_rate, 1),
            "collision_count": collisions,
            "user_schedules": results,
            "matrix_view": grid.get_matrix_view()
        }
