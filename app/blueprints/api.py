import datetime
import uuid

from flask import Blueprint, jsonify, request, session

from app.models import User, db
from app.services import sheets, storage
from app.services.fields import FIELD_KEYS
from app.services.gemini import extract_invoice

api_bp = Blueprint("api", __name__)

# Server-side temp storage for images awaiting confirmation (img_token → (bytes, mime))
_pending: dict[str, tuple[bytes, str]] = {}


def _current_user() -> User | None:
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@api_bp.route("/api/sheet/connect", methods=["POST"])
def connect_sheet():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    try:
        spreadsheet_id = sheets.connect_spreadsheet(data.get("planilla", ""))
    except sheets.SheetAccessError as e:
        return jsonify({"ok": False, "error": str(e)})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)})

    user.spreadsheet_id = spreadsheet_id
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/api/extract", methods=["POST"])
def extract():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    files = request.files.getlist("archivos") or request.files.getlist("image")
    if not files:
        return jsonify({"error": "missing files"}), 400

    resultados = []
    for file in files:
        mime_type = file.content_type or "image/jpeg"
        if mime_type not in ("image/jpeg", "image/png", "image/webp", "application/pdf"):
            resultados.append({"nombre": file.filename, "ok": False,
                                "error": f"Formato no soportado ({mime_type})"})
            continue
        image_bytes = file.read()
        try:
            fields = extract_invoice(image_bytes, mime_type)
        except Exception as e:
            resultados.append({"nombre": file.filename, "ok": False, "error": str(e)})
            continue

        img_token = str(uuid.uuid4())
        _pending[img_token] = (image_bytes, mime_type)
        resultados.append({"nombre": file.filename, "ok": True, "fields": fields, "img_token": img_token})

    return jsonify(resultados)


@api_bp.route("/api/invoices", methods=["POST"])
def save_invoice():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if not user.spreadsheet_id:
        return jsonify({"ok": False, "error": "No hay planilla configurada. Andá a Configuración."}), 400

    data = request.get_json(force=True)
    img_token = data.pop("img_token", None)

    imagen = ""
    if img_token and img_token in _pending:
        image_bytes, mime_type = _pending.pop(img_token)
        imagen = storage.save_image(user.id, image_bytes, mime_type, datetime.datetime.now())

    row = {key: data.get(key, "") for key in FIELD_KEYS}
    row["imagen"] = imagen
    row["cargada_el"] = datetime.datetime.now().isoformat()

    try:
        sheets.append_invoice(user.spreadsheet_id, row)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502

    user.invoices_this_month += 1
    db.session.commit()

    return jsonify({"ok": True})


@api_bp.route("/api/invoices", methods=["GET"])
def get_invoices():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if not user.spreadsheet_id:
        return jsonify({"invoices": []})

    month = request.args.get("month")
    invoices = sheets.list_invoices(user.spreadsheet_id, month)
    return jsonify({"invoices": invoices})
