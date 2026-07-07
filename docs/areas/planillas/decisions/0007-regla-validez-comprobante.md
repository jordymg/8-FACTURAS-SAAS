# ADR-0007 (planillas): Regla de validez del comprobante y manejo de duda

**Date:** 2026-07-06
**Status:** ADOPTADA — corrige la regla de CAE del ADR-0005

## Contexto
La regla del ADR-0005 ("si la IA no detecta CAE → Tipo Factura = X") produjo
un falso positivo en producción: un Ticket A perfectamente válido fue
catalogado como comprobante en negro. La causa es de dominio, no de código:
el CAE no es la única evidencia de autorización de un comprobante argentino.
Existen al menos cuatro vías: CAE (factura electrónica), CAEA (autorización
anticipada), controlador fiscal homologado (tickets y tique-facturas, sin
CAE) y CAI (talonarios impresos).

## Decisión
La regla pasa a ser: **Tipo Factura = "X" solo si la IA no detecta NINGUNA**
evidencia de autorización (ni CAE, ni CAEA, ni CAI, ni marcas de controlador
fiscal — logo fiscal / código de equipo).

**Ante la duda, la IA nunca elige un valor.** Si no puede determinar con
certeza si el comprobante está autorizado (foto cortada, marca ilegible,
caso ambiguo), el campo Tipo Factura queda vacío y el formulario de revisión
lo muestra resaltado en rojo, con la indicación de que el usuario debe
revisarlo y completarlo antes de guardar.

Este **principio de duda** (vacío + rojo + revisión obligatoria del usuario)
queda establecido como regla general del formulario de revisión, aplicable a
cualquier campo donde la extracción no tenga certeza — no solo Tipo Factura.

## Alternativas consideradas
- Duda → "X" igual (comportamiento actual): descartada, genera falsos
  comprobantes en negro sobre documentos válidos.
- Duda → dejar la letra impresa y marcar para revisión: descartada, la letra
  impresa puede no corresponder a un comprobante autorizado; la IA estaría
  eligiendo un valor sin certeza.

## Consecuencias
- **Prompt de Gemini**: debe reconocer las 4 vías de autorización y devolver,
  además del valor, una señal de certeza/duda por campo (o al menos para
  Tipo Factura) — el esquema de respuesta cambia.
- **Frontend (formulario de revisión)**: nuevo estado visual "campo en duda"
  (vacío + rojo) que bloquea el guardado hasta que el usuario lo complete.
- **`docs/ISSUES.md`**: loguear el caso del Ticket A como issue (lo encontró
  el uso real; causa de dominio fiscal que puede volver a morder).
- **Prevención**: armar un set de casos de prueba del prompt (factura
  electrónica A/B/C, ticket consumidor final, tique-factura A, comprobante
  con CAI, presupuesto sin autorización) para validar la regla en cada
  cambio futuro del prompt.
