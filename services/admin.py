"""Service 4: admin portal (role-based access). Production idea: admin.payco.example, ideally on a restricted network."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from db import audit, get_db
from security import admin_required, money

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    stats = db.execute("""SELECT (SELECT COUNT(*) FROM users) users, (SELECT COUNT(*) FROM transactions) txs,
        (SELECT COUNT(*) FROM transactions WHERE flagged=1) flagged,
        (SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE status='approved') volume""").fetchone()
    users = db.execute("SELECT id,username,email,role,active,balance_cents FROM users ORDER BY id").fetchall()
    txs = db.execute("SELECT t.*, u.username FROM transactions t JOIN users u ON u.id=t.user_id ORDER BY t.id DESC LIMIT 25").fetchall()
    logs = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 25").fetchall()
    return render_template("admin/dashboard.html", stats=stats, users=users, txs=txs, logs=logs, money=money)


@bp.route("/users/<int:user_id>/active", methods=["POST"])
@admin_required
def set_active(user_id):
    if user_id == session["user_id"]:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("admin.dashboard"))
    value = 1 if request.form.get("active") == "1" else 0
    db = get_db()
    if db.execute("UPDATE users SET active=? WHERE id=?", (value, user_id)).rowcount == 0:
        abort(404)
    db.commit()
    audit("admin_set_active", session["user_id"], f"user={user_id} active={value}")
    flash("Account updated.", "success")
    return redirect(url_for("admin.dashboard"))
