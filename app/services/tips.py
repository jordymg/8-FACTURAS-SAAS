"""Tips que se muestran rotando en la home (ADR-0004 área App) y, a futuro,
en la pantalla de espera (ADR-0005 general) — misma fuente para ambos.
Editable sin tocar código: ver strings/tips.txt."""

import os

_TIPS_PATH = os.path.join(os.path.dirname(__file__), "../../strings/tips.txt")


def get_tips() -> list[str]:
    """Lee strings/tips.txt: un tip por línea, ignora vacías y comentarios
    (#). Si el archivo falta, está vacío, o tiene algún problema de
    lectura, devuelve una lista vacía — nunca rompe la home."""
    try:
        with open(os.path.normpath(_TIPS_PATH), encoding="utf-8") as f:
            lineas = f.readlines()
    except OSError:
        return []
    return [l.strip() for l in lineas if l.strip() and not l.strip().startswith("#")]
