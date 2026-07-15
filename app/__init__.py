import datetime
import os
from flask import Flask
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from werkzeug.middleware.proxy_fix import ProxyFix
from app.models import db

load_dotenv()


# Columnas de User agregadas después del primer db.create_all() — ver
# _ensure_schema. Nombre → tipo SQL (compatible con SQLite y Postgres).
# invoices_month (VARCHAR(7)) quedó obsoleta al pasar el tope de facturas de
# mes-calendario a ciclo-por-fecha-de-alta — se deja de crear/usar, pero si
# ya existe en una base (producción) queda como columna huérfana inofensiva.
_COLUMNAS_NUEVAS = {
    "spreadsheet_title": "VARCHAR(256)",  # ADR-0003 área App
    "created_at": "DATE",  # ADR-0008 repo general (ancla el ciclo mensual)
    "invoices_cycle_start": "DATE",  # ADR-0008 repo general (tope mensual)
}

# Duración de la sesión: 90 días de INACTIVIDAD, no desde el login — con
# SESSION_REFRESH_EACH_REQUEST=True (default de Flask) la cookie se
# reemite en cada request y el vencimiento se corre. Ver
# docs/decisions/0012-sesion-90-dias-oauth-sin-reconsentimiento.md.
SESSION_LIFETIME_DIAS = 90


def _ensure_schema(app: Flask) -> None:
    """El proyecto no tiene Alembic/Flask-Migrate — db.create_all() solo crea
    tablas que no existen, no altera las que ya existen. Este chequeo
    liviano agrega columnas nuevas del modelo que falten en una base ya
    creada (SQLite local o Postgres de Render), sin introducir un framework
    de migraciones para cambios de schema chicos. Ver ADR-0003 área App."""
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return
    columnas = {c["name"] for c in inspector.get_columns("users")}
    faltantes = {n: t for n, t in _COLUMNAS_NUEVAS.items() if n not in columnas}
    if not faltantes:
        return
    with db.engine.connect() as conn:
        for nombre, tipo in faltantes.items():
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {nombre} {tipo}"))
        # Backfill: usuarios ya existentes no tienen fecha de alta real
        # guardada — se usa la fecha de hoy como mejor aproximación
        # disponible, así el ciclo mensual arranca a andar ya mismo.
        if "created_at" in faltantes:
            conn.execute(text(
                "UPDATE users SET created_at = :hoy WHERE created_at IS NULL"
            ), {"hoy": datetime.date.today().isoformat()})
        conn.commit()


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.secret_key = os.environ["SECRET_KEY"]
    # Render (y la mayoría de los hosts) terminan TLS en un proxy y reenvían por HTTP
    # puertas adentro. Sin esto, Flask ve el request como http y oauthlib rechaza el
    # login (InsecureTransportError) aunque el usuario esté en https de verdad.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Sesión persistente de 90 días renovables (ver SESSION_LIFETIME_DIAS
    # arriba). Render define la env var RENDER=true en todos sus servicios
    # — se usa para distinguir producción (HTTPS real, cookie Secure) de
    # local (HTTP en localhost, cookie no Secure o el navegador la descarta).
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=SESSION_LIFETIME_DIAS)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("RENDER") == "true"

    db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
    # Render supplies postgres:// but SQLAlchemy 1.4+ requires postgresql://
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.context_processor
    def inject_asset_version():
        def asset_version(rel_path: str) -> int:
            full_path = os.path.join(app.static_folder, rel_path)
            try:
                return int(os.path.getmtime(full_path))
            except OSError:
                return 0
        return {"asset_version": asset_version}

    from app.blueprints.web import web_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        _ensure_schema(app)

    return app
