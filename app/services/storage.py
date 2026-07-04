"""
Guardado de la imagen original de cada comprobante.

Interino: disco local del servidor, una carpeta por usuario, con nombre de
archivo único por comprobante. En Render free el disco es efímero (se borra
en cada redeploy/restart) — antes de producción hay que decidir si esto pasa
a Drive del usuario (requiere scope OAuth con verificación de Google) o a un
storage tipo S3/Cloudflare R2. Ver docs/decisions/0004-service-account-sheets.md.
"""

import os
import uuid
from pathlib import Path

from app.services.formats import MIME_EXTENSIONS

_UPLOADS_ROOT = Path(os.getenv("UPLOADS_DIR", "instance/uploads"))


def save_image(user_id: str, image_bytes: bytes, mime_type: str, taken_at) -> str:
    """Guarda la imagen en instance/uploads/{user_id}/{fecha}_{uuid8}.{ext}.
    Devuelve la ruta relativa guardada (para registrar en la planilla)."""
    ext = MIME_EXTENSIONS.get(mime_type, "bin")
    filename = f"{taken_at:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}.{ext}"

    user_dir = _UPLOADS_ROOT / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / filename).write_bytes(image_bytes)

    return f"{user_id}/{filename}"
