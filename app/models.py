import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id: str = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_sub: str = db.Column(db.String(128), unique=True, nullable=False)
    email: str = db.Column(db.String(256), nullable=False)
    sheet_id: str = db.Column(db.String(128))
    drive_folder_id: str = db.Column(db.String(128))
    tokens: str = db.Column(db.Text)  # Fernet-encrypted JSON
    sub_status: str = db.Column(db.String(16), default="trial")  # trial / active / blocked
    invoices_this_month: int = db.Column(db.Integer, default=0)
