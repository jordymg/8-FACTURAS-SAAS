import json
import os
from typing import Optional

from google import genai
from google.genai import types

from app.services.fields import FIELDS, FIELD_KEYS

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
    "Sobre impuestos, percepciones y retenciones: el comprobante puede discriminar varios "
    "por separado (IVA a distintas alícuotas, percepciones de IVA e IIBB, retenciones de "
    "Ganancias e IVA, SIRTAC, Impuestos Internos). Cada uno tiene su propia columna — ver la "
    "descripción de cada campo. NO sumes ni mezcles dos impuestos distintos en un mismo "
    "campo (ej. Impuestos Internos NO es IVA, una Percepción de IIBB NO es una Retención de "
    "Ganancias). Si un monto no corresponde claramente a ninguno de los campos definidos, "
    "dejalo afuera — no lo fuerces en el campo que más se parezca.\n\n"
    "Regla de duda (importante, ver ADR-0008 del área de Planillas): si no podés determinar "
    "con certeza el valor de un campo — por ejemplo, si no ves ninguna evidencia clara de que "
    "el comprobante esté autorizado (CAE, CAEA, CAI, o marcas de un controlador fiscal "
    "homologado) para decidir el campo 'tipo' — completá igual el campo con el valor que te "
    "parezca más probable (NUNCA lo dejes vacío por duda) y agregá su clave a "
    "'campos_inciertos', para que una persona lo revise antes de guardar."
)


def extract_invoice(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[dict]:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
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
    return json.loads(response.text)
