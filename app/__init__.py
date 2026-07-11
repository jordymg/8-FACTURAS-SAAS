import os
from flask import Flask
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from werkzeug.middleware.proxy_fix import ProxyFix
from app.models import db

load_dotenv()


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
    if "spreadsheet_title" not in columnas:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN spreadsheet_title VARCHAR(256)"))
            conn.commit()


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.secret_key = os.environ["SECRET_KEY"]
    # Render (y la mayoría de los hosts) terminan TLS en un proxy y reenvían por HTTP
    # puertas adentro. Sin esto, Flask ve el request como http y oauthlib rechaza el
    # login (InsecureTransportError) aunque el usuario esté en https de verdad.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
