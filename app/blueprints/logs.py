"""Visor web del log de tiempos/errores de extracción (app/services/tiempos.py)
— pedido del CEO 2026-08-19: quería poder ver esto sin entrar por SSH.
Acceso por token en la URL (LOG_VIEWER_TOKEN), no por login de Google — es
para un solo dueño de la app, no un usuario más del sistema de cuentas."""
import os
import re

from flask import Blueprint, abort, render_template, request

logs_bp = Blueprint("logs", __name__)

LOG_FILE = os.getenv("LOG_FILE", "/var/log/facturas-saas/app.log")
MAX_LINEAS_MOSTRADAS = 300

_RE_TIMESTAMP = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ (.*)$")


def _tipo_de_linea(resto_sin_prefijo: str) -> str:
    if resto_sin_prefijo.startswith("extract lote"):
        return "Tanda"
    if resto_sin_prefijo.startswith("extract ["):
        return "Foto"
    if resto_sin_prefijo.startswith("invoices"):
        return "Guardado"
    return "Otro"


def _parsear_linea(linea: str) -> dict:
    m = _RE_TIMESTAMP.match(linea)
    fecha_hora, resto = (m.group(1), m.group(2)) if m else ("", linea)
    resto = resto[len("TIEMPOS "):] if resto.startswith("TIEMPOS ") else resto
    segmentos = [s.strip() for s in resto.split("|")]
    return {
        "fecha_hora": fecha_hora,
        "tipo": _tipo_de_linea(resto),
        "es_error": "error" in resto.lower(),
        "segmentos": segmentos,
    }


@logs_bp.route("/log")
def ver_log():
    token_esperado = os.environ.get("LOG_VIEWER_TOKEN")
    if not token_esperado or request.args.get("token") != token_esperado:
        abort(404)

    lineas = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            lineas = f.readlines()[-MAX_LINEAS_MOSTRADAS:]

    entradas = [_parsear_linea(linea.rstrip("\n")) for linea in lineas if linea.strip()]
    entradas.reverse()  # más reciente primero
    return render_template(
        "log.html",
        entradas=entradas,
        total=len(entradas),
        token=request.args.get("token"),
    )
