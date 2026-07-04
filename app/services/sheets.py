import json
import os
import re
from functools import lru_cache

import gspread
from google.oauth2 import service_account

from app.services.fields import FIELD_KEYS

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@lru_cache(maxsize=1)
def _client() -> gspread.Client:
    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SA_CREDENTIALS_FILE"], scopes=_SCOPES
    )
    return gspread.authorize(creds)


@lru_cache(maxsize=1)
def sa_email() -> str:
    path = os.environ["GOOGLE_SA_CREDENTIALS_FILE"]
    data = json.loads(open(path, encoding="utf-8").read())
    return data.get("client_email", "")


def extract_spreadsheet_id(text: str) -> str:
    """Acepta URL completa de Google Sheets o directamente el spreadsheet ID."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", text)
    return match.group(1) if match else text.strip()


class SheetAccessError(Exception):
    """La Service Account no tiene acceso a la planilla indicada."""


def connect_spreadsheet(text: str) -> str:
    """Valida que la SA puede abrir la planilla del usuario. Devuelve el spreadsheet_id."""
    spreadsheet_id = extract_spreadsheet_id(text)
    if not spreadsheet_id:
        raise ValueError("ID de planilla inválido.")
    try:
        _client().open_by_key(spreadsheet_id)
    except gspread.exceptions.APIError as e:
        if e.response.status_code == 403:
            raise SheetAccessError(
                f"Sin acceso. Compartí la planilla con {sa_email()} como Editor."
            ) from e
        raise
    return spreadsheet_id


ROW_KEYS = FIELD_KEYS + ["imagen", "cargada_el"]


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
