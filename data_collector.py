"""
Real-Time Environmental Data Collector
=======================================
Fetches live readings from Open-Meteo for all areas and stores in database.

Usage:
    python data_collector.py          # Fetch once
    python data_collector.py --loop   # Fetch every 15 minutes
"""

import time
import argparse
from datetime import datetime

from database import get_db_connection
from data_fetcher import fetch_live_reading, store_reading, SOURCE

FETCH_INTERVAL = 900  # 15 minutes in seconds


def collect_all_readings():
    """Fetch and store real readings for all monitoring areas."""
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database.")
        return False

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, latitude, longitude FROM areas")
    areas = cursor.fetchall()
    cursor.close()
    conn.close()

    success = 0
    for area in areas:
        reading = fetch_live_reading(area['latitude'], area['longitude'])
        if reading:
            store_reading(area['id'], reading)
            print(f"  {area['name']}: AQI={reading['aqi']}, Temp={reading['temperature']}°C, Humidity={reading['humidity']}%")
            success += 1
        else:
            print(f"  {area['name']}: Failed to fetch live data")

    print(f"Collected live data for {success}/{len(areas)} areas at {datetime.now().strftime('%H:%M:%S')} (source: {SOURCE})")
    return success > 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EcoSense Live Data Collector')
    parser.add_argument('--loop', action='store_true', help='Run continuously every 15 minutes')
    args = parser.parse_args()

    if args.loop:
        print(f"Live data collector running every {FETCH_INTERVAL // 60} minutes. Press Ctrl+C to stop.")
        while True:
            collect_all_readings()
            time.sleep(FETCH_INTERVAL)
    else:
        collect_all_readings()
