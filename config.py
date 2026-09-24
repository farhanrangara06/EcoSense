"""EcoSense Configuration - Edit MySQL settings here."""

import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'ecosense-dev-secret-key-change-me')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'ecosense'),
    'port': int(os.environ.get('DB_PORT', 3306)),
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'reports')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

DATA_FRESH_MINUTES = 15   # Re-fetch live data after this many minutes
DATA_STALE_MINUTES = 60
LIVE_DATA_SOURCE = 'open-meteo'  # Real-time data provider (free, no API key)

# Demo thresholds (not official government standards)
AQI_THRESHOLDS = {'good': (0, 50), 'moderate': (51, 100), 'poor': (101, 200), 'hazardous': (201, 9999)}
TEMP_THRESHOLDS = {'good': (0, 28), 'moderate': (29, 35), 'poor': (36, 40), 'hazardous': (41, 999)}
HUMIDITY_THRESHOLDS = {'good': (30, 60), 'moderate': (61, 75), 'poor': (76, 85), 'hazardous': (86, 100)}
