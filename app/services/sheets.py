from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

_HEADERS = [
    "fecha", "tipo_comprobante", "numero", "cuit_emisor",
    "razon_social", "neto", "iva", "total", "imagen_url", "cargada_el",
]


def _service(credentials: Credentials):
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def create_spreadsheet(credentials: Credentials, email: str) -> str:
    service = _service(credentials)
    spreadsheet = service.spreadsheets().create(body={
        "properties": {"title": f"Facturas — {email}"},
        "sheets": [{"properties": {"title": "Facturas"}}],
    }).execute()
    sheet_id = spreadsheet["spreadsheetId"]
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Facturas!A1",
        valueInputOption="RAW",
        body={"values": [_HEADERS]},
    ).execute()
    return sheet_id


def append_invoice(credentials: Credentials, sheet_id: str, row: dict) -> None:
    service = _service(credentials)
    values = [[str(row.get(h, "")) for h in _HEADERS]]
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Facturas!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()


def list_invoices(credentials: Credentials, sheet_id: str, month: str | None = None) -> list[dict]:
    service = _service(credentials)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="Facturas!A1:J1000",
    ).execute()
    rows = result.get("values", [])
    if len(rows) <= 1:
        return []
    headers = rows[0]
    invoices = [dict(zip(headers, row)) for row in rows[1:]]
    if month:
        invoices = [inv for inv in invoices if inv.get("fecha", "").startswith(month)]
    return invoices
