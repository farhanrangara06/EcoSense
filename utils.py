"""Utility functions: severity classification, trend analysis, time helpers."""

from datetime import datetime
from config import AQI_THRESHOLDS, TEMP_THRESHOLDS, HUMIDITY_THRESHOLDS, DATA_FRESH_MINUTES, DATA_STALE_MINUTES

SEVERITY_INFO = {
    'good': {'label': 'Good', 'emoji': '🟢', 'class': 'severity-good'},
    'moderate': {'label': 'Moderate', 'emoji': '🟡', 'class': 'severity-moderate'},
    'poor': {'label': 'Poor', 'emoji': '🟠', 'class': 'severity-poor'},
    'hazardous': {'label': 'Hazardous', 'emoji': '🔴', 'class': 'severity-hazardous'},
}

AQI_EXPLANATIONS = {
    'good': 'Air quality is currently good.',
    'moderate': 'Air quality is acceptable, but some people may notice discomfort.',
    'poor': 'Air quality is poor. Sensitive people should consider reducing prolonged outdoor activity.',
    'hazardous': 'Air pollution is very high. Follow local health guidance and avoid unnecessary outdoor exposure.',
}

TEMP_EXPLANATIONS = {
    'good': 'Temperature is comfortable for most outdoor activities.',
    'moderate': 'Temperature is warm. Stay hydrated during outdoor activity.',
    'poor': 'It is quite hot. Limit prolonged outdoor exposure.',
    'hazardous': 'Extreme heat conditions. Avoid outdoor activity if possible.',
}

HUMIDITY_EXPLANATIONS = {
    'good': 'Humidity levels are within a normal range.',
    'moderate': 'Humidity is slightly elevated but generally acceptable.',
    'poor': 'Humidity is high. It may feel uncomfortable outdoors.',
    'hazardous': 'Very high humidity. Take precautions in hot conditions.',
}

DEMO_SCENARIOS = {
    'normal': {'aqi': 45, 'temperature': 28, 'humidity': 55, 'label': 'Normal Conditions'},
    'pollution_spike': {'aqi': 187, 'temperature': 32, 'humidity': 72, 'label': 'Pollution Spike'},
    'severe_pollution': {'aqi': 250, 'temperature': 31, 'humidity': 68, 'label': 'Severe Pollution'},
    'hot_weather': {'aqi': 95, 'temperature': 39, 'humidity': 45, 'label': 'Hot Weather'},
    'high_humidity': {'aqi': 110, 'temperature': 30, 'humidity': 90, 'label': 'High Humidity'},
}


def classify_value(value, thresholds):
    """Classify a numeric value into good/moderate/poor/hazardous."""
    for level, (low, high) in thresholds.items():
        if low <= value <= high:
            return level
    return 'hazardous'


def get_severity(value, param_type):
    """Return full severity info for an environmental parameter."""
    thresholds = {'aqi': AQI_THRESHOLDS, 'temperature': TEMP_THRESHOLDS, 'humidity': HUMIDITY_THRESHOLDS}
    explanations = {'aqi': AQI_EXPLANATIONS, 'temperature': TEMP_EXPLANATIONS, 'humidity': HUMIDITY_EXPLANATIONS}
    level = classify_value(value, thresholds[param_type])
    info = SEVERITY_INFO[level]
    return {
        'level': level,
        'label': info['label'],
        'emoji': info['emoji'],
        'class': info['class'],
        'explanation': explanations[param_type][level],
    }


def time_ago(dt):
    """Return human-readable time difference from now."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', ''))
    diff = datetime.now() - dt
    minutes = int(diff.total_seconds() / 60)
    if minutes < 1:
        return 'just now'
    if minutes < 60:
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    hours = minutes // 60
    if hours < 24:
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    days = hours // 24
    return f'{days} day{"s" if days != 1 else ""} ago'


def get_data_freshness(dt):
    """Determine if data is live, stale, or outdated."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(str(dt).replace('Z', ''))
    minutes = int((datetime.now() - dt).total_seconds() / 60)
    if minutes <= DATA_FRESH_MINUTES:
        return {'status': 'live', 'message': time_ago(dt), 'warning': False}
    if minutes <= DATA_STALE_MINUTES:
        return {'status': 'stale', 'message': time_ago(dt), 'warning': True,
                'warning_text': 'Data may be outdated'}
    return {'status': 'outdated', 'message': time_ago(dt), 'warning': True,
            'warning_text': 'Live data temporarily unavailable'}


def analyze_trend(values, param_type='aqi'):
    """Simple trend analysis comparing first half vs second half of values."""
    if len(values) < 2:
        return {'direction': 'stable', 'emoji': '🟡', 'label': 'Stable',
                'summary': 'Not enough data for trend analysis.', 'prev_avg': 0, 'curr_avg': 0, 'change_pct': 0}

    mid = len(values) // 2
    prev_avg = sum(values[:mid]) / mid if mid > 0 else values[0]
    curr_avg = sum(values[mid:]) / (len(values) - mid)

    if prev_avg == 0:
        change_pct = 0
    else:
        change_pct = round(((curr_avg - prev_avg) / prev_avg) * 100, 1)

    # For AQI/temp/humidity high values = worse (except we want improving when values decrease for aqi)
    higher_is_worse = param_type in ('aqi', 'temperature', 'humidity')

    if abs(change_pct) < 5:
        return {'direction': 'stable', 'emoji': '🟡', 'label': 'Stable',
                'summary': f'{param_type.upper()} has remained relatively stable.',
                'prev_avg': round(prev_avg, 1), 'curr_avg': round(curr_avg, 1), 'change_pct': change_pct}

    if higher_is_worse:
        if curr_avg > prev_avg:
            direction, emoji, label = 'worsening', '🔴', 'Worsening'
            summary = f'Average {param_type.upper()} increased from {round(prev_avg)} to {round(curr_avg)}.'
        else:
            direction, emoji, label = 'improving', '🟢', 'Improving'
            summary = f'Average {param_type.upper()} decreased from {round(prev_avg)} to {round(curr_avg)}.'
    else:
        direction, emoji, label = 'stable', '🟡', 'Stable'
        summary = f'{param_type.upper()} has remained relatively stable.'

    return {'direction': direction, 'emoji': emoji, 'label': label, 'summary': summary,
            'prev_avg': round(prev_avg, 1), 'curr_avg': round(curr_avg, 1), 'change_pct': change_pct}


def format_report_id(report_id):
    """Format report ID as EW-001."""
    return f'EW-{report_id:03d}'
