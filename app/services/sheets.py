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

    _formatear_encabezado(sheet)

    return spreadsheet_id, titulo


def _formatear_encabezado(sheet: gspread.Worksheet) -> None:
    """Escribe el encabezado canónico + aplica todas las reglas de formato
    e integridad (protección, fecha, moneda, fila congelada, anchos de
    columna) sobre `sheet1` en `connect_spreadsheet()`. Las pestañas
    anuales nuevas (`crear_pestanas()`, ADR-0003 área Planillas) aplican
    el mismo formato pero con sus propios requests en lote, para poder
    mandar todo junto en un único `batch_update` — ver el docstring de
    `crear_pestanas()` para el porqué."""
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


def rename_spreadsheet(spreadsheet_id: str, titulo_actual: str, titulo_nuevo: str) -> str:
    """Le pone un nombre a la planilla en Google Drive (ADR-0005 área App)
    — se usa solo en la primera conexión de cada usuario, nunca en
    reconexiones (para no pisarle un nombre que ya haya elegido a mano).
    Si falla, no rompe el flujo de conexión — devuelve `titulo_actual` sin
    cambiar, la planilla igual queda conectada y utilizable."""
    try:
        spreadsheet = _client().open_by_key(spreadsheet_id)
        spreadsheet.update_title(titulo_nuevo)
        return titulo_nuevo
    except Exception:
        return titulo_actual


def asegurar_pestana_del_anio(spreadsheet_id: str, fecha: datetime.date) -> str:
    """Crea la pestaña del año calendario de `fecha` si todavía no existe
    (ADR-0003 área Planillas, versión 2026-07-12: una sola pestaña por
    AÑO, no por mes — ej. toda la factura de 2026 vive en una pestaña
    llamada "2026"). Se llama:
    - Al conectar por primera vez (crea la pestaña del año actual).
    - Cada vez que se guarda una factura (`POST /api/invoices`), como
      chequeo barato — si ya cambiamos de año y todavía no existe esa
      pestaña, se crea ahí mismo.
    Devuelve el nombre de la pestaña (exista ya, o se acabe de crear)."""
    nombre = str(fecha.year)
    crear_pestanas(spreadsheet_id, [nombre])
    return nombre


def crear_pestanas(spreadsheet_id: str, nombres: list[str]) -> list[str]:
    """Crea (si no existen ya) las pestañas pedidas (hoy siempre una por
    año, ej. "2026"), con el encabezado y formato canónico (ADR-0003 área
    Planillas — alcance acotado: solo crea las pestañas,
    `append_invoice`/`list_invoices`/`find_duplicate` siguen usando
    `sheet1` únicamente, no leen/escriben estas pestañas todavía).
    Devuelve `nombres` tal cual (ya existieran o se acaben de crear) — no
    hace nada si ya están todas.

    IMPORTANTE — por qué va todo en 2 llamadas a la API, no N×7: crear una
    pestaña con `add_worksheet` + todo su formato (negrita, fecha, moneda,
    fila congelada, anchos de columna, protección) son ~7 llamadas de
    escritura. Con las 12 pestañas del año de una sola vez esto superaba
    la cuota de "escrituras por minuto" de la API de Sheets (HTTP 429,
    confirmado empíricamente — ver Issue #006 en docs/ISSUES.md). Ahora
    que se crea de a una pestaña por vez esto ya no es un riesgo real,
    pero se mantiene el mismo mecanismo en lotes por prolijidad y por si
    en algún momento se llama con más de una pestaña junta: se arman TODOS
    los requests en una sola lista y se mandan juntos en un único
    `spreadsheet.batch_update(...)` — más un segundo llamado con
    `values_batch_update(...)` para el texto del encabezado."""
    spreadsheet = _client().open_by_key(spreadsheet_id)
    existentes = {ws.title: ws.id for ws in spreadsheet.worksheets()}
    a_crear = [n for n in nombres if n not in existentes]
    if not a_crear:
        return nombres

    # sheetId nuevos que no choquen con los que ya existen en la planilla
    # (se pueden pre-asignar en el request de addSheet, y los requests de
    # formato del mismo batch ya los pueden referenciar).
    siguiente_id = max(existentes.values(), default=0) + 1000
    id_de = {}
    for nombre in a_crear:
        id_de[nombre] = siguiente_id
        siguiente_id += 1

    n_cols = len(ROW_KEYS)
    fecha_col_idx = ROW_KEYS.index("fecha")
    money_start_idx = ROW_KEYS.index(_MONEY_KEYS[0])
    money_end_idx = ROW_KEYS.index(_MONEY_KEYS[-1]) + 1

    requests = []
    for nombre in a_crear:
        sid = id_de[nombre]
        requests.append({"addSheet": {"properties": {
            "sheetId": sid, "title": nombre,
            "gridProperties": {"rowCount": 1000, "columnCount": n_cols},
        }}})
        requests.append({"repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat.textFormat.bold",
        }})
        requests.append({"repeatCell": {
            "range": {"sheetId": sid, "startColumnIndex": fecha_col_idx, "endColumnIndex": fecha_col_idx + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}}},
            "fields": "userEnteredFormat.numberFormat",
        }})
        requests.append({"repeatCell": {
            "range": {"sheetId": sid, "startColumnIndex": money_start_idx, "endColumnIndex": money_end_idx},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'}}},
            "fields": "userEnteredFormat.numberFormat",
        }})
        requests.append({"updateSheetProperties": {
            "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }})
        for i, key in enumerate(ROW_KEYS):
            requests.append({"updateDimensionProperties": {
                "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": _COLUMN_WIDTHS[key]},
                "fields": "pixelSize",
            }})
        requests.append({"addProtectedRange": {"protectedRange": {
            "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
            "description": "Encabezado de la planilla - no editar a mano",
            "editors": {"users": [sa_email()]},
        }}})

    spreadsheet.batch_update({"requests": requests})

    last_col = _last_col_letter(n_cols)
    spreadsheet.values_batch_update({
        "valueInputOption": "USER_ENTERED",
        "data": [{"range": f"'{nombre}'!A1:{last_col}1", "values": [ROW_LABELS]} for nombre in a_crear],
    })

    return nombres


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
    """Guarda la factura en la pestaña del AÑO al que corresponde su fecha
    (ADR-0003 área Planillas — ya no se guarda en `sheet1`/"Hoja 1"). Si esa
    pestaña todavía no existe (ej. factura de un año que recién empieza),
    se crea acá mismo con el encabezado canónico."""
    fecha = str(row.get("fecha", ""))
    anio = int(fecha[:4]) if fecha[:4].isdigit() else datetime.date.today().year
    asegurar_pestana_del_anio(spreadsheet_id, datetime.date(anio, 1, 1))
    sheet = _client().open_by_key(spreadsheet_id).worksheet(str(anio))

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


def list_invoices(spreadsheet_id: str, month: str | None = None, anio: int | None = None) -> list[dict]:
    """Lee las facturas de la pestaña del AÑO pedido (ADR-0003 área
    Planillas — ya no lee `sheet1`/"Hoja 1"). Por defecto, el año actual —
    para "Últimas facturas" y detección de duplicados, que en la práctica
    casi siempre importan del año en curso (limitación conocida: no busca
    en años anteriores). Si la pestaña de ese año todavía no existe (nunca
    se guardó ninguna factura ese año), devuelve lista vacía sin error."""
    anio = anio or datetime.date.today().year
    spreadsheet = _client().open_by_key(spreadsheet_id)
    try:
        sheet = spreadsheet.worksheet(str(anio))
    except gspread.exceptions.WorksheetNotFound:
        return []
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
