import datetime
import json
import os
import re
from functools import lru_cache

import gspread
from google.oauth2 import service_account

from app.services.fields import FIELD_KEYS

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


ROW_KEYS = FIELD_KEYS + ["imagen", "cargada_el"]


def _last_col_letter(n: int) -> str:
    """Letra de columna A1 para la n-ésima columna (1-indexed, hasta 26)."""
    return chr(64 + n)


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


def connect_spreadsheet(text: str) -> str:
    """Valida que la SA puede abrir la planilla del usuario y le escribe el
    encabezado si está vacía. Devuelve el spreadsheet_id."""
    spreadsheet_id = extract_spreadsheet_id(text)
    if not spreadsheet_id:
        raise ValueError("ID de planilla inválido.")
    try:
        sheet = _client().open_by_key(spreadsheet_id).sheet1
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
    sheet.update([ROW_KEYS], range_name=f"A1:{last_col}1", value_input_option="USER_ENTERED")
    sheet.format(f"A1:{last_col}1", {"textFormat": {"bold": True}})

    # Reglas de integridad y formato visual — ver docs/areas/planillas/
    # (punto 5 y ADR-0004). Se aplican siempre (planilla nueva o ya
    # existente), no solo la primera vez.
    _protect_header_once(sheet, last_col)
    # Fecha: se guarda AAAA-MM-DD (columna A), se muestra DD/MM/AAAA.
    sheet.format("A:A", {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}})
    # Moneda: valor numérico real (columnas F/G/H = neto/iva/total), se muestra con formato de moneda.
    sheet.format("F:H", {"numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'}})
    sheet.freeze(rows=1)
    sheet.columns_auto_resize(0, len(ROW_KEYS))

    return spreadsheet_id


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


def append_invoice(spreadsheet_id: str, row: dict) -> None:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    values = [row.get(key, "") for key in ROW_KEYS]
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


def list_invoices(spreadsheet_id: str, month: str | None = None) -> list[dict]:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    rows = sheet.get_all_values(value_render_option="UNFORMATTED_VALUE")
    if len(rows) <= 1:
        return []
    headers = rows[0]
    invoices = [dict(zip(headers, row)) for row in rows[1:]]
    for inv in invoices:
        if "fecha" in inv:
            inv["fecha"] = _serial_to_iso_date(inv["fecha"])
    if month:
        invoices = [inv for inv in invoices if inv.get("fecha", "").startswith(month)]
    return invoices
