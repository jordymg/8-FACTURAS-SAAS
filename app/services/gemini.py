import json
import os
from typing import Optional

from google import genai
from google.genai import types

_PROMPT = (
    "Extract the following fields from this Argentine invoice image and return ONLY a valid JSON object. "
    "If a field is not visible or cannot be determined, use null.\n"
    "Fields:\n"
    "- fecha: invoice date in YYYY-MM-DD format\n"
    "- tipo_comprobante: document type (e.g. 'Factura A', 'Factura B', 'Factura C', 'Ticket', 'Nota de Crédito A')\n"
    "- numero: invoice number as 'XXXX-XXXXXXXX' (punto de venta hyphen número)\n"
    "- cuit_emisor: issuer CUIT, 11 digits, no dashes or spaces\n"
    "- razon_social: issuer business name\n"
    "- neto: pre-tax amount as a float, no currency symbols\n"
    "- iva: VAT amount as a float, no currency symbols\n"
    "- total: total amount as a float, no currency symbols\n"
    "Return ONLY the JSON object, no markdown fences, no explanation."
)


def extract_invoice(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[dict]:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            _PROMPT,
        ],
    )
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(text)
