"""SQLite helpers, schema and audit logging."""
import os
import secrets
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer','admin')),
    active INTEGER NOT NULL DEFAULT 1, balance_cents INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT NOT NULL UNIQUE, user_id INTEGER NOT NULL REFERENCES users(id),
    merchant TEXT NOT NULL, method TEXT NOT NULL, note TEXT, amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('approved','declined')), reason TEXT,
    flagged INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, user_id INTEGER, detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db:
        db.close()


def audit(event, user_id=None, detail=""):
    """Write a security-relevant event. Never put passwords or secrets in `detail`."""
    get_db().execute("INSERT INTO audit_log (event, user_id, detail) VALUES (?,?,?)", (event, user_id, detail[:200]))
    get_db().commit()


def init_db(app):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.executescript(SCHEMA)
        if not db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            pw = os.environ.get("DEMO_ADMIN_PASSWORD")
            generated = pw is None
            pw = pw or secrets.token_urlsafe(12)
            db.execute("INSERT INTO users (username,email,password_hash,role,balance_cents) VALUES (?,?,?,?,0)",
                       ("admin", "admin@payco.invalid", generate_password_hash(pw), "admin"))
            if generated:
                print(f"\n*** First run: admin account created. Username: admin  Password: {pw}\n"
                      "*** Save it now; it is not stored in plain text.\n")
    app.teardown_appcontext(close_db)
