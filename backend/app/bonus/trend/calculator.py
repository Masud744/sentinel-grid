"""
Bonus Module 2: Short-Term Risk Trend Calculator (Isolated).

Tracks whether a zone's risk score is trending upwards over a rolling window
of its last 10-15 readings using simple moving average and linear slope estimation.

IMPORTANT: This trend signal is strictly informational/predictive and is NEVER allowed
to mutate the live risk score or trigger physical hardware actuation.
"""

from typing import List, Dict, Any


def calculate_risk_trend(recent_scores: List[float]) -> Dict[str, Any]:
    """
    Computes slope and moving average trend over recent risk scores.
    Returns:
      {
        "is_trending_up": bool,
        "slope": float,
        "moving_avg": float,
        "sample_count": int
      }
    """
    if not recent_scores or len(recent_scores) < 3:
        return {
            "is_trending_up": False,
            "slope": 0.0,
            "moving_avg": round(recent_scores[-1], 2) if recent_scores else 0.0,
            "sample_count": len(recent_scores)
        }

    n = len(recent_scores)
    moving_avg = sum(recent_scores) / n

    # Simple linear regression slope calculation
    x_mean = (n - 1) / 2.0
    y_mean = moving_avg

    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent_scores))
    den = sum((i - x_mean) ** 2 for i in range(n))

    slope = num / den if den != 0 else 0.0

    # Flag as trending up if slope > 0.5 points per reading
    is_trending_up = slope > 0.5

    return {
        "is_trending_up": is_trending_up,
        "slope": round(slope, 3),
        "moving_avg": round(moving_avg, 2),
        "sample_count": n
    }
