import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id: str = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_sub: str = db.Column(db.String(128), unique=True, nullable=False)
    email: str = db.Column(db.String(256), nullable=False)
    spreadsheet_id: str = db.Column(db.String(128))  # planilla del usuario, compartida con la SA
    # Título real del spreadsheet en Google, leído una vez al conectar
    # (ver app/services/sheets.py::connect_spreadsheet) — no se relee en
    # cada visita (ADR-0003 área App). Nulo para conexiones anteriores a
    # este campo, hasta que el usuario reconecte.
    spreadsheet_title: str = db.Column(db.String(256))
    sub_status: str = db.Column(db.String(16), default="trial")  # trial / active / blocked
    # Fecha de alta — ancla el ciclo mensual del tope de facturas (ej. alta
    # el 10 -> ciclo del 10 al 9 del mes siguiente, no por mes calendario).
    # Para usuarios de antes de este campo, se hace backfill con la fecha
    # del día en que se agrega la columna (ver app/__init__.py::_ensure_schema).
    created_at = db.Column(db.Date)
    invoices_this_month: int = db.Column(db.Integer, default=0)
    # Fecha de inicio del ciclo actual al que corresponde invoices_this_month
    # — permite resetear el contador sin un cron (ver
    # app/services/limites.py, ADR-0008 general).
    invoices_cycle_start = db.Column(db.Date)
