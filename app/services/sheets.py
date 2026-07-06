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

    if not sheet.get_all_values():
        sheet.append_row(ROW_KEYS, value_input_option="USER_ENTERED")
        sheet.format(f"A1:{chr(64 + len(ROW_KEYS))}1", {"textFormat": {"bold": True}})

    return spreadsheet_id


def append_invoice(spreadsheet_id: str, row: dict) -> None:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    values = [row.get(key, "") for key in ROW_KEYS]
    sheet.append_row(values, value_input_option="USER_ENTERED")


def list_invoices(spreadsheet_id: str, month: str | None = None) -> list[dict]:
    sheet = _client().open_by_key(spreadsheet_id).sheet1
    rows = sheet.get_all_values()
    if len(rows) <= 1:
        return []
    headers = rows[0]
    invoices = [dict(zip(headers, row)) for row in rows[1:]]
    if month:
        invoices = [inv for inv in invoices if inv.get("fecha", "").startswith(month)]
    return invoices
