"""
EcoSense - Community Environmental Awareness & Action Platform
Main Flask Application
"""

import base64
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, LIVE_DATA_SOURCE
from database import get_db_connection, init_database
from data_fetcher import (get_cached_or_live_reading, fetch_hourly_history, get_area,
                          prefetch_all_areas, get_all_cities_overview)
import threading
from utils import (get_severity, time_ago, get_data_freshness, analyze_trend,
                   format_report_id, DEMO_SCENARIOS)
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── Auth Decorators ───────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Helper: Get reading with demo mode override ─────────────────

def get_latest_reading(area_id):
    """Fetch live reading from Open-Meteo (or demo scenario if active)."""
    demo = session.get('demo_scenario')
    if demo and demo in DEMO_SCENARIOS:
        scenario = DEMO_SCENARIOS[demo]
        return {
            'aqi': scenario['aqi'], 'temperature': scenario['temperature'],
            'humidity': scenario['humidity'], 'timestamp': datetime.now(),
            'source': 'demo_mode', 'demo': True, 'demo_label': scenario['label'],
        }

    return get_cached_or_live_reading(area_id)


def parse_ts(ts):
    """Parse timestamp from datetime or string (SQLite)."""
    if isinstance(ts, datetime):
        return ts
    return datetime.fromisoformat(str(ts).replace('Z', ''))


def enrich_reading(reading):
    """Add severity, explanations, and freshness info to a reading."""
    if not reading:
        return None
    result = dict(reading)
    ts = parse_ts(reading['timestamp'])
    result['aqi_info'] = get_severity(float(reading['aqi']), 'aqi')
    result['temp_info'] = get_severity(float(reading['temperature']), 'temperature')
    result['humidity_info'] = get_severity(float(reading['humidity']), 'humidity')
    result['freshness'] = get_data_freshness(ts)
    result['time_ago'] = time_ago(ts)
    result['timestamp_str'] = ts.strftime('%d %b %Y, %I:%M %p')
    if reading.get('source') == LIVE_DATA_SOURCE:
        result['source_label'] = 'Live data from Open-Meteo'
    elif reading.get('demo'):
        result['source_label'] = 'Demo scenario (not real data)'
    elif reading.get('api_unavailable'):
        result['source_label'] = 'Last known reading (live feed unavailable)'
    else:
        result['source_label'] = reading.get('source', 'unknown')
    return result


# ─── Page Routes ─────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/trends')
def trends():
    return render_template('trends.html')


@app.route('/report')
@login_required
def report_page():
    return render_template('report.html')


@app.route('/my-reports')
@login_required
def my_reports_page():
    return render_template('my_reports.html')


@app.route('/cities')
def cities_page():
    return render_template('cities.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = get_db_connection()
        if not conn:
            flash('Database unavailable. Please try again.', 'danger')
            return render_template('login.html')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash(f'Welcome, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        conn = get_db_connection()
        if not conn:
            flash('Database unavailable.', 'danger')
            return render_template('register.html')
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,'citizen')",
                (name, email, generate_password_hash(password)))
            conn.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Email already registered.', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['role'] = user['role']
        redirect_to = url_for('admin_dashboard') if user['role'] == 'admin' else url_for('dashboard')
        return jsonify({'success': True, 'redirect': redirect_to})
    return jsonify({'error': 'Invalid email or password.'}), 401


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    if not name or not email or not password:
        return jsonify({'error': 'All fields are required.'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,'citizen')",
            (name, email, generate_password_hash(password)))
        conn.commit()
        return jsonify({'success': True, 'redirect': url_for('login')})
    except Exception:
        return jsonify({'error': 'Email already registered.'}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/api/logout', methods=['GET', 'POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'redirect': url_for('index')})


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Admin Page Routes ─────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')


@app.route('/admin/reports')
@admin_required
def admin_reports_page():
    return render_template('admin/reports.html')


@app.route('/admin/reports/<int:report_id>')
@admin_required
def admin_report_detail(report_id):
    return render_template('admin/report_details.html', report_id=report_id)


@app.route('/admin/areas')
@admin_required
def admin_areas_page():
    return render_template('admin/areas.html')


@app.route('/admin/readings')
@admin_required
def admin_readings_page():
    return render_template('admin/readings.html')


# ─── API Routes ────────────────────────────────────────────────────

@app.route('/api/areas')
def api_areas():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable', 'areas': []}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM areas ORDER BY state, city, name")
    areas = cursor.fetchall()
    states = sorted(set(a['state'] for a in areas if a.get('state')))
    for a in areas:
        if a.get('created_at'):
            a['created_at'] = str(a['created_at'])
    cursor.close()
    conn.close()
    return jsonify({'areas': areas, 'states': states, 'total': len(areas)})


@app.route('/api/cities/overview')
def api_cities_overview():
    refresh = request.args.get('refresh', '') == '1'
    cities = get_all_cities_overview(live_refresh=refresh)
    return jsonify({
        'cities': cities,
        'total': len(cities),
        'source': LIVE_DATA_SOURCE,
        'with_data': sum(1 for c in cities if c.get('aqi')),
    })


@app.route('/api/areas/<int:area_id>/latest')
def api_latest(area_id):
    reading = get_latest_reading(area_id)
    if not reading:
        return jsonify({'error': 'No readings available', 'available': False}), 404
    return jsonify({'reading': enrich_reading(reading), 'available': True})


@app.route('/api/areas/<int:area_id>/history')
def api_history(area_id):
    period = request.args.get('period', '7d')
    param = request.args.get('param', 'aqi')

    period_map = {'24h': 1, '7d': 7, '30d': 30}
    days = period_map.get(period, 7)

    # Fetch real hourly history from Open-Meteo API
    area = get_area(area_id)
    if area and area.get('latitude') and area.get('longitude'):
        history = fetch_hourly_history(area['latitude'], area['longitude'], days, param)
        labels, values = history['labels'], history['values']
        # For 24h view, show only last 24 data points
        if period == '24h' and len(values) > 24:
            labels, values = labels[-24:], values[-24:]
    else:
        labels, values = [], []

    trend = analyze_trend(values, param) if values else {
        'direction': 'stable', 'emoji': '🟡', 'label': 'Stable',
        'summary': 'Not enough data for trend analysis.', 'prev_avg': 0, 'curr_avg': 0, 'change_pct': 0}
    return jsonify({'labels': labels, 'values': values, 'param': param,
                    'period': period, 'trend': trend, 'source': LIVE_DATA_SOURCE})


@app.route('/api/reports', methods=['POST'])
@login_required
def api_submit_report():
    data = request.get_json(silent=True) or {}
    area_id = data.get('area_id') or request.form.get('area_id')
    issue_type = (data.get('issue_type') or request.form.get('issue_type', '')).strip()
    description = (data.get('description') or request.form.get('description', '')).strip()

    if not area_id or not issue_type or not description:
        return jsonify({'error': 'Area, issue type, and description are required.'}), 400

    photo_path = None
    if data.get('photo_data') and data.get('photo_type'):
        ext = data['photo_type'].split('/')[-1] if '/' in data['photo_type'] else 'jpg'
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_photo.{ext}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as photo_file:
            photo_file.write(base64.b64decode(data['photo_data']))
        photo_path = f'uploads/reports/{filename}'
    elif 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_path = f'uploads/reports/{filename}'

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO concern_reports (user_id,area_id,issue_type,description,photo,status) VALUES (%s,%s,%s,%s,%s,'Pending')",
        (session['user_id'], area_id, issue_type, description, photo_path))
    report_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO report_status_history (report_id,status,admin_note,changed_by) VALUES (%s,'Pending','Report submitted by citizen',%s)",
        (report_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'report_id': format_report_id(report_id), 'id': report_id})


@app.route('/api/my-reports')
@login_required
def api_my_reports():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cr.*, a.name as area_name FROM concern_reports cr
        JOIN areas a ON cr.area_id = a.id
        WHERE cr.user_id=%s ORDER BY cr.created_at DESC""", (session['user_id'],))
    reports = cursor.fetchall()
    for r in reports:
        r['report_code'] = format_report_id(r['id'])
        r['created_at'] = str(r['created_at'])
    cursor.close()
    conn.close()
    return jsonify({'reports': reports})


@app.route('/api/reports/<int:report_id>')
@login_required
def api_report_detail(report_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cr.*, a.name as area_name, u.name as user_name FROM concern_reports cr
        JOIN areas a ON cr.area_id = a.id JOIN users u ON cr.user_id = u.id
        WHERE cr.id=%s""", (report_id,))
    report = cursor.fetchone()
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    # Citizens can only view their own reports
    if session.get('role') != 'admin' and report['user_id'] != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    cursor.execute("""
        SELECT h.*, u.name as admin_name FROM report_status_history h
        LEFT JOIN users u ON h.changed_by = u.id
        WHERE h.report_id=%s ORDER BY h.changed_at ASC""", (report_id,))
    history = cursor.fetchall()
    report['report_code'] = format_report_id(report['id'])
    report['created_at'] = str(report['created_at'])
    for h in history:
        h['changed_at'] = str(h['changed_at'])
    cursor.close()
    conn.close()
    return jsonify({'report': report, 'history': history})


@app.route('/api/admin/reports')
@admin_required
def api_admin_reports():
    status_filter = request.args.get('status', '')
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor(dictionary=True)
    query = """SELECT cr.*, a.name as area_name, u.name as user_name FROM concern_reports cr
               JOIN areas a ON cr.area_id=a.id JOIN users u ON cr.user_id=u.id"""
    params = []
    if status_filter:
        query += " WHERE cr.status=%s"
        params.append(status_filter)
    query += " ORDER BY cr.created_at DESC"
    cursor.execute(query, params)
    reports = cursor.fetchall()
    stats = {'total': 0, 'pending': 0, 'reviewed': 0, 'resolved': 0}
    for r in reports:
        r['report_code'] = format_report_id(r['id'])
        r['created_at'] = str(r['created_at'])
        stats['total'] += 1
        stats[r['status'].lower()] = stats.get(r['status'].lower(), 0) + 1
    cursor.close()
    conn.close()
    return jsonify({'reports': reports, 'stats': stats})


@app.route('/api/admin/reports/<int:report_id>', methods=['PUT'])
@admin_required
def api_admin_update_report(report_id):
    data = request.get_json()
    new_status = data.get('status')
    admin_note = data.get('admin_note', '')
    if new_status not in ('Pending', 'Reviewed', 'Resolved'):
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor()
    cursor.execute("UPDATE concern_reports SET status=%s WHERE id=%s", (new_status, report_id))
    cursor.execute(
        "INSERT INTO report_status_history (report_id,status,admin_note,changed_by) VALUES (%s,%s,%s,%s)",
        (report_id, new_status, admin_note, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/demo-mode', methods=['POST', 'DELETE'])
def api_demo_mode():
    if request.method == 'DELETE':
        session.pop('demo_scenario', None)
        return jsonify({'success': True, 'demo': False})
    data = request.get_json()
    scenario = data.get('scenario')
    if scenario and scenario in DEMO_SCENARIOS:
        session['demo_scenario'] = scenario
        return jsonify({'success': True, 'demo': True, 'scenario': DEMO_SCENARIOS[scenario]})
    session.pop('demo_scenario', None)
    return jsonify({'success': True, 'demo': False})


@app.route('/api/demo-scenarios')
def api_demo_scenarios():
    return jsonify({'scenarios': DEMO_SCENARIOS})


@app.route('/api/admin/areas', methods=['POST', 'PUT'])
@admin_required
def api_admin_areas():
    data = request.get_json()
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO areas (name,city,state,description,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s)",
            (data['name'], data['city'], data.get('state', ''), data.get('description', ''),
             data.get('latitude'), data.get('longitude')))
    else:
        cursor.execute(
            "UPDATE areas SET name=%s,city=%s,state=%s,description=%s,latitude=%s,longitude=%s WHERE id=%s",
            (data['name'], data['city'], data.get('state', ''), data.get('description', ''),
             data.get('latitude'), data.get('longitude'), data['id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/readings', methods=['POST'])
@admin_required
def api_admin_add_reading():
    data = request.get_json()
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO environmental_readings (area_id,aqi,temperature,humidity,timestamp,source) VALUES (%s,%s,%s,%s,%s,%s)",
        (data['area_id'], data['aqi'], data['temperature'], data['humidity'],
         data.get('timestamp', datetime.now()), data.get('source', 'manual')))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/session')
def api_session():
    return jsonify({
        'logged_in': 'user_id' in session,
        'user_name': session.get('user_name'),
        'role': session.get('role'),
        'demo_scenario': session.get('demo_scenario'),
    })


# ─── Run Application ───────────────────────────────────────────────

def prefetch_live_data_background():
    """Fetch real-time readings for all cities in background (non-blocking)."""
    def _run():
        print("Background: fetching live data for all Indian cities...")
        count = prefetch_all_areas(max_workers=10)
        print(f"Background: live data updated for {count} cities.")
    threading.Thread(target=_run, daemon=True).start()


if __name__ == '__main__':
    print("Initializing EcoSense database...")
    init_database()
    prefetch_live_data_background()
    print("Starting EcoSense server at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
