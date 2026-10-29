"""Shared security controls: CSRF, headers, access decorators and input validation."""
import functools
import re
import secrets
from decimal import Decimal, InvalidOperation

from flask import abort, flash, jsonify, redirect, request, session, url_for

from db import get_db

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def register_security(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if not secrets.compare_digest(request.form.get("csrf_token", ""), session.get("csrf", "")):
                abort(400, "Invalid or missing CSRF token.")

    @app.after_request
    def headers(resp):
        resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        if request.is_secure:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp

    for code, msg in ((400, None), (403, "Forbidden: you do not have permission."), (404, "Page not found."),
                      (413, "Request too large."), (429, "Too many attempts. Please wait and try again.")):
        app.register_error_handler(code, _make_handler(code, msg))


def _make_handler(code, fixed):
    def handler(e):
        message = fixed or getattr(e, "description", "Bad request.")
        if request.path.startswith("/api/"):
            return jsonify(error=message), code
        from flask import render_template
        return render_template("error.html", code=code, message=message), code
    return handler


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    row = get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if row is None or not row["active"]:
        session.clear()
        return None
    return row


def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if current_user() is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Authentication required."), 401
            flash("Please log in first.", "error")
            return redirect(url_for("portal.login"))
        return view(*a, **kw)
    return wrapped


def admin_required(view):
    """Role is re-checked in the database on every request (not trusted from the cookie)."""
    @functools.wraps(view)
    @login_required
    def wrapped(*a, **kw):
        if current_user()["role"] != "admin":
            abort(403)
        return view(*a, **kw)
    return wrapped


def parse_amount_cents(text):
    """'12.50' -> 1250. Rejects non-numbers, NaN/inf, negatives, zero and >2 decimal places."""
    try:
        d = Decimal(text.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Amount must be a number like 12.50.")
    if not d.is_finite() or d <= 0:
        raise ValueError("Amount must be greater than zero.")
    if d != d.quantize(Decimal("0.01")):
        raise ValueError("Amount can have at most 2 decimal places.")
    if d > Decimal("1000000"):
        raise ValueError("Amount is too large.")
    return int(d * 100)


def money(cents):
    return f"${cents / 100:,.2f}"
