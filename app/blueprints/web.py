import json
import os

from flask import Blueprint, redirect, render_template, session, url_for

from app.models import User, db

web_bp = Blueprint("web", __name__)

_STRINGS_PATH = os.path.join(os.path.dirname(__file__), "../../strings/es.json")


def _strings() -> dict:
    with open(os.path.normpath(_STRINGS_PATH), encoding="utf-8") as f:
        return json.load(f)


@web_bp.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("web.app_view"))
    return render_template("landing.html")


@web_bp.route("/app")
def app_view():
    if not session.get("user_id"):
        return redirect(url_for("web.landing"))
    user = db.session.get(User, session["user_id"])
    return render_template("app.html", user=user, strings=_strings())
