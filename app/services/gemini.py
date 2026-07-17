import json
import os
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.services.fields import FIELDS, FIELD_KEYS

# Reintentos ante 503 de Gemini (alta demanda) — ADR-0005 general. Solo se
# reintentan errores transitorios de servidor (genai_errors.ServerError,
# 5xx); errores de cliente (imagen inválida, API key, etc.) propagan
# directo, sin reintento.
MAX_REINTENTOS_503 = 3
BACKOFF_SEG = [2, 4, 8]  # espera creciente entre intentos, ~15s peor caso
MENSAJE_ERROR_FINAL = (
    "No pudimos procesar tu factura en este momento. Esperá unos minutos y "
    "volvé a intentar. La foto no se perdió, solo tocá reintentar."
)


class GeminiSobrecargadoError(Exception):
    """Se agotaron los MAX_REINTENTOS_503 reintentos ante un 503 (alta
    demanda) de Gemini — el mensaje ya es el texto listo para el usuario
    (ver MENSAJE_ERROR_FINAL), app/blueprints/api.py lo muestra tal cual
    vía str(e), sin necesitar saber nada de reintentos."""


def _generate_content_con_reintentos(client: genai.Client, **kwargs) -> tuple:
    """Devuelve (response, tiempos) — tiempos trae reintentos, duración total
    (todos los intentos + esperas de backoff) y duración del último intento
    (el exitoso) por separado, para poder distinguir en los logs "Gemini
    tardó" de "hubo reintentos" (instrumentación, ver ADR-0014)."""
    intentos_fallidos = 0
    t_inicio = time.monotonic()
    while True:
        t_intento = time.monotonic()
        try:
            response = client.models.generate_content(**kwargs)
            ahora = time.monotonic()
            tiempos = {
                "reintentos": intentos_fallidos,
                "duracion_total": ahora - t_inicio,
                "duracion_ultimo_intento": ahora - t_intento,
            }
            return response, tiempos
        except genai_errors.ServerError:
            if intentos_fallidos >= MAX_REINTENTOS_503:
                raise GeminiSobrecargadoError(MENSAJE_ERROR_FINAL) from None
            time.sleep(BACKOFF_SEG[intentos_fallidos])
            intentos_fallidos += 1


_PROMPT = (
    "Sos un asistente que extrae datos de comprobantes argentinos (facturas y presupuestos "
    "de proveedores) a partir de una foto, para el libro de compras de un contador.\n\n"
    "Mirá la imagen y devolvé los datos del comprobante. Reglas generales:\n\n"
    "- Extraé SOLO lo que ves en la imagen. Si un dato no está o no se lee con claridad, "
    'dejalo como string vacío "". NUNCA inventes ni completes con suposiciones.\n'
    "- Los importes los devolvés como número con punto decimal y SIN separador de miles. "
    'Ejemplo: si en la factura dice "1.234,56" devolvés "1234.56".\n'
    "- La fecha la devolvés en formato AAAA-MM-DD.\n"
    "- El CUIT es el del proveedor (quien emite), no el del receptor.\n"
    '- Moneda: "ARS" si son pesos argentinos, "USD" si son dólares.\n\n'
    "Sobre impuestos, percepciones y retenciones: IVA a cada alícuota (10,5%/21%/27%) e "
    "Impuestos Internos tienen su propia columna — ver la descripción de cada campo, y NO "
    "los sumes en 'otros_impuestos'. Cualquier otra percepción, retención o impuesto que el "
    "comprobante discrimine por separado (ej. percepción de IVA, percepción de IIBB, "
    "retención de Ganancias, retención de IVA, SIRTAC, u otros) va SUMADO en "
    "'otros_impuestos', no cada uno en un campo propio.\n\n"
    "Regla de duda (importante, ver ADR-0008 del área de Planillas): si no podés determinar "
    "con certeza el valor de un campo — por ejemplo, si no ves ninguna evidencia clara de que "
    "el comprobante esté autorizado (CAE, CAEA, CAI, o marcas de un controlador fiscal "
    "homologado) para decidir el campo 'tipo' — completá igual el campo con el valor que te "
    "parezca más probable (NUNCA lo dejes vacío por duda) y agregá su clave a "
    "'campos_inciertos', para que una persona lo revise antes de guardar."
)


def extract_invoice(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[dict, dict]:
    """Devuelve (campos_extraídos, tiempos_gemini) — ver docstring de
    `_generate_content_con_reintentos` para el contenido de `tiempos_gemini`."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response, tiempos_gemini = _generate_content_con_reintentos(
        client,
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            _PROMPT,
        ],
        config=types.GenerateContentConfig(
            # temperature=0: queremos la lectura más probable del comprobante,
            # siempre la misma para la misma imagen — no variación creativa.
            # Sin esto, la misma foto podía devolver datos levemente distintos
            # entre una llamada y otra.
            temperature=0,
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    **{
                        f["key"]: {"type": "string", "description": f["description"]} for f in FIELDS
                    },
                    "campos_inciertos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Claves (de los campos de arriba) donde completaste un valor pero "
                            "con baja certeza — el campo SIEMPRE debe tener tu mejor estimación "
                            "(nunca vacío por duda), esto solo marca cuáles conviene que una "
                            "persona revise antes de guardar. Lista vacía si no hay ninguna duda."
                        ),
                    },
                },
                "required": FIELD_KEYS + ["campos_inciertos"],
            },
        ),
    )
    return json.loads(response.text), tiempos_gemini
