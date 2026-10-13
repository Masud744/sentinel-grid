"""
Multi-Zone Incident Priority Ranking Engine.

When multiple campus zones enter CRITICAL state simultaneously, this engine orders them by urgency:
1. Primary Sort Key: Risk Score (Higher score = higher priority)
2. Secondary Sort Key: Occupancy Factor (Occupied labs with human life at risk take precedence)
3. Tertiary Sort Key: Duration in Critical State (Longer unaddressed incidents take precedence)

Every ranked zone is annotated with a clear, human-readable decision explanation.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from app.schemas.zone import PriorityQueueItem


def rank_critical_incidents(critical_zones_data: List[Dict[str, Any]]) -> List[PriorityQueueItem]:
    """
    Ranks active CRITICAL zones and generates explanation strings.
    Input list dict format:
    [
      {
        "zone_id": "...",
        "zone_name": "IoT Lab",
        "risk_score": 85.5,
        "state": "CRITICAL",
        "occupancy_factor": 1.0,
        "critical_since": datetime_obj
      }, ...
    ]
    """
    now = datetime.now(timezone.utc)

    # Calculate duration for sorting
    processed_items = []
    for item in critical_zones_data:
        critical_since = item.get("critical_since") or now
        if critical_since.tzinfo is None:
            critical_since = critical_since.replace(tzinfo=timezone.utc)
        
        duration_seconds = max(0.0, (now - critical_since).total_seconds())

        processed_items.append({
            "zone_id": item["zone_id"],
            "zone_name": item["zone_name"],
            "risk_score": item["risk_score"],
            "state": item["state"],
            "occupancy_factor": item.get("occupancy_factor", 0.3),
            "duration_seconds": duration_seconds,
        })

    # Sort tuple: (-risk_score, -occupancy_factor, -duration_seconds)
    sorted_items = sorted(
        processed_items,
        key=lambda x: (x["risk_score"], x["occupancy_factor"], x["duration_seconds"]),
        reverse=True
    )

    ranked_queue: List[PriorityQueueItem] = []
    for rank_idx, item in enumerate(sorted_items, start=1):
        occ_str = "Occupied" if item["occupancy_factor"] >= 1.0 else "Vacant"
        dur_str = f"{int(item['duration_seconds'])}s"

        reason = (
            f"Rank #{rank_idx}: Risk Score {item['risk_score']:.1f}/100 "
            f"({occ_str}, Critical for {dur_str})"
        )

        queue_item = PriorityQueueItem(
            rank=rank_idx,
            zone_id=item["zone_id"],
            zone_name=item["zone_name"],
            risk_score=item["risk_score"],
            state=item["state"],
            occupancy_factor=item["occupancy_factor"],
            duration_critical_seconds=round(item["duration_seconds"], 1),
            reason=reason,
        )
        ranked_queue.append(queue_item)

    return ranked_queue
