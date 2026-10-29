"""Service 1: main company website (public, static content). Production idea: www.payco.example"""
from flask import Blueprint, render_template

bp = Blueprint("site", __name__)


@bp.route("/")
def home():
    return render_template("site/home.html")


@bp.route("/about")
def about():
    return render_template("site/about.html")
