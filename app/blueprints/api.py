import datetime
import uuid

from flask import Blueprint, jsonify, request, session

from app.models import User, db
from app.services.drive import upload_image
from app.services.gemini import extract_invoice
from app.services.sheets import append_invoice, list_invoices
from app.services.tokens import decrypt_tokens, encrypt_tokens

api_bp = Blueprint("api", __name__)

# Server-side temp storage for images awaiting confirmation (user_id → {img_token: (bytes, mime)})
_pending: dict[str, tuple[bytes, str]] = {}


def _current_user() -> User | None:
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@api_bp.route("/api/extract", methods=["POST"])
def extract():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"error": "missing image"}), 400

    file = request.files["image"]
    image_bytes = file.read()
    mime_type = file.content_type or "image/jpeg"

    fields = extract_invoice(image_bytes, mime_type)
    if fields is None:
        return jsonify({"error": "extraction_failed"}), 422

    img_token = str(uuid.uuid4())
    _pending[img_token] = (image_bytes, mime_type)

    return jsonify({"fields": fields, "img_token": img_token})


@api_bp.route("/api/invoices", methods=["POST"])
def save_invoice():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    img_token = data.pop("img_token", None)
    credentials = decrypt_tokens(user.tokens)

    imagen_url = ""
    if img_token and img_token in _pending:
        image_bytes, mime_type = _pending.pop(img_token)
        ext = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]
        filename = f"factura_{datetime.datetime.now():%Y%m%d_%H%M%S}.{ext}"
        imagen_url = upload_image(credentials, user.drive_folder_id, filename, image_bytes, mime_type)

    row = {**data, "imagen_url": imagen_url, "cargada_el": datetime.datetime.now().isoformat()}
    append_invoice(credentials, user.sheet_id, row)

    user.tokens = encrypt_tokens(credentials)
    user.invoices_this_month += 1
    db.session.commit()

    return jsonify({"ok": True})


@api_bp.route("/api/invoices", methods=["GET"])
def get_invoices():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    month = request.args.get("month")
    credentials = decrypt_tokens(user.tokens)
    invoices = list_invoices(credentials, user.sheet_id, month)

    user.tokens = encrypt_tokens(credentials)
    db.session.commit()

    return jsonify({"invoices": invoices})
