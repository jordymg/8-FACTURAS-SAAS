"""Extracción vía Mistral (La Plateforme) — tercer proveedor en la carrera
(ver app/services/extraccion.py). Validado 2026-08-19 contra una factura
de prueba real: rápido y sin vueltas, respuesta limpia sin necesitar
apagar ningún modo "thinking" (a diferencia de Groq, ver groq_extract.py).

modelo con visión usado: mistral-small-latest (configurable vía
MISTRAL_MODEL). A diferencia de Groq/OpenRouter (compatibles con el
formato OpenAI, image_url como {"url": "..."}), la API de Mistral espera
image_url como STRING plano — mismo dato, forma distinta, es la diferencia
real entre este archivo y groq_extract.py/openrouter_extract.py."""
import base64
import os
import time

import requests

from app.services.extraction_prompt import fields_desde_json, parsear_json_extraido, prompt_con_schema_json

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
USER_AGENT = "facturas-saas/1.0 (+https://facturas.mcfly.ar)"


class MistralExtraccionError(Exception):
    """Falla la extracción vía Mistral — sin reintentos acá, es una de las
    patas de la carrera en app/services/extraccion.py, no hace falta
    reintentar internamente si las otras ya están corriendo en paralelo."""


def extract_invoice_mistral(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[dict, dict]:
    """Devuelve (campos_extraídos, tiempos) — mismo contrato que
    gemini.py::extract_invoice / groq_extract.py::extract_invoice_groq."""
    modelo = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": modelo,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_con_schema_json()},
                {"type": "image_url", "image_url": f"data:{mime_type};base64,{b64}"},
            ],
        }],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    t_inicio = time.monotonic()
    try:
        resp = requests.post(
            MISTRAL_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}",
                "User-Agent": USER_AGENT,
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise MistralExtraccionError(f"{resp.status_code}: {resp.text[:500]}")
        contenido = resp.json()["choices"][0]["message"]["content"]
        datos = parsear_json_extraido(contenido)
    except MistralExtraccionError:
        raise
    except Exception as e:
        raise MistralExtraccionError(str(e)) from e
    duracion = time.monotonic() - t_inicio

    fields = fields_desde_json(datos)
    tiempos = {"reintentos": 0, "duracion_total": duracion, "duracion_ultimo_intento": duracion}
    return fields, tiempos
