"""Instrumentación de tiempos por etapa del procesamiento de facturas (ver
ADR-0014) — logger propio, no el root logger, para no terminar mostrando
también el nivel INFO de librerías de terceros (gspread, google-genai) que
comparten el logging estándar de Python.

Además de stdout (que junta journald), escribe a un archivo rotativo
propio (`LOG_FILE`, default `/var/log/facturas-saas/app.log`) para poder
abrir un incidente puntual sin depender de `journalctl`/permisos de systemd.
Si el directorio no existe o no hay permiso de escritura (ej. corriendo en
una máquina de desarrollo), se ignora el archivo y sigue solo por stdout —
no debe tirar abajo la app por un problema de logging."""
import logging
import logging.handlers
import os

LOG_TIEMPOS = os.getenv("LOG_TIEMPOS", "true").strip().lower() not in ("false", "0", "")
LOG_FILE = os.getenv("LOG_FILE", "/var/log/facturas-saas/app.log")

_logger = logging.getLogger("tiempos")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _formatter = logging.Formatter("%(asctime)s %(message)s")

    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)

    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        _file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        _file_handler.setFormatter(_formatter)
        _logger.addHandler(_file_handler)
    except OSError:
        pass  # sin permiso/directorio en este entorno — queda solo stdout

    _logger.propagate = False


def log(mensaje: str) -> None:
    if LOG_TIEMPOS:
        _logger.info(mensaje)
