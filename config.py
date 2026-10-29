"""Configuration. Secrets are read from environment variables, never hard-coded."""
import os
import secrets
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SECRET_KEY_IS_TEMPORARY = not os.environ.get("SECRET_KEY")
    DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "payco.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=20)
    MAX_CONTENT_LENGTH = 16 * 1024
    # Simulation rules (educational only)
    STARTING_BALANCE_CENTS = 100_000      # fictional $1,000.00 demo wallet
    MAX_PAYMENT_CENTS = 100_000           # payments above this are declined
    REVIEW_THRESHOLD_CENTS = 50_000       # payments at/above this are flagged for admin review
    MERCHANTS = ("Demo Coffee Shop", "Demo Book Store", "Demo Utility Co", "Demo Charity")
    METHODS = ("Demo Wallet",)            # NO card numbers, CVVs or bank details are ever collected
