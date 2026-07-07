import datetime
import os

from flask import Blueprint, jsonify, request, session

from app.models import User, db
from app.services import sheets
from app.services.fields import FIELD_KEYS
from app.services.formats import MIME_EXTENSIONS
from app.services.gemini import extract_invoice

api_bp = Blueprint("api", __name__)


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
    except (sheets.SheetAccessError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)})

    user.spreadsheet_id = spreadsheet_id
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/api/extract", methods=["POST"])
def extract():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if "GEMINI_API_KEY" not in os.environ:
        return jsonify({"error": "Gemini no está configurado (falta GEMINI_API_KEY)."}), 500

    files = request.files.getlist("archivos") or request.files.getlist("image")
    if not files:
        return jsonify({"error": "missing files"}), 400

    # Se lee la planilla una sola vez por lote (no por archivo) para chequear
    # duplicados (ADR-0009) — evita releer todo el Sheet varias veces si se
    # suben varias fotos juntas.
    invoices_existentes = sheets.list_invoices(user.spreadsheet_id) if user.spreadsheet_id else []
    # Además del Sheet, dos fotos de la MISMA tanda pueden ser la misma
    # factura (ninguna está guardada todavía, así que find_duplicate contra
    # el Sheet no las vería entre sí).
    vistos_en_lote = set()

    resultados = []
    for file in files:
        mime_type = file.content_type or "image/jpeg"
        if mime_type not in MIME_EXTENSIONS:
            resultados.append({"nombre": file.filename, "ok": False,
                                "error": f"Formato no soportado ({mime_type})"})
            continue
        # MVP sin persistencia: la imagen se lee en memoria solo para mandarla
        # a Gemini y se descarta acá — no se guarda en ningún lado.
        image_bytes = file.read()
        try:
            fields = extract_invoice(image_bytes, mime_type)
        except Exception as e:
            resultados.append({"nombre": file.filename, "ok": False, "error": str(e)})
            continue

        # campos_inciertos no es un dato del comprobante — es la señal de duda
        # de la IA (ADR-0007), se manda aparte para que el frontend resalte
        # esos campos en rojo en vez de tratarlos como un valor más.
        inciertos = fields.pop("campos_inciertos", [])
        duplicado = sheets.find_duplicate(
            invoices_existentes, fields.get("proveedor"), fields.get("numero"), fields.get("fecha")
        )
        if not duplicado and fields.get("proveedor") and fields.get("numero") and fields.get("fecha"):
            clave = (
                sheets.norm_text(fields["proveedor"]),
                sheets.norm_id(fields["numero"]),
                str(fields["fecha"]).strip(),
            )
            if clave in vistos_en_lote:
                duplicado = "__MISMA_TANDA__"  # ver static/js/app.js: mensaje distinto al de un duplicado en el Sheet
            vistos_en_lote.add(clave)
        resultados.append({
            "nombre": file.filename, "ok": True, "fields": fields,
            "inciertos": inciertos, "duplicado": duplicado,
        })

    return jsonify(resultados)


@api_bp.route("/api/invoices", methods=["POST"])
def save_invoice():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if not user.spreadsheet_id:
        return jsonify({"ok": False, "error": "No hay planilla configurada. Andá a Configuración."}), 400

    data = request.get_json(force=True)
    row = {key: data.get(key, "") for key in FIELD_KEYS}
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
