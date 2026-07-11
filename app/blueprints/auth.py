import datetime
import os

import requests
from flask import Blueprint, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow

from app.models import User, db

auth_bp = Blueprint("auth", __name__)

# Login solo para identificar al usuario (email). El acceso a Sheets lo hace
# la Service Account, no el usuario — no pedimos scopes sensibles acá.
_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _flow(redirect_uri: str) -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=_SCOPES,
        redirect_uri=redirect_uri,
    )


@auth_bp.route("/auth/google")
def google_login():
    flow = _flow(url_for("auth.google_callback", _external=True))
    # nota: el redirect_uri debe coincidir EXACTO con el registrado en
    # Google Cloud Console para este client_id (ver docs/decisions/0004).
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    session["oauth_state"] = state
    if flow.code_verifier:
        session["code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@auth_bp.route("/oauth2callback")
def google_callback():
    if request.args.get("state") != session.pop("oauth_state", None):
        return "State mismatch — possible CSRF", 400

    flow = _flow(url_for("auth.google_callback", _external=True))
    code_verifier = session.pop("code_verifier", None)
    flow.fetch_token(
        authorization_response=request.url,
        **({"code_verifier": code_verifier} if code_verifier else {}),
    )
    credentials = flow.credentials

    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=5,
    ).json()
    google_sub = userinfo["id"]
    email = userinfo["email"]

    user = User.query.filter_by(google_sub=google_sub).first()
    if not user:
        # created_at ancla el ciclo mensual del tope de facturas (ADR-0008).
        user = User(google_sub=google_sub, email=email, created_at=datetime.date.today())
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for("web.app_view"))


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("web.landing"))
