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
    "Regla de duda (importante, ver ADR-0007 del área de Planillas): si no podés determinar "
    "con certeza el valor de un campo — por ejemplo, si no ves ninguna evidencia clara de que "
    "el comprobante esté autorizado (CAE, CAEA, CAI, o marcas de un controlador fiscal "
    "homologado) para decidir el campo 'tipo' — NO inventes ni elijas el valor que te parezca "
    "más probable: dejá ese campo como string vacío y agregá su clave a 'campos_inciertos'. Es "
    "mejor marcar duda (para que una persona lo revise) que arriesgar un valor incorrecto."
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
                "properties": {
                    **{
                        f["key"]: {"type": "string", "description": f["description"]} for f in FIELDS
                    },
                    "campos_inciertos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Claves (de los campos de arriba) donde NO estás seguro del valor "
                            "extraído. En esos casos el campo correspondiente debe quedar vacío "
                            '("") y su clave va acá, para que una persona lo revise a mano antes '
                            "de guardar. Lista vacía si no hay ninguna duda."
                        ),
                    },
                },
                "required": FIELD_KEYS + ["campos_inciertos"],
            },
        ),
    )
    return json.loads(response.text)
