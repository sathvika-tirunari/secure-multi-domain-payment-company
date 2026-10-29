"""Service 2: customer portal (register, login, dashboard). Production idea: portal.payco.example"""
import sqlite3
import time

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import audit, get_db
from security import EMAIL_RE, USERNAME_RE, current_user, login_required, money

bp = Blueprint("portal", __name__, url_prefix="/portal")
_failed = {}  # (ip, username) -> (count, first_time); in-memory throttle for the demo
MAX_ATTEMPTS, LOCK_SECONDS = 5, 300


def password_errors(pw):
    errs = []
    if not 10 <= len(pw) <= 128:
        errs.append("Password must be 10-128 characters long.")
    if not (any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw)):
        errs.append("Password needs at least one letter and one number.")
    return errs


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        e = request.form.get("email", "").strip().lower()
        p, c = request.form.get("password", ""), request.form.get("confirm", "")
        errs = []
        if not USERNAME_RE.match(u):
            errs.append("Username must be 3-30 letters, numbers or underscores.")
        if len(e) > 254 or not EMAIL_RE.match(e):
            errs.append("Enter a valid email address.")
        errs += password_errors(p)
        if p != c:
            errs.append("Password and confirmation do not match.")
        if not errs:
            try:
                db = get_db()
                cur = db.execute(
                    "INSERT INTO users (username,email,password_hash,role,balance_cents) VALUES (?,?,?,'customer',?)",
                    (u, e, generate_password_hash(p), current_app.config["STARTING_BALANCE_CENTS"]))
                db.commit()
                audit("register", cur.lastrowid, u)
                flash("Account created. Please log in.", "success")
                return redirect(url_for("portal.login"))
            except sqlite3.IntegrityError:
                errs.append("That username or email is already registered.")
        for m in errs:
            flash(m, "error")
        return render_template("portal/register.html", username=u, email=e), 400
    return render_template("portal/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username", "").strip(), request.form.get("password", "")
        key = (request.remote_addr, u.lower())
        count, first = _failed.get(key, (0, 0))
        if count >= MAX_ATTEMPTS and time.time() - first < LOCK_SECONDS:
            audit("login_blocked", None, u)
            abort(429)
        row = get_db().execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if row and row["active"] and check_password_hash(row["password_hash"], p):
            _failed.pop(key, None)
            session.clear()
            session.permanent = True
            session["user_id"] = row["id"]
            audit("login_ok", row["id"])
            return redirect(url_for("admin.dashboard") if row["role"] == "admin" else url_for("portal.dashboard"))
        if time.time() - first >= LOCK_SECONDS:
            count, first = 0, time.time()
        _failed[key] = (count + 1, first or time.time())
        audit("login_failed", row["id"] if row else None, u)
        flash("Invalid username or password, or the account is disabled.", "error")
        return render_template("portal/login.html", username=u), 401
    return render_template("portal/login.html")


@bp.route("/")
@login_required
def dashboard():
    user = current_user()
    txs = get_db().execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 10", (user["id"],)).fetchall()
    return render_template("portal/dashboard.html", user=user, txs=txs, money=money)


@bp.route("/logout", methods=["POST"])
def logout():
    audit("logout", session.get("user_id"))
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("site.home"))
