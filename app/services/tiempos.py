"""Instrumentación de tiempos por etapa del procesamiento de facturas (ver
ADR-0014) — logger propio, no el root logger, para no terminar mostrando
también el nivel INFO de librerías de terceros (gspread, google-genai) que
comparten el logging estándar de Python."""
import logging
import os

LOG_TIEMPOS = os.getenv("LOG_TIEMPOS", "true").strip().lower() not in ("false", "0", "")

_logger = logging.getLogger("tiempos")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.propagate = False


def log(mensaje: str) -> None:
    if LOG_TIEMPOS:
        _logger.info(mensaje)
