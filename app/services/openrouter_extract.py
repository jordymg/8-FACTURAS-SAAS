"""Extracción vía OpenRouter — cuarto proveedor en la carrera (ver
app/services/extraccion.py). Validado 2026-08-19 contra una factura de
prueba real.

Usa el modelo "openrouter/free" (configurable vía OPENROUTER_MODEL): no es
un modelo puntual, es un router automático de OpenRouter entre varios
modelos gratis con visión disponibles en ese momento. Se probó primero
fijando un modelo puntual (google/gemma-4-31b-it:free) y dio 429 por pool
compartido saturado; otro (nvidia/nemotron-nano-12b-v2-vl:free) dio 504.
El router "openrouter/free" resolvió bien las dos veces probado, eligiendo
él solo cuál de los modelos disponibles atenderlo — más resiliente que
apostar a uno solo del pool gratis de OpenRouter, que es compartido entre
todos los usuarios de la plataforma (no solo nosotros)."""
import base64
import os
import time

import requests

from app.services.extraction_prompt import fields_desde_json, parsear_json_extraido, prompt_con_schema_json

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
USER_AGENT = "facturas-saas/1.0 (+https://facturas.mcfly.ar)"


class OpenRouterExtraccionError(Exception):
    """Falla la extracción vía OpenRouter — sin reintentos acá, es una de
    las patas de la carrera en app/services/extraccion.py."""


def extract_invoice_openrouter(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[dict, dict]:
    """Devuelve (campos_extraídos, tiempos) — mismo contrato que
    gemini.py::extract_invoice."""
    modelo = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": modelo,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_con_schema_json()},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ],
        }],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    t_inicio = time.monotonic()
    try:
        resp = requests.post(
            OPENROUTER_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                "User-Agent": USER_AGENT,
                # No son obligatorios pero OpenRouter los recomienda para
                # identificar la app en su dashboard — no afecta el cupo.
                "HTTP-Referer": "https://facturas.mcfly.ar",
                "X-Title": "facturas-saas",
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise OpenRouterExtraccionError(f"{resp.status_code}: {resp.text[:500]}")
        contenido = resp.json()["choices"][0]["message"]["content"]
        datos = parsear_json_extraido(contenido)
    except OpenRouterExtraccionError:
        raise
    except Exception as e:
        raise OpenRouterExtraccionError(str(e)) from e
    duracion = time.monotonic() - t_inicio

    fields = fields_desde_json(datos)
    tiempos = {"reintentos": 0, "duracion_total": duracion, "duracion_ultimo_intento": duracion}
    return fields, tiempos
