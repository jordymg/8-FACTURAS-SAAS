"""Extracción vía Groq — proveedor de respaldo cuando Gemini agota sus
reintentos (ver app/services/gemini.py::GeminiSobrecargadoError). Validado
2026-08-18 contra una factura de prueba real: mucho más rápido que Gemini
en la práctica (<1s vs 6-16s), pero sin garantía de disponibilidad ni de
calidad de extracción equivalente — por eso es respaldo, no reemplazo.

Único modelo con soporte de imagen disponible en la cuenta al momento de
integrar esto: qwen/qwen3.6-27b (configurable vía GROQ_MODEL por si Groq
cambia qué modelos ofrece — mismo problema que ya pasó con Gemini)."""
import base64
import json
import os
import time

import requests

from app.services.extraction_prompt import PROMPT
from app.services.fields import FIELDS, FIELD_KEYS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Sin User-Agent, Cloudflare (delante de la API de Groq) devuelve 403
# "error code: 1010" — bloquea el User-Agent default de requests/urllib.
USER_AGENT = "facturas-saas/1.0 (+https://facturas.mcfly.ar)"


class GroqExtraccionError(Exception):
    """Falla la extracción vía Groq — sin reintentos acá (ya es el
    respaldo de Gemini, que sí reintenta); se propaga tal cual para que
    app/blueprints/api.py decida qué mostrar si también falla."""


def _schema_texto() -> str:
    lineas = [f'- "{f["key"]}": {f["description"]}' for f in FIELDS]
    return "\n".join(lineas)


def extract_invoice_groq(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[dict, dict]:
    """Devuelve (campos_extraídos, tiempos) — mismo contrato que
    gemini.py::extract_invoice, para que app/blueprints/api.py pueda usar
    cualquiera de los dos sin distinguir cuál respondió."""
    modelo = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    # Groq (API compatible con OpenAI) no tiene un equivalente exacto al
    # response_schema estructurado de Gemini — json_object solo garantiza
    # JSON válido, no las claves puntuales. Se listan las claves y su
    # descripción directo en el prompt para compensar.
    prompt_json = (
        PROMPT
        + "\n\nDevolvé SOLO un objeto JSON (sin texto ni explicación alrededor) con "
        "EXACTAMENTE estas claves:\n"
        + _schema_texto()
        + '\n- "campos_inciertos": lista de claves (de las de arriba) con baja certeza, '
        "[] si no hay ninguna."
    )
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": modelo,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_json},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ],
        }],
        "temperature": 0,
        # Sin esto, este modelo (qwen/qwen3.6-27b es un modelo "thinking") le
        # dedica todo el presupuesto de completion_tokens a razonar en voz
        # alta sobre el prompt completo (probado: se le va TODO pensando el
        # caso límite del campo "tipo") y nunca llega a escribir el JSON —
        # 400 "json_validate_failed" con failed_generation vacío. Apaga el
        # razonamiento, responde directo.
        "reasoning_effort": "none",
        "response_format": {"type": "json_object"},
    }

    t_inicio = time.monotonic()
    try:
        resp = requests.post(
            GROQ_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
                "User-Agent": USER_AGENT,
            },
            timeout=30,
        )
        resp.raise_for_status()
        contenido = resp.json()["choices"][0]["message"]["content"]
        datos = json.loads(contenido)
    except Exception as e:
        raise GroqExtraccionError(str(e)) from e
    duracion = time.monotonic() - t_inicio

    fields = {k: str(datos.get(k, "") or "") for k in FIELD_KEYS}
    fields["campos_inciertos"] = datos.get("campos_inciertos") or []
    tiempos = {"reintentos": 0, "duracion_total": duracion, "duracion_ultimo_intento": duracion}
    return fields, tiempos
