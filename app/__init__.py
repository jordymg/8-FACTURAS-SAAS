import os
from flask import Flask
from dotenv import load_dotenv
from app.models import db

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.secret_key = os.environ["SECRET_KEY"]

    db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
    # Render supplies postgres:// but SQLAlchemy 1.4+ requires postgresql://
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.blueprints.web import web_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app
