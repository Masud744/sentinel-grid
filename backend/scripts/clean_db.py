import sqlite3
import os

paths = [
    r"d:\PROJECT\SentinelGrid Smart Campus Safety & Response System\backend\scs_rg.db",
    r"d:\PROJECT\SentinelGrid Smart Campus Safety & Response System\scs_rg.db"
]

for p in paths:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM zones WHERE id NOT IN ('iot-lab-001', 'server-room-001', 'ds-lab-001')")
        cursor.execute("DELETE FROM incidents WHERE zone_id NOT IN ('iot-lab-001', 'server-room-001', 'ds-lab-001')")
        cursor.execute("DELETE FROM sensor_readings WHERE zone_id NOT IN ('iot-lab-001', 'server-room-001', 'ds-lab-001')")
        conn.commit()
        conn.close()
        print(f"Cleaned {p}")
