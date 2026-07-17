import datetime
import os
import time

from flask import Blueprint, jsonify, request, session

from app.models import User, db
from app.services import sheets, tiempos
from app.services.fields import FIELD_KEYS
from app.services.formats import MIME_EXTENSIONS
from app.services.gemini import extract_invoice
from app.services.limites import LIMITE_MENSUAL, UMBRAL_AVISO, facturas_del_mes, registrar_factura_cargada

api_bp = Blueprint("api", __name__)


def _current_user() -> User | None:
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@api_bp.route("/health", methods=["GET"])
def health():
    # Respuesta estática e instantánea, sin DB/Sheets/Gemini — el único
    # propósito es que Render vea tráfico entrante (ver ADR-0013,
    # keep-alive vía GitHub Actions cron).
    return jsonify({"status": "ok"})


@api_bp.route("/api/sheet/connect", methods=["POST"])
def connect_sheet():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    try:
        spreadsheet_id, titulo = sheets.connect_spreadsheet(data.get("planilla", ""))
    except (sheets.SheetAccessError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)})

    # El título elegido por el usuario solo se aplica en la primera
    # conexión — si ya tenía una planilla conectada antes, no le pisamos un
    # nombre que ya haya elegido a mano (ADR-0005 área App). El año lo
    # agrega el sistema, el usuario solo escribe el nombre base.
    es_primera_conexion = not user.spreadsheet_id
    nombre_elegido = (data.get("titulo") or "").strip()
    if es_primera_conexion and nombre_elegido:
        titulo_nuevo = f"{nombre_elegido} {datetime.date.today().year}"
        titulo = sheets.rename_spreadsheet(spreadsheet_id, titulo, titulo_nuevo)

    # La pestaña del año actual se crea al conectar (ADR-0003 área
    # Planillas: una sola pestaña por año calendario, ej. "2026" — no una
    # por mes). Si falla, no corta la conexión: el usuario queda igual
    # conectado con sheet1 funcionando.
    if es_primera_conexion:
        if not user.created_at:
            user.created_at = datetime.date.today()
        try:
            sheets.asegurar_pestana_del_anio(spreadsheet_id, datetime.date.today())
        except Exception:
            pass

    user.spreadsheet_id = spreadsheet_id
    user.spreadsheet_title = titulo
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/api/extract", methods=["POST"])
def extract():
    t_request_inicio = time.monotonic()
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if "GEMINI_API_KEY" not in os.environ:
        return jsonify({"error": "Nuestro sistema no está disponible en este momento. Probá de nuevo en unos minutos."}), 500

    files = request.files.getlist("archivos") or request.files.getlist("image")
    if not files:
        return jsonify({"error": "missing files"}), 400

    # Se lee la planilla una sola vez por lote (no por archivo) para chequear
    # duplicados (ADR-0009) — evita releer todo el Sheet varias veces si se
    # suben varias fotos juntas.
    t_lectura_inicio = time.monotonic()
    invoices_existentes = sheets.list_invoices(user.spreadsheet_id) if user.spreadsheet_id else []
    duracion_lectura_planilla = time.monotonic() - t_lectura_inicio
    # Además del Sheet, dos fotos de la MISMA tanda pueden ser la misma
    # factura (ninguna está guardada todavía, así que find_duplicate contra
    # el Sheet no las vería entre sí).
    vistos_en_lote = set()

    resultados = []
    total_fotos = len(files)
    for idx, file in enumerate(files, start=1):
        t_foto_inicio = time.monotonic()
        mime_type = file.content_type or "image/jpeg"
        if mime_type not in MIME_EXTENSIONS:
            resultados.append({"nombre": file.filename, "ok": False,
                                "error": f"Formato no soportado ({mime_type})"})
            continue
        # MVP sin persistencia: la imagen se lee en memoria solo para mandarla
        # a Gemini y se descarta acá — no se guarda en ningún lado.
        image_bytes = file.read()
        tamano_mb = len(image_bytes) / (1024 * 1024)
        duracion_recepcion = time.monotonic() - t_foto_inicio
        try:
            fields, tiempos_gemini = extract_invoice(image_bytes, mime_type)
        except Exception as e:
            resultados.append({"nombre": file.filename, "ok": False, "error": str(e)})
            tiempos.log(
                f"TIEMPOS extract [{idx}/{total_fotos}] — imagen: {tamano_mb:.1f}MB | "
                f"recepción: {duracion_recepcion:.2f}s | gemini: error | "
                f"total: {time.monotonic() - t_foto_inicio:.2f}s"
            )
            continue

        # campos_inciertos no es un dato del comprobante — es la señal de duda
        # de la IA (ADR-0007), se manda aparte para que el frontend resalte
        # esos campos en rojo en vez de tratarlos como un valor más.
        inciertos = fields.pop("campos_inciertos", [])
        t_dup_inicio = time.monotonic()
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
        duracion_duplicados = time.monotonic() - t_dup_inicio
        resultados.append({
            "nombre": file.filename, "ok": True, "fields": fields,
            "inciertos": inciertos, "duplicado": duplicado,
        })

        tiempos.log(
            f"TIEMPOS extract [{idx}/{total_fotos}] — imagen: {tamano_mb:.1f}MB | "
            f"recepción: {duracion_recepcion:.2f}s | "
            f"gemini: {tiempos_gemini['duracion_total']:.2f}s "
            f"(reintentos: {tiempos_gemini['reintentos']}, "
            f"último intento: {tiempos_gemini['duracion_ultimo_intento']:.2f}s) | "
            f"duplicados: {duracion_duplicados:.2f}s | "
            f"total: {time.monotonic() - t_foto_inicio:.2f}s"
        )

    tiempos.log(
        f"TIEMPOS extract lote — fotos: {total_fotos} | "
        f"lectura_planilla: {duracion_lectura_planilla:.2f}s | "
        f"total_lote: {time.monotonic() - t_request_inicio:.2f}s"
    )

    return jsonify(resultados)


@api_bp.route("/api/invoices", methods=["POST"])
def save_invoice():
    t_request_inicio = time.monotonic()
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if not user.spreadsheet_id:
        return jsonify({"ok": False, "error": "No hay planilla configurada. Andá a Configuración."}), 400

    data = request.get_json(force=True)
    row = {key: data.get(key, "") for key in FIELD_KEYS}
    row["cargada_el"] = datetime.datetime.now().isoformat()

    t_sheet_inicio = time.monotonic()
    try:
        pestana_creada = sheets.append_invoice(user.spreadsheet_id, row)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    duracion_sheet = time.monotonic() - t_sheet_inicio

    registrar_factura_cargada(user)
    db.session.commit()

    tiempos.log(
        f"TIEMPOS invoices — sheet: {duracion_sheet:.2f}s"
        f"{' (pestaña del año creada en este guardado)' if pestana_creada else ''} | "
        f"total: {time.monotonic() - t_request_inicio:.2f}s"
    )

    return jsonify({"ok": True})


@api_bp.route("/api/invoices", methods=["GET"])
def get_invoices():
    user = _current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if not user.spreadsheet_id:
        return jsonify({
            "invoices": [], "facturas_mes": facturas_del_mes(user),
            "limite_mensual": LIMITE_MENSUAL, "umbral_aviso": UMBRAL_AVISO,
        })

    month = request.args.get("month")
    invoices = sheets.list_invoices(user.spreadsheet_id, month)
    return jsonify({
        "invoices": invoices,
        "facturas_mes": facturas_del_mes(user),
        "limite_mensual": LIMITE_MENSUAL,
        "umbral_aviso": UMBRAL_AVISO,
    })
