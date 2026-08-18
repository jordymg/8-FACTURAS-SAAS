"""Chequeos de consistencia sobre los campos ya extraídos (por cualquier
proveedor de IA) — no vuelven a llamar a ningún servicio externo, son
aritmética simple sobre lo que ya se extrajo. Complementan, no reemplazan,
la incertidumbre que ya marca la propia IA (ADR-0008)."""

_CAMPOS_QUE_SUMAN_AL_TOTAL = ["neto", "iva_105", "iva_21", "iva_27", "otros_impuestos", "imp_internos"]
_TOLERANCIA_PESOS = 1.0  # margen por redondeo — no es una fuente de verdad, solo una señal


def _a_numero(valor) -> float:
    return float(str(valor or "0").strip().replace(",", "."))


def chequear_total(fields: dict, inciertos: list[str]) -> list[str]:
    """Si neto + IVAs + otros impuestos + imp. internos no suma el total
    (con margen de redondeo), marca 'total' como campo incierto — misma
    señal visual (tarjeta roja) que usa la IA para sus propias dudas, para
    que la persona lo revise antes de guardar. Si algún campo no es
    numérico o falta el total, no se puede chequear: no bloquea nada."""
    try:
        suma = sum(_a_numero(fields.get(c)) for c in _CAMPOS_QUE_SUMAN_AL_TOTAL)
        total = _a_numero(fields.get("total"))
    except ValueError:
        return inciertos
    if total and abs(suma - total) > _TOLERANCIA_PESOS and "total" not in inciertos:
        return inciertos + ["total"]
    return inciertos
