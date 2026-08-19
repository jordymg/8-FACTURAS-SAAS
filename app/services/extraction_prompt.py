"""Prompt de extracción de comprobantes — compartido entre proveedores de
IA (gemini.py, groq_extract.py, mistral_extract.py, openrouter_extract.py).
Único lugar a editar si cambian las reglas de negocio (ADR-0008, ADR-0009
planillas), para que no diverjan entre proveedores.

También trae los helpers compartidos por los proveedores "estilo OpenAI"
(Groq, Mistral, OpenRouter) que no tienen el response_schema estructurado
de Gemini: arman el mismo texto de schema en el prompt y parsean la
respuesta de la misma forma — Gemini no los usa, tiene su propio
response_schema real."""
import json

from app.services.fields import FIELD_KEYS, FIELDS

PROMPT = (
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


def _schema_texto() -> str:
    lineas = [f'- "{f["key"]}": {f["description"]}' for f in FIELDS]
    return "\n".join(lineas)


def prompt_con_schema_json() -> str:
    """PROMPT + el listado de claves esperadas — para proveedores sin un
    response_schema real (Gemini si lo tiene, no necesita esto)."""
    return (
        PROMPT
        + "\n\nDevolvé SOLO un objeto JSON (sin texto ni markdown alrededor) con "
        "EXACTAMENTE estas claves:\n"
        + _schema_texto()
        + '\n- "campos_inciertos": lista de claves (de las de arriba) con baja certeza, '
        "[] si no hay ninguna."
    )


def parsear_json_extraido(contenido: str) -> dict:
    """Algunos proveedores devuelven el JSON envuelto en un bloque
    ```json ... ``` pese a pedírselo explícitamente sin markdown — se lo
    saca si está, antes de json.loads."""
    texto = contenido.strip()
    if texto.startswith("```"):
        texto = texto.strip("`")
        if texto.startswith("json"):
            texto = texto[4:]
    return json.loads(texto.strip())


def fields_desde_json(datos: dict) -> dict:
    fields = {k: str(datos.get(k, "") or "") for k in FIELD_KEYS}
    fields["campos_inciertos"] = datos.get("campos_inciertos") or []
    return fields
