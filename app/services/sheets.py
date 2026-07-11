import datetime
import json
import os
import re
from functools import lru_cache

import gspread
from google.oauth2 import service_account

from app.services.fields import FIELDS, FIELD_KEYS

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _sa_info() -> dict:
    """Credenciales de la Service Account: como JSON en una variable de entorno
    (Render, producción) o como archivo en disco (local, ver .env)."""
    raw = os.getenv("GOOGLE_SA_CREDENTIALS_JSON")
    if raw:
        return json.loads(raw)
    path = os.environ["GOOGLE_SA_CREDENTIALS_FILE"]
    return json.loads(open(path, encoding="utf-8").read())


@lru_cache(maxsize=1)
def _client() -> gspread.Client:
    creds = service_account.Credentials.from_service_account_info(_sa_info(), scopes=_SCOPES)
    return gspread.authorize(creds)


@lru_cache(maxsize=1)
def sa_email() -> str:
    return _sa_info().get("client_email", "")


def extract_spreadsheet_id(text: str) -> str:
    """Acepta URL completa de Google Sheets o directamente el spreadsheet ID."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", text)
    return match.group(1) if match else text.strip()


class SheetAccessError(Exception):
    """La Service Account no tiene acceso a la planilla, o la planilla es inválida."""


# Orden completo de columnas de la planilla — estructura v2 (ADR-0005 +
# ADR-0006, docs/areas/planillas/decisions/). cod_proveedor y cuenta no las
# completa ni la IA ni el usuario, quedan en blanco (ver ADR-0006).
# cargada_el la completa la app automáticamente.
ROW_KEYS = [
    "fecha", "proveedor", "cod_proveedor", "cuit", "categoria", "cuenta",
    "tipo", "punto_venta", "numero", "neto", "iva_105", "iva_21", "iva_27",
    "perc_iva", "perc_iibb_arba", "iibb_caba", "ret_ganancias", "ret_iva",
    "sirtac", "imp_internos", "total", "moneda", "cargada_el",
]

# Texto de encabezado (lo que ve el cliente/contador) — distinto de la clave
# interna que usa el código. Ver tabla del ADR-0005 para el texto exacto.
_EXTRA_LABELS = {
    "cod_proveedor": "Cód. Proveedor",
    "cuenta": "CUENTA",
    "cargada_el": "Fecha de Carga",
}
_FIELD_LABELS = {f["key"]: f["label"] for f in FIELDS}
ROW_LABELS = [_FIELD_LABELS.get(key, _EXTRA_LABELS.get(key, key)) for key in ROW_KEYS]

# Anchos de columna fijos (en píxeles) — reemplaza el auto-resize, que dejaba
# algunas columnas muy angostas. Ajustable a mano en Sheets después; esto es
# solo el punto de partida al crear/reconectar una planilla.
_COLUMN_WIDTHS = {
    "fecha": 95, "proveedor": 220, "cod_proveedor": 110, "cuit": 110,
    "categoria": 130, "cuenta": 90, "tipo": 95, "punto_venta": 95,
    "numero": 100, "neto": 100, "iva_105": 90, "iva_21": 85, "iva_27": 85,
    "perc_iva": 95, "perc_iibb_arba": 110, "iibb_caba": 95,
    "ret_ganancias": 110, "ret_iva": 90, "sirtac": 85, "imp_internos": 100,
    "total": 110, "moneda": 80, "cargada_el": 140,
}

# Columnas con montos — se muestran con formato de moneda (ADR-0004).
_MONEY_KEYS = [
    "neto", "iva_105", "iva_21", "iva_27", "perc_iva", "perc_iibb_arba",
    "iibb_caba", "ret_ganancias", "ret_iva", "sirtac", "imp_internos", "total",
]

# Estas columnas son identificadores, no cantidades — si se dejan como
# USER_ENTERED, Sheets las interpreta como número y pierden los ceros a la
# izquierda (ej. "0014" → 14, "00017367" → 17367). Se fuerzan a texto con el
# truco estándar de Sheets: un apóstrofe inicial (no queda visible, solo le
# dice a Sheets "no lo interpretes como número").
_FORCE_TEXT_KEYS = {"cuit", "punto_venta", "numero"}


def _last_col_letter(n: int) -> str:
    """Letra de columna A1 para la n-ésima columna (1-indexed, hasta 26)."""
    return chr(64 + n)


def _col_letter_of(key: str) -> str:
    return _last_col_letter(ROW_KEYS.index(key) + 1)


def _real_row_count(sheet: gspread.Worksheet) -> int:
    """Cantidad de filas con contenido real.

    get_all_values() en una planilla recién creada y realmente vacía devuelve
    [[]] (una fila "vacía"), no [] — eso es truthy en Python, así que un
    chequeo ingenuo como `if not sheet.get_all_values()` nunca detecta una
    planilla vacía. Filtramos las filas fantasma (sin ninguna celda con
    contenido) para contar solo las que tienen datos de verdad. Ver Issue #001
    en docs/ISSUES.md.
    """
    return len([r for r in sheet.get_all_values() if any(cell.strip() for cell in r)])


def connect_spreadsheet(text: str) -> tuple[str, str]:
    """Valida que la SA puede abrir la planilla del usuario y le escribe el
    encabezado si está vacía. Devuelve (spreadsheet_id, título) — el título
    se lee acá una sola vez, no se relee en cada visita (ADR-0003 área App)."""
    spreadsheet_id = extract_spreadsheet_id(text)
    if not spreadsheet_id:
        raise ValueError("ID de planilla inválido.")
    try:
        spreadsheet = _client().open_by_key(spreadsheet_id)
        sheet = spreadsheet.sheet1
        titulo = spreadsheet.title
    except gspread.exceptions.APIError as e:
        if e.response.status_code == 403:
            raise SheetAccessError(
                f"Sin acceso. Compartí la planilla con {sa_email()} como Editor."
            ) from e
        raise SheetAccessError(f"No se pudo abrir la planilla: {e}") from e
    except Exception as e:
        raise SheetAccessError(f"No se pudo abrir la planilla: {e}") from e

    last_col = _last_col_letter(len(ROW_KEYS))

    # El encabezado se (re)escribe siempre con nuestros textos canónicos, aun
    # si la planilla ya tenía datos y un encabezado propio (con otros nombres
    # de columna, typos, etc.) — así "Últimas facturas" en la app siempre
    # encuentra las claves que espera (proveedor, moneda...). Los datos ya
    # cargados (fila 2 en adelante) no se tocan. Rango explícito, no
    # append_row (ver Issue #001 en docs/ISSUES.md).
    sheet.update([ROW_LABELS], range_name=f"A1:{last_col}1", value_input_option="USER_ENTERED")
    sheet.format(f"A1:{last_col}1", {"textFormat": {"bold": True}})

    # Reglas de integridad y formato visual — ver docs/areas/planillas/
    # (punto 5 y ADR-0004). Se aplican siempre (planilla nueva o ya
    # existente), no solo la primera vez.
    _protect_header_once(sheet, last_col)
    # Fecha: se guarda AAAA-MM-DD, se muestra DD/MM/AAAA.
    fecha_col = _col_letter_of("fecha")
    sheet.format(f"{fecha_col}:{fecha_col}", {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}})
    # Moneda: valor numérico real en las columnas de montos, se muestra con formato de moneda.
    money_range = f"{_col_letter_of(_MONEY_KEYS[0])}:{_col_letter_of(_MONEY_KEYS[-1])}"
    sheet.format(money_range, {"numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'}})
    sheet.freeze(rows=1)
    _apply_column_widths(sheet)

    return spreadsheet_id, titulo


def _protect_header_once(sheet: gspread.Worksheet, last_col: str) -> None:
    """Protege A1:{last_col}1 — pero no duplica la protección si reconectan
    la misma planilla más de una vez."""
    already_protected = any(
        pr["range"].get("startRowIndex") == 0 and pr["range"].get("endRowIndex") == 1
        for pr in sheet.spreadsheet.list_protected_ranges(sheet.id)
    )
    if not already_protected:
        sheet.add_protected_range(
            f"A1:{last_col}1",
            editor_users_emails=[sa_email()],
            description="Encabezado de la planilla - no editar a mano",
        )


def _apply_column_widths(sheet: gspread.Worksheet) -> None:
    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet.id,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i + 1,
                },
                "properties": {"pixelSize": _COLUMN_WIDTHS[key]},
                "fields": "pixelSize",
            }
        }
        for i, key in enumerate(ROW_KEYS)
    ]
    sheet.spreadsheet.batch_update({"requests": requests})


def _to_number_or_blank(value):
    """Convierte a float de verdad en vez de dejarlo como string.

    Si mandamos "13192.36" como texto con USER_ENTERED, Sheets intenta
    parsearlo según la configuración regional de la planilla — en una
    planilla en español (coma decimal) un punto decimal no se reconoce como
    número y queda como texto (rompe el formato de moneda y las fórmulas del
    ADR-0002). Mandar un número de Python de verdad evita depender de la
    configuración regional."""
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def append_invoice(spreadsheet_id: str, row: dict) -> None:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    values = []
    for key in ROW_KEYS:
        val = row.get(key, "")
        if key in _FORCE_TEXT_KEYS and val:
            val = f"'{val}"
        elif key in _MONEY_KEYS:
            val = _to_number_or_blank(val)
        values.append(val)
    # Calculamos nosotros la próxima fila libre y escribimos en un rango
    # explícito — no usamos append_row (ver Issue #001 en docs/ISSUES.md).
    next_row = _real_row_count(sheet) + 1
    last_col = _last_col_letter(len(ROW_KEYS))
    sheet.update([values], range_name=f"A{next_row}:{last_col}{next_row}", value_input_option="USER_ENTERED")


_SHEETS_EPOCH = datetime.date(1899, 12, 30)


def _serial_to_iso_date(value) -> str:
    """La columna fecha se guarda como fecha real de Sheets (para que el
    formato DD/MM/AAAA del ADR-0004 y las fórmulas por mes del ADR-0002
    funcionen), así que al leerla sin formato viene como número de serie de
    Sheets, no como el string original. La convertimos de vuelta a AAAA-MM-DD."""
    if isinstance(value, (int, float)):
        return (_SHEETS_EPOCH + datetime.timedelta(days=int(value))).isoformat()
    return str(value)


def norm_id(value) -> str:
    """Normaliza un identificador numérico (numero de factura) para comparar
    sin que importen ceros a la izquierda ni separadores (ej. "0017367" y
    "17367" deben matchear) — ver ADR-0009."""
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.lstrip("0") or "0"


def norm_text(value) -> str:
    """Normaliza texto (proveedor) para comparar sin que importen mayúsculas
    ni espacios de más — ver ADR-0009."""
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def find_duplicate(invoices: list[dict], proveedor: str, numero: str, fecha: str) -> str | None:
    """Busca, entre las facturas ya cargadas, una con el mismo
    proveedor+numero+fecha (ADR-0009 — no usa CUIT porque las facturas en
    negro suelen no tenerlo, y son justo las que más necesitan este aviso).
    Devuelve el `cargada_el` de la fila existente, o None si no hay
    coincidencia. `invoices` viene de list_invoices() — se pasa ya leído para
    no releer la planilla entera por cada archivo de un lote."""
    if not (proveedor and numero and fecha):
        return None
    prov_n, numero_n, fecha_n = norm_text(proveedor), norm_id(numero), str(fecha).strip()
    for inv in invoices:
        if (
            norm_text(inv.get("proveedor", "")) == prov_n
            and norm_id(inv.get("numero", "")) == numero_n
            and str(inv.get("fecha", "")).strip() == fecha_n
        ):
            # cargada_el también se guarda como fecha/hora real de Sheets (ver
            # _serial_to_iso_date) — la convertimos para que se pueda mostrar
            # en el aviso ("ya la subiste el ...") en vez de un número de serie.
            return _serial_to_iso_date(inv.get("cargada_el"))
    return None


def list_invoices(spreadsheet_id: str, month: str | None = None) -> list[dict]:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    rows = sheet.get_all_values(value_render_option="UNFORMATTED_VALUE")
    if len(rows) <= 1:
        return []
    # Zipeamos contra ROW_KEYS (nuestras claves internas), no contra el texto
    # real de la fila 1 — ese es el encabezado legible para el cliente
    # (ROW_LABELS), no necesariamente igual a la clave que usa el código.
    invoices = [dict(zip(ROW_KEYS, row)) for row in rows[1:]]
    for inv in invoices:
        if "fecha" in inv:
            inv["fecha"] = _serial_to_iso_date(inv["fecha"])
    if month:
        invoices = [inv for inv in invoices if inv.get("fecha", "").startswith(month)]
    return invoices
