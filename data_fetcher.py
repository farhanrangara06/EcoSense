"""
Real-Time Environmental Data Fetcher
=====================================
Fetches live AQI, temperature, and humidity from Open-Meteo (free, no API key).
Data is based on area coordinates (latitude/longitude).

Source: https://open-meteo.com
"""

import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from config import DATA_FRESH_MINUTES, AQI_THRESHOLDS
from database import get_db_connection
from utils import classify_value, SEVERITY_INFO

WEATHER_URL = 'https://api.open-meteo.com/v1/forecast'
AIR_QUALITY_URL = 'https://air-quality-api.open-meteo.com/v1/air-quality'
SOURCE = 'open-meteo'


def _fetch_json(url, timeout=12):
    """Fetch JSON from a URL with error handling."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'EcoSense/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        print(f"API fetch error: {e}")
        return None


def fetch_live_reading(latitude, longitude):
    """
    Fetch current air quality, temperature, and humidity for coordinates.
    Returns dict with aqi, temperature, humidity, timestamp, source.
    """
    if not latitude or not longitude:
        return None

    lat, lon = float(latitude), float(longitude)

    # Weather: temperature & humidity
    weather_url = (
        f"{WEATHER_URL}?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m&timezone=auto"
    )
    weather = _fetch_json(weather_url)
    if not weather or 'current' not in weather:
        return None

    # Air quality: US AQI (matches our demo thresholds)
    aqi_url = (
        f"{AIR_QUALITY_URL}?latitude={lat}&longitude={lon}"
        f"&current=us_aqi&timezone=auto"
    )
    aqi_data = _fetch_json(aqi_url)

    current = weather['current']
    aqi = 0
    if aqi_data and 'current' in aqi_data:
        aqi = aqi_data['current'].get('us_aqi') or 0

    # If AQI unavailable, estimate from PM2.5 if present
    if not aqi and aqi_data and 'current' in aqi_data:
        pm25 = aqi_data['current'].get('pm2_5')
        if pm25:
            aqi = min(500, round(pm25 * 2.5))

    ts_str = current.get('time', datetime.now().isoformat())
    try:
        timestamp = datetime.fromisoformat(ts_str)
    except ValueError:
        timestamp = datetime.now()

    return {
        'aqi': round(float(aqi), 1),
        'temperature': round(float(current.get('temperature_2m', 0)), 1),
        'humidity': round(float(current.get('relative_humidity_2m', 0)), 1),
        'timestamp': timestamp,
        'source': SOURCE,
    }


def fetch_hourly_history(latitude, longitude, days=7, param='aqi'):
    """
    Fetch hourly historical data from Open-Meteo for trend charts.
    Returns {labels: [...], values: [...]}.
    """
    if not latitude or not longitude:
        return {'labels': [], 'values': []}

    lat, lon = float(latitude), float(longitude)
    days = min(max(days, 1), 30)

    if param == 'aqi':
        url = (
            f"{AIR_QUALITY_URL}?latitude={lat}&longitude={lon}"
            f"&hourly=us_aqi&past_days={days}&timezone=auto"
        )
        data = _fetch_json(url)
        if not data or 'hourly' not in data:
            return {'labels': [], 'values': []}
        times = data['hourly']['time']
        values = data['hourly'].get('us_aqi', [])
    else:
        fields = 'temperature_2m,relative_humidity_2m'
        key = 'temperature_2m' if param == 'temperature' else 'relative_humidity_2m'
        url = (
            f"{WEATHER_URL}?latitude={lat}&longitude={lon}"
            f"&hourly={fields}&past_days={days}&timezone=auto"
        )
        data = _fetch_json(url)
        if not data or 'hourly' not in data:
            return {'labels': [], 'values': []}
        times = data['hourly']['time']
        values = data['hourly'].get(key, [])

    labels, vals = [], []
    for t, v in zip(times, values):
        if v is None:
            continue
        try:
            ts = datetime.fromisoformat(t)
            labels.append(ts.strftime('%d %b %H:%M'))
            vals.append(float(v))
        except (ValueError, TypeError):
            continue

    return {'labels': labels, 'values': vals}


def get_area(area_id):
    """Get area record with coordinates."""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM areas WHERE id=%s", (area_id,))
    area = cursor.fetchone()
    cursor.close()
    conn.close()
    return area


def store_reading(area_id, reading):
    """Save a reading to the database."""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    ts = reading['timestamp']
    if isinstance(ts, datetime):
        ts = ts.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO environmental_readings (area_id,aqi,temperature,humidity,timestamp,source) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (area_id, reading['aqi'], reading['temperature'], reading['humidity'],
         ts, reading.get('source', SOURCE)))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def is_stale(timestamp):
    """Check if a reading is older than the cache window."""
    if not timestamp:
        return True
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(str(timestamp).replace('Z', ''))
    age = datetime.now() - timestamp
    return age > timedelta(minutes=DATA_FRESH_MINUTES)


def get_cached_or_live_reading(area_id):
    """
    Return fresh live data from API (cached in DB for 15 minutes).
    Falls back to last known reading if API is unavailable.
    """
    area = get_area(area_id)
    if not area:
        return None

    # Try latest real reading from DB first
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM environmental_readings WHERE area_id=%s AND source=%s "
        "ORDER BY timestamp DESC LIMIT 1",
        (area_id, SOURCE))
    cached = cursor.fetchone()
    cursor.close()
    conn.close()

    if cached and not is_stale(cached['timestamp']):
        cached['live'] = True
        return cached

    # Fetch fresh data from Open-Meteo
    live = fetch_live_reading(area.get('latitude'), area.get('longitude'))
    if live:
        live['area_id'] = area_id
        live['live'] = True
        store_reading(area_id, live)
        return live

    # API failed — return last known real reading
    if cached:
        cached['live'] = False
        cached['api_unavailable'] = True
        return cached

    # Last resort: any reading in DB
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM environmental_readings WHERE area_id=%s ORDER BY timestamp DESC LIMIT 1",
        (area_id,))
    fallback = cursor.fetchone()
    cursor.close()
    conn.close()
    if fallback:
        fallback['live'] = False
        fallback['api_unavailable'] = True
    return fallback


def fetch_and_store_area(area):
    """Fetch live data for one area and store in DB. Returns (area, reading) or None."""
    reading = fetch_live_reading(area.get('latitude'), area.get('longitude'))
    if reading:
        store_reading(area['id'], reading)
        return {'area': area, 'reading': reading}
    return None


def prefetch_all_areas(max_workers=8):
    """Fetch live data for all cities in parallel."""
    conn = get_db_connection()
    if not conn:
        return 0
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, city, state, latitude, longitude FROM areas ORDER BY state, name")
    areas = cursor.fetchall()
    cursor.close()
    conn.close()

    success = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_and_store_area, dict(a)): a for a in areas}
        for future in as_completed(futures):
            result = future.result()
            if result:
                a, r = result['area'], result['reading']
                print(f"  {a['name']}, {a['state']}: AQI={r['aqi']}, {r['temperature']}°C")
                success += 1
    return success


def get_all_cities_overview(live_refresh=False):
    """Return latest cached reading for every city. Optionally refresh stale ones in parallel."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.name, a.city, a.state, a.latitude, a.longitude,
               r.aqi, r.temperature, r.humidity, r.timestamp, r.source
        FROM areas a
        LEFT JOIN environmental_readings r ON r.id = (
            SELECT id FROM environmental_readings
            WHERE area_id = a.id AND source = %s
            ORDER BY timestamp DESC LIMIT 1
        )
        ORDER BY a.state, a.name
    """, (SOURCE,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if live_refresh:
        stale_areas = [dict(r) for r in rows if not r.get('aqi') or is_stale(r.get('timestamp'))]
        if stale_areas:
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(fetch_and_store_area, stale_areas[:30]))
            return get_all_cities_overview(live_refresh=False)

    overview = []
    for r in rows:
        aqi = r.get('aqi')
        level = classify_value(float(aqi), AQI_THRESHOLDS) if aqi else 'moderate'
        info = SEVERITY_INFO.get(level, SEVERITY_INFO['moderate'])
        overview.append({
            'id': r['id'], 'name': r['name'], 'city': r['city'], 'state': r['state'],
            'aqi': aqi, 'temperature': r.get('temperature'), 'humidity': r.get('humidity'),
            'timestamp': str(r.get('timestamp', '')),
            'severity': info['label'], 'emoji': info['emoji'],
            'severity_class': info['class'],
        })
    return overview
