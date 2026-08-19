"""Orquesta la extracción entre los proveedores disponibles — se lanzan
TODOS en simultáneo (no uno primero y los demás como respaldo) y se usa el
que responda primero con éxito. Decisión del CEO 2026-08-19: priorizar la
experiencia de usuario (que ande rápido y a la primera) sobre la
eficiencia de cómputo — con el volumen actual de la app, duplicar (ahora
cuadruplicar) la llamada en cada foto es un costo aceptable. Sumado el
mismo día: Mistral y OpenRouter, tras un caso real donde Gemini agotó su
cuota diaria gratis y Groq falló al mismo tiempo — más proveedores en la
carrera significa que hacen falta que TODOS fallen a la vez para que el
usuario vea un error."""
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from app.services.gemini import MENSAJE_ERROR_FINAL, extract_invoice
from app.services.groq_extract import extract_invoice_groq
from app.services.mistral_extract import extract_invoice_mistral
from app.services.openrouter_extract import extract_invoice_openrouter

PROVEEDORES = {
    "gemini": extract_invoice,
    "groq (carrera)": extract_invoice_groq,
    "mistral (carrera)": extract_invoice_mistral,
    "openrouter (carrera)": extract_invoice_openrouter,
}


class TodosLosProveedoresFallaronError(Exception):
    """Se levanta cuando los 4 proveedores de PROVEEDORES fallan en la
    misma foto. str(self) da el mensaje amigable ya aprobado para mostrar
    al usuario (MENSAJE_ERROR_FINAL) — NUNCA el error crudo de ningún
    proveedor (podría traer nombres de modelo o mensajes técnicos, contra
    ADR-0009 "nunca mencionar IA"). El detalle real de cada proveedor
    queda en .errores, para que app/blueprints/api.py lo loguee sin
    mostrárselo al usuario."""

    def __init__(self, errores: dict[str, Exception]):
        super().__init__(MENSAJE_ERROR_FINAL)
        self.errores = errores


def extraer_con_carrera(image_bytes: bytes, mime_type: str) -> tuple[dict, dict, str]:
    """Devuelve (fields, tiempos, proveedor_usado). Lanza los proveedores
    de PROVEEDORES en threads separados y devuelve el primero que termine
    CON ÉXITO — si el más rápido falla, sigue esperando a los demás antes
    de rendirse. Si todos fallan, levanta TodosLosProveedoresFallaronError.
    No usa `with` sobre el executor: haría que la función bloquee hasta
    que las threads perdedoras también terminen (el `__exit__` por default
    espera a todas) — acá se descarta con `shutdown(wait=False)` para no
    perder el beneficio de la carrera."""
    t_inicio = time.monotonic()
    ex = ThreadPoolExecutor(max_workers=len(PROVEEDORES))
    futuros = {ex.submit(fn, image_bytes, mime_type): nombre for nombre, fn in PROVEEDORES.items()}
    try:
        errores: dict[str, Exception] = {}
        pendientes = set(futuros)
        while pendientes:
            listos, pendientes = wait(pendientes, return_when=FIRST_COMPLETED)
            for futuro in listos:
                proveedor = futuros[futuro]
                try:
                    fields, tiempos_proveedor = futuro.result()
                except Exception as e:
                    errores[proveedor] = e
                    continue
                tiempos_proveedor = dict(tiempos_proveedor)
                tiempos_proveedor["duracion_carrera"] = time.monotonic() - t_inicio
                return fields, tiempos_proveedor, proveedor
        raise TodosLosProveedoresFallaronError(errores)
    finally:
        ex.shutdown(wait=False)
