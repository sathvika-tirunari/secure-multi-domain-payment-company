"""Service 5: JSON API / backend (read-only). Production idea: api.payco.example"""
from flask import Blueprint, jsonify

from db import get_db
from security import admin_required, current_user, login_required

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health():
    return jsonify(status="ok", demo=True)


@bp.route("/me/transactions")
@login_required
def my_transactions():
    rows = get_db().execute("SELECT ref,merchant,amount_cents,status,reason,created_at FROM transactions "
                            "WHERE user_id=? ORDER BY id DESC LIMIT 50", (current_user()["id"],)).fetchall()
    return jsonify(transactions=[dict(r) for r in rows], simulated=True)


@bp.route("/admin/stats")
@admin_required
def stats():
    r = get_db().execute("SELECT COUNT(*) n, COALESCE(SUM(amount_cents),0) s FROM transactions WHERE status='approved'").fetchone()
    return jsonify(approved_count=r["n"], approved_total_cents=r["s"], simulated=True)
