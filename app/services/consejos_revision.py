"""Consejos que se muestran rotando en la pantalla de revisión de
facturas (ADR-0007 área App) — carrusel independiente del tip de la home
(ADR-0004 área App, `app/services/tips.py`), con su propio archivo
porque el contenido es de otro contexto (consejos de uso de esa pantalla
+ novedades/mejoras pedidas por clientes). Editable sin tocar código: ver
strings/consejos-revision.txt."""

import os

_CONSEJOS_PATH = os.path.join(os.path.dirname(__file__), "../../strings/consejos-revision.txt")


def get_consejos_revision() -> list[str]:
    """Lee strings/consejos-revision.txt: un consejo por línea, ignora
    vacías y comentarios (#). Si el archivo falta, está vacío, o tiene
    algún problema de lectura, devuelve una lista vacía — nunca rompe la
    pantalla de revisión."""
    try:
        with open(os.path.normpath(_CONSEJOS_PATH), encoding="utf-8") as f:
            lineas = f.readlines()
    except OSError:
        return []
    return [l.strip() for l in lineas if l.strip() and not l.strip().startswith("#")]
