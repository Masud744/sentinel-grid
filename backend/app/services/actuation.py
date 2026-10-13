"""
Zone Hardware Actuation Signal Evaluator.

Determines simulated physical actuator commands (Buzzer, LEDs, Relay Power Cut)
based strictly on validated server-computed state:
- CRITICAL: Buzzer ON, RED LED, Relay Power Cut ON
- WARNING: Buzzer OFF, YELLOW LED, Relay Power Cut OFF (visual notice only)
- SAFE: Buzzer OFF, GREEN LED, Relay Power Cut OFF
"""

from app.schemas.ingest import ActuationCommand


def evaluate_actuation(state: str) -> ActuationCommand:
    if state == "CRITICAL":
        return ActuationCommand(
            buzzer=True,
            led="RED",
            relay_power_cut=True,
        )
    elif state == "WARNING":
        return ActuationCommand(
            buzzer=False,
            led="YELLOW",
            relay_power_cut=False,
        )
    else:  # SAFE
        return ActuationCommand(
            buzzer=False,
            led="GREEN",
            relay_power_cut=False,
        )
