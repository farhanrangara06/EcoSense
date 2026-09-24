"""Build static site and API data for Netlify deployment."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flask import render_template

from app import app
from indian_cities import INDIAN_CITIES

PUBLIC = ROOT / 'public'
DATA_DIR = ROOT / 'netlify' / 'functions' / 'data'


def build_areas_data():
    areas = [
        {
            'id': i + 1,
            'name': city[0],
            'city': city[1],
            'state': city[2],
            'description': city[3],
            'latitude': city[4],
            'longitude': city[5],
        }
        for i, city in enumerate(INDIAN_CITIES)
    ]
    states = sorted({area['state'] for area in areas})
    payload = {'areas': areas, 'states': states, 'total': len(areas)}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'areas.json').write_text(json.dumps(payload), encoding='utf-8')
    lib_data = ROOT / 'lib' / 'data'
    lib_data.mkdir(parents=True, exist_ok=True)
    (lib_data / 'areas.json').write_text(json.dumps(payload), encoding='utf-8')
    return payload


def build_static_pages():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    if (ROOT / 'static').exists():
        shutil.copytree(ROOT / 'static', PUBLIC / 'static')

    headers_src = ROOT / 'netlify' / '_headers'
    if headers_src.exists():
        shutil.copy2(headers_src, PUBLIC / '_headers')

    template_map = {
        'index.html': 'index.html',
        'dashboard.html': 'dashboard.html',
        'trends.html': 'trends.html',
        'cities.html': 'cities.html',
        'login.html': 'login.html',
        'register.html': 'register.html',
        'logout.html': 'logout.html',
        'report.html': 'report.html',
        'my-reports.html': 'my_reports.html',
        'admin.html': 'admin/dashboard.html',
        'admin/reports.html': 'admin/reports.html',
        'admin/areas.html': 'admin/areas.html',
        'admin/readings.html': 'admin/readings.html',
        'admin/report-details.html': 'admin/report_details.html',
    }

    with app.test_request_context('/'):
        for outfile, template in template_map.items():
            outpath = PUBLIC / outfile
            outpath.parent.mkdir(parents=True, exist_ok=True)
            if template == 'admin/report_details.html':
                html = render_template(template, report_id=1)
            else:
                html = render_template(template)
            outpath.write_text(html, encoding='utf-8')
            print(f'Built {outfile}')


def main():
    build_areas_data()
    build_static_pages()
    print('Netlify build complete.')


if __name__ == '__main__':
    main()
