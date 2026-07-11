import json
import os

from flask import Blueprint, redirect, render_template, session, url_for

from app.models import User, db
from app.services import sheets
from app.services.fields import FIELDS
from app.services.tips import get_tips

web_bp = Blueprint("web", __name__)

_STRINGS_PATH = os.path.join(os.path.dirname(__file__), "../../strings/es.json")


def _strings() -> dict:
    with open(os.path.normpath(_STRINGS_PATH), encoding="utf-8") as f:
        return json.load(f)


def _current_user() -> User | None:
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@web_bp.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("web.app_view"))
    return render_template("landing.html")


@web_bp.route("/app")
def app_view():
    user = _current_user()
    if not user:
        return redirect(url_for("web.landing"))
    if not user.spreadsheet_id:
        return redirect(url_for("web.config_view"))
    return render_template(
        "app.html", user=user, strings=_strings(),
        campos_json=json.dumps(FIELDS, ensure_ascii=False),
        tips_json=json.dumps(get_tips(), ensure_ascii=False),
    )


@web_bp.route("/app/config")
def config_view():
    user = _current_user()
    if not user:
        return redirect(url_for("web.landing"))
    return render_template("config.html", user=user, sa_email=sheets.sa_email(), strings=_strings())
