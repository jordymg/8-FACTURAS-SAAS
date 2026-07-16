"""Mensajes que se muestran rotando en la pantalla de espera (cold start
de Render y reintentos automáticos ante 503 de Gemini, ADR-0005 general)
— carrusel independiente de los otros dos (tips de home, consejos de
revisión), con su propio archivo. Editable sin tocar código: ver
strings/mensajes-espera.txt."""

import os

_MENSAJES_ESPERA_PATH = os.path.join(os.path.dirname(__file__), "../../strings/mensajes-espera.txt")


def get_mensajes_espera() -> list[str]:
    """Lee strings/mensajes-espera.txt: un mensaje por línea, ignora
    vacías y comentarios (#). Si el archivo falta, está vacío, o tiene
    algún problema de lectura, devuelve una lista vacía — nunca rompe la
    pantalla de espera."""
    try:
        with open(os.path.normpath(_MENSAJES_ESPERA_PATH), encoding="utf-8") as f:
            lineas = f.readlines()
    except OSError:
        return []
    return [l.strip() for l in lineas if l.strip() and not l.strip().startswith("#")]
