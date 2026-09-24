"""Database connection – MySQL primary, SQLite auto-fallback for quick start."""

import os
import sqlite3
import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from config import DB_CONFIG
from indian_cities import INDIAN_CITIES

SQLITE_PATH = os.environ.get(
    'SQLITE_PATH',
    os.path.join('/tmp', 'ecosense.db') if os.environ.get('NETLIFY') else
    os.path.join(os.path.dirname(__file__), 'ecosense.db'))
DB_BACKEND = None  # 'mysql' or 'sqlite'


class SQLiteRowDict(dict):
    """Dict row wrapper for SQLite compatibility."""
    pass


class SQLiteCursor:
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()
        self._cols = []
        self.lastrowid = None

    def execute(self, sql, params=None):
        sql = sql.replace('%s', '?')
        sql = sql.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
        sql = sql.replace("ENUM('citizen', 'admin')", 'TEXT')
        sql = sql.replace("ENUM('Pending','Reviewed','Resolved')", 'TEXT')
        sql = sql.replace('DECIMAL(6,2)', 'REAL').replace('DECIMAL(5,2)', 'REAL').replace('DECIMAL(10,7)', 'REAL')
        sql = sql.replace('INDEX idx_area_timestamp (area_id, timestamp)', '')
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        self.lastrowid = self._cursor.lastrowid
        self._cols = [d[0] for d in self._cursor.description] if self._cursor.description else []
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return SQLiteRowDict({self._cols[i]: row[i] for i in range(len(self._cols))})

    def fetchall(self):
        return [SQLiteRowDict({self._cols[i]: r[i] for i in range(len(self._cols))}) for r in self._cursor.fetchall()]

    def close(self):
        self._cursor.close()


class SQLiteConnection:
    def __init__(self, path):
        self._conn = sqlite3.connect(path, check_same_thread=False)

    def cursor(self, dictionary=False):
        return SQLiteCursor(self._conn)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_db_connection():
    """Connect to MySQL; fall back to SQLite if MySQL is unavailable."""
    global DB_BACKEND
    if DB_BACKEND == 'sqlite':
        return SQLiteConnection(SQLITE_PATH)

    try:
        import mysql.connector
        conn = mysql.connector.connect(**DB_CONFIG)
        DB_BACKEND = 'mysql'
        return conn
    except Exception as e:
        print(f"MySQL unavailable ({e}). Using SQLite fallback: {SQLITE_PATH}")
        DB_BACKEND = 'sqlite'
        return SQLiteConnection(SQLITE_PATH)


def init_database():
    """Create tables and seed initial data."""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, password TEXT NOT NULL,
            role TEXT DEFAULT 'citizen',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            city TEXT NOT NULL, state TEXT DEFAULT 'Maharashtra',
            description TEXT, latitude REAL, longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS environmental_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, area_id INTEGER NOT NULL,
            aqi REAL NOT NULL, temperature REAL NOT NULL,
            humidity REAL NOT NULL, timestamp TEXT NOT NULL,
            source TEXT DEFAULT 'simulator',
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concern_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, area_id INTEGER NOT NULL,
            issue_type TEXT NOT NULL, description TEXT NOT NULL, photo TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL, status TEXT NOT NULL,
            admin_note TEXT, changed_by INTEGER, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES concern_reports(id) ON DELETE CASCADE,
            FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL)
    """)
    conn.commit()

    sync_indian_cities(cursor)
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role='admin'")
    if cursor.fetchone()['cnt'] == 0:
        seed_admin(cursor)
    conn.commit()
    cursor.close()
    conn.close()
    backend = DB_BACKEND or 'sqlite'
    print(f"Database ready ({backend}). Admin: admin@ecosense.in / admin123")
    return True


def sync_indian_cities(cursor):
    """Add all Indian cities from indian_cities.py (skips duplicates)."""
    added = 0
    for city in INDIAN_CITIES:
        cursor.execute(
            "SELECT id FROM areas WHERE name=%s AND state=%s", (city[0], city[2]))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO areas (name, city, state, description, latitude, longitude) "
                "VALUES (%s,%s,%s,%s,%s,%s)", city)
            added += 1
    if added:
        print(f"Added {added} new cities to database ({len(INDIAN_CITIES)} total configured).")


def seed_admin(cursor):
    pwd = generate_password_hash('admin123')
    cursor.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)",
        ('Admin', 'admin@ecosense.in', pwd, 'admin'))


def seed_readings(cursor):
    cursor.execute("SELECT id FROM areas")
    area_ids = [r['id'] for r in cursor.fetchall()]
    now = datetime.now()
    for area_id in area_ids:
        base_aqi = random.randint(80, 160)
        for days_ago in range(30, -1, -1):
            for hour in range(0, 24, 3):
                ts = (now - timedelta(days=days_ago, hours=24 - hour)).strftime('%Y-%m-%d %H:%M:%S')
                aqi = max(20, min(300, base_aqi + random.randint(-30, 30) + (days_ago // 3)))
                temp = round(random.uniform(24, 36), 1)
                humidity = round(random.uniform(45, 85), 1)
                cursor.execute(
                    "INSERT INTO environmental_readings (area_id,aqi,temperature,humidity,timestamp,source) VALUES (%s,%s,%s,%s,%s,%s)",
                    (area_id, aqi, temp, humidity, ts, 'simulator'))

