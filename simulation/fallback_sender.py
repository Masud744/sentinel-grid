"""
Fallback Telemetry Generator (Python CLI).

Directly feeds raw sensor JSON telemetry to the backend ingestion endpoint.
Supports simulating single or multi-zone hazard scenarios for reliable offline demos and testing.
"""

import sys
import time
import random
import argparse
import requests

DEFAULT_BACKEND_URL = "http://localhost:8000/api/v1/ingest"

ZONES_CONFIG = {
    "iot_lab": {
        "name": "IoT Lab",
        "api_key": "zone-key-iot-lab-001",
        "sensors": ["fire", "gas", "occupancy"]
    },
    "server_room": {
        "name": "Server Room",
        "api_key": "zone-key-server-room-002",
        "sensors": ["fire", "water", "occupancy"]
    },
    "ds_lab": {
        "name": "Data Science Lab",
        "api_key": "zone-key-ds-lab-003",
        "sensors": ["fire", "water", "occupancy"]
    }
}


def generate_payload(zone_key: str, scenario: str, seq: int) -> dict:
    if scenario == "safe":
        fire = 0
        gas = random.uniform(10.0, 50.0) if zone_key == "iot_lab" else 0.0
        water = random.uniform(0.0, 2.0) if zone_key != "iot_lab" else 0.0
        occ = random.choice([0, 1])
    elif scenario == "warning":
        fire = 0
        gas = random.uniform(350.0, 500.0) if zone_key == "iot_lab" else 0.0
        water = random.uniform(15.0, 25.0) if zone_key != "iot_lab" else 0.0
        occ = 1
    elif scenario == "critical":
        fire = 1
        gas = random.uniform(600.0, 850.0) if zone_key == "iot_lab" else 0.0
        water = random.uniform(30.0, 48.0) if zone_key != "iot_lab" else 0.0
        occ = 1
    elif scenario == "spike_flapping":
        fire = random.choice([0, 1])
        gas = random.uniform(200.0, 700.0)
        water = random.uniform(5.0, 35.0)
        occ = 1
    else:  # default safe
        fire, gas, water, occ = 0, 20.0, 0.0, 0

    return {
        "sequence_id": seq,
        "timestamp": int(time.time()),
        "sensors": {
            "fire_signal": fire,
            "gas_level_raw": round(gas, 2),
            "water_level_raw": round(water, 2),
            "occupancy_raw": occ,
        }
    }


def run_sender(target_url: str, scenario: str, zone_keys: list, interval: float, count: int):
    print(f"=== SCS-RG Telemetry Fallback Sender ===")
    print(f"Target Backend URL: {target_url}")
    print(f"Scenario: {scenario.upper()}")
    print(f"Active Zones: {', '.join(zone_keys)}")
    print(f"Interval: {interval}s | Iterations: {'Infinite' if count <= 0 else count}\n")

    seq_map = {z: 1000 for z in zone_keys}
    iteration = 0

    try:
        while True:
            iteration += 1
            for zk in zone_keys:
                cfg = ZONES_CONFIG[zk]
                seq_map[zk] += 1
                payload = generate_payload(zk, scenario, seq_map[zk])
                headers = {"X-Zone-API-Key": cfg["api_key"]}

                try:
                    res = requests.post(target_url, json=payload, headers=headers, timeout=3.0)
                    if res.status_code == 200:
                        data = res.json()
                        act = data.get("actuation", {})
                        print(f"[{time.strftime('%H:%M:%S')}] [{cfg['name']}] Seq #{payload['sequence_id']} -> "
                              f"Score: {data['risk_score']} | State: {data['state']} | "
                              f"Buzzer: {'ON' if act.get('buzzer') else 'OFF'} | LED: {act.get('led')}")
                    else:
                        print(f"[{cfg['name']}] HTTP Error {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"[{cfg['name']}] Request Failed: {str(e)}")

            if count > 0 and iteration >= count:
                break
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nFallback sender stopped by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SCS-RG Fallback Sensor Telemetry Sender")
    parser.add_argument("--url", default=DEFAULT_BACKEND_URL, help="Backend ingestion endpoint URL")
    parser.add_argument("--scenario", choices=["safe", "warning", "critical", "spike_flapping"], default="safe", help="Hazard scenario")
    parser.add_argument("--zones", nargs="+", choices=["iot_lab", "server_room", "ds_lab"], default=["iot_lab", "server_room", "ds_lab"], help="Target zones")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds")
    parser.add_argument("--count", type=int, default=0, help="Number of telemetry frames to send (0 = infinite)")

    args = parser.parse_args()
    run_sender(args.url, args.scenario, args.zones, args.interval, args.count)
