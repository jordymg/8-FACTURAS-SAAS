import os

import googleapiclient.discovery
from flask import Blueprint, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow

from app.models import User, db
from app.services.drive import create_invoice_folder
from app.services.sheets import create_spreadsheet
from app.services.tokens import encrypt_tokens

auth_bp = Blueprint("auth", __name__)

_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
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
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    session["oauth_state"] = state
    # Persist PKCE verifier so the callback's fresh Flow can pass it to fetch_token
    if flow.code_verifier:
        session["code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@auth_bp.route("/auth/callback")
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

    userinfo_svc = googleapiclient.discovery.build(
        "oauth2", "v2", credentials=credentials, cache_discovery=False
    )
    userinfo = userinfo_svc.userinfo().get().execute()
    google_sub = userinfo["id"]
    email = userinfo["email"]

    user = User.query.filter_by(google_sub=google_sub).first()
    if not user:
        user = User(google_sub=google_sub, email=email)
        db.session.add(user)
        db.session.flush()
        user.sheet_id = create_spreadsheet(credentials, email)
        user.drive_folder_id = create_invoice_folder(credentials, email)

    user.tokens = encrypt_tokens(credentials)
    db.session.commit()
    session["user_id"] = user.id
    return redirect(url_for("web.app_view"))


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("web.landing"))
