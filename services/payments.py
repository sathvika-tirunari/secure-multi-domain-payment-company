"""Service 3: MOCK payment application. Production idea: pay.payco.example

SIMULATION ONLY. No card numbers, CVVs, bank logins or real payment data are collected,
and no real financial service is contacted. Outcomes come from simple local rules.
"""
import secrets

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from db import audit, get_db
from security import current_user, login_required, money, parse_amount_cents

bp = Blueprint("pay", __name__, url_prefix="/pay")


def simulate_payment(user, amount_cents, cfg):
    """Return (status, reason, flagged). Pure local rules."""
    if amount_cents > cfg["MAX_PAYMENT_CENTS"]:
        return "declined", "Over the demo per-payment limit.", 0
    if amount_cents > user["balance_cents"]:
        return "declined", "Insufficient demo balance.", 0
    return "approved", "Approved (simulated).", int(amount_cents >= cfg["REVIEW_THRESHOLD_CENTS"])


@bp.route("/", methods=["GET", "POST"])
@login_required
def new_payment():
    user = current_user()
    cfg = current_app.config
    if request.method == "POST":
        merchant = request.form.get("merchant", "")
        method = request.form.get("method", "")
        note = request.form.get("note", "").strip()
        errs = []
        try:
            cents = parse_amount_cents(request.form.get("amount", ""))
        except ValueError as exc:
            cents = None
            errs.append(str(exc))
        if merchant not in cfg["MERCHANTS"]:
            errs.append("Choose a merchant from the list.")
        if method not in cfg["METHODS"]:
            errs.append("Choose a payment method from the list.")
        if len(note) > 100:
            errs.append("Note must be 100 characters or fewer.")
        if errs:
            for m in errs:
                flash(m, "error")
            return render_template("pay/form.html", user=user, cfg=cfg, money=money), 400
        status, reason, flagged = simulate_payment(user, cents, cfg)
        ref = "SIM-" + secrets.token_hex(6).upper()
        db = get_db()
        db.execute("INSERT INTO transactions (ref,user_id,merchant,method,note,amount_cents,status,reason,flagged) "
                   "VALUES (?,?,?,?,?,?,?,?,?)", (ref, user["id"], merchant, method, note, cents, status, reason, flagged))
        if status == "approved":
            db.execute("UPDATE users SET balance_cents = balance_cents - ? WHERE id=?", (cents, user["id"]))
        db.commit()
        audit("payment_" + status, user["id"], f"{ref} {cents}")
        flash(f"{ref}: {status.upper()} - {reason}", "success" if status == "approved" else "error")
        return redirect(url_for("portal.dashboard"))
    return render_template("pay/form.html", user=user, cfg=cfg, money=money)
