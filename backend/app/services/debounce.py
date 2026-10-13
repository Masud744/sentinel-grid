"""
Sensor Signal Debounce and Warmup State Manager.

Maintains per-zone state across consecutive telemetry frames:
1. Fire Debounce: Requires 5 consecutive HIGH readings (1.0s at 200ms rate). Linear decay on signal drop over 3.0s.
2. Sensor Warmup: Ignores Gas/Water spikes during first 30s post node boot.
3. Occupancy Stabilizer: Holds state changes for 1.5s to eliminate contact flicker.
4. Heartbeat Monitor: Flags zone as OFFLINE if telemetry gap > 5 seconds.
"""

import time
from typing import Dict, Any, Tuple


class ZoneDebounceState:
    def __init__(self, zone_id: str):
        self.zone_id = zone_id
        self.boot_time = time.time()
        self.last_seen = time.time()
        
        # Fire debounce
        self.consecutive_fire_high = 0
        self.debounced_fire_signal = 0
        self.fire_decay_start_time = None

        # Occupancy hold
        self.last_raw_occupancy = 0
        self.occupancy_candidate_time = time.time()
        self.debounced_occupancy = 0

    def is_warmed_up(self) -> bool:
        """Returns True if node has been online for > 30 seconds."""
        return (time.time() - self.boot_time) >= 30.0

    def is_online(self, timeout_seconds: float = 5.0) -> bool:
        """Returns False if no telemetry received within timeout threshold."""
        return (time.time() - self.last_seen) <= timeout_seconds

    def update_fire(self, raw_fire: int) -> int:
        now = time.time()
        self.last_seen = now

        if raw_fire == 1:
            self.consecutive_fire_high += 1
            self.fire_decay_start_time = None
            if self.consecutive_fire_high >= 5:
                self.debounced_fire_signal = 1
        else:
            self.consecutive_fire_high = 0
            if self.debounced_fire_signal == 1:
                if self.fire_decay_start_time is None:
                    self.fire_decay_start_time = now
                
                # Decay over 3.0 seconds
                elapsed = now - self.fire_decay_start_time
                if elapsed >= 3.0:
                    self.debounced_fire_signal = 0
                    self.fire_decay_start_time = None

        return self.debounced_fire_signal

    def update_occupancy(self, raw_occ: int) -> int:
        now = time.time()
        self.last_seen = now

        if raw_occ != self.last_raw_occupancy:
            self.last_raw_occupancy = raw_occ
            self.occupancy_candidate_time = now
        else:
            # If candidate state has held for >= 1.5 seconds, accept state change
            if (now - self.occupancy_candidate_time) >= 1.5:
                self.debounced_occupancy = raw_occ

        return self.debounced_occupancy

    def filter_gas_water(self, raw_gas: float, raw_water: float) -> Tuple[float, float]:
        self.last_seen = time.time()
        if not self.is_warmed_up():
            # During warmup phase, ignore spikes and return zeroed baseline readings
            return 0.0, 0.0
        return max(0.0, raw_gas), max(0.0, raw_water)


# Global in-memory registry of zone debouncers
_debounce_registry: Dict[str, ZoneDebounceState] = {}


def get_zone_debouncer(zone_id: str) -> ZoneDebounceState:
    if zone_id not in _debounce_registry:
        _debounce_registry[zone_id] = ZoneDebounceState(zone_id)
    return _debounce_registry[zone_id]
