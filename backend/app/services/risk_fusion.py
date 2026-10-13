"""
Server-Side Multi-Hazard Risk Fusion Engine.

Implements the exact weighted formula:
  risk_score = w_fire * fire_signal + w_gas * gas_level_norm + w_water * water_level_norm + w_occ * occupancy_factor
  weights: w_fire = 40, w_gas = 25, w_water = 20, w_occ = 15 (Sum = 100)

State Thresholds:
  risk_score < 30        -> SAFE
  30 <= risk_score < 65  -> WARNING
  risk_score >= 65       -> CRITICAL
"""

from typing import Tuple, Dict, Any

W_FIRE = 40.0
W_GAS = 25.0
W_WATER = 20.0
W_OCC = 15.0

MAX_GAS_PPM = 1000.0
MAX_WATER_CM = 50.0


def normalize_gas(gas_ppm: float) -> float:
    """Normalizes raw PPM reading to 0.0 - 1.0."""
    if gas_ppm < 0:
        return 0.0
    return min(1.0, gas_ppm / MAX_GAS_PPM)


def normalize_water(water_cm: float) -> float:
    """Normalizes raw depth reading in cm to 0.0 - 1.0."""
    if water_cm < 0:
        return 0.0
    return min(1.0, water_cm / MAX_WATER_CM)


def compute_occupancy_factor(occupancy_raw: int) -> float:
    """Returns 1.0 if occupied, 0.3 if vacant."""
    return 1.0 if occupancy_raw == 1 else 0.3


def compute_risk_score(
    fire_debounced: int,
    gas_raw: float,
    water_raw: float,
    occupancy_raw: int
) -> Tuple[float, str, Dict[str, Any]]:
    """
    Computes server-side risk score and assigns state.
    Returns: (risk_score, state, breakdown_details)
    """
    fire_sig = 1.0 if fire_debounced == 1 else 0.0
    gas_norm = normalize_gas(gas_raw)
    water_norm = normalize_water(water_raw)
    occ_factor = compute_occupancy_factor(occupancy_raw)

    score_fire = W_FIRE * fire_sig
    score_gas = W_GAS * gas_norm
    score_water = W_WATER * water_norm
    score_occ = W_OCC * occ_factor

    total_risk = round(score_fire + score_gas + score_water + score_occ, 2)

    if total_risk < 30.0:
        state = "SAFE"
    elif total_risk < 65.0:
        state = "WARNING"
    else:
        state = "CRITICAL"

    breakdown = {
        "fire_contribution": score_fire,
        "gas_contribution": score_gas,
        "water_contribution": score_water,
        "occupancy_contribution": score_occ,
        "raw_inputs": {
            "fire_signal": fire_debounced,
            "gas_ppm": gas_raw,
            "water_cm": water_raw,
            "occupancy": occupancy_raw,
        }
    }

    return total_risk, state, breakdown
