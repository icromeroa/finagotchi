import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app, g

from database import init_db

BOGOTA = timezone(timedelta(hours=-5), name="America/Bogota")
ACCESS_TOKEN_MAX_AGE = 60 * 60
REFRESH_TOKEN_DAYS = 30


def now_utc():
    return datetime.now(timezone.utc)


def iso_utc(moment=None):
    moment = moment or now_utc()
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_date(moment=None):
    moment = moment or now_utc()
    return moment.astimezone(BOGOTA).date().isoformat()


def local_date_from_timestamp(value):
    if not value:
        return local_date()
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return local_date()
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(BOGOTA).date().isoformat()


def token_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_token():
    return secrets.token_urlsafe(48)


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        if not Path(path).exists() and str(path) != ":memory:":
            init_db.init_sqlite(path)
        g.db = init_db.connect(path)
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def dict_row(row):
    return dict(row) if row is not None else None


def dict_rows(rows):
    return [dict(row) for row in rows]


def clamp(value, low=0, high=100):
    return max(low, min(high, int(value)))


def init_app(app):
    app.teardown_appcontext(close_db)
