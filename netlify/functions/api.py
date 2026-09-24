import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('NETLIFY', '1')

from serverless_wsgi import handle_request
from database import init_database
from app import app

_db_ready = False


def _ensure_db():
    global _db_ready
    if not _db_ready:
        init_database()
        _db_ready = True


def handler(event, context):
    _ensure_db()
    return handle_request(app, event, context)
