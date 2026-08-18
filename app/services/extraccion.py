"""Orquesta la extracción entre los proveedores disponibles: Gemini y Groq
se lanzan en simultáneo (no uno primero y el otro como respaldo) — se usa
la que responda primero con éxito. Decisión del CEO 2026-08-19: priorizar
la experiencia de usuario (que ande rápido) sobre la eficiencia de cómputo
(se duplica la llamada en cada foto, no solo cuando una falla) — con el
volumen actual de la app el costo extra es insignificante. Si en algún
momento esto escala, revisar."""
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from app.services.gemini import extract_invoice
from app.services.groq_extract import extract_invoice_groq


def extraer_con_carrera(image_bytes: bytes, mime_type: str) -> tuple[dict, dict, str]:
    """Devuelve (fields, tiempos, proveedor_usado). Lanza extract_invoice
    (Gemini) y extract_invoice_groq (Groq) en threads separados y devuelve
    la primera que termine CON ÉXITO — si la más rápida falla, sigue
    esperando a la otra antes de rendirse. Si ambas fallan, relanza el
    error de Gemini (ya trae el mensaje amigable pensado para el usuario,
    ver GeminiSobrecargadoError). No usa `with` sobre el executor: haría
    que la función bloquee hasta que la thread perdedora también termine
    (el `__exit__` por default espera a todas) — acá se descarta con
    `shutdown(wait=False)` para no perder el beneficio de la carrera."""
    t_inicio = time.monotonic()
    ex = ThreadPoolExecutor(max_workers=2)
    futuros = {
        ex.submit(extract_invoice, image_bytes, mime_type): "gemini",
        ex.submit(extract_invoice_groq, image_bytes, mime_type): "groq (carrera)",
    }
    try:
        error_gemini = None
        error_groq = None
        pendientes = set(futuros)
        while pendientes:
            listos, pendientes = wait(pendientes, return_when=FIRST_COMPLETED)
            for futuro in listos:
                proveedor = futuros[futuro]
                try:
                    fields, tiempos_proveedor = futuro.result()
                except Exception as e:
                    if proveedor == "gemini":
                        error_gemini = e
                    else:
                        error_groq = e
                    continue
                tiempos_proveedor = dict(tiempos_proveedor)
                tiempos_proveedor["duracion_carrera"] = time.monotonic() - t_inicio
                return fields, tiempos_proveedor, proveedor
        raise error_gemini from error_groq
    finally:
        ex.shutdown(wait=False)
