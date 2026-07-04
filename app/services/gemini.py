import json
import os
from typing import Optional

from google import genai
from google.genai import types

from app.services.fields import FIELD_KEYS

_PROMPT = (
    "Sos un asistente que extrae datos de comprobantes argentinos (facturas y presupuestos "
    "de proveedores) a partir de una foto.\n\n"
    "Mirá la imagen y devolvé los datos del comprobante. Reglas:\n\n"
    "- Extraé SOLO lo que ves en la imagen. Si un dato no está o no se lee con claridad, "
    'dejalo como string vacío "". NUNCA inventes ni completes con suposiciones.\n'
    "- Los importes los devolvés como número con punto decimal y SIN separador de miles. "
    'Ejemplo: si en la factura dice "1.234,56" devolvés "1234.56".\n'
    "- La fecha la devolvés en formato AAAA-MM-DD.\n"
    "- El tipo de comprobante: distinguí Factura A, Factura B, Factura C, Presupuesto, "
    "Nota de Crédito, Remito, etc. según lo que diga el comprobante.\n"
    "- El CUIT es el del proveedor (quien emite), no el del receptor.\n"
    "- Neto gravado e IVA: en Factura A suelen venir discriminados. En B y C el IVA va "
    "incluido en el total y no se discrimina, así que dejá iva y neto vacíos si no aparecen "
    "por separado.\n"
    '- Moneda: "ARS" si son pesos argentinos, "USD" si son dólares.'
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
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {key: {"type": "string"} for key in FIELD_KEYS},
                "required": FIELD_KEYS,
            },
        ),
    )
    return json.loads(response.text)
