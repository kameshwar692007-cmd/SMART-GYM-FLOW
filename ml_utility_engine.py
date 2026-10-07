"""
Novel Machine Learning Engine for Gym Equipment Utility Analysis
Features:
1. Cross-Elasticity Spillover Modeling (CESM) - Disentangling Intrinsic vs Phantom Demand
2. Multi-Output Random Forest Utility & Congestion Forecaster
3. Biomechanical Fatigue-Aware Routing Constraints
4. Counterfactual "What-If" Floor Rebalancing Simulator
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------------
# 1. Biomechanical Co-Activation & Fatigue Penalty Matrix
# ---------------------------------------------------------------------------
# Higher penalty means high compound fatigue if executed back-to-back
BIOMECHANICAL_FATIGUE_MATRIX = {
    ("squat_rack", "leg_press"): 0.85,       # High quad/glute pre-exhaustion
    ("squat_rack", "hack_squat"): 0.90,      # Severe spinal/knee joint fatigue
    ("deadlift_platform", "squat_rack"): 0.95, # Severe CNS and lumbar spine strain
    ("comp_bench", "dumbbell_bench"): 0.70,   # High tricep/pectoral synergist fatigue
    ("bench_press", "chest_press_machine"): 0.65,
    ("lat_pulldown", "seated_cable_row"): 0.60 # Latissimus dorsi & bicep fatigue
}

def calculate_fatigue_penalty(exercise_sequence: List[str]) -> float:
    """Calculates cumulative physiological fatigue penalty for an exercise sequence."""
    total_penalty = 0.0
    for i in range(len(exercise_sequence) - 1):
        pair = (exercise_sequence[i], exercise_sequence[i+1])
        rev_pair = (exercise_sequence[i+1], exercise_sequence[i])
        penalty = BIOMECHANICAL_FATIGUE_MATRIX.get(pair, BIOMECHANICAL_FATIGUE_MATRIX.get(rev_pair, 0.20))
        total_penalty += penalty
    return round(total_penalty, 3)


# ---------------------------------------------------------------------------
# 2. Cross-Elasticity Spillover Model (CESM)
# ---------------------------------------------------------------------------
class CrossElasticitySpilloverModel:
    """
    Novel Contribution:
    Disentangles Intrinsic Demand from Spillover Phantom Demand caused by
    choked substitute equipment.
    Observed_Demand(B) = Intrinsic_Demand(B) + sum_A [ Elasticity(A->B) * Max(0, Congestion(A) - Threshold) ]
    """
    # Cross-elasticity coefficients between equipment types
    DEFAULT_ELASTICITY = {
        ("bench_press", "dumbbell_bench"): 0.75,
        ("bench_press", "chest_press_machine"): 0.50,
        ("bench_press", "cable_crossover"): 0.35,
        ("squat_rack", "leg_press"): 0.80,
        ("squat_rack", "hack_squat"): 0.60,
        ("leg_press", "hack_squat"): 0.65,
        ("lat_pulldown", "seated_cable_row"): 0.70,
        ("comp_bench", "power_cage"): 0.40,
        ("deadlift_platform", "power_cage"): 0.55
    }

    def __init__(self, elasticity_map: Optional[Dict[Tuple[str, str], float]] = None):
        self.elasticity_map = elasticity_map or self.DEFAULT_ELASTICITY

    def analyze_spillover(
        self,
        equipment_counts: Dict[str, int],
        demographic_muscle_demand: Dict[str, int],
        category_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Computes Intrinsic Demand vs Phantom Spillover Demand for each equipment type.
        """
        # 1. Base intrinsic demand estimation from member targets
        intrinsic_demand: Dict[str, float] = {}
        for eq_type, qty in equipment_counts.items():
            cat = category_map.get(eq_type, "Full Body")
            demand_pool = demographic_muscle_demand.get(cat, 5)
            # Intrinsic demand distributed roughly by equipment prominence
            intrinsic_demand[eq_type] = round(demand_pool * (qty / max(1, qty * 1.5)), 2)

        # 2. Calculate primary congestion pressure (Demand / Capacity)
        congestion_pressure: Dict[str, float] = {}
        for eq_type, qty in equipment_counts.items():
            ratio = intrinsic_demand[eq_type] / max(1, qty)
            congestion_pressure[eq_type] = max(0.0, ratio - 1.0) # Excess overflow index

        # 3. Calculate phantom spillover across the directed network
        phantom_spillover: Dict[str, float] = {eq_type: 0.0 for eq_type in equipment_counts}
        spillover_edges: List[Dict[str, Any]] = []

        for (source, target), coeff in self.elasticity_map.items():
            if source in congestion_pressure and target in phantom_spillover:
                overflow = congestion_pressure[source]
                if overflow > 0:
                    displaced_users = overflow * coeff * equipment_counts[source]
                    phantom_spillover[target] += displaced_users
                    spillover_edges.append({
                        "source": source,
                        "target": target,
                        "elasticity": coeff,
                        "displaced_load": round(displaced_users, 2)
                    })

        # 4. Synthesize results
        breakdown = []
        root_cause_bottlenecks = []
        for eq_type, qty in equipment_counts.items():
            base = intrinsic_demand[eq_type]
            phantom = round(phantom_spillover[eq_type], 2)
            total_observed = round(base + phantom, 2)
            capacity = qty * 4.0 # 4 fifteen-minute slots per hour
            utilization_pct = min(100.0, round((total_observed / capacity) * 100, 1))

            is_trigger = congestion_pressure[eq_type] > 0.3
            if is_trigger:
                root_cause_bottlenecks.append({
                    "equipment": eq_type,
                    "overflow_severity": round(congestion_pressure[eq_type], 2),
                    "spillover_caused": sum(e["displaced_load"] for e in spillover_edges if e["source"] == eq_type)
                })

            breakdown.append({
                "equipment_type": eq_type,
                "quantity": qty,
                "intrinsic_demand": base,
                "phantom_spillover_demand": phantom,
                "total_observed_demand": total_observed,
                "effective_utilization_pct": utilization_pct,
                "phantom_load_share_pct": round((phantom / max(0.01, total_observed)) * 100, 1)
            })

        return {
            "equipment_breakdown": breakdown,
            "spillover_network_edges": spillover_edges,
            "root_cause_trigger_bottlenecks": root_cause_bottlenecks
        }


# ---------------------------------------------------------------------------
# 3. Multi-Output ML Utility & Congestion Forecaster
# ---------------------------------------------------------------------------
class GymUtilityMLForecaster:
    """
    Multi-Output Random Forest Model predicting:
    - Continuous Equipment Utilization %
    - Queue Risk Probability (0.0 to 1.0)
    - Idle Capital Waste (Hours/Day)
    """
    MODEL_FILE = "gym_utility_rf.joblib"
    SCALER_FILE = "gym_utility_scaler.joblib"

    def __init__(self, model_dir: str = "."):
        self.model_dir = Path(model_dir)
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: List[str] = [
            "unit_quantity",
            "active_crowd_size",
            "muscle_demand_ratio",
            "goal_hypertrophy_pct",
            "goal_strength_pct",
            "goal_weightloss_pct",
            "swap_alternatives_count",
            "hour_of_day",
            "is_peak_hour"
        ]

    def generate_training_dataset(self, n_samples: int = 2500) -> pd.DataFrame:
        """Generates realistic synthetic multi-session data across varied operational loads."""
        np.random.seed(42)
        records = []

        for _ in range(n_samples):
            qty = np.random.randint(1, 6)
            crowd = np.random.randint(5, 45)
            muscle_ratio = np.random.uniform(0.1, 0.6) # e.g. 40% people doing Chest
            
            # Demographic goal mix (sums to 1.0)
            g1, g2, g3 = np.random.dirichlet([3, 2, 2])
            swap_count = np.random.randint(0, 4)
            hour = np.random.randint(6, 23)
            is_peak = 1 if (17 <= hour <= 21) or (6 <= hour <= 9) else 0

            # Ground truth utility physics simulation
            demand_load = (crowd * muscle_ratio * (1.2 if is_peak else 0.85))
            # Strength goal users take longer rest (lower turnover -> higher dwell time)
            dwell_multiplier = 1.0 + (g2 * 0.4) - (g3 * 0.2)
            effective_demand = demand_load * dwell_multiplier
            capacity = qty * 3.5 # capacity per slot factor

            # Calculate true utilization rate
            raw_util = (effective_demand / capacity)
            utilization_pct = float(np.clip(raw_util * 100 + np.random.normal(0, 3.5), 5.0, 100.0))

            # Queue risk: exponential rise as utilization exceeds 75%
            queue_risk = float(np.clip(1.0 / (1.0 + np.exp(-0.1 * (utilization_pct - 75))) + np.random.normal(0, 0.03), 0.0, 1.0))

            # Idle waste hours (out of 16-hour operating day)
            idle_hours = float(np.clip((1.0 - (utilization_pct / 100.0)) * 16.0 + np.random.normal(0, 0.4), 0.0, 16.0))

            records.append({
                "unit_quantity": qty,
                "active_crowd_size": crowd,
                "muscle_demand_ratio": round(muscle_ratio, 3),
                "goal_hypertrophy_pct": round(g1, 3),
                "goal_strength_pct": round(g2, 3),
                "goal_weightloss_pct": round(g3, 3),
                "swap_alternatives_count": swap_count,
                "hour_of_day": hour,
                "is_peak_hour": is_peak,
                # Target Labels
                "target_utilization_pct": round(utilization_pct, 2),
                "target_queue_risk": round(queue_risk, 3),
                "target_idle_hours": round(idle_hours, 2)
            })

        return pd.DataFrame(records)

    def train_and_save(self) -> Dict[str, float]:
        """Trains the Multi-Output Random Forest Regressor and serializes to disk."""
        df = self.generate_training_dataset(n_samples=2500)
        X = df[self.feature_columns]
        Y = df[["target_utilization_pct", "target_queue_risk", "target_idle_hours"]]

        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train_scaled, Y_train)

        # Evaluation
        score = float(self.model.score(X_test_scaled, Y_test))

        # Save artifacts
        joblib.dump(self.model, self.model_dir / self.MODEL_FILE)
        joblib.dump(self.scaler, self.model_dir / self.SCALER_FILE)

        return {"r2_score": round(score, 4), "samples_trained": len(df)}

    def load(self):
        """Loads serialized models from disk."""
        model_path = self.model_dir / self.MODEL_FILE
        scaler_path = self.model_dir / self.SCALER_FILE
        if not model_path.exists() or not scaler_path.exists():
            # Auto train if missing
            self.train_and_save()
        else:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)

    def predict(self, feature_dicts: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """Generates ML predictions for a batch of equipment scenarios."""
        if self.model is None or self.scaler is None:
            self.load()

        df_input = pd.DataFrame(feature_dicts)[self.feature_columns]
        scaled = self.scaler.transform(df_input)
        preds = self.model.predict(scaled)

        results = []
        for p in preds:
            results.append({
                "predicted_utilization_pct": float(np.clip(round(p[0], 1), 0.0, 100.0)),
                "predicted_queue_risk": float(np.clip(round(p[1], 3), 0.0, 1.0)),
                "predicted_idle_hours_loss": float(np.clip(round(p[2], 1), 0.0, 16.0))
            })
        return results

    def counterfactual_what_if(
        self,
        current_fleet: Dict[str, int],
        proposed_modification: Dict[str, int],
        crowd_size: int = 25,
        hour: int = 18
    ) -> Dict[str, Any]:
        """
        Predicts gym-wide utility delta if a manager modifies equipment quantities
        (e.g., removing 1 Hack Squat and adding 1 Olympic Bench).
        """
        def build_features(fleet_dict: Dict[str, int]):
            feats = []
            for eq_name, qty in fleet_dict.items():
                feats.append({
                    "unit_quantity": max(1, qty),
                    "active_crowd_size": crowd_size,
                    "muscle_demand_ratio": 0.35, # average demand
                    "goal_hypertrophy_pct": 0.50,
                    "goal_strength_pct": 0.30,
                    "goal_weightloss_pct": 0.20,
                    "swap_alternatives_count": 2,
                    "hour_of_day": hour,
                    "is_peak_hour": 1 if (17 <= hour <= 21) else 0
                })
            return feats

        base_preds = self.predict(build_features(current_fleet))
        new_fleet = dict(current_fleet)
        new_fleet.update(proposed_modification)
        new_preds = self.predict(build_features(new_fleet))

        base_avg_util = np.mean([p["predicted_utilization_pct"] for p in base_preds])
        new_avg_util = np.mean([p["predicted_utilization_pct"] for p in new_preds])
        base_queue = np.mean([p["predicted_queue_risk"] for p in base_preds])
        new_queue = np.mean([p["predicted_queue_risk"] for p in new_preds])

        return {
            "current_avg_utilization_pct": round(float(base_avg_util), 1),
            "projected_avg_utilization_pct": round(float(new_avg_util), 1),
            "current_avg_queue_risk": round(float(base_queue), 3),
            "projected_avg_queue_risk": round(float(new_queue), 3),
            "bottleneck_relief_pct": round(float((base_queue - new_queue) / max(0.01, base_queue) * 100), 1),
            "capital_efficiency_gain": "Positive" if new_avg_util > base_avg_util else "Neutral"
        }
