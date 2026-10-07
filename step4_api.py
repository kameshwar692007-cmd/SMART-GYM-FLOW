from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
from multi_user_scheduler import GymCatalog, MultiUserGymScheduler
from ml_utility_engine import GymUtilityMLForecaster, CrossElasticitySpilloverModel, calculate_fatigue_penalty

# Initialize the API
app = FastAPI(
    title="Smart Gym AI Routing & Machine Learning Floor Dispatch API",
    description="Novel Cross-Elasticity Spillover Modeling, Multi-Output Utility Forecasting, and Zero-Hardware Floor Optimization."
)

# Global multi-gym scheduler & ML models
catalog = GymCatalog("gym_catalogs.json")
scheduler = MultiUserGymScheduler(catalog=catalog, num_slots=8)
ml_forecaster = GymUtilityMLForecaster(model_dir=".")
ml_forecaster.load()
cesm_engine = CrossElasticitySpilloverModel()

# Backward-compatibility equipment data from Step 1
df_equip = pd.read_csv("gym_equipment.csv")
current_gym_state = {
    "BP_01": True,
    "DB_01": False,
    "SQ_01": True,
    "LP_01": True,
    "CB_01": False,
    "PD_01": False
}

# --- Pydantic Models ---
class LegacyUserProfile(BaseModel):
    user_id: str
    goal: str
    target_muscle: str
    available_mins: int

class UserCheckInRequest(BaseModel):
    user_id: str = Field(..., example="User_101")
    target_muscle: str = Field(..., example="Chest")
    available_mins: int = Field(default=45, example=45)
    start_slot: int = Field(default=0, example=0)

class BatchSimulateRequest(BaseModel):
    num_users: int = Field(default=10, ge=1, le=50)
    target_muscle_mix: Optional[List[str]] = Field(default=None)

class SpilloverAnalysisRequest(BaseModel):
    gym_id: str = Field(..., example="commercial_gym")
    active_members: int = Field(default=25, ge=5, le=100)
    muscle_demand_overrides: Optional[Dict[str, int]] = Field(default=None)

class WhatIfRequest(BaseModel):
    gym_id: str = Field(..., example="commercial_gym")
    modifications: Dict[str, int] = Field(..., example={"bench_press": 4, "hack_squat": 0})
    crowd_size: int = Field(default=25)


# --- Legacy Endpoints ---
@app.get("/gym-state")
def get_legacy_gym_state():
    return {"status": "success", "data": current_gym_state}

@app.post("/prescribe-and-route")
def legacy_prescribe_and_route(user: LegacyUserProfile):
    if user.target_muscle == "Full Body":
        relevant_machines = df_equip
    else:
        relevant_machines = df_equip[df_equip['category'] == user.target_muscle]

    num_exercises = max(1, user.available_mins // 15)
    if len(relevant_machines) < num_exercises:
        prescribed = relevant_machines['machine_id'].tolist()
    else:
        prescribed = relevant_machines.sample(num_exercises, random_state=42)['machine_id'].tolist()

    final_schedule = []
    wait_queue = []
    for machine in prescribed:
        if not current_gym_state.get(machine, True):
            final_schedule.append(machine)
        else:
            swap_id = df_equip.loc[df_equip['machine_id'] == machine, 'swap_id'].values[0]
            if swap_id != "None" and not current_gym_state.get(swap_id, True):
                final_schedule.append(swap_id)
            else:
                wait_queue.append(machine)

    if wait_queue:
        final_schedule.extend(wait_queue)

    return {
        "user_id": user.user_id,
        "original_prescription": prescribed,
        "optimized_schedule": final_schedule,
        "total_workout_time_mins": len(final_schedule) * 15
    }


# --- Multi-Gym & Multi-User Endpoints ---
@app.get("/gyms")
def list_gyms():
    gyms = []
    for gym_id in catalog.get_gym_ids():
        info = catalog.get_gym_info(gym_id)
        fleet = catalog.get_equipment_fleet(gym_id)
        gyms.append({
            "gym_id": gym_id,
            "name": info["name"],
            "description": info["description"],
            "total_units": len(fleet),
            "equipment_types": len(info["equipment_types"])
        })
    return {"status": "success", "gyms": gyms}

@app.get("/gyms/{gym_id}/fleet")
def get_gym_fleet(gym_id: str):
    try:
        fleet = catalog.get_equipment_fleet(gym_id)
        return {"status": "success", "gym_id": gym_id, "fleet": fleet}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/gyms/{gym_id}/matrix")
def get_reservation_matrix(gym_id: str):
    if gym_id not in scheduler.gym_grids:
        raise HTTPException(status_code=404, detail=f"Gym {gym_id} not found")
    grid = scheduler.gym_grids[gym_id]
    return {"status": "success", "gym_id": gym_id, "matrix": grid.get_matrix_view()}

@app.post("/gyms/{gym_id}/check-in")
def check_in_user(gym_id: str, request: UserCheckInRequest):
    if gym_id not in scheduler.gym_grids:
        raise HTTPException(status_code=404, detail=f"Gym {gym_id} not found")

    result = scheduler.schedule_user(
        gym_id=gym_id,
        user_id=request.user_id,
        target_muscle=request.target_muscle,
        available_mins=request.available_mins,
        start_slot=request.start_slot
    )
    # Append biomechanical fatigue metric
    assigned_types = [s["instance_id"].rsplit("_", 1)[0] for s in result["schedule"]]
    result["biomechanical_fatigue_penalty"] = calculate_fatigue_penalty(assigned_types)
    return {"status": "success", "data": result}

@app.post("/gyms/{gym_id}/batch-simulate")
def batch_simulate_traffic(gym_id: str, req: BatchSimulateRequest):
    if gym_id not in scheduler.gym_grids:
        raise HTTPException(status_code=404, detail=f"Gym {gym_id} not found")

    muscle_options = req.target_muscle_mix or ["Chest", "Legs", "Back", "Full Body"]
    users = []
    for i in range(1, req.num_users + 1):
        users.append({
            "user_id": f"Member_{i:02d}",
            "target_muscle": muscle_options[(i - 1) % len(muscle_options)],
            "available_mins": 45
        })

    result = scheduler.batch_simulate(gym_id=gym_id, users=users)
    return {"status": "success", "simulation": result}

@app.post("/gyms/{gym_id}/reset")
def reset_gym_floor(gym_id: str):
    if gym_id not in scheduler.gym_grids:
        raise HTTPException(status_code=404, detail=f"Gym {gym_id} not found")
    scheduler.reset_gym(gym_id)
    return {"status": "success", "message": f"Floor for {gym_id} reset to empty"}


# --- NOVELTY ML ENDPOINTS ---
@app.get("/ml/status")
def get_ml_status():
    """Returns status of trained ML models and feature registry."""
    return {
        "status": "active",
        "model_type": "Multi-Output RandomForestRegressor (100 estimators, max_depth=12)",
        "features": ml_forecaster.feature_columns,
        "target_metrics": ["predicted_utilization_pct", "predicted_queue_risk", "predicted_idle_hours_loss"],
        "novelty_components": [
            "Cross-Elasticity Spillover Modeling (CESM)",
            "Disentangling Intrinsic vs Phantom Demand",
            "Biomechanical Physiological Fatigue Constraints",
            "Counterfactual What-If Layout ROI Optimization"
        ]
    }

@app.post("/ml/spillover-analysis")
def analyze_spillover(req: SpilloverAnalysisRequest):
    """Executes the Cross-Elasticity Spillover Model (CESM) on a gym facility."""
    try:
        gym_info = catalog.get_gym_info(req.gym_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    eq_counts = {eq["type_id"]: eq.get("quantity", 1) for eq in gym_info["equipment_types"]}
    category_map = {eq["type_id"]: eq["category"] for eq in gym_info["equipment_types"]}

    # Approximate demand by muscle if not provided
    if req.muscle_demand_overrides:
        demographic_demand = req.muscle_demand_overrides
    else:
        # Default distribution based on crowd size
        demographic_demand = {
            "Chest": int(req.active_members * 0.40),
            "Legs": int(req.active_members * 0.30),
            "Back": int(req.active_members * 0.20),
            "Full Body": int(req.active_members * 0.10)
        }

    analysis = cesm_engine.analyze_spillover(eq_counts, demographic_demand, category_map)
    return {
        "status": "success",
        "gym_id": req.gym_id,
        "active_members": req.active_members,
        "analysis": analysis
    }

@app.post("/ml/what-if-rebalance")
def run_what_if_rebalance(req: WhatIfRequest):
    """Predicts ROI and queue risk reduction for candidate equipment changes."""
    try:
        gym_info = catalog.get_gym_info(req.gym_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    current_fleet = {eq["type_id"]: eq.get("quantity", 1) for eq in gym_info["equipment_types"]}
    result = ml_forecaster.counterfactual_what_if(
        current_fleet=current_fleet,
        proposed_modification=req.modifications,
        crowd_size=req.crowd_size
    )
    return {"status": "success", "result": result}
