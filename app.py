"""Secure Multi-Domain Payment Company: EDUCATIONAL DEMO. Simulated payments only.

Run:  python app.py   then open http://127.0.0.1:5000
"""
import os

from flask import Flask

import db
from config import Config
from security import register_security
from services import admin, api, payments, portal, site


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    if app.config["SECRET_KEY_IS_TEMPORARY"]:
        print("NOTE: SECRET_KEY not set; using a temporary random key (sessions reset on restart).")
    register_security(app)
    for module in (site, portal, payments, admin, api):
        app.register_blueprint(module.bp)
    db.init_db(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
